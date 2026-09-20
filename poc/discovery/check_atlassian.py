#!/usr/bin/env python3
"""
Verify whether one Atlassian API token reaches both Jira and Confluence,
and inventory the pod's projects and spaces.

Credentials come from the environment. Never pass them on the command line,
where they land in shell history and process listings.

    export ATLASSIAN_SITE=your-site            # the bit before .atlassian.net
    export ATLASSIAN_EMAIL=svc-ai@example.com
    export ATLASSIAN_TOKEN=...                 # id.atlassian.com > Security > API tokens

    python3 check_atlassian.py --project-key NSVC --space-key NSDOCS
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

TIMEOUT = 30


def call(base, path, auth, params=None):
    url = base + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": "Basic " + auth,
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")[:300]
    except Exception as e:                                  # noqa: BLE001
        return 0, str(e)


def show(label, status, ok_note="", fail_hint=""):
    mark = "PASS" if 200 <= status < 300 else "FAIL"
    print("  [%s] %-34s HTTP %s  %s" % (mark, label, status or "---",
                                        ok_note if mark == "PASS" else fail_hint))
    return 200 <= status < 300


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-key", help="Jira project key for the pod, e.g. NSVC")
    ap.add_argument("--space-key", help="Confluence space key for the pod")
    args = ap.parse_args()

    site = os.environ.get("ATLASSIAN_SITE")
    email = os.environ.get("ATLASSIAN_EMAIL")
    token = os.environ.get("ATLASSIAN_TOKEN")
    if not all([site, email, token]):
        sys.exit("Set ATLASSIAN_SITE, ATLASSIAN_EMAIL and ATLASSIAN_TOKEN first.")

    base = "https://%s.atlassian.net" % site
    auth = base64.b64encode(("%s:%s" % (email, token)).encode()).decode()
    print("\nSite: %s\nUser: %s\n" % (base, email))

    print("[1] Identity")
    status, body = call(base, "/rest/api/3/myself", auth)
    show("Jira: who am I", status,
         ok_note=body.get("displayName", "") if isinstance(body, dict) else "",
         fail_hint="token or email is wrong")

    print("\n[2] Product access on the same token")
    status, body = call(base, "/rest/api/3/project/search", auth, {"maxResults": 1})
    jira_ok = show("Jira: list projects", status,
                   fail_hint="account lacks Jira access")

    status, body = call(base, "/wiki/rest/api/space", auth, {"limit": 1})
    conf_ok = show("Confluence: list spaces", status,
                   fail_hint="no Confluence licence on this account, or wrong site")

    print("\n[3] Pod scope")
    if args.project_key:
        status, body = call(base, "/rest/api/3/search/jql", auth,
                            {"jql": "project = %s ORDER BY updated DESC" % args.project_key,
                             "maxResults": 1, "fields": "key"})
        if status == 404 or status == 410:
            status, body = call(base, "/rest/api/3/search", auth,
                                {"jql": "project = %s" % args.project_key,
                                 "maxResults": 1, "fields": "key"})
        total = body.get("total") if isinstance(body, dict) else None
        show("Jira project %s" % args.project_key, status,
             ok_note="%s issues" % total if total is not None else "reachable",
             fail_hint="project key wrong, or no browse permission")

    if args.space_key:
        status, body = call(base, "/wiki/rest/api/content", auth,
                            {"spaceKey": args.space_key, "limit": 1, "type": "page"})
        total = body.get("size") if isinstance(body, dict) else None
        show("Confluence space %s" % args.space_key, status,
             ok_note="reachable" if total is not None else "",
             fail_hint="space key wrong, or space permissions exclude this account")

    print("\n" + "=" * 62)
    if jira_ok and conf_ok:
        print("One token covers both. Jira credentials alone are enough.")
    elif jira_ok and not conf_ok:
        print("Jira works, Confluence does not. The account almost certainly")
        print("has no Confluence licence. Ask for Confluence product access on")
        print("this same account rather than a second token.")
    else:
        print("Jira itself failed. Fix the site, email or token before Confluence.")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()
