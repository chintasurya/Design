"""Test doubles for Salesforce, Jira, OpenAI and the CLIs. No network anywhere."""
from __future__ import annotations

import json
import os
from types import SimpleNamespace

from app.config import Settings
from app.graph.model import Edge, Graph, Node


def settings(tmp_path, **over) -> Settings:
    base = dict(
        gcp_project="", bq_dataset="agent_kg", graph_store="local",
        local_graph_path=str(tmp_path / "kg.json"), run_store="memory",
        jira_base_url="https://example.atlassian.net", jira_email="me@example.com", jira_project_key="KAN",
        jira_start_transition="In Progress", jira_done_transition="Done",
        sf_login_url="https://example.my.salesforce.com", sf_api_version="62.0",
        kg_standard_objects=("Account", "Contact"), kg_flow_metadata_max=10,
        codex_auth_mode="apikey", openai_model="", codex_model="", codex_bin="codex", codex_home=str(tmp_path / "codex-home"),
        codex_sandbox="workspace-write", codex_timeout_s=60, sf_bin="sf",
        workspace_root=str(tmp_path / "runs"), max_fix_attempts=2, auto_deploy=False,
    )
    base.update(over)
    return Settings(**base)


def sample_graph() -> Graph:
    g = Graph()
    g.add_node(Node("sobj:account", "SObject", "Account", "Account", properties={"label": "Account"}))
    g.add_node(Node("sobj:contact", "SObject", "Contact", "Contact", properties={"label": "Contact"}))
    g.add_node(Node("field:account.rating", "Field", "Account Rating", "Account.Rating",
                    properties={"label": "Account Rating", "type": "picklist"}))
    g.add_node(Node("field:account.risk_score__c", "Field", "Risk Score", "Account.Risk_Score__c",
                    properties={"label": "Risk Score", "type": "double"}))
    g.add_node(Node("trigger:accounttrigger", "ApexTrigger", "AccountTrigger", "AccountTrigger"))
    g.add_node(Node("apex:accounttriggerhandler", "ApexClass", "AccountTriggerHandler", "AccountTriggerHandler"))
    g.add_node(Node("apex:contactservice", "ApexClass", "ContactService", "ContactService"))
    g.add_node(Node("apex:accountingcode", "ApexClass", "AccountingCode", "AccountingCode"))
    for e in [Edge("SOBJECT_HAS_FIELD", "sobj:account", "field:account.rating"),
              Edge("SOBJECT_HAS_FIELD", "sobj:account", "field:account.risk_score__c"),
              Edge("TRIGGER_FIRES_ON_SOBJECT", "trigger:accounttrigger", "sobj:account"),
              Edge("TRIGGER_CALLS_APEX", "trigger:accounttrigger", "apex:accounttriggerhandler"),
              Edge("APEX_REFERENCES_SOBJECT", "apex:contactservice", "sobj:contact"),
              Edge("APEX_REFERENCES_SOBJECT", "apex:contactservice", "sobj:account")]:
        g.add_edge(e)
    return g


