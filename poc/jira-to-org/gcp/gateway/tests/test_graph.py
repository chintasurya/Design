from app.graph.ingest import SalesforceIngest, ingest_jira
from app.graph.model import Graph, tokens
from app.graph.store import GraphService, LocalJsonStore
from app.graph.model import Edge, Node

from .fakes import FakeJira, FakeSalesforce, issue, sample_graph


def test_tokens_split_identifiers_whole():
    assert tokens("AccountTriggerHandler") == ["account", "trigger", "handler"]
    assert tokens("Risk_Score__c") == ["risk", "score"]
    assert "date" not in tokens("UPDATE the record")


def test_search_matches_whole_tokens_not_substrings():
    g = sample_graph()
    ids = [n.id for n, _ in g.search("Update the account rating")]
    assert "sobj:account" in ids and "field:account.rating" in ids
    assert "apex:accountingcode" not in ids  # 'Account' must not match 'AccountingCode'


def test_field_exists_by_api_name_or_label_and_unknown_object_is_not_absent():
    g = sample_graph()
    assert g.field_exists("Account", "Risk_Score__c")["exists"]
    assert g.field_exists("account", "risk score")["exists"]
    assert not g.field_exists("Account", "Churn_Date__c")["exists"]
    unknown = g.field_exists("Opportunity", "Amount")
    assert unknown["object_found"] is False and "unknown" in unknown["note"]


def test_neighbourhood_walks_behaviour_and_never_expands_through_an_unnamed_object():
    g = sample_graph()
    nodes, _ = g.neighbourhood(["sobj:contact"], hops=3)
    ids = {n.id for n in nodes}
    assert "apex:contactservice" in ids and "sobj:account" in ids
    # Account was reached, not named: its trigger must not be pulled in through it
    assert "trigger:accounttrigger" not in ids
    nodes, edges = g.neighbourhood(["sobj:account"], hops=2)
    assert "apex:accounttriggerhandler" in {n.id for n in nodes}


def test_local_store_round_trip_keeps_agent_facts_across_rebuilds(tmp_path):
    svc = GraphService(LocalJsonStore(str(tmp_path / "kg.json")))
    svc.replace(sample_graph())
    svc.record([Node("ticket:kan-1", "JiraTicket", "KAN-1", "KAN-1", "JIRA")],
               [Edge("TICKET_IMPLEMENTED_BY", "ticket:kan-1", "apex:contactservice", "developer-agent")])
    svc.replace(sample_graph())  # a rebuild replaces the snapshot only
    g = GraphService(LocalJsonStore(str(tmp_path / "kg.json"))).graph()
    assert "ticket:kan-1|TICKET_IMPLEMENTED_BY|apex:contactservice" in g.edges
    assert len(g.nodes) == len(sample_graph().nodes) + 1


def test_salesforce_ingest_builds_typed_edges():
    g = SalesforceIngest(FakeSalesforce(), ("Account", "Contact")).run()
    e = set(g.edges)
    assert "trigger:accounttrigger|TRIGGER_FIRES_ON_SOBJECT|sobj:account" in e
    assert "trigger:accounttrigger|TRIGGER_CALLS_APEX|apex:accounttriggerhandler" in e
    assert "apex:accounttriggerhandler|APEX_CALLS_APEX|apex:invoiceservice" in e
    assert "flow:invoice_on_create|FLOW_TRIGGERS_ON_SOBJECT|sobj:invoice__c" in e
    assert "flow:invoice_on_create|FLOW_UPDATES_SOBJECT|sobj:invoice__c" in e  # $Record resolved
    assert "flow:invoice_on_create|FLOW_READS_SOBJECT|sobj:account" in e
    assert "flow:invoice_on_create|FLOW_CALLS_APEX|apex:invoiceservice" in e
    assert "lwc:invoicecard|LWC_CALLS_APEX|apex:invoiceservice" in e
    assert "apex:invoiceservice|APEX_REFERENCES_SOBJECT|sobj:invoice__c" in e
    assert "apex:accounttriggerhandler|APEX_REFERENCES_FIELD|field:account.risk_score__c" in e
    assert "vr:account.require_rating|VALIDATES_SOBJECT|sobj:account" in e
    assert "field:invoice__c.account__c|FIELD_REFERENCES_SOBJECT|sobj:account" in e
    assert "sobj:account|SOBJECT_HAS_RECORDTYPE|rt:account.partner" in e
    # whole identifiers: AccountingCode is never 'a reference to Account'
    assert "apex:accountingcode|APEX_REFERENCES_SOBJECT|sobj:account" not in e
    assert g.nodes["apex:invoiceservicetest"].properties["is_test"] is True
    assert all("_body" not in n.properties for n in g.nodes.values())
    assert any(n.startswith("objects in scope: Account, Contact, Invoice__c") for n in g.notes)
    # a field with no FLS is invisible to describe but exists: the Tooling API says so
    assert g.nodes["field:account.region__c"].properties["fls_hidden"] is True
    assert g.field_exists("Account", "Region__c")["exists"]
    assert "field-level security" in g.field_exists("Account", "Region")["note"]
    assert not g.nodes["field:account.risk_score__c"].properties.get("fls_hidden")
    # installed packages are left out, and say so
    assert "sobj:pkg__audit__c" not in g.nodes and "flow:pkg_flow" not in g.nodes
    assert any("1 managed-package objects left out" in n for n in g.notes)
    assert any("1 managed-package flows left out" in n for n in g.notes)


def test_a_refused_section_becomes_a_note_not_a_failed_build():
    sf = FakeSalesforce()
    original = sf.tooling_query

    def refuse_dependencies(soql):
        if "MetadataComponentDependency" in soql:
            raise RuntimeError("INVALID_TYPE")
        return original(soql)

    sf.tooling_query = refuse_dependencies
    g = SalesforceIngest(sf, ("Account",)).run()
    assert any(n.startswith("dependency api: skipped") for n in g.notes)
    assert "trigger:accounttrigger|TRIGGER_FIRES_ON_SOBJECT|sobj:account" in g.edges


def test_jira_ingest_links_tickets_to_components():
    g = SalesforceIngest(FakeSalesforce(), ("Account", "Contact")).run()
    jira = FakeJira([issue("KAN-1", "Add a risk score to Account", "Use AccountTriggerHandler"),
                     issue("KAN-2", "Child task", parent="KAN-1")])
    ingest_jira(jira, g)
    assert "ticket:kan-1|TICKET_MENTIONS|apex:accounttriggerhandler" in g.edges
    assert "ticket:kan-1|TICKET_PARENT_OF|ticket:kan-2" in g.edges
    assert isinstance(Graph.from_dict(g.to_dict()), Graph)
