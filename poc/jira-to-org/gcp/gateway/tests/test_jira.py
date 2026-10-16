import json

import httpx

from app.jira import JiraClient, acceptance_criteria, adf_to_text, simplify, text_to_adf


def client(handler):
    return JiraClient("https://x.atlassian.net", "me@x.com", "tok", "KAN", transport=httpx.MockTransport(handler))


def test_adf_round_trip_and_acceptance_criteria():
    doc = {"type": "doc", "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "As a rep I want a score."}]},
        {"type": "heading", "content": [{"type": "text", "text": "Acceptance Criteria"}]},
        {"type": "bulletList", "content": [
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Score 0-100"}]}]},
            {"type": "listItem", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Shown on Account"}]}]}]}]}
    text = adf_to_text(doc)
    assert acceptance_criteria(text) == ["Score 0-100", "Shown on Account"]
    assert adf_to_text(text_to_adf("one\ntwo\n\nthree")).split() == ["one", "two", "three"]


def test_search_uses_the_jql_endpoint_and_pages():
    pages = [{"issues": [{"key": "KAN-1", "fields": {}}], "nextPageToken": "p2"},
             {"issues": [{"key": "KAN-2", "fields": {}}], "isLast": True}]
    seen = []

    def handler(req: httpx.Request):
        assert req.url.path == "/rest/api/3/search/jql"
        seen.append(json.loads(req.content))
        return httpx.Response(200, json=pages[len(seen) - 1])

    keys = [i["key"] for i in client(handler).search("project = KAN", 10)]
    assert keys == ["KAN-1", "KAN-2"] and seen[1]["nextPageToken"] == "p2"


def test_transition_matches_name_or_target_status_and_tolerates_absence():
    posted = []

    def handler(req: httpx.Request):
        if req.method == "GET":
            return httpx.Response(200, json={"transitions": [
                {"id": "21", "name": "Start work", "to": {"name": "In Progress"}},
                {"id": "31", "name": "Done", "to": {"name": "Done"}}]})
        posted.append(json.loads(req.content))
        return httpx.Response(204)

    c = client(handler)
    assert c.transition("KAN-1", "in progress") == "In Progress"
    assert posted == [{"transition": {"id": "21"}}]
    assert c.transition("KAN-1", "In Review") is None


def test_simplify_flattens_links_and_comments():
    raw = {"key": "KAN-3", "fields": {
        "summary": "S", "status": {"name": "To Do"}, "issuetype": {"name": "Story"},
        "issuelinks": [{"type": {"outward": "blocks"}, "outwardIssue": {"key": "KAN-4", "fields": {"summary": "T"}}}],
        "comment": {"comments": [{"body": text_to_adf("looks good")}]}}}
    t = simplify(raw, "u")
    assert t["links"] == [{"key": "KAN-4", "relation": "blocks", "summary": "T"}]
    assert t["recent_comments"] == ["looks good"]
