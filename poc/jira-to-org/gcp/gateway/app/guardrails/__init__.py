"""Guardrails: the development standards every agent follows.

The pack lives in GCP, not in Salesforce: Firestore collection
`guardrail_rules` (one document per rule: area, title, rule, severity,
check) plus `guardrail_packs/active` (name, summary). Edit a rule in the
Firestore console, or edit `ascension-guardrails.json` and run
`infra/load_guardrails.py`; agents pick changes up within a minute.

severity: block (a deploy cannot happen while it is broken), warn (shown
on the scorecard), off (ignored). `check` names the automated check in
checks.py that enforces the rule; rules without one are given to the agents
as instructions only.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from typing import Iterable

BUNDLED = os.path.join(os.path.dirname(__file__), "ascension-guardrails.json")

# what each kind of component is governed by
AREAS_FOR = {
    "Flow": ("Flow",), "ApexTrigger": ("Trigger", "Apex", "Test"), "ApexClass": ("Apex", "Test"),
    "LWC": ("LWC",), "CustomField": ("Field",), "CustomObject": ("Object",), "ValidationRule": ("ValidationRule",),
    "PermissionSet": ("PermissionSet",), "Layout": ("Layout",), "Other": (),
}


def load_bundled() -> dict:
    with open(BUNDLED, encoding="utf-8") as fh:
        return json.load(fh)


def fingerprint(pack: dict) -> str:
    return hashlib.sha256(json.dumps(pack.get("rules", []), sort_keys=True).encode()).hexdigest()[:10]


class FirestoreGuardrails:
    def __init__(self, project: str):
        from google.cloud import firestore

        self.db = firestore.Client(project=project)

    def load(self) -> dict | None:
        rules = [d.to_dict() for d in self.db.collection("guardrail_rules").stream()]
        if not rules:
            return None
        meta = self.db.collection("guardrail_packs").document("active").get()
        info = meta.to_dict() if meta.exists else {}
        rules.sort(key=lambda r: (r.get("order", 999), r.get("id", "")))
        return {"name": info.get("name", "Guardrails"), "summary": info.get("summary", ""), "rules": rules}


class GuardrailService:
    def __init__(self, source=None, ttl_s: int = 60):
        self.source = source
        self.ttl_s = ttl_s
        self._pack: dict | None = None
        self._at = 0.0
        self._lock = threading.Lock()

    def pack(self) -> dict:
        with self._lock:
            if self._pack is None or time.time() - self._at > self.ttl_s:
                pack = None
                if self.source is not None:
                    try:
                        pack = self.source.load()
                    except Exception:  # noqa: BLE001 - never run without standards: fall back to the bundled pack
                        pack = None
                pack = pack or {**load_bundled(), "fallback": self.source is not None}
                pack["version"] = fingerprint(pack)
                self._pack, self._at = pack, time.time()
            return self._pack

    def rules(self, areas: Iterable[str] | None = None) -> list[dict]:
        wanted = set(areas) if areas is not None else None
        return [r for r in self.pack()["rules"] if r.get("severity") != "off"
                and (wanted is None or r.get("area") in wanted)]

    def by_id(self) -> dict[str, dict]:
        return {r["id"]: r for r in self.pack()["rules"]}

    def brief(self, areas: Iterable[str]) -> str:
        """The rules for these areas as short instruction lines. Only what the
        change touches is sent to the model, so the standards cost few tokens."""
        lines = [f"- [{r['id']}] {r['title']}: {r['rule']}" for r in self.rules(areas)]
        return "\n".join(lines)


def areas_for_components(components: Iterable[dict]) -> list[str]:
    areas = {"General"}
    for c in components:
        areas.update(AREAS_FOR.get(c.get("type", ""), ()))
    return sorted(areas)
