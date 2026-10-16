"""Per-developer Codex sign-in: each Salesforce user connects their own Codex.

"Connect to Codex" starts `codex login --device-auth` in a Codex home that
belongs to that Salesforce user. The CLI prints a link and a one-time code
(it expires after 15 minutes); the developer opens the link, signs in to
their own ChatGPT / Codex account (their plan, their workspace, their
limits) and enters the code. The CLI then finishes on its own and writes
`auth.json`.

Cloud Run instances are disposable, so each developer's `auth.json` is also
kept in Secret Manager (one secret, `codex-sessions`, holding a map keyed by a
hash of the Salesforce username) and restored on demand. Codex refreshes its
tokens during runs, so the file is saved back after every run.

The username is never used as a path or secret name: only its hash.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import threading
import time
from typing import Any, Callable, Protocol

from .config import Settings
from .graph.store import now_iso

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
URL = re.compile(r"https://\S+")
LOGIN_TTL_S = 15 * 60


class SessionVault(Protocol):
    def load(self) -> dict[str, dict]: ...
    def save(self, sessions: dict[str, dict]) -> None: ...


class MemoryVault:
    def __init__(self) -> None:
        self.data: dict[str, dict] = {}

    def load(self) -> dict[str, dict]:
        return json.loads(json.dumps(self.data))

    def save(self, sessions: dict[str, dict]) -> None:
        self.data = json.loads(json.dumps(sessions))


class SecretManagerVault:
    """All sessions in one secret; each save adds a version and destroys the
    previous one, so superseded refresh tokens do not linger."""

    def __init__(self, project: str, secret_id: str = "codex-sessions"):
        from google.cloud import secretmanager

        self.client = secretmanager.SecretManagerServiceClient()
        self.parent = self.client.secret_path(project, secret_id)

    def load(self) -> dict[str, dict]:
        try:
            res = self.client.access_secret_version(request={"name": f"{self.parent}/versions/latest"})
            data = json.loads(res.payload.data.decode() or "{}")
            return data if isinstance(data, dict) else {}
        except Exception:  # noqa: BLE001 - an unreadable vault means nobody is signed in yet
            return {}

    def save(self, sessions: dict[str, dict]) -> None:
        payload = json.dumps(sessions).encode()
        if len(payload) > 60_000:
            raise RuntimeError("codex-sessions is near Secret Manager's 64 KiB limit; sign some developers out")
        new = self.client.add_secret_version(request={"parent": self.parent, "payload": {"data": payload}})
        for v in self.client.list_secret_versions(request={"parent": self.parent, "filter": "state:ENABLED"}):
            if v.name != new.name:
                try:
                    self.client.destroy_secret_version(request={"name": v.name})
                except Exception:  # noqa: BLE001 - hygiene, not correctness
                    pass


def user_key(user: str) -> str:
    return hashlib.sha256(user.strip().lower().encode()).hexdigest()[:24]


def account_from_auth(auth_text: str) -> dict:
    """Email and plan from the id_token in auth.json. Display only: nothing is
    authorized on these claims, so the signature is not checked here."""
    try:
        tokens = json.loads(auth_text).get("tokens") or {}
        token = tokens.get("id_token")
        if isinstance(token, dict):
            token = token.get("raw_jwt") or ""
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        auth = claims.get("https://api.openai.com/auth") or {}
        return {"email": claims.get("email"), "plan": auth.get("chatgpt_plan_type")}
    except Exception:  # noqa: BLE001
        return {}


def parse_device_prompt(text: str) -> tuple[str | None, str | None]:
    """The CLI prints: '1. Open this link ...' / URL / '2. Enter this one-time code ...' / CODE."""
    lines = [ANSI.sub("", line).strip() for line in text.splitlines()]
    url = next((m.group(0) for line in lines for m in [URL.search(line)] if m), None)
    code = None
    for i, line in enumerate(lines):
        if "one-time code" in line.lower():
            code = next((nxt for nxt in lines[i + 1:] if nxt), None)
            break
    return url, code


class _Login:
    def __init__(self, proc: Any):
        self.proc = proc
        self.lines: list[str] = []
        self.started = time.time()
        self.ready = threading.Event()

    def reader(self) -> None:
        for line in self.proc.stdout:
            self.lines.append(line)
            if parse_device_prompt("".join(self.lines))[1]:
                self.ready.set()
        self.ready.set()


def _spawn(cmd: list[str], env: dict) -> Any:
    return subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env)


class CodexSessions:
    def __init__(self, settings: Settings, vault: SessionVault, spawn: Callable[[list[str], dict], Any] = _spawn):
        self.s = settings
        self.vault = vault
        self.spawn = spawn
        self._logins: dict[str, _Login] = {}
        self._cache: dict[str, dict] | None = None
        self._lock = threading.RLock()

    # -- storage -------------------------------------------------------------
    def home(self, user: str) -> str:
        path = os.path.join(self.s.codex_home, "users", user_key(user))
        os.makedirs(path, exist_ok=True)
        return path

    def _auth_path(self, user: str) -> str:
        return os.path.join(self.home(user), "auth.json")

    def _sessions(self) -> dict[str, dict]:
        if self._cache is None:
            self._cache = self.vault.load()
        return self._cache

    def _restore(self, user: str) -> bool:
        """Put the developer's auth.json back on this instance if it is missing."""
        path = self._auth_path(user)
        if os.path.exists(path):
            return True
        entry = self._sessions().get(user_key(user))
        if not entry or not entry.get("auth"):
            return False
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(entry["auth"])
        os.chmod(path, 0o600)
        return True

    def save(self, user: str) -> None:
        """Keep the latest auth.json (Codex refreshes tokens during runs)."""
        with self._lock:
            path = self._auth_path(user)
            if not os.path.exists(path):
                return
            with open(path, encoding="utf-8") as fh:
                auth = fh.read()
            sessions = self._sessions()
            key = user_key(user)
            if sessions.get(key, {}).get("auth") == auth:
                return
            sessions[key] = {"auth": auth, "saved_at": now_iso(), **account_from_auth(auth)}
            self.vault.save(sessions)

    # -- state -----------------------------------------------------------------
    def connected(self, user: str) -> bool:
        with self._lock:
            return bool(user) and self._restore(user)

    def require_home(self, user: str) -> str:
        if not self.connected(user):
            raise PermissionError("Connect to Codex first")
        return self.home(user)

    def status(self, user: str) -> dict:
        with self._lock:
            if self.connected(user):
                with open(self._auth_path(user), encoding="utf-8") as fh:
                    account = account_from_auth(fh.read())
                return {"mode": "chatgpt", "connected": True, "account": account,
                        "message": "Connected to your Codex account"
                                   + (f" ({account.get('email')})" if account.get("email") else "") + "."}
            login = self._logins.get(user_key(user))
            if login and login.proc.poll() is None and time.time() - login.started < LOGIN_TTL_S:
                url, code = parse_device_prompt("".join(login.lines))
                return {"mode": "chatgpt", "connected": False, "pending": True, "verificationUrl": url,
                        "userCode": code, "expiresAt": login.started + LOGIN_TTL_S,
                        "message": "Open the link, sign in to your Codex account and enter the code."}
            if login:
                tail = ANSI.sub("", "".join(login.lines)).strip().splitlines()[-3:]
                self._logins.pop(user_key(user), None)
                return {"mode": "chatgpt", "connected": False, "pending": False,
                        "message": "Codex sign-in did not finish: " + (" ".join(tail) or "it expired")}
            return {"mode": "chatgpt", "connected": False, "pending": False,
                    "message": "Not connected. Click Connect to Codex to sign in with your own Codex account."}

    def connect(self, user: str) -> dict:
        """Already signed in: say so. Otherwise start a device sign-in (or report the one in progress)."""
        with self._lock:
            current = self.status(user)
            if current["connected"] or current.get("pending"):
                return current
            env = {"PATH": os.environ.get("PATH", ""), "HOME": self.home(user), "CODEX_HOME": self.home(user),
                   "LANG": "C.UTF-8"}
            login = _Login(self.spawn([self.s.codex_bin, "login", "--device-auth"], env))
            self._logins[user_key(user)] = login
            threading.Thread(target=self._watch, args=(user, login), daemon=True).start()
        login.ready.wait(30)
        return self.status(user)

    def _watch(self, user: str, login: _Login) -> None:
        login.reader()
        code = login.proc.wait()
        with self._lock:
            if code == 0 and os.path.exists(self._auth_path(user)):
                self.save(user)
                self._logins.pop(user_key(user), None)

    def logout(self, user: str) -> dict:
        with self._lock:
            login = self._logins.pop(user_key(user), None)
            if login and login.proc.poll() is None:
                login.proc.kill()
            shutil.rmtree(self.home(user), ignore_errors=True)
            sessions = self._sessions()
            if sessions.pop(user_key(user), None) is not None:
                self.vault.save(sessions)
        return {"mode": "chatgpt", "connected": False, "message": "Signed out of Codex."}
