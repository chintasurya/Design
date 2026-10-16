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
              on_line: Callable[[str], None]) -> dict:
    """Run `codex exec` in the workspace. Codex gets no Salesforce or Jira
    credential: its environment is PATH and its own home, nothing else. The
    gateway, not Codex, deploys - and only after validation and approval."""
    conn.require()
    s = conn.settings
    last = os.path.join(workspace, ".codex-last-message.txt")
    cmd = [s.codex_bin, "exec", "--json", "--skip-git-repo-check", "--ephemeral",
           "-C", workspace, "-s", s.codex_sandbox, "-o", last,
           "-c", 'approval_policy="never"', "-c", 'shell_environment_policy.inherit="core"']
    if s.codex_model:
        cmd += ["-m", s.codex_model]
    cmd.append("-")
    env = {"PATH": os.environ.get("PATH", ""), "HOME": conn.codex_home(), "CODEX_HOME": conn.codex_home(),
           "LANG": "C.UTF-8"}
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env, cwd=workspace)
    timer = threading.Timer(s.codex_timeout_s, proc.kill)
    timer.start()
    raw_tail: list[str] = []
    try:
        assert proc.stdin and proc.stdout
        proc.stdin.write(prompt)
        proc.stdin.close()
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                summary = summarize_event(json.loads(line))
            except json.JSONDecodeError:
                summary = None
                raw_tail = (raw_tail + [line])[-20:]
            if summary:
                on_line(summary)
        code = proc.wait()
    finally:
        timer.cancel()
    final = ""
    if os.path.exists(last):
        with open(last, encoding="utf-8") as fh:
            final = fh.read().strip()
        os.remove(last)
    return {"exit_code": code, "final_message": final, "log_tail": "\n".join(raw_tail)}
