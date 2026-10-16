"""Salesforce REST/Tooling client.

Two ways in, both against the org's My Domain:

* **SFDX auth URL** (`SF_AUTH_URL`, `force://<client id>:<secret>:<refresh token>@<host>`):
  the refresh-token grant on the login a person approved in the browser.
  This is how the POC runs: no app to create in Setup.
* **Client credentials** (`SF_CLIENT_ID` + `SF_CLIENT_SECRET`): an External
  Client App with a Run As user, so the gateway holds no refresh token. The
  token endpoint must be My Domain: the generic login hosts reject this flow
  with `request not supported on this domain`.
"""
from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote

import httpx


class SalesforceError(RuntimeError):
    pass


class SalesforceClient:
    TOKEN_TTL_S = 25 * 60

    def __init__(self, login_url: str, client_id: str, client_secret: str = "",
                 api_version: str = "62.0", transport: httpx.BaseTransport | None = None,
                 refresh_token: str = ""):
        if not (login_url and client_id and (client_secret or refresh_token)):
            raise SalesforceError("Salesforce is not configured (SF_AUTH_URL, or SF_LOGIN_URL + "
                                  "SF_CLIENT_ID + SF_CLIENT_SECRET)")
        self.login_url = login_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.api_version = api_version
        self.transport = transport
        self._token: str | None = None
        self._instance_url: str | None = None
        self._token_at = 0.0

    @classmethod
    def from_auth_url(cls, auth_url: str, api_version: str = "62.0",
                      transport: httpx.BaseTransport | None = None) -> "SalesforceClient":
        match = re.match(r"^force://([^:]+):([^:]*):([^@]+)@(.+)$", auth_url.strip())
        if not match:
            raise SalesforceError("SF_AUTH_URL is not an SFDX auth URL (force://id:secret:token@host)")
        client_id, secret, token, host = match.groups()
        host = host if host.startswith("http") else f"https://{host}"
        return cls(host, client_id, secret, api_version, transport, refresh_token=token)

    # -- auth ---------------------------------------------------------------
    def _authenticate(self) -> None:
        if self.refresh_token:
            data = {"grant_type": "refresh_token", "client_id": self.client_id,
                    "refresh_token": self.refresh_token}
            if self.client_secret:
                data["client_secret"] = self.client_secret
        else:
            data = {"grant_type": "client_credentials",
                    "client_id": self.client_id, "client_secret": self.client_secret}
        with httpx.Client(timeout=30, transport=self.transport) as http:
            res = http.post(f"{self.login_url}/services/oauth2/token", data=data)
        if res.status_code != 200:
            raise SalesforceError(f"Salesforce token request failed ({res.status_code}): {res.text[:300]}")
        body = res.json()
        self._token = body["access_token"]
        self._instance_url = body.get("instance_url", self.login_url).rstrip("/")
        self._token_at = time.time()

    def session(self) -> tuple[str, str]:
        """(access_token, instance_url), refreshed when stale."""
        if not self._token or time.time() - self._token_at > self.TOKEN_TTL_S:
            self._authenticate()
        return self._token, self._instance_url  # type: ignore[return-value]

    # -- http ---------------------------------------------------------------
    def _request(self, method: str, path: str, **kw: Any) -> dict:
        for attempt in (1, 2):
            token, instance = self.session()
            url = path if path.startswith("http") else f"{instance}{path}"
            with httpx.Client(timeout=60, transport=self.transport) as http:
                res = http.request(method, url, headers={"Authorization": f"Bearer {token}"}, **kw)
            if res.status_code == 401 and attempt == 1:
                self._token = None
                continue
            if res.status_code >= 300:
                raise SalesforceError(f"Salesforce {method} {path[:120]} -> {res.status_code}: {res.text[:400]}")
            return res.json() if res.content else {}
        raise SalesforceError("unreachable")

    def _paged(self, path: str) -> list[dict]:
        page = self._request("GET", path)
        records = list(page.get("records", []))
        while not page.get("done", True) and page.get("nextRecordsUrl"):
            page = self._request("GET", page["nextRecordsUrl"])
            records.extend(page.get("records", []))
        return records

    def query(self, soql: str) -> list[dict]:
        return self._paged(f"/services/data/v{self.api_version}/query?q={quote(soql)}")

    def tooling_query(self, soql: str) -> list[dict]:
        return self._paged(f"/services/data/v{self.api_version}/tooling/query?q={quote(soql)}")

    def describe_global(self) -> list[dict]:
        return self._request("GET", f"/services/data/v{self.api_version}/sobjects").get("sobjects", [])

    def describe(self, sobject: str) -> dict:
        return self._request("GET", f"/services/data/v{self.api_version}/sobjects/{sobject}/describe")

    def userinfo(self) -> dict:
        return self._request("GET", "/services/oauth2/userinfo")
