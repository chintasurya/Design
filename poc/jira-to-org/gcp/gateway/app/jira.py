"""Jira Cloud REST v3 client: read tickets, comment, transition.

Uses `POST /rest/api/3/search/jql`; the old `/rest/api/3/search` endpoint was
retired by Atlassian in 2025.
"""
from __future__ import annotations

import re
from typing import Any

import httpx

TICKET_KEY = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d+)\b")

ISSUE_FIELDS = [
    "summary", "description", "status", "issuetype", "priority", "labels",
    "components", "issuelinks", "parent", "subtasks", "comment", "assignee",
    "reporter", "created", "updated",
]


class JiraError(RuntimeError):
    pass


def adf_to_text(node: Any) -> str:
    """Flatten Atlassian Document Format to plain text, keeping list and heading breaks."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(adf_to_text(n) for n in node)
    kind = node.get("type")
    if kind == "text":
        return node.get("text", "")
    if kind == "hardBreak":
        return "\n"
    if kind in {"mention", "emoji"}:
        return node.get("attrs", {}).get("text", "")
    inner = adf_to_text(node.get("content", []))
    if kind == "listItem":
        return "- " + inner.strip() + "\n"
    if kind in {"paragraph", "heading", "codeBlock", "blockquote", "rule"}:
        return inner.strip() + "\n"
    if kind in {"bulletList", "orderedList", "table"}:
        return inner + "\n"
    if kind == "tableRow":
        return inner.strip() + "\n"
    if kind in {"tableCell", "tableHeader"}:
        return inner.strip() + " | "
    return inner


def text_to_adf(text: str) -> dict:
    paragraphs = [p for p in text.split("\n\n") if p.strip()] or [text]
    content = []
    for para in paragraphs:
        lines = para.split("\n")
        nodes: list[dict] = []
        for i, line in enumerate(lines):
            if i:
                nodes.append({"type": "hardBreak"})
            if line:
                nodes.append({"type": "text", "text": line})
        content.append({"type": "paragraph", "content": nodes})
    return {"type": "doc", "version": 1, "content": content}


def acceptance_criteria(description: str) -> list[str]:
    """Lines under an 'Acceptance Criteria' heading, if the ticket has one."""
    lines = description.splitlines()
    out: list[str] = []
    inside = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(acceptance criteria|ac)\s*:?\s*$", stripped, re.I):
            inside = True
            continue
        if inside:
            if not stripped:
                if out:
                    break
                continue
            if stripped.endswith(":") and not stripped.startswith("-"):
                break
            out.append(stripped.lstrip("-*• ").strip())
    return [o for o in out if o]


class JiraClient:
    def __init__(self, base_url: str, email: str, token: str, project_key: str,
                 transport: httpx.BaseTransport | None = None):
        if not (base_url and email and token):
            raise JiraError("Jira is not configured (JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN)")
        self.base_url = base_url.rstrip("/")
        self.project_key = project_key
        self.http = httpx.Client(
            base_url=self.base_url, auth=(email, token), timeout=30,
            headers={"Accept": "application/json"}, transport=transport,
        )

    def browse_url(self, key: str) -> str:
        return f"{self.base_url}/browse/{key}"

    def _check(self, res: httpx.Response) -> dict:
        if res.status_code >= 300:
            raise JiraError(f"Jira {res.request.method} {res.request.url.path} -> "
                            f"{res.status_code}: {res.text[:300]}")
        return res.json() if res.content else {}

    def myself(self) -> dict:
        return self._check(self.http.get("/rest/api/3/myself"))

    def get_issue(self, key: str) -> dict:
        return self._check(self.http.get(f"/rest/api/3/issue/{key}",
                                         params={"fields": ",".join(ISSUE_FIELDS)}))

    def search(self, jql: str, max_results: int = 25) -> list[dict]:
        issues: list[dict] = []
        token = None
        while len(issues) < max_results:
            body: dict[str, Any] = {
                "jql": jql, "fields": ISSUE_FIELDS,
                "maxResults": min(100, max_results - len(issues)),
            }
            if token:
                body["nextPageToken"] = token
            page = self._check(self.http.post("/rest/api/3/search/jql", json=body))
            issues.extend(page.get("issues", []))
            token = page.get("nextPageToken")
            if not token or page.get("isLast"):
                break
        return issues

    def project_issues(self, only_open: bool = False, max_results: int = 25) -> list[dict]:
        jql = f'project = "{self.project_key}"'
        if only_open:
            jql += " AND statusCategory != Done"
        return self.search(jql + " ORDER BY updated DESC", max_results)

    def add_comment(self, key: str, text: str) -> dict:
        return self._check(self.http.post(f"/rest/api/3/issue/{key}/comment",
                                          json={"body": text_to_adf(text)}))

    def transition(self, key: str, name: str) -> str | None:
        """Move the ticket to the transition (or target status) called `name`.

        Returns the status reached, or None when the workflow has no such
        transition from the current status. Never raises for a missing one:
        a board without an 'In Progress' column must not stop a deploy.
        """
        data = self._check(self.http.get(f"/rest/api/3/issue/{key}/transitions"))
        wanted = name.strip().lower()
        for t in data.get("transitions", []):
            if wanted in {t.get("name", "").lower(), t.get("to", {}).get("name", "").lower()}:
                self._check(self.http.post(f"/rest/api/3/issue/{key}/transitions",
                                           json={"transition": {"id": t["id"]}}))
                return t.get("to", {}).get("name", name)
        return None


def simplify(issue: dict, browse_url: str = "") -> dict:
    """The shape an agent sees: plain text, no ADF, no avatars."""
    f = issue.get("fields", {})
    description = adf_to_text(f.get("description")).strip()
    comments = f.get("comment", {}).get("comments", []) if f.get("comment") else []
    links = []
    for link in f.get("issuelinks", []) or []:
        other = link.get("outwardIssue") or link.get("inwardIssue") or {}
        direction = "outward" if "outwardIssue" in link else "inward"
        links.append({
            "key": other.get("key"),
            "relation": link.get("type", {}).get(direction, link.get("type", {}).get("name")),
            "summary": other.get("fields", {}).get("summary"),
        })
    return {
        "key": issue.get("key"),
        "url": browse_url,
        "summary": f.get("summary"),
        "type": (f.get("issuetype") or {}).get("name"),
        "status": (f.get("status") or {}).get("name"),
        "priority": (f.get("priority") or {}).get("name"),
        "labels": f.get("labels") or [],
        "components": [c.get("name") for c in f.get("components") or []],
        "assignee": (f.get("assignee") or {}).get("displayName"),
        "parent": (f.get("parent") or {}).get("key"),
        "subtasks": [s.get("key") for s in f.get("subtasks") or []],
        "links": links,
        "description": description,
        "acceptance_criteria": acceptance_criteria(description),
        "recent_comments": [adf_to_text(c.get("body")).strip() for c in comments[-5:]],
        "updated": f.get("updated"),
    }
