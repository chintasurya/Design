"""Graph storage. BigQuery on GCP, a JSON file for local runs and tests.

BigQuery layout (dataset `agent_kg` by default):

  nodes, edges         the latest ingested snapshot, replaced on every rebuild
  agent_nodes,         facts the agents wrote back (ticket -> what was built);
  agent_edges          append-only, so a rebuild never erases provenance
  snapshots            one row per rebuild: counts and notes

Writes use load jobs, not streaming inserts, so rows are immediately
queryable and updatable and nothing sits in a streaming buffer.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Protocol

from .model import Edge, Graph, Node


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GraphStore(Protocol):
    def save_snapshot(self, graph: Graph) -> str: ...
    def load(self) -> tuple[Graph, dict]: ...
    def append_agent_facts(self, nodes: list[Node], edges: list[Edge]) -> None: ...


class LocalJsonStore:
    def __init__(self, path: str):
        self.path = path
        self._lock = threading.Lock()

    def _read(self) -> dict:
        if not os.path.exists(self.path):
            return {"snapshot": {}, "graph": {"nodes": [], "edges": []}, "agent": {"nodes": [], "edges": []}}
        with open(self.path, encoding="utf-8") as fh:
            return json.load(fh)

    def _write(self, data: dict) -> None:
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        os.replace(tmp, self.path)

    def save_snapshot(self, graph: Graph) -> str:
        with self._lock:
            data = self._read()
            snap = {"snapshot_id": uuid.uuid4().hex[:12], "built_at": now_iso(), **graph.stats(), "notes": graph.notes}
            data["snapshot"], data["graph"] = snap, graph.to_dict()
            self._write(data)
            return snap["snapshot_id"]

    def load(self) -> tuple[Graph, dict]:
        with self._lock:
            data = self._read()
        g = Graph.from_dict({"nodes": data["graph"]["nodes"] + data["agent"]["nodes"],
                             "edges": data["graph"]["edges"] + data["agent"]["edges"],
                             "notes": data["graph"].get("notes", [])})
        return g, data.get("snapshot", {})

    def append_agent_facts(self, nodes: list[Node], edges: list[Edge]) -> None:
        with self._lock:
            data = self._read()
            data["agent"]["nodes"].extend(asdict(n) for n in nodes)
            data["agent"]["edges"].extend(asdict(e) for e in edges)
            self._write(data)


class BigQueryStore:
    def __init__(self, project: str, dataset: str, location: str = "US"):
        from google.cloud import bigquery  # imported lazily: tests never need it

        self.bq = bigquery
        self.client = bigquery.Client(project=project)
        self.dataset = f"{project}.{dataset}"
        self.location = location
        self._ensured = False

    # schemas ---------------------------------------------------------------
    def _schemas(self) -> dict:
        F = self.bq.SchemaField
        node = [F("id", "STRING", "REQUIRED"), F("node_type", "STRING"), F("name", "STRING"),
                F("api_name", "STRING"), F("source_system", "STRING"), F("properties", "STRING"),
                F("snapshot_id", "STRING"), F("written_at", "TIMESTAMP")]
        edge = [F("id", "STRING", "REQUIRED"), F("edge_type", "STRING"), F("from_id", "STRING"),
                F("to_id", "STRING"), F("origin", "STRING"), F("confidence", "FLOAT"),
                F("snapshot_id", "STRING"), F("written_at", "TIMESTAMP")]
        snap = [F("snapshot_id", "STRING", "REQUIRED"), F("built_at", "TIMESTAMP"), F("nodes", "INTEGER"),
                F("edges", "INTEGER"), F("node_types", "STRING"), F("edge_types", "STRING"), F("notes", "STRING")]
        return {"nodes": node, "edges": edge, "agent_nodes": node, "agent_edges": edge, "snapshots": snap}

    def ensure(self) -> None:
        if self._ensured:
            return
        ds = self.bq.Dataset(self.dataset)
        ds.location = self.location
        self.client.create_dataset(ds, exists_ok=True)
        for name, schema in self._schemas().items():
            self.client.create_table(self.bq.Table(f"{self.dataset}.{name}", schema=schema), exists_ok=True)
        self._ensured = True

    def _load(self, table: str, rows: list[dict], truncate: bool) -> None:
        if not rows and not truncate:
            return
        cfg = self.bq.LoadJobConfig(
            schema=self._schemas()[table],
            write_disposition="WRITE_TRUNCATE" if truncate else "WRITE_APPEND",
            source_format=self.bq.SourceFormat.NEWLINE_DELIMITED_JSON,
        )
        self.client.load_table_from_json(rows, f"{self.dataset}.{table}", job_config=cfg).result()

    @staticmethod
    def _node_row(n: Node, snap: str, at: str) -> dict:
        return {"id": n.id, "node_type": n.node_type, "name": n.name, "api_name": n.api_name,
                "source_system": n.source_system, "properties": json.dumps(n.properties, default=str),
                "snapshot_id": snap, "written_at": at}

    @staticmethod
    def _edge_row(e: Edge, snap: str, at: str) -> dict:
        return {"id": e.id, "edge_type": e.edge_type, "from_id": e.from_id, "to_id": e.to_id,
                "origin": e.origin, "confidence": e.confidence, "snapshot_id": snap, "written_at": at}

    # store API -------------------------------------------------------------
    def save_snapshot(self, graph: Graph) -> str:
        self.ensure()
        snap, at = uuid.uuid4().hex[:12], now_iso()
        self._load("nodes", [self._node_row(n, snap, at) for n in graph.nodes.values()], truncate=True)
        self._load("edges", [self._edge_row(e, snap, at) for e in graph.edges.values()], truncate=True)
        st = graph.stats()
        self._load("snapshots", [{"snapshot_id": snap, "built_at": at, "nodes": st["nodes"], "edges": st["edges"],
                                  "node_types": json.dumps(st["node_types"]), "edge_types": json.dumps(st["edge_types"]),
                                  "notes": json.dumps(graph.notes)}], truncate=False)
        return snap

    def load(self) -> tuple[Graph, dict]:
        self.ensure()
        q = self.client.query
        g = Graph()
        for table in ("nodes", "agent_nodes"):
            for r in q(f"SELECT id, node_type, name, api_name, source_system, properties FROM `{self.dataset}.{table}`").result():
                g.add_node(Node(r.id, r.node_type, r.name or "", r.api_name or "", r.source_system or "",
                                json.loads(r.properties or "{}")))
        for table in ("edges", "agent_edges"):
            for r in q(f"SELECT edge_type, from_id, to_id, origin, confidence FROM `{self.dataset}.{table}`").result():
                g.add_edge(Edge(r.edge_type, r.from_id, r.to_id, r.origin or "", float(r.confidence or 1.0)))
        g.prune_dangling()
        snap: dict = {}
        rows = list(q(f"SELECT * FROM `{self.dataset}.snapshots` ORDER BY built_at DESC LIMIT 1").result())
        if rows:
            r = rows[0]
            snap = {"snapshot_id": r.snapshot_id, "built_at": r.built_at.isoformat(), "nodes": r.nodes,
                    "edges": r.edges, "notes": json.loads(r.notes or "[]")}
            g.notes = snap["notes"]
        return g, snap

    def append_agent_facts(self, nodes: list[Node], edges: list[Edge]) -> None:
        self.ensure()
        at = now_iso()
        self._load("agent_nodes", [self._node_row(n, "agent", at) for n in nodes], truncate=False)
        self._load("agent_edges", [self._edge_row(e, "agent", at) for e in edges], truncate=False)


class GraphService:
    """Caches the loaded graph; agents read from memory, rebuilds replace it."""

    def __init__(self, store: GraphStore, ttl_s: int = 600):
        self.store = store
        self.ttl_s = ttl_s
        self._graph: Graph | None = None
        self._snapshot: dict = {}
        self._loaded_at = 0.0
        self._lock = threading.Lock()

    def graph(self) -> Graph:
        with self._lock:
            if self._graph is None or time.time() - self._loaded_at > self.ttl_s:
                self._graph, self._snapshot = self.store.load()
                self._loaded_at = time.time()
            return self._graph

    def snapshot(self) -> dict:
        self.graph()
        return self._snapshot

    def replace(self, graph: Graph) -> str:
        snap = self.store.save_snapshot(graph)
        with self._lock:
            self._graph = None  # reload so agent facts are merged back in
        return snap

    def record(self, nodes: list[Node], edges: list[Edge]) -> None:
        self.store.append_agent_facts(nodes, edges)
        with self._lock:
            if self._graph is not None:
                for n in nodes:
                    self._graph.add_node(n)
                for e in edges:
                    self._graph.add_edge(e)
