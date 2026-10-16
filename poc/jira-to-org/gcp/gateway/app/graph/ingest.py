"""Connectors + ingestors: Salesforce metadata and Jira tickets into one graph.

Every section is isolated: a query the org refuses becomes a note on the
graph, not a failed build. The notes travel with the snapshot so anyone
reading an answer can see what the graph did and did not cover.
"""
from __future__ import annotations

import re
from typing import Callable

from ..jira import JiraClient, simplify
from ..salesforce import SalesforceClient
from .model import COMPONENT_TYPES, Edge, Graph, Node, slug

SF_ID = re.compile(r"^[a-zA-Z0-9]{15}([a-zA-Z0-9]{3})?$")
MAX_OBJECTS = 150


def sobj_id(api: str) -> str:
    return f"sobj:{api.lower()}"


def _safely(graph: Graph, section: str, fn: Callable[[], object]) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - recorded, never swallowed silently
        graph.notes.append(f"{section}: skipped ({type(exc).__name__}: {str(exc)[:200]})")


class SalesforceIngest:
    def __init__(self, sf: SalesforceClient, standard_objects: tuple[str, ...], flow_metadata_max: int = 100):
        self.sf = sf
        self.standard_objects = standard_objects
        self.flow_metadata_max = flow_metadata_max
        self.graph = Graph()
        self.label_to_api: dict[str, str] = {}
        self.api_names: dict[str, str] = {}
        self.custom_object_ids: dict[str, str] = {}
        self.custom_field_ids: dict[str, tuple[str, str]] = {}
        self.class_names: dict[str, str] = {}
        self.scoped: list[str] = []

    # -- helpers ------------------------------------------------------------
    def ensure_sobject(self, api: str, boundary: bool = True) -> str:
        api = self.api_names.get(api.lower(), api)
        nid = sobj_id(api)
        if nid not in self.graph.nodes:
            label = next((l for l, a in self.label_to_api.items() if a == api), api)
            self.graph.add_node(Node(nid, "SObject", api, api,
                                     properties={"label": label, "boundary": boundary}))
        return nid

    def resolve_object(self, value: str | None) -> str | None:
        if not value:
            return None
        if SF_ID.match(value) and value[:3] == "01I":
            return self.custom_object_ids.get(value[:15])
        return self.api_names.get(value.lower()) or self.label_to_api.get(value.lower()) or value

    def run(self) -> Graph:
        g = self.graph
        _safely(g, "describeGlobal", self._global)
        _safely(g, "custom object ids", self._custom_ids)
        _safely(g, "objects", self._objects)
        _safely(g, "apex classes", self._classes)
        _safely(g, "apex triggers", self._triggers)
        _safely(g, "flows", self._flows)
        _safely(g, "lightning web components", self._lwc)
        _safely(g, "validation rules", self._validation_rules)
        _safely(g, "dependency api", self._dependencies)
        _safely(g, "apex body scan", self._body_scan)
        for n in g.nodes.values():  # bodies are scan input, never stored
            n.properties.pop("_body", None)
        dropped = g.prune_dangling()
        g.notes.append(f"objects in scope: {', '.join(self.scoped) or 'none'}")
        if dropped:
            g.notes.append(f"{dropped} edges dropped: an endpoint was outside the graph")
        return g

    # -- sections -----------------------------------------------------------
    def _global(self) -> None:
        for o in self.sf.describe_global():
            self.api_names[o["name"].lower()] = o["name"]
            self.label_to_api[o["label"].lower()] = o["name"]
            self.label_to_api.setdefault(o.get("labelPlural", "").lower(), o["name"])
        custom = sorted(a for a in self.api_names.values() if a.endswith("__c"))
        standard = [self.api_names[s.lower()] for s in self.standard_objects if s.lower() in self.api_names]
        self.scoped = (standard + custom)[:MAX_OBJECTS]
        if len(standard) + len(custom) > MAX_OBJECTS:
            self.graph.notes.append(f"object scope capped at {MAX_OBJECTS}")

    def _custom_ids(self) -> None:
        for r in self.sf.tooling_query("SELECT Id, DeveloperName, NamespacePrefix FROM CustomObject"):
            ns = f"{r['NamespacePrefix']}__" if r.get("NamespacePrefix") else ""
            self.custom_object_ids[r["Id"][:15]] = f"{ns}{r['DeveloperName']}__c"
        for r in self.sf.tooling_query(
                "SELECT Id, DeveloperName, TableEnumOrId FROM CustomField WHERE NamespacePrefix = null"):
            obj = self.resolve_object(r.get("TableEnumOrId"))
            if obj:
                self.custom_field_ids[r["Id"][:15]] = (obj, f"{r['DeveloperName']}__c")

    def _objects(self) -> None:
        g = self.graph
        for api in self.scoped:
            try:
                d = self.sf.describe(api)
            except Exception as exc:  # noqa: BLE001
                g.notes.append(f"describe {api}: {str(exc)[:120]}")
                continue
            oid = sobj_id(api)
            g.add_node(Node(oid, "SObject", d.get("label", api), api, properties={
                "label": d.get("label"), "custom": d.get("custom"), "key_prefix": d.get("keyPrefix"),
                "boundary": False}))
            for f in d.get("fields", []):
                fid = f"field:{api.lower()}.{f['name'].lower()}"
                props = {"label": f.get("label"), "type": f.get("type"), "custom": f.get("custom"),
                         "length": f.get("length"), "required": not f.get("nillable", True) and f.get("createable", False),
                         "reference_to": f.get("referenceTo") or [], "formula": bool(f.get("calculated"))}
                if f.get("picklistValues"):
                    props["values"] = [p["value"] for p in f["picklistValues"][:25]]
                g.add_node(Node(fid, "Field", f.get("label", f["name"]), f"{api}.{f['name']}", properties=props))
                g.add_edge(Edge("SOBJECT_HAS_FIELD", oid, fid))
                for ref in f.get("referenceTo") or []:
                    if ref.lower() in self.api_names:
                        g.add_edge(Edge("FIELD_REFERENCES_SOBJECT", fid, self.ensure_sobject(ref)))
            for rt in d.get("recordTypeInfos", []):
                if rt.get("master"):
                    continue
                dev = rt.get("developerName") or rt.get("name")
                rid = f"rt:{api.lower()}.{slug(dev)}"
                g.add_node(Node(rid, "RecordType", rt.get("name", dev), f"{api}.{dev}",
                                properties={"label": rt.get("name"), "active": rt.get("active")}))
                g.add_edge(Edge("SOBJECT_HAS_RECORDTYPE", oid, rid))

    def _classes(self) -> None:
        rows = self.sf.query("SELECT Id, Name, ApiVersion, Status, Body FROM ApexClass "
                             "WHERE NamespacePrefix = null ORDER BY Name LIMIT 2000")
        for r in rows:
            body = r.get("Body") or ""
            self.class_names[r["Name"].lower()] = r["Name"]
            self.graph.add_node(Node(f"apex:{r['Name'].lower()}", "ApexClass", r["Name"], r["Name"], properties={
                "api_version": r.get("ApiVersion"), "status": r.get("Status"),
                "is_test": bool(re.search(r"@isTest", body, re.I)), "length": len(body),
                "_body": body[:60000]}))

    def _triggers(self) -> None:
        rows = self.sf.query(
            "SELECT Id, Name, TableEnumOrId, Status, Body, UsageBeforeInsert, UsageAfterInsert, "
            "UsageBeforeUpdate, UsageAfterUpdate, UsageBeforeDelete, UsageAfterDelete, UsageAfterUndelete "
            "FROM ApexTrigger WHERE NamespacePrefix = null LIMIT 2000")
        for r in rows:
            events = [k[5:] for k, v in r.items() if k.startswith("Usage") and v is True]
            tid = f"trigger:{r['Name'].lower()}"
            obj = self.resolve_object(r.get("TableEnumOrId"))
            self.graph.add_node(Node(tid, "ApexTrigger", r["Name"], r["Name"], properties={
                "status": r.get("Status"), "events": events, "trigger_object": obj,
                "_body": (r.get("Body") or "")[:60000]}))
            if obj:
                self.graph.add_edge(Edge("TRIGGER_FIRES_ON_SOBJECT", tid, self.ensure_sobject(obj)))

    def _flows(self) -> None:
        g = self.graph
        rows = self.sf.query(
            "SELECT Id, ApiName, Label, ProcessType, TriggerType, TriggerObjectOrEventLabel, IsActive, "
            "ActiveVersionId, Description FROM FlowDefinitionView LIMIT 200")
        if len(rows) == 200:
            g.notes.append("FlowDefinitionView returned 200 rows, its single-batch maximum; some flows may be missing")
        active: list[tuple[str, str, str | None]] = []
        for r in rows:
            fid = f"flow:{r['ApiName'].lower()}"
            obj = self.resolve_object(r.get("TriggerObjectOrEventLabel"))
            g.add_node(Node(fid, "Flow", r.get("Label") or r["ApiName"], r["ApiName"], properties={
                "label": r.get("Label"), "process_type": r.get("ProcessType"),
                "trigger_type": r.get("TriggerType"), "trigger_object": obj,
                "active": r.get("IsActive"), "description": r.get("Description")}))
            if obj and r.get("TriggerType"):
                g.add_edge(Edge("FLOW_TRIGGERS_ON_SOBJECT", fid, self.ensure_sobject(obj)))
            if r.get("IsActive") and r.get("ActiveVersionId"):
                active.append((fid, r["ActiveVersionId"], obj))
        for fid, version_id, trigger_obj in active[: self.flow_metadata_max]:
            try:
                rec = self.sf.tooling_query(f"SELECT Id, Metadata FROM Flow WHERE Id = '{version_id}'")
            except Exception as exc:  # noqa: BLE001
                g.notes.append(f"flow metadata unreadable ({str(exc)[:100]}); flow internals not in graph")
                return
            if rec:
                self._flow_internals(fid, rec[0].get("Metadata") or {}, trigger_obj)
        if len(active) > self.flow_metadata_max:
            g.notes.append(f"flow internals read for {self.flow_metadata_max} of {len(active)} active flows")

    def _flow_internals(self, fid: str, md: dict, trigger_obj: str | None) -> None:
        g = self.graph

        def target(item: dict) -> str | None:
            if item.get("object"):
                return self.resolve_object(item["object"])
            if (item.get("inputReference") or "").startswith("$Record"):
                return trigger_obj
            return None

        for key, edge in (("recordCreates", "FLOW_CREATES_SOBJECT"), ("recordUpdates", "FLOW_UPDATES_SOBJECT"),
                          ("recordLookups", "FLOW_READS_SOBJECT"), ("recordDeletes", "FLOW_UPDATES_SOBJECT")):
            for item in md.get(key) or []:
                obj = target(item)
                if obj:
                    g.add_edge(Edge(edge, fid, self.ensure_sobject(obj)))
                    if key == "recordUpdates":
                        for a in item.get("inputAssignments") or []:
                            if a.get("field"):
                                g.nodes[fid].properties.setdefault("fields_updated", []).append(f"{obj}.{a['field']}")
        for sub in md.get("subflows") or []:
            if sub.get("flowName"):
                g.add_edge(Edge("FLOW_CALLS_SUBFLOW", fid, f"flow:{sub['flowName'].lower()}"))
        for call in md.get("actionCalls") or []:
            if (call.get("actionType") or "").lower() == "apex" and call.get("actionName"):
                g.add_edge(Edge("FLOW_CALLS_APEX", fid, f"apex:{call['actionName'].lower()}"))

    def _lwc(self) -> None:
        for r in self.sf.tooling_query("SELECT Id, DeveloperName, MasterLabel, Description "
                                       "FROM LightningComponentBundle WHERE NamespacePrefix = null"):
            self.graph.add_node(Node(f"lwc:{r['DeveloperName'].lower()}", "LWC", r.get("MasterLabel") or r["DeveloperName"],
                                     r["DeveloperName"], properties={"description": r.get("Description")}))

    def _validation_rules(self) -> None:
        for r in self.sf.tooling_query("SELECT Id, ValidationName, Active, ErrorMessage, "
                                       "EntityDefinition.QualifiedApiName FROM ValidationRule"):
            obj = (r.get("EntityDefinition") or {}).get("QualifiedApiName")
            if not obj:
                continue
            vid = f"vr:{obj.lower()}.{r['ValidationName'].lower()}"
            self.graph.add_node(Node(vid, "ValidationRule", r["ValidationName"], f"{obj}.{r['ValidationName']}",
                                     properties={"active": r.get("Active"), "error_message": r.get("ErrorMessage")}))
            self.graph.add_edge(Edge("VALIDATES_SOBJECT", vid, self.ensure_sobject(obj)))

    def _dep_node(self, kind: str, name: str, ref_id: str) -> str | None:
        if kind == "ApexClass":
            return f"apex:{name.lower()}"
        if kind == "ApexTrigger":
            return f"trigger:{name.lower()}"
        if kind == "LightningComponentBundle":
            return f"lwc:{name.lower()}"
        if kind == "Flow":
            return f"flow:{name.lower()}"
        if kind == "StandardEntity":
            return self.ensure_sobject(name) if name.lower() in self.api_names else None
        if kind == "CustomObject":
            api = self.custom_object_ids.get((ref_id or "")[:15])
            return self.ensure_sobject(api) if api else None
        if kind == "CustomField":
            hit = self.custom_field_ids.get((ref_id or "")[:15])
            return f"field:{hit[0].lower()}.{hit[1].lower()}" if hit else None
        return None

    def _dependencies(self) -> None:
        rows = self.sf.tooling_query(
            "SELECT MetadataComponentId, MetadataComponentName, MetadataComponentType, RefMetadataComponentId, "
            "RefMetadataComponentName, RefMetadataComponentType FROM MetadataComponentDependency "
            "WHERE MetadataComponentType IN ('ApexClass','ApexTrigger','LightningComponentBundle','Flow') LIMIT 2000")
        if len(rows) >= 2000:
            self.graph.notes.append("dependency api returned its 2000-row maximum; some dependencies missing")
        for r in rows:
            src = self._dep_node(r["MetadataComponentType"], r["MetadataComponentName"], r["MetadataComponentId"])
            dst = self._dep_node(r["RefMetadataComponentType"], r["RefMetadataComponentName"], r["RefMetadataComponentId"])
            if not (src and dst):
                continue
            s_kind, d_kind = src.split(":")[0], dst.split(":")[0]
            edge = {("lwc", "apex"): "LWC_CALLS_APEX", ("trigger", "apex"): "TRIGGER_CALLS_APEX",
                    ("apex", "apex"): "APEX_CALLS_APEX", ("flow", "apex"): "FLOW_CALLS_APEX",
                    ("apex", "sobj"): "APEX_REFERENCES_SOBJECT", ("trigger", "sobj"): "APEX_REFERENCES_SOBJECT",
                    ("apex", "field"): "APEX_REFERENCES_FIELD", ("trigger", "field"): "APEX_REFERENCES_FIELD",
                    }.get((s_kind, d_kind), "DEPENDS_ON")
            self.graph.add_edge(Edge(edge, src, dst, origin="dependency-api"))

    def _body_scan(self) -> None:
        """Fallback for what the dependency API missed. Whole identifiers only:
        `Account` must not match `AccountingCode`."""
        g = self.graph
        objects = {a.lower(): a for a in self.scoped}
        for node in list(g.nodes.values()):
            body = node.properties.pop("_body", None)
            if not body or node.node_type not in {"ApexClass", "ApexTrigger"}:
                continue
            idents = set(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", body))
            lowered = {i.lower() for i in idents}
            for low in lowered & set(objects):
                g.add_edge(Edge("APEX_REFERENCES_SOBJECT", node.id, sobj_id(objects[low]),
                                origin="body-scan", confidence=0.6))
            for low in lowered & set(self.class_names):
                if f"apex:{low}" == node.id:
                    continue
                edge = "TRIGGER_CALLS_APEX" if node.node_type == "ApexTrigger" else "APEX_CALLS_APEX"
                g.add_edge(Edge(edge, node.id, f"apex:{low}", origin="body-scan", confidence=0.6))


def ingest_jira(jira: JiraClient, graph: Graph, max_issues: int = 300) -> None:
    """Tickets become nodes; parent, links and component mentions become edges.
    Run after the Salesforce ingest so mentions can resolve."""
    issues = jira.project_issues(max_results=max_issues)
    for issue in issues:
        t = simplify(issue, jira.browse_url(issue["key"]))
        tid = f"ticket:{t['key'].lower()}"
        graph.add_node(Node(tid, "JiraTicket", t["summary"] or t["key"], t["key"], source_system="JIRA",
                            properties={"summary": t["summary"], "status": t["status"], "type": t["type"],
                                        "url": t["url"], "labels": t["labels"]}))
        if t["parent"]:
            graph.add_edge(Edge("TICKET_PARENT_OF", f"ticket:{t['parent'].lower()}", tid, origin="jira"))
        for link in t["links"]:
            if link.get("key"):
                graph.add_edge(Edge("TICKET_LINKS_TO", tid, f"ticket:{link['key'].lower()}", origin="jira"))
        text = f"{t['summary']}\n{t['description']}"
        for node, score in graph.search(text, limit=8, types=COMPONENT_TYPES):
            if score >= 1.5:
                graph.add_edge(Edge("TICKET_MENTIONS", tid, node.id, origin="text-match", confidence=0.5))
    graph.notes.append(f"jira: {len(issues)} tickets from project {jira.project_key}")
    graph.prune_dangling()
