#!/usr/bin/env python3
"""Publish the guardrails pack to Firestore (the agents read it from there).

    GCP_PROJECT=jira-to-org-poc-2610 python3 load_guardrails.py [path/to/pack.json]

Writes one document per rule to `guardrail_rules` (area, title, rule,
severity, check, order) and the pack's name and summary to
`guardrail_packs/active`. Rules no longer in the file are deleted, so the file
stays the source of truth. Authenticates with `gcloud auth print-access-token`.
Edits made later in the Firestore console are picked up by the agents within
a minute; re-running this script overwrites them with the file.
"""
import json
import os
import subprocess
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT = os.path.join(HERE, "..", "gateway", "app", "guardrails", "ascension-guardrails.json")


def fs_value(v):
    if v is None:
        return {"nullValue": None}
    if isinstance(v, bool):
        return {"booleanValue": v}
    if isinstance(v, int):
        return {"integerValue": str(v)}
    return {"stringValue": str(v)}


def call(method, url, token, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as res:
        return json.loads(res.read() or b"{}")


def main():
    project = os.environ["GCP_PROJECT"]
    pack = json.load(open(sys.argv[1] if len(sys.argv) > 1 else DEFAULT))
    token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
    base = f"https://firestore.googleapis.com/v1/projects/{project}/databases/(default)/documents"
    for order, rule in enumerate(pack["rules"]):
        fields = {k: fs_value(rule.get(k)) for k in ("id", "area", "title", "rule", "severity", "check")}
        fields["order"] = fs_value(order)
        call("PATCH", f"{base}/guardrail_rules/{rule['id']}", token, {"fields": fields})
    keep = {r["id"] for r in pack["rules"]}
    listed = call("GET", f"{base}/guardrail_rules?pageSize=300", token).get("documents", [])
    removed = 0
    for doc in listed:
        if doc["name"].rsplit("/", 1)[-1] not in keep:
            call("DELETE", f"https://firestore.googleapis.com/v1/{doc['name']}", token)
            removed += 1
    call("PATCH", f"{base}/guardrail_packs/active", token,
         {"fields": {"name": fs_value(pack["name"]), "summary": fs_value(pack.get("summary", ""))}})
    print(f"published {len(pack['rules'])} rules to {project}/guardrail_rules ({removed} removed)")


if __name__ == "__main__":
    main()