class FakeSalesforce:
    """Duck-types SalesforceClient."""

    login_url = "https://example.my.salesforce.com"

    def __init__(self) -> None:
        self.tooling_calls: list[str] = []

    def session(self):
        return "00Dtoken", "https://example.my.salesforce.com"

    def describe_global(self):
        return [{"name": "Account", "label": "Account", "labelPlural": "Accounts", "custom": False},
                {"name": "Contact", "label": "Contact", "labelPlural": "Contacts", "custom": False},
                {"name": "Invoice__c", "label": "Invoice", "labelPlural": "Invoices", "custom": True},
                {"name": "pkg__Audit__c", "label": "Audit", "labelPlural": "Audits", "custom": True}]

    def describe(self, name):
        fields = {
            "Account": [{"name": "Id", "label": "Account ID", "type": "id"},
                        {"name": "Rating", "label": "Account Rating", "type": "picklist",
                         "picklistValues": [{"value": "Hot"}, {"value": "Cold"}]},
                        {"name": "Risk_Score__c", "label": "Risk Score", "type": "double", "custom": True}],
            "Contact": [{"name": "AccountId", "label": "Account ID", "type": "reference", "referenceTo": ["Account"]}],
            "Invoice__c": [{"name": "Account__c", "label": "Account", "type": "reference", "referenceTo": ["Account"],
                            "custom": True}],
        }[name]
        return {"label": name.replace("__c", ""), "custom": name.endswith("__c"), "fields": fields,
                "recordTypeInfos": [{"master": True, "name": "Master"},
                                    {"master": False, "name": "Partner", "developerName": "Partner"}]
                if name == "Account" else []}

    def query(self, soql):
        if "FROM ApexClass" in soql:
            return [{"Name": "AccountTriggerHandler", "Body": "public with sharing class AccountTriggerHandler {"
                     " void run(List<Account> rows) { InvoiceService.create(rows); } }"},
                    {"Name": "InvoiceService", "Body": "public class InvoiceService { static void create("
                     "List<Account> a) { insert new Invoice__c(); } }"},
                    {"Name": "AccountingCode", "Body": "public class AccountingCode {}"},
                    {"Name": "InvoiceServiceTest", "Body": "@isTest private class InvoiceServiceTest {}"}]
        if "FROM ApexTrigger" in soql:
            return [{"Name": "AccountTrigger", "TableEnumOrId": "Account", "UsageAfterInsert": True,
                     "UsageBeforeUpdate": True, "Body": "trigger AccountTrigger on Account (after insert) "
                     "{ new AccountTriggerHandler().run(Trigger.new); }"}]
        if "FROM FlowDefinitionView" in soql:
            return [{"ApiName": "Invoice_On_Create", "Label": "Invoice On Create", "ProcessType": "AutoLaunchedFlow",
                     "TriggerType": "RecordAfterSave", "TriggerObjectOrEventLabel": "Invoice", "IsActive": True,
                     "ActiveVersionId": "301000000000001"},
                    {"ApiName": "Pkg_Flow", "Label": "Pkg Flow", "TriggerType": "RecordAfterSave",
                     "TriggerObjectOrEventLabel": "Account", "IsActive": True, "ActiveVersionId": "301000000000009",
                     "NamespacePrefix": "pkg"}]
        raise AssertionError(soql)

    def tooling_query(self, soql):
        self.tooling_calls.append(soql)
        if "FROM CustomObject" in soql:
            return [{"Id": "01I000000000001AAA", "DeveloperName": "Invoice", "NamespacePrefix": None}]
        if "FROM CustomField" in soql:
            return [{"Id": "00N000000000001AAA", "DeveloperName": "Risk_Score", "TableEnumOrId": "Account"},
                    {"Id": "00N000000000002AAA", "DeveloperName": "Region", "TableEnumOrId": "Account"}]
        if "FROM Flow WHERE" in soql:
            return [{"Metadata": {"recordUpdates": [{"inputReference": "$Record",
                                                     "inputAssignments": [{"field": "Status__c"}]}],
                                  "recordLookups": [{"object": "Account"}],
                                  "actionCalls": [{"actionType": "apex", "actionName": "InvoiceService"}]}}]
        if "FROM LightningComponentBundle" in soql:
            return [{"DeveloperName": "invoiceCard", "MasterLabel": "Invoice Card"}]
        if "FROM ValidationRule" in soql:
            return [{"ValidationName": "Require_Rating", "Active": True, "ErrorMessage": "Rating required",
                     "EntityDefinition": {"QualifiedApiName": "Account"}}]
        if "FROM MetadataComponentDependency" in soql:
            return [{"MetadataComponentId": "x", "MetadataComponentName": "invoiceCard",
                     "MetadataComponentType": "LightningComponentBundle", "RefMetadataComponentId": "y",
                     "RefMetadataComponentName": "InvoiceService", "RefMetadataComponentType": "ApexClass"},
                    {"MetadataComponentId": "x", "MetadataComponentName": "InvoiceService",
                     "MetadataComponentType": "ApexClass", "RefMetadataComponentId": "01I000000000001",
                     "RefMetadataComponentName": "Invoice", "RefMetadataComponentType": "CustomObject"},
                    {"MetadataComponentId": "x", "MetadataComponentName": "AccountTriggerHandler",
                     "MetadataComponentType": "ApexClass", "RefMetadataComponentId": "00N000000000001",
                     "RefMetadataComponentName": "Risk_Score", "RefMetadataComponentType": "CustomField"}]
        raise AssertionError(soql)


