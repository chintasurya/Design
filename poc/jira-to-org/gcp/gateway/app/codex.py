"""Codex: the connection the LWC asks for first, and the CLI the Developer agent drives.

One OpenAI API key serves both agents:

* the Requirement agent calls the Responses API with function tools;
* the Developer agent runs the Codex CLI (`codex exec`) in a scratch SFDX
  workspace, logged in with the same key.

The key lives in Secret Manager. If the LWC supplies one at connect time it is
verified first and only then written as a new secret version; it is never
stored in Salesforce and never logged.
"""
from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from typing import Callable

import httpx

from .config import Settings, secret

OPENAI_API = "https://api.openai.com/v1"
# Tried in order when OPENAI_MODEL is not set; the first one the key can use wins.
MODEL_PREFERENCE = ("gpt-5.3-codex", "gpt-5.2-codex", "gpt-5.1-codex-max", "gpt-5.1-codex",
                    "gpt-5-codex", "gpt-5.2", "gpt-5.1", "gpt-5")


# Codex's built-in coding-agent instructions, tool definitions and environment
# block are ~13k input tokens on every call, measured live. The agents here
# need almost none of that, so each run replaces the instructions with its own
# short file and switches off what it does not use.
LEAN_COMMON = ["--disable", "apps", "--disable", "plugins", "--disable", "multi_agent",
               "-c", 'web_search="disabled"', "-c", "include_environment_context=false",
               "-c", "project_doc_max_bytes=0"]
# Both agents: everything is in the message, so no tools at all (each tool turn
# re-sends the whole context).
# Measured against a capture server (codex-cli 0.163.0): these cut what Codex adds
# to every request from ~1.9k tokens to 0: goals/image/user-input tools, the bundled
# skills list, and the permissions/apps/collaboration-mode text.
LEAN_NO_TOOLS = LEAN_COMMON + ["--disable", "shell_tool", "--disable", "unified_exec",
                               "--disable", "apply_patch_freeform", "--disable", "goals", "--disable", "view_image",
                               "--disable", "default_mode_request_user_input",
                               "-c", "tools.experimental_request_user_input.enabled=false",
                               "-c", "skills.bundled.enabled=false",
                               "-c", "include_skill_instructions=false", "-c", "include_permissions_instructions=false",
                               "-c", "include_apps_instructions=false",
                               "-c", "include_collaboration_mode_instructions=false",
                               "-c", 'model_reasoning_effort="low"', "-c", 'model_reasoning_summary="none"']


class CodexNotConnectedError(RuntimeError):
    pass


class CodexConnection:
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.settings = settings
        self.transport = transport
        self._key = secret("OPENAI_API_KEY")
        self.model: str | None = None
        self.connected_at: float | None = None
        self.cli_version: str | None = None
        self._lock = threading.Lock()

    @property
    def key_configured(self) -> bool:
        return bool(self._key)

    @property
    def connected(self) -> bool:
        return self.connected_at is not None and self.model is not None

    def require(self) -> None:
        if not self.connected:
            raise CodexNotConnectedError("Connect to Codex first")

    def api_key(self) -> str:
        self.require()
        return self._key

    def status(self) -> dict:
        return {"connected": self.connected, "keyConfigured": self.key_configured, "model": self.model,
                "codexCli": self.cli_version, "connectedAt": self.connected_at}

    # -- connect -------------------------------------------------------------
    def connect(self, api_key: str | None = None) -> dict:
        candidate = (api_key or "").strip() or self._key
        if not candidate:
            return {**self.status(), "connected": False, "needsKey": True,
                    "message": "No OpenAI API key is configured on the gateway. Paste one to connect."}
        with httpx.Client(timeout=20, transport=self.transport) as http:
            res = http.get(f"{OPENAI_API}/models", headers={"Authorization": f"Bearer {candidate}"})
        if res.status_code == 401:
            return {**self.status(), "connected": False, "needsKey": True,
                    "message": "OpenAI rejected the key (401). Check it and try again."}
        if res.status_code >= 300:
            return {**self.status(), "connected": False,
                    "message": f"OpenAI returned {res.status_code}: {res.text[:200]}"}
        available = {m["id"] for m in res.json().get("data", [])}
        model = self._pick_model(available)
        if not model:
            return {**self.status(), "connected": False,
                    "message": (f"Model {self.settings.openai_model} is not available to this key."
                                if self.settings.openai_model else
                                "None of the Codex-capable models are available to this key.")}
        with self._lock:
            if api_key and candidate != self._key:
                self._persist(candidate)
            self._key = candidate
            self.model = model
            self.cli_version = self._codex_login(candidate)
            self.connected_at = time.time()
        return {**self.status(), "message": f"Connected to Codex ({model})."}

    def _pick_model(self, available: set[str]) -> str | None:
        if self.settings.openai_model:
            return self.settings.openai_model if self.settings.openai_model in available else None
        return next((m for m in MODEL_PREFERENCE if m in available), None)

    def _persist(self, key: str) -> None:
        if not self.settings.gcp_project:
            return
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        parent = client.secret_path(self.settings.gcp_project, "openai-api-key")
        client.add_secret_version(request={"parent": parent, "payload": {"data": key.encode()}})

    # -- Codex CLI -----------------------------------------------------------
    def codex_home(self) -> str:
        # outside /tmp: Codex refuses to create its helper binaries under it
        home = self.settings.codex_home
        os.makedirs(home, exist_ok=True)
        return home

    def _codex_login(self, key: str) -> str | None:
        """Log the CLI in with the key. A missing CLI is reported, not fatal:
        the Requirement agent works without it."""
        env = {"PATH": os.environ.get("PATH", ""), "HOME": self.codex_home(), "CODEX_HOME": self.codex_home()}
        try:
            version = subprocess.run([self.settings.codex_bin, "--version"], capture_output=True, text=True,
                                     timeout=30, env=env).stdout.strip()
            subprocess.run([self.settings.codex_bin, "login", "--with-api-key"], input=key, capture_output=True,
                           text=True, timeout=60, env=env, check=True)
            return version or "unknown"
        except (OSError, subprocess.SubprocessError):
            return None

    def openai_client(self):
        from openai import OpenAI

        return OpenAI(api_key=self.api_key(), timeout=180)


