from app.graph.model import Graph, Node
from .test_api import KEY, api  # noqa: F401 - fixture
from app.guardrails import GuardrailService, areas_for_components, load_bundled
from app.guardrails.checks import run_checks, strip_apex, loop_bodies

S = "force-app/main/default/"
RULES = load_bundled()["rules"]

GOOD_TRIGGER = "trigger Account on Account (before insert, after update) {\n\tnew AccountTriggerHandler().run();\n}\n"
GOOD_HANDLER = '''/**
 * Account trigger logic.
 */
public with sharing class AccountTriggerHandler extends TriggerHandler {
	/** Flags hot accounts. */
	protected override void afterUpdate() {
		List<Task> tasksToCreate = new List<Task>();
		for (Account accountRecord : (List<Account>) Trigger.new) {
			tasksToCreate.add(new Task(WhatId = accountRecord.Id, Subject = 'Follow up'));
		}
		try {
			insert tasksToCreate;
		} catch (DmlException dmlError) {
			System.debug(LoggingLevel.ERROR, dmlError.getMessage());
		}
	}
}
'''
GOOD_TEST = '''@isTest
private class AccountTriggerHandlerTest {
	@isTest
	static void createsTasksInBulk() {
		List<Account> accounts = new List<Account>();
		for (Integer index = 0; index < 200; index++) {
			accounts.add(new Account(Name = 'A' + index));
		}
		insert accounts;
		System.assertEquals(200, [SELECT COUNT() FROM Account]);
	}
}
'''
BAD_HANDLER = '''public class Account_Helper {
	public static void DoWork(List<Account> rows) {
		for (Account a : rows) {
			List<Contact> cs = [SELECT Id FROM Contact WHERE AccountId = :a.Id];
			update cs;
			Id owner = '005000000000001AAA';
		}
		Account first = (Account) Trigger.new[0];
	}
}
'''
FLOW_OK = '''<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Creates a renewal opportunity when one is won.</description>
    <label>Create Renewal Opportunity</label>
    <recordCreates><name>CreateRenewal</name><faultConnector><targetReference>ErrorHandler</targetReference></faultConnector></recordCreates>
    <variables><name>renewalName</name></variables>
    <start><object>Opportunity</object></start>
</Flow>'''
FLOW_BAD = '''<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Renewal_Opportunity Flow</label>
    <recordCreates><name>CreateRenewal</name></recordCreates>
    <variables><name>Renewal_Name</name></variables>
</Flow>'''
FIELD_BAD = '''<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata"><fullName>Next_Step_Date__c</fullName></CustomField>'''
FIELD_OK = '''<?xml version="1.0" encoding="UTF-8"?>
<CustomField xmlns="http://soap.sforce.com/2006/04/metadata"><fullName>NextStepDate__c</fullName>
<description>When the next step is due.</description><inlineHelpText>Date the next step is due</inlineHelpText></CustomField>'''


def f(path, content, status="added"):
    return {"path": S + path, "content": content, "status": status}


def rules_hit(card):
    return {x["rule"] for x in card["blocked"] + card["warnings"]}


def test_standards_following_code_passes_clean():
    card = run_checks(RULES, [f("triggers/Account.trigger", GOOD_TRIGGER),
                              f("classes/AccountTriggerHandler.cls", GOOD_HANDLER),
                              f("classes/AccountTriggerHandlerTest.cls", GOOD_TEST),
                              f("flows/CreateRenewalOpportunity.flow-meta.xml", FLOW_OK),
                              f("objects/Opportunity/fields/NextStepDate__c.field-meta.xml", FIELD_OK)],
                      coverage={"AccountTriggerHandler": 96.0})
    assert card["blocked"] == [], card["blocked"]
    assert {"APX-03", "APX-04", "TRG-02", "FLW-02", "TST-01"} <= set(card["passed"])


def test_every_broken_rule_is_named_with_a_fix():
    card = run_checks(RULES, [f("classes/Account_Helper.cls", BAD_HANDLER),
                              f("flows/Renewal_Opportunity.flow-meta.xml", FLOW_BAD),
                              f("objects/Opportunity/fields/Next_Step_Date__c.field-meta.xml", FIELD_BAD),
                              f("triggers/AccountTrigger.trigger",
                                "trigger AccountTrigger on Account (before insert) { for (Account a : Trigger.new) "
                                "{ a.Name = 'x'; } }"),
                              f("profiles/Admin.profile-meta.xml", "<Profile/>")],
                      coverage={"Account_Helper": 40.0})
    blocked = {x["rule"] for x in card["blocked"]}
    assert {"APX-01", "APX-02", "APX-03", "APX-04", "APX-05", "GEN-02", "FLW-01", "FLW-02", "NAM-02",
            "TRG-01", "TRG-02", "TST-02", "TST-01", "GEN-04"} <= blocked
    messages = " ".join(x["message"] for x in card["blocked"])
    assert "NextStepDate__c" in messages and "new AccountTriggerHandler().run();" in messages
    assert "005000000000001AAA" in messages


