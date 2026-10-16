"""Per-developer Codex sign-in: each Salesforce user connects their own Codex.

"Connect to Codex" signs the developer in to their own ChatGPT / Codex
account (their plan, their workspace and SSO, their limits), in a Codex home
that belongs to that Salesforce user. Two flows:

* browser (default): `codex login` prints the normal OpenAI sign-in link and
  waits for the redirect on 127.0.0.1:1455 inside the gateway. The developer
  signs in (SSO works), their browser fails to open that localhost address,
  and they paste it into the console; the gateway replays it to the waiting
  CLI, which exchanges the code (PKCE: useless without that process) and
  writes `auth.json`. The CLI owns one fixed port, so one browser sign-in
  runs at a time per gateway instance.
* device: `codex login --device-auth` prints a link and a one-time code;
  this needs device-code sign-in enabled on the ChatGPT account.

Cloud Run instances are disposable, so each developer's `auth.json` is also
kept in Secret Manager (one secret, `codex-sessions`, holding a map keyed by a
hash of the Salesforce username) and restored on demand. Codex refreshes its
tokens during runs, so the file is saved back after every run.

The username is never used as a path or secret name: only its hash.
"""
from __future__ import annotations

import base64
import hashlib
import urllib.error
import urllib.parse
import urllib.request
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
USAGE_URL = "https://chatgpt.com/backend-api/wham/usage"  # what Codex's /status reads
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


def _window(w: Any) -> dict | None:
    if not isinstance(w, dict) or w.get("used_percent") is None:
        return None
    return {"used_percent": float(w["used_percent"]),
            "window_minutes": round(int(w.get("limit_window_seconds") or 0) / 60),
            "resets_at": w.get("reset_at")}


def parse_plan_usage(body: dict) -> dict:
    """The /wham/usage payload, reduced to what the dashboard shows."""
    rl = body.get("rate_limit") or {}
    cr = body.get("credits") or {}
    balance = cr.get("balance")
    try:
        balance = float(balance) if balance not in (None, "") else None
    except (TypeError, ValueError):
        balance = None
    return {"plan": body.get("plan_type"), "limit_reached": bool(rl.get("limit_reached")),
            "primary": _window(rl.get("primary_window")), "secondary": _window(rl.get("secondary_window")),
            "credits": {"has_credits": bool(cr.get("has_credits")), "unlimited": bool(cr.get("unlimited")),
                        "balance": balance},
            "at": now_iso()}