def summarize_event(event: dict) -> str | None:
    """One line per `codex exec --json` event worth showing; None for noise."""
    kind = event.get("type", "")
    item = event.get("item") or {}
    if kind == "item.completed":
        it = item.get("type", "")
        if it == "agent_message":
            return f"codex: {str(item.get('text', ''))[:300]}"
        if it == "command_execution":
            return f"ran `{str(item.get('command', ''))[:200]}` (exit {item.get('exit_code')})"
        if it == "file_change":
            changes = item.get("changes") or []
            return "edited " + ", ".join(f"{c.get('path')} ({c.get('kind')})" for c in changes)[:300]
        return None
    if kind == "turn.completed":
        usage = event.get("usage") or {}
        return f"turn completed · tokens in {usage.get('input_tokens')} out {usage.get('output_tokens')}"
    if kind in {"turn.failed", "error"}:
        return f"codex error: {json.dumps(event)[:300]}"
    return None


def run_codex(conn: CodexConnection, workspace: str, prompt: str,
              on_line: Callable[[str], None], home: str | None = None, sandbox: str | None = None,
              output_schema: dict | None = None, instructions: str | None = None,
              extra_args: list[str] | None = None, timeout_s: int | None = None) -> dict:
    """Run `codex exec` in the workspace. Codex gets no Salesforce or Jira
    credential: its environment is PATH and its own home, nothing else. The
    gateway, not Codex, deploys - and only after validation and approval.

    `home` is a developer's own signed-in Codex home (ChatGPT sign-in mode);
    without it the gateway's API-key login is used."""
    if home is None:
        conn.require()
        home = conn.codex_home()
    s = conn.settings
    last = os.path.join(workspace, ".codex-last-message.txt")
    cmd = [s.codex_bin, "exec", "--json", "--skip-git-repo-check", "--ephemeral",
           "-C", workspace, "-s", sandbox or s.codex_sandbox, "-o", last,
           "-c", 'approval_policy="never"', "-c", 'shell_environment_policy.inherit="core"']
    if instructions:
        # outside the workspace, so it is never mistaken for part of the change set
        instr_path = os.path.join(home, f"instructions-{os.path.basename(workspace)}.md")
        with open(instr_path, "w", encoding="utf-8") as fh:
            fh.write(instructions)
        cmd += ["-c", f'model_instructions_file="{instr_path}"']
    cmd += extra_args or []
    if output_schema is not None:
        schema_path = os.path.join(workspace, ".codex-output-schema.json")
        with open(schema_path, "w", encoding="utf-8") as fh:
            json.dump(output_schema, fh)
        cmd += ["--output-schema", schema_path]
    if s.codex_model:
        cmd += ["-m", s.codex_model]
    cmd.append("-")
    env = {"PATH": os.environ.get("PATH", ""), "HOME": home, "CODEX_HOME": home, "LANG": "C.UTF-8"}
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env, cwd=workspace)
    timer = threading.Timer(timeout_s or s.codex_timeout_s, proc.kill)
    timer.start()
    raw_tail: list[str] = []
    usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0, "turns": 0}
    try:
        assert proc.stdin and proc.stdout
        proc.stdin.write(prompt)
        proc.stdin.close()
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                raw_tail = (raw_tail + [line])[-20:]
                continue
            if event.get("type") == "turn.completed":
                u = event.get("usage") or {}
                for k in ("input_tokens", "cached_input_tokens", "output_tokens"):
                    usage[k] += int(u.get(k) or 0)
                usage["turns"] += 1
            summary = summarize_event(event)
            if summary:
                on_line(summary)
                if summary.startswith("codex error"):
                    raw_tail = (raw_tail + [summary])[-20:]  # so a failed call says why
        code = proc.wait()
    finally:
        timer.cancel()
    final = ""
    if os.path.exists(last):
        with open(last, encoding="utf-8") as fh:
            final = fh.read().strip()
        os.remove(last)
    return {"exit_code": code, "final_message": final, "log_tail": "\n".join(raw_tail), "usage": usage}