def test_a_soql_for_loop_is_the_recommended_pattern_not_a_violation():
    code = "for (Account a : [SELECT Id FROM Account]) { names.add(a.Name); }"
    assert loop_bodies(strip_apex(code)) == [" { names.add(a.Name); }"]
    assert "'insert x'" not in strip_apex("String s = 'insert x';")  # strings never count


def test_one_trigger_per_object_uses_the_graph():
    g = Graph()
    g.add_node(Node("trigger:opportunitytaskautocreatetrigger", "ApexTrigger", "OpportunityTaskAutoCreateTrigger",
                    "OpportunityTaskAutoCreateTrigger", properties={"trigger_object": "Opportunity"}))
    card = run_checks(RULES, [f("triggers/Opportunity.trigger",
                                "trigger Opportunity on Opportunity (after insert) { new OpportunityTriggerHandler().run(); }"),
                              f("classes/OpportunityTriggerHandler.cls", GOOD_HANDLER.replace("Account", "Opportunity"))],
                      graph=g)
    msgs = [x["message"] for x in card["blocked"] if x["rule"] == "TRG-01"]
    assert msgs and "already has trigger OpportunityTaskAutoCreateTrigger" in msgs[0]


def test_severity_comes_from_the_pack_and_off_disables_a_rule():
    rules = [dict(r, severity="off") if r["id"] == "APX-03" else r for r in RULES]
    card = run_checks(rules, [f("classes/Account_Helper.cls", BAD_HANDLER)])
    assert "APX-03" not in rules_hit(card) and "APX-03" not in card["checked"]


def test_service_falls_back_to_the_bundled_pack_and_briefs_only_relevant_areas():
    class Broken:
        def load(self):
            raise RuntimeError("firestore down")

    svc = GuardrailService(Broken())
    assert svc.pack()["fallback"] is True and len(svc.rules()) == len(RULES)
    areas = areas_for_components([{"type": "Flow"}, {"type": "CustomField"}])
    assert areas == ["Field", "Flow", "General"]
    brief = svc.brief(areas)
    assert "[FLW-02]" in brief and "[NAM-02]" in brief and "[TRG-02]" not in brief


def test_guardrails_endpoint_shows_the_pack(api):  # noqa: F811
    client, _ = api
    out = client.get("/v1/guardrails", headers=KEY).json()
    assert out["name"].startswith("Ascension") and len(out["rules"]) == len(RULES) and out["source"] == "bundled file"


def test_requirement_agent_plans_flow_first():
    from app.agents.requirement import SPEC_SCHEMA, ground_spec, planning_instructions

    assert "approach" in SPEC_SCHEMA["required"]
    text = planning_instructions(GuardrailService())
    assert "[GEN-01] Declarative first" in text and "[TRG-02]" in text and "[APX-03]" not in text
    spec = {"ticket_key": "KAN-9", "approach": {"build_with": "Trigger", "why_not_flow": " ",
                                                "existing_automation": ""},
            "components": [], "ready_for_development": True, "open_questions": []}
    out = ground_spec(spec, Graph(), {})
    assert out["ready_for_development"] is False and out["open_questions"][0].startswith("[GEN-01]")
    ok = ground_spec({**spec, "approach": {"build_with": "Flow", "why_not_flow": "", "existing_automation": ""},
                      "ready_for_development": True, "open_questions": []}, Graph(), {})
    assert ok["ready_for_development"] is True


def test_an_existing_badly_named_trigger_may_be_fixed_in_place():
    body = "trigger OpportunityTaskAutoCreateTrigger on Opportunity (after insert) { new OpportunityTriggerHandler().run(); }"
    card = run_checks(RULES, [f("triggers/OpportunityTaskAutoCreateTrigger.trigger", body, status="modified"),
                              f("classes/OpportunityTriggerHandler.cls", GOOD_HANDLER.replace("Account", "Opportunity")),
                              f("classes/OpportunityTriggerHandlerTest.cls", GOOD_TEST.replace("Account", "Opportunity"))])
    assert card["blocked"] == [], card["blocked"]
    logic = body.replace("new OpportunityTriggerHandler().run();", "for (Opportunity o : Trigger.new) { o.Name = 'x'; }")
    card = run_checks(RULES, [f("triggers/OpportunityTaskAutoCreateTrigger.trigger", logic, status="modified")])
    assert "TRG-02" in {x["rule"] for x in card["blocked"]}  # but its logic still has to move to the handler
