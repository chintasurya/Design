import os

import pytest

from app.agents.developer import (DeveloperAgent, DeveloperError, SalesforceCli, component_root, deploy_outcome,
                                  node_for_path)
from app.agents.requirement import RequirementAgent
from app.codex import CodexConnection
from app.graph.store import GraphService, LocalJsonStore
from app.runs import MemoryRunStore, RunContext

from .fakes import (FAILURE, SUCCESS, FakeCliRunner, FakeJira, FakeOpenAI, FakeSalesforce, call, issue,
                    sample_graph, settings, write)

SPEC = {
    "ticket_key": "KAN-7", "title": "Account risk score", "summary": "Compute a risk score on Account.",
    "acceptance_criteria": ["Score is 0-100"],
    "components": [{"action": "create", "type": "ApexClass", "api_name": "AccountRisk", "description": "calc",
                    "exists_in_org": False, "evidence": "not in graph"},
                   {"action": "modify", "type": "ApexClass", "api_name": "AccountService", "description": "call it",
                    "exists_in_org": True, "evidence": "apex:accountservice"}],
    "reuse": [], "impact": ["AccountTrigger"], "test_plan": ["unit test"], "open_questions": [],
    "risk": "low", "ready_for_development": True,
}


def graphs(tmp_path):
    svc = GraphService(LocalJsonStore(str(tmp_path / "kg.json")))
    svc.replace(sample_graph())
    return svc


def ctx():
    store = MemoryRunStore()
    run = store.create("t", {})
    return RunContext(store, run["id"]), store, run["id"]


# -- Requirement agent --------------------------------------------------------
def test_requirement_agent_reads_ticket_queries_graph_and_grounds_the_spec(tmp_path):
    jira = FakeJira([issue("KAN-7", "Add Risk Score to Account", "Acceptance Criteria\n- Score is 0-100")])
    spec = {**SPEC, "components": [{"action": "create", "type": "CustomField", "api_name": "Account.Risk_Score__c",
                                    "description": "score", "exists_in_org": False, "evidence": "model guess"}]}
    client = FakeOpenAI([
        [call("get_jira_ticket", {"key": "kan-7"}, "a"), call("query_knowledge_graph", {"text": "account risk"}, "b")],
        [call("check_field_exists", {"object": "Account", "field": "Risk_Score__c"}, "c")],
        [call("submit_requirement_spec", spec, "d")],
        "Risk_Score__c already exists, so it will be reused.",
    ])
    c, store, rid = ctx()
    out = RequirementAgent(client, "gpt-test", jira, graphs(tmp_path)).chat("Analyze KAN-7", None, c)

    assert out["reply"].startswith("Risk_Score__c already exists")
    comp = out["spec"]["components"][0]
    # the model said create; the graph says it exists, so the plan changes and says why
    assert comp["exists_in_org"] is True and comp["action"] == "modify"
    assert any("already exists" in q for q in out["spec"]["open_questions"])
    assert out["spec"]["ticket"]["key"] == "KAN-7"
    # every follow-up turn chains on the previous response and re-sends the instructions and tools
    assert client.requests[1]["previous_response_id"] == "resp_1"
    assert all(r["tools"] and r["instructions"] for r in client.requests)
    usage = store.get(rid)["usage"]
    # four Responses calls, each 1000 in / 200 out, attributed to the ticket from the spec
    assert usage == {"agent": "requirement", "model": "gpt-test", "ticket": "KAN-7", "calls": 4,
                     "input_tokens": 4000, "cached_input_tokens": 1600, "output_tokens": 800,
                     "reasoning_tokens": 200, "total_tokens": 4800}
    steps = [s["name"] for s in store.get(rid)["steps"]]
    assert "Read KAN-7" in steps and any(s.startswith("Field check Account.Risk_Score__c: exists") for s in steps)


def test_requirement_agent_keeps_jql_inside_the_project(tmp_path):
    agent = RequirementAgent(None, "m", FakeJira(), graphs(tmp_path))
    assert agent._scoped_jql("status = Done ORDER BY created") == 'project = "KAN" AND (status = Done) ORDER BY created'
    assert agent._scoped_jql('project = "KAN" AND x') == 'project = "KAN" AND x'


def test_tool_errors_go_back_to_the_model(tmp_path):
    client = FakeOpenAI([[call("get_jira_ticket", {"key": "KAN-404"})], "That ticket does not exist."])
    c, _, _ = ctx()
    out = RequirementAgent(client, "m", FakeJira(), graphs(tmp_path)).chat("KAN-404?", "resp_prev", c)
    assert client.requests[0]["previous_response_id"] == "resp_prev"
    assert "error" in client.requests[1]["input"][0]["output"]
    assert out["spec"] is None