def issue(key, summary, description="", status="To Do", links=None, parent=None):
    adf = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": line}]}
                                      for line in description.split("\n")]} if description else None
    return {"key": key, "fields": {
        "summary": summary, "description": adf, "status": {"name": status}, "issuetype": {"name": "Story"},
        "priority": {"name": "Medium"}, "labels": [], "components": [], "issuelinks": links or [],
        "parent": {"key": parent} if parent else None, "subtasks": [], "comment": {"comments": []}}}


class FakeJira:
    project_key = "KAN"

    def __init__(self, issues=None):
        self.issues = {i["key"]: i for i in (issues or [])}
        self.comments: list[tuple[str, str]] = []
        self.transitions: list[tuple[str, str]] = []

    def browse_url(self, key):
        return f"https://example.atlassian.net/browse/{key}"

    def get_issue(self, key):
        return self.issues[key]

    def search(self, jql, max_results=25):
        return list(self.issues.values())[:max_results]

    def project_issues(self, only_open=False, max_results=25):
        return list(self.issues.values())[:max_results]

    def add_comment(self, key, text):
        self.comments.append((key, text))

    def transition(self, key, name):
        self.transitions.append((key, name))
        return name


def call(name, args, call_id="c1"):
    return SimpleNamespace(type="function_call", name=name, arguments=json.dumps(args), call_id=call_id)


class FakeOpenAI:
    """Replays scripted Responses: each entry is a list of output items, or a final text."""

    def __init__(self, script):
        self.script = list(script)
        self.requests: list[dict] = []
        self.responses = self

    def create(self, **kwargs):
        self.requests.append(kwargs)
        step = self.script.pop(0)
        rid = f"resp_{len(self.requests)}"
        usage = SimpleNamespace(input_tokens=1000, output_tokens=200,
                                input_tokens_details=SimpleNamespace(cached_tokens=400),
                                output_tokens_details=SimpleNamespace(reasoning_tokens=50))
        if isinstance(step, str):
            return SimpleNamespace(id=rid, output=[SimpleNamespace(type="message")], output_text=step,
                                   usage=usage, model="gpt-test")
        return SimpleNamespace(id=rid, output=step, output_text="", usage=usage, model="gpt-test")


def write(ws, rel, content):
    path = os.path.join(ws, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)


SUCCESS = {"status": 0, "result": {"success": True, "status": "Succeeded", "id": "0Af000000000001",
                                   "numberComponentsDeployed": 3, "details": {"runTestResult": {"numTestsRun": 2}}}}
FAILURE = {"status": 1, "name": "FailedDeployError", "message": "Deploy failed.",
           "result": {"success": False, "status": "Failed", "id": "0Af000000000002",
                      "details": {"componentFailures": {"componentType": "ApexClass", "fullName": "AccountRisk",
                                                        "problem": "Variable does not exist: scor", "lineNumber": 7}}}}


class FakeCliRunner:
    """Stands in for subprocess: answers `sf` commands from a script."""

    def __init__(self, deploys):
        self.deploys = list(deploys)
        self.commands: list[list[str]] = []
        self.envs: list[dict] = []

    def __call__(self, cmd, cwd=None, env=None, timeout=0, stdin=None):
        self.commands.append(cmd)
        self.envs.append(dict(env or {}))
        if cmd[1:3] == ["org", "login"]:
            return 0, json.dumps({"status": 0, "result": {"username": "agent@example.com"}})
        if cmd[1:3] == ["project", "retrieve"]:
            write(cwd, "force-app/main/default/classes/AccountService.cls", "public class AccountService {}")
            return 0, json.dumps({"status": 0, "result": {"files": [{"fullName": "AccountService"}]}})
        if cmd[1:3] == ["project", "deploy"]:
            return 0, json.dumps(self.deploys.pop(0))
        raise AssertionError(cmd)