def _fetch_usage(access_token: str, account_id: str | None) -> dict:
    headers = {"Authorization": f"Bearer {access_token}", "originator": "codex_cli_rs",
               "User-Agent": "codex_cli_rs", "Accept": "application/json"}
    if account_id:
        headers["ChatGPT-Account-Id"] = account_id
    req = urllib.request.Request(USAGE_URL, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as res:
        return json.loads(res.read().decode())


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


def parse_browser_prompt(text: str) -> str | None:
    """`codex login` prints 'navigate to this URL to authenticate:' then the authorize URL."""
    for line in (ANSI.sub("", line).strip() for line in text.splitlines()):
        m = URL.search(line)
        if m and "/oauth/authorize" in m.group(0):
            return m.group(0)
    return None


def callback_target(auth_url: str, pasted: str) -> str:
    """The local address to replay the pasted redirect to, after checking it is
    the callback this login is waiting for and nothing else."""
    redirect = urllib.parse.parse_qs(urllib.parse.urlparse(auth_url).query).get("redirect_uri", [""])[0]
    expected = urllib.parse.urlparse(redirect)
    got = urllib.parse.urlparse(pasted.strip())
    if got.scheme != "http" or got.hostname not in {"localhost", "127.0.0.1"}:
        raise ValueError("Paste the address that starts with http://localhost:1455/auth/callback")
    if got.path != (expected.path or "/auth/callback") or (got.port or 80) != (expected.port or 1455):
        raise ValueError("That is not the Codex sign-in callback address")
    query = urllib.parse.parse_qs(got.query)
    if "error" in query:
        raise ValueError("Codex sign-in was refused: " + query.get("error_description", query["error"])[0])
    if not query.get("code") or not query.get("state"):
        raise ValueError("The address is missing its code; copy the whole address bar")
    return f"http://127.0.0.1:{expected.port or 1455}{got.path}?{got.query}"


def _replay(url: str) -> None:
    """GET the callback on the CLI's local server, then its local success page,
    which is what lets the CLI exit."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect)
    try:
        res = opener.open(url, timeout=60)
        location = res.headers.get("Location")
    except urllib.error.HTTPError as err:
        if err.code not in (301, 302, 303, 307, 308):
            raise RuntimeError(err.read().decode(errors="replace")[:300] or f"HTTP {err.code}") from err
        location = err.headers.get("Location")
    if location and urllib.parse.urlparse(location).hostname in {"localhost", "127.0.0.1"}:
        try:
            opener.open(location.replace("://localhost", "://127.0.0.1"), timeout=30).read()
        except Exception:  # noqa: BLE001 - the success page is a courtesy; auth.json is what matters
            pass


class _Login:
    def __init__(self, proc: Any, flow: str, user: str):
        self.proc = proc
        self.flow = flow
        self.user = user
        self.lines: list[str] = []
        self.started = time.time()
        self.ready = threading.Event()

    def text(self) -> str:
        return "".join(self.lines)

    def prompt_ready(self) -> bool:
        if self.flow == "browser":
            return parse_browser_prompt(self.text()) is not None
        return parse_device_prompt(self.text())[1] is not None

    def reader(self) -> None:
        for line in self.proc.stdout:
            self.lines.append(line)
            if self.prompt_ready():
                self.ready.set()
        self.ready.set()


def _spawn(cmd: list[str], env: dict) -> Any:
    return subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, env=env)


class CodexSessions:
    def __init__(self, settings: Settings, vault: SessionVault, spawn: Callable[[list[str], dict], Any] = _spawn,
                 replay: Callable[[str], None] = _replay,
                 fetch_usage: Callable[[str, str | None], dict] = _fetch_usage):
        self.s = settings
        self.flow = getattr(settings, "codex_login_flow", "device")
        self.vault = vault
        self.spawn = spawn
        self.replay = replay
        self.fetch_usage = fetch_usage
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
                if login.flow == "browser":
                    return {"mode": "chatgpt", "connected": False, "pending": True, "flow": "browser",
                            "authUrl": parse_browser_prompt(login.text()), "expiresAt": login.started + LOGIN_TTL_S,
                            "message": "Sign in to Codex with your account (SSO works), then paste the address "
                                       "your browser ends up on."}
                url, code = parse_device_prompt(login.text())
                return {"mode": "chatgpt", "connected": False, "pending": True, "flow": "device",
                        "verificationUrl": url, "userCode": code, "expiresAt": login.started + LOGIN_TTL_S,
                        "message": "Open the link, sign in to your Codex account and enter the code."}
            if login and login.proc.poll() is None:
                login.proc.kill()  # expired
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
            if self.flow == "browser":
                busy = [lg for lg in self._logins.values()
                        if lg.flow == "browser" and lg.proc.poll() is None
                        and time.time() - lg.started < LOGIN_TTL_S]
                if busy:
                    return {"mode": "chatgpt", "connected": False, "pending": False, "busy": True,
                            "message": "Another developer is signing in to Codex right now. "
                                       "Try again in a minute."}
            env = {"PATH": os.environ.get("PATH", ""), "HOME": self.home(user), "CODEX_HOME": self.home(user),
                   "LANG": "C.UTF-8", "BROWSER": "/bin/true"}  # nothing to open on a server
            cmd = [self.s.codex_bin, "login", "-c", 'cli_auth_credentials_store="file"']
            if self.flow != "browser":
                cmd.append("--device-auth")
            login = _Login(self.spawn(cmd, env), self.flow, user)
            self._logins[user_key(user)] = login
            threading.Thread(target=self._watch, args=(user, login), daemon=True).start()
        login.ready.wait(30)
        return self.status(user)

    def complete(self, user: str, pasted_url: str) -> dict:
        """Browser flow: replay the redirect the developer pasted to the waiting CLI."""
        with self._lock:
            login = self._logins.get(user_key(user))
            if not login or login.flow != "browser" or login.proc.poll() is not None:
                return {**self.status(user), "message": "No Codex sign-in is waiting. Click Connect to Codex again."}
            target = callback_target(parse_browser_prompt(login.text()) or "", pasted_url)
        self.replay(target)
        for _ in range(100):  # the CLI exchanges the code and writes auth.json
            if login.proc.poll() is not None:
                break
            time.sleep(0.2)
        with self._lock:
            if os.path.exists(self._auth_path(user)):
                self.save(user)
                self._logins.pop(user_key(user), None)
        return self.status(user)

    def _watch(self, user: str, login: _Login) -> None:
        login.reader()
        code = login.proc.wait()
        with self._lock:
            if code == 0 and os.path.exists(self._auth_path(user)):
                self.save(user)
                self._logins.pop(user_key(user), None)

    def plan_usage(self, user: str) -> dict | None:
        """The developer's Codex plan right now: % of the 5-hour and weekly
        limits used, and credits. None when it cannot be read (no session,
        expired token, endpoint unreachable); the dashboard says so."""
        if not self.connected(user):
            return None
        try:
            with open(self._auth_path(user), encoding="utf-8") as fh:
                tokens = (json.load(fh).get("tokens") or {})
            if not tokens.get("access_token"):
                return None
            return parse_plan_usage(self.fetch_usage(tokens["access_token"], tokens.get("account_id")))
        except Exception:  # noqa: BLE001 - usage is informational; a run never fails for it
            return None

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