# -- Developer agent ----------------------------------------------------------
def connected(s):
    conn = CodexConnection(s)
    conn.model, conn.connected_at = "gpt-test", 1.0
    return conn


def codex_writes(files_per_attempt):
    attempts = []

    def runner(conn, ws, prompt, on_line, home=None, **_):
        attempts.append(prompt)
        runner.homes.append(home)
        for rel, content in files_per_attempt[len(attempts) - 1].items():
            write(ws, rel, content)
        on_line("edited files")
        return {"exit_code": 0, "final_message": f"attempt {len(attempts)} done",
                "usage": {"input_tokens": 5000, "cached_input_tokens": 3000, "output_tokens": 700, "turns": 1}}

    runner.attempts = attempts
    runner.homes = []
    return runner


CLS = "force-app/main/default/classes/"
GOOD = {CLS + "AccountRisk.cls": "/** Account risk score. */\npublic with sharing class AccountRisk {\n"
                                  "\t/** Score from 0 to 100. */\n\tpublic static Integer score() { return 1; }\n}\n",
        CLS + "AccountRisk.cls-meta.xml": "<ApexClass/>",
        CLS + "AccountRiskTest.cls": "@isTest\nprivate class AccountRiskTest {\n\t@isTest\n\tstatic void scores() "
                                      "{ System.assertEquals(1, AccountRisk.score()); }\n}\n",
        CLS + "AccountRiskTest.cls-meta.xml": "<ApexClass/>"}
NO_ASSERT = {**GOOD, CLS + "AccountRiskTest.cls": "@isTest\nprivate class AccountRiskTest {\n\t@isTest\n"
                                                   "\tstatic void scores() { AccountRisk.score(); }\n}\n"}


def developer(tmp_path, runner, deploys, **over):
    s = settings(tmp_path, **over)
    cli_runner = FakeCliRunner(deploys)
    jira = FakeJira([issue("KAN-7", "Account risk score")])
    agent = DeveloperAgent(s, connected(s), SalesforceCli(s, FakeSalesforce(), cli_runner), jira,
                           graphs(tmp_path), codex_runner=runner)
    return agent, cli_runner, jira


def test_develop_validates_then_waits_then_deploys_and_records(tmp_path):
    runner = codex_writes([GOOD])
    agent, cli, jira = developer(tmp_path, runner, [SUCCESS, SUCCESS])
    c, store, rid = ctx()
    result = agent.develop(rid, SPEC, c)

    assert store.get(rid)["status"] == "waiting_approval"
    assert result["tests"] == ["AccountRiskTest"]
    assert result["deploy_targets"] == [CLS + "AccountRisk.cls", CLS + "AccountRiskTest.cls"]
    ws = agent.workspace(rid)
    assert os.path.exists(os.path.join(ws, "SPEC.md")) and os.path.exists(os.path.join(ws, "AGENTS.md"))
    retrieve = next(cmd for cmd in cli.commands if cmd[1:3] == ["project", "retrieve"])
    assert retrieve[-2:] == ["--metadata", "ApexClass:AccountService"]
    dry = [cmd for cmd in cli.commands if cmd[1:3] == ["project", "deploy"]][0]
    assert "--dry-run" in dry and dry[dry.index("--test-level") + 1] == "RunSpecifiedTests"
    # the token only exists inside sf commands, never in what Codex was given
    assert all(e.get("SF_ACCESS_TOKEN") == "00Dtoken" for e in cli.envs)
    assert jira.transitions == [("KAN-7", "In Progress")]

    agent.deploy(rid, result, c)
    run = store.get(rid)
    assert run["status"] == "succeeded" and run["result"]["deployment"]["id"] == "0Af000000000001"
    assert "--dry-run" not in [cmd for cmd in cli.commands if cmd[1:3] == ["project", "deploy"]][1]
    assert jira.comments[0][0] == "KAN-7" and "AccountRisk.cls" in jira.comments[0][1]
    assert jira.transitions[-1] == ("KAN-7", "Done")
    g = agent.graphs.graph()
    assert "ticket:kan-7|TICKET_IMPLEMENTED_BY|apex:accountrisk" in g.edges


