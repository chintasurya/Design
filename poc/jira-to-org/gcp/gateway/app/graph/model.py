"""The knowledge graph: typed nodes, typed edges, search and bounded traversal.

Node ids are stable and readable: `sobj:account`, `field:account.rating`,
`apex:accountservice`, `trigger:accounttrigger`, `flow:account_after_save`,
`lwc:accountcard`, `vr:account.require_rating`, `ticket:kan-12`.

Two rules carried over from the earlier Network Services POC, both paid for:

* Traversal walks behaviour before structure. An object with 200 fields would
  otherwise spend the node budget on columns and never reach the trigger or
  flow that answers the question.
* An SObject that the question did not name is a destination, not a corridor.
  Expanding through Account fans out to every class that mentions Account.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Iterable

BEHAVIOUR_EDGES = (
    "TRIGGER_FIRES_ON_SOBJECT", "FLOW_TRIGGERS_ON_SOBJECT", "FLOW_CREATES_SOBJECT",
    "FLOW_UPDATES_SOBJECT", "FLOW_CALLS_SUBFLOW", "FLOW_CALLS_APEX",
    "TRIGGER_CALLS_APEX", "APEX_CALLS_APEX", "LWC_CALLS_APEX", "VALIDATES_SOBJECT",
    "APEX_REFERENCES_SOBJECT", "APEX_REFERENCES_FIELD", "DEPENDS_ON",
    "TICKET_IMPLEMENTED_BY", "TICKET_MENTIONS",
)
STRUCTURE_EDGES = (
    "SOBJECT_HAS_FIELD", "SOBJECT_HAS_RECORDTYPE", "FIELD_REFERENCES_SOBJECT",
    "FLOW_READS_SOBJECT", "TICKET_PARENT_OF", "TICKET_LINKS_TO",
)
EDGE_PRIORITY = {e: i for i, e in enumerate(BEHAVIOUR_EDGES + STRUCTURE_EDGES)}

COMPONENT_TYPES = ("SObject", "Field", "RecordType", "ApexClass", "ApexTrigger",
                   "Flow", "LWC", "ValidationRule")

STOPWORDS = {
    "a", "an", "the", "and", "or", "to", "of", "on", "in", "for", "with", "is", "are",
    "be", "as", "at", "by", "it", "this", "that", "when", "should", "must", "will",
    "can", "new", "create", "add", "update", "field", "object", "record", "records",
    "user", "users", "page", "show", "need", "needs", "want", "we", "i", "so", "from",
    "into", "if", "not", "all", "any", "has", "have", "c", "id", "name", "type",
}


def tokens(text: str) -> list[str]:
    """Whole identifier tokens: camelCase, snake_case and `__c` split apart."""
    text = re.sub(r"__c\b|__r\b", " ", text or "")
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", text)
    return [t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t]


def content_tokens(text: str) -> set[str]:
    return {t for t in tokens(text) if t not in STOPWORDS and len(t) > 1}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9_.\-]+", "_", (text or "").lower()).strip("_")


@dataclass
class Node:
    id: str
    node_type: str
    name: str
    api_name: str = ""
    source_system: str = "SALESFORCE"
    properties: dict = field(default_factory=dict)

    def label(self) -> str:
        return f"{self.node_type} {self.api_name or self.name}"


@dataclass
class Edge:
    edge_type: str
    from_id: str
    to_id: str
    origin: str = "ingest"
    confidence: float = 1.0

    @property
    def id(self) -> str:
        return f"{self.from_id}|{self.edge_type}|{self.to_id}"


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        self.notes: list[str] = []
        self._out: dict[str, list[Edge]] = defaultdict(list)
        self._in: dict[str, list[Edge]] = defaultdict(list)
        self._index_dirty = True
        self._token_index: dict[str, set[str]] = defaultdict(set)

    # -- building -----------------------------------------------------------
    def add_node(self, node: Node) -> Node:
        existing = self.nodes.get(node.id)
        if existing:
            existing.properties.update(node.properties)
            return existing
        self.nodes[node.id] = node
        self._index_dirty = True
        return node

    def add_edge(self, edge: Edge) -> None:
        if edge.from_id == edge.to_id or edge.id in self.edges:
            return
        self.edges[edge.id] = edge
        self._out[edge.from_id].append(edge)
        self._in[edge.to_id].append(edge)

    def prune_dangling(self) -> int:
        """Drop edges whose endpoints never arrived. Returns how many."""
        bad = [e for e in self.edges.values() if e.from_id not in self.nodes or e.to_id not in self.nodes]
        for e in bad:
            del self.edges[e.id]
            self._out[e.from_id].remove(e)
            self._in[e.to_id].remove(e)
        return len(bad)

    def merge(self, other: "Graph") -> None:
        for n in other.nodes.values():
            self.add_node(Node(**asdict(n)))
        for e in other.edges.values():
            self.add_edge(Edge(**{k: v for k, v in asdict(e).items()}))

    # -- lookup -------------------------------------------------------------
    def _reindex(self) -> None:
        self._token_index = defaultdict(set)
        for n in self.nodes.values():
            for t in content_tokens(f"{n.name} {n.api_name} {n.properties.get('label', '')}"):
                self._token_index[t].add(n.id)
        self._index_dirty = False

    def neighbours(self, node_id: str) -> list[tuple[Edge, str]]:
        out = [(e, e.to_id) for e in self._out.get(node_id, [])]
        inn = [(e, e.from_id) for e in self._in.get(node_id, [])]
        return sorted(out + inn, key=lambda p: EDGE_PRIORITY.get(p[0].edge_type, 99))

    def find_sobject(self, name: str) -> Node | None:
        key = slug(re.sub(r"__c$", "", name.strip(), flags=re.I)).replace("_", "")
        for n in self.nodes.values():
            if n.node_type != "SObject":
                continue
            candidates = {slug(n.api_name).replace("_", ""), slug(re.sub(r"__c$", "", n.api_name, flags=re.I)).replace("_", ""),
                          slug(n.properties.get("label", "")).replace("_", "")}
            if key in candidates:
                return n
        return None

    def field_exists(self, sobject: str, field_name: str) -> dict:
        """Budget-free existence check. Never inferred from a bounded traversal."""
        obj = self.find_sobject(sobject)
        if not obj:
            return {"object_found": False, "object": sobject, "exists": False,
                    "note": f"{sobject} is not in the graph; existence is unknown, not absent"}
        want = slug(re.sub(r"__c$", "", field_name.strip(), flags=re.I)).replace("_", "")
        for e in self._out.get(obj.id, []):
            if e.edge_type != "SOBJECT_HAS_FIELD":
                continue
            f = self.nodes[e.to_id]
            names = {slug(re.sub(r"__c$", "", f.api_name.split(".")[-1], flags=re.I)).replace("_", ""),
                     slug(f.properties.get("label", "")).replace("_", "")}
            if want in names:
                found = {"object_found": True, "object": obj.api_name, "exists": True,
                         "field": f.api_name, "label": f.properties.get("label"),
                         "data_type": f.properties.get("type")}
                if f.properties.get("fls_hidden"):
                    found["note"] = "exists but no field-level security grants access; reuse it and grant FLS"
                return found
        return {"object_found": True, "object": obj.api_name, "exists": False}

    def search(self, text: str, limit: int = 12, types: Iterable[str] | None = None) -> list[tuple[Node, float]]:
        """Rank nodes whose name tokens appear in the text (whole tokens only)."""
        if self._index_dirty:
            self._reindex()
        wanted = content_tokens(text)
        allowed = set(types) if types else None
        scores: dict[str, float] = defaultdict(float)
        for t in wanted:
            for nid in self._token_index.get(t, ()):
                scores[nid] += 1.0
        ranked = []
        for nid, hits in scores.items():
            n = self.nodes[nid]
            if allowed and n.node_type not in allowed:
                continue
            own = content_tokens(f"{n.name} {n.api_name}") or {"_"}
            coverage = len(own & wanted) / len(own)
            if coverage < 0.5:
                continue
            bonus = 0.5 if n.node_type in {"SObject", "ApexClass", "ApexTrigger", "Flow", "LWC"} else 0.0
            ranked.append((n, round(hits * coverage + bonus, 3)))
        # tickets by key
        for key in re.findall(r"\b[A-Za-z][A-Za-z0-9]{1,9}-\d+\b", text or ""):
            n = self.nodes.get(f"ticket:{key.lower()}")
            if n:
                ranked.append((n, 10.0))
        ranked.sort(key=lambda p: (-p[1], p[0].id))
        seen, out = set(), []
        for n, s in ranked:
            if n.id not in seen:
                seen.add(n.id)
                out.append((n, s))
        return out[:limit]

    def neighbourhood(self, seed_ids: list[str], hops: int = 2, max_nodes: int = 60,
                      exclude_types: Iterable[str] = ()) -> tuple[list[Node], list[Edge]]:
        excluded = set(exclude_types)
        seeds = [s for s in seed_ids if s in self.nodes]
        seen = set(seeds)
        frontier = list(seeds)
        edges: dict[str, Edge] = {}
        for _ in range(hops):
            nxt = []
            for nid in frontier:
                node = self.nodes[nid]
                # an SObject the question did not name is never expanded through
                if node.node_type == "SObject" and nid not in seeds:
                    continue
                for e, other in self.neighbours(nid):
                    if self.nodes[other].node_type in excluded:
                        continue
                    edges[e.id] = e
                    if other not in seen:
                        if len(seen) >= max_nodes:
                            break
                        seen.add(other)
                        nxt.append(other)
            frontier = nxt
        nodes = [self.nodes[i] for i in seen]
        return nodes, [e for e in edges.values() if e.from_id in seen and e.to_id in seen]

    # -- presentation -------------------------------------------------------
    def describe_edge(self, e: Edge) -> str:
        a, b = self.nodes[e.from_id], self.nodes[e.to_id]
        verb = e.edge_type.lower().replace("_", " ")
        return f"{a.label()} --{verb}--> {b.label()}"

    def out_edges(self, node_id: str) -> list[Edge]:
        return list(self._out.get(node_id, []))

    def context_slice(self, text: str, max_nodes: int = 60, max_related: int = 120, max_matches: int = 12) -> dict:
        """What an agent gets: the matches, then the behaviour around them, as sentences."""
        matches = self.search(text, limit=max_matches)
        seed_ids = [n.id for n, _ in matches]
        nodes, edges = self.neighbourhood(seed_ids, hops=2, max_nodes=max_nodes)
        edges.sort(key=lambda e: EDGE_PRIORITY.get(e.edge_type, 99))
        return {
            "matches": [{"id": n.id, "type": n.node_type, "api_name": n.api_name or n.name,
                         "score": s, "properties": _short_props(n)} for n, s in matches],
            "related": [self.describe_edge(e) for e in edges[:max_related]],
            "node_count": len(nodes),
            "graph_size": {"nodes": len(self.nodes), "edges": len(self.edges)},
        }

    def stats(self) -> dict:
        by_type: dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            by_type[n.node_type] += 1
        by_edge: dict[str, int] = defaultdict(int)
        for e in self.edges.values():
            by_edge[e.edge_type] += 1
        return {"nodes": len(self.nodes), "edges": len(self.edges),
                "node_types": dict(sorted(by_type.items())), "edge_types": dict(sorted(by_edge.items()))}

    def schema(self) -> dict:
        """The graph at type level: which kinds of thing connect to which, and how often."""
        node_counts: dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            node_counts[n.node_type] += 1
        links: dict[tuple[str, str, str], int] = defaultdict(int)
        for e in self.edges.values():
            links[(self.nodes[e.from_id].node_type, e.edge_type, self.nodes[e.to_id].node_type)] += 1
        return {
            "node_types": [{"type": t, "count": c} for t, c in sorted(node_counts.items(), key=lambda p: -p[1])],
            "edge_types": [{"from_type": a, "edge_type": et, "to_type": b, "count": c}
                           for (a, et, b), c in sorted(links.items(), key=lambda p: -p[1])],
        }

    def ego(self, node_id: str, max_nodes: int = 36) -> dict:
        """One component and what it touches directly, behaviour first, for drawing.
        Fields are folded into a count unless the centre is a field itself."""
        centre = self.nodes[node_id]
        nodes: dict[str, Node] = {node_id: centre}
        edges: list[dict] = []
        hidden_fields = 0
        for e, other in self.neighbours(node_id):
            o = self.nodes[other]
            if o.node_type == "Field" and centre.node_type == "SObject":
                hidden_fields += 1
                continue
            if other not in nodes:
                if len(nodes) >= max_nodes:
                    continue
                nodes[other] = o
            edges.append({"from": e.from_id, "to": e.to_id, "type": e.edge_type, "origin": e.origin})
        return {
            "centre": node_id,
            "nodes": [{"id": n.id, "type": n.node_type, "label": n.api_name or n.name,
                       "degree": len(self._out.get(n.id, [])) + len(self._in.get(n.id, [])),
                       "properties": _short_props(n)} for n in nodes.values()],
            "edges": edges,
            "fields_folded": hidden_fields,
        }

    # -- serialisation ------------------------------------------------------
    def to_dict(self) -> dict:
        return {"nodes": [asdict(n) for n in self.nodes.values()],
                "edges": [asdict(e) for e in self.edges.values()],
                "notes": self.notes}

    @classmethod
    def from_dict(cls, data: dict) -> "Graph":
        g = cls()
        for n in data.get("nodes", []):
            g.add_node(Node(**n))
        for e in data.get("edges", []):
            g.add_edge(Edge(**e))
        g.notes = list(data.get("notes", []))
        g.prune_dangling()
        return g


def _short_props(n: Node) -> dict:
    keep = ("label", "type", "status", "summary", "process_type", "trigger_object", "fls_hidden",
            "events", "custom", "reference_to", "active", "error_message", "description")
    return {k: v for k, v in n.properties.items() if k in keep and v not in (None, "", [])}