def test_validation_errors_go_back_to_codex_and_the_loop_is_bounded(tmp_path):
    runner = codex_writes([GOOD, {CLS + "AccountRisk.cls": "public with sharing class AccountRisk {}"}])
    agent, _, _ = developer(tmp_path, runner, [FAILURE, SUCCESS])
    c, store, rid = ctx()
    agent.develop(rid, SPEC, c)
    assert len(runner.attempts) == 2 and "Variable does not exist: scor" in runner.attempts[1]
    assert store.get(rid)["status"] == "waiting_approval"
    u = store.get(rid)["usage"]  # both Codex attempts are counted
    assert (u["agent"], u["ticket"], u["calls"], u["total_tokens"]) == ("developer", "KAN-7", 2, 11400)

    always_failing = codex_writes([GOOD, GOOD, GOOD])
    agent, _, _ = developer(tmp_path, always_failing, [FAILURE, FAILURE, FAILURE])
    c, store, rid = ctx()
    with pytest.raises(DeveloperError, match="no valid change after 3"):
        agent.develop(rid, SPEC, c)


def test_guard_refuses_profiles_deletions_and_untested_apex(tmp_path):
    bad = {"force-app/main/default/profiles/Admin.profile-meta.xml": "<Profile/>",
           CLS + "Untested.cls": "public class Untested {}"}
    runner = codex_writes([bad, bad, bad])
    agent, cli, _ = developer(tmp_path, runner, [], max_fix_attempts=2)
    c, store, rid = ctx()
    with pytest.raises(DeveloperError):
        agent.develop(rid, SPEC, c)
    assert "profiles is outside what the agent may change" in runner.attempts[1]
    assert "Apex changed but no @isTest class was written" in runner.attempts[1]
    assert not [cmd for cmd in cli.commands if cmd[1:3] == ["project", "deploy"]]  # nothing reached the org


def test_deploy_rebuilds_a_lost_workspace_from_the_stored_change_set(tmp_path):
    runner = codex_writes([GOOD])
    agent, _, _ = developer(tmp_path, runner, [SUCCESS, SUCCESS])
    c, store, rid = ctx()
    result = agent.develop(rid, SPEC, c)
    import shutil
    shutil.rmtree(agent.workspace(rid))
    agent.deploy(rid, result, c)
    assert os.path.exists(os.path.join(agent.workspace(rid), CLS + "AccountRisk.cls"))
    assert store.get(rid)["status"] == "succeeded"


def test_helpers():
    assert component_root("force-app/main/default/lwc/card/card.js") == "force-app/main/default/lwc/card"
    assert component_root(CLS + "A.cls-meta.xml") == CLS + "A.cls"
    node, edge = node_for_path("force-app/main/default/objects/Account/fields/Score__c.field-meta.xml")
    assert node.id == "field:account.score__c" and edge.from_id == "sobj:account"
    out = deploy_outcome(FAILURE)
    assert not out["success"] and out["errors"] == ["ApexClass AccountRisk: Variable does not exist: scor (line 7)"]
    assert deploy_outcome(SUCCESS)["success"]


def test_guardrail_findings_go_back_to_codex_and_land_on_the_scorecard(tmp_path):
    runner = codex_writes([NO_ASSERT, GOOD])
    agent, _, _ = developer(tmp_path, runner, [SUCCESS])
    c, store, rid = ctx()
    result = agent.develop(rid, SPEC, c)
    assert "[TST-02 Meaningful tests]" in runner.attempts[1] and "no assertions" in runner.attempts[1]
    # the standards the change touches are in the instructions, and only those
    assert "[TRG-02]" not in agent._instructions({"components": [{"type": "Flow"}]})
    assert "[APX-03]" in agent._instructions(SPEC) and "[TST-01]" in agent._instructions(SPEC)
    card = result["guardrails"]
    assert card["blocked"] == [] and "APX-03" in card["passed"] and card["pack"].startswith("Ascension")


def test_coverage_under_ninety_percent_goes_back_to_codex(tmp_path):
    low = {"status": 0, "result": {**SUCCESS["result"], "details": {"runTestResult": {
        "numTestsRun": 1, "codeCoverage": [{"name": "AccountRisk", "numLocations": 10, "numLocationsNotCovered": 3}]}}}}
    runner = codex_writes([GOOD, GOOD])
    agent, _, _ = developer(tmp_path, runner, [low, SUCCESS])
    c, store, rid = ctx()
    agent.develop(rid, SPEC, c)
    assert "AccountRisk is at 70% coverage; it needs 90%" in runner.attempts[1]
