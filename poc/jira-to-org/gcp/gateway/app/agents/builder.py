"""Declarative builder: metadata the gateway writes itself, with no model call.

A ticket that only adds custom fields (and their access) needs no code
generation: the Requirement agent's spec already holds each field's type,
label and help text. Writing that XML from a template costs 0 tokens, where
an agentic Codex run cost ~45k per attempt. Anything this builder cannot
build goes to Codex.
"""
from __future__ import annotations

import os
import re
from xml.sax.saxutils import escape

SOURCE_ROOT = "force-app/main/default"
PERMISSION_SET = "HarnessAgentAccess"
PERMISSION_SET_PATH = f"{SOURCE_ROOT}/permissionsets/{PERMISSION_SET}.permissionset-meta.xml"
NS = "http://soap.sforce.com/2006/04/metadata"
API_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*\.[A-Za-z][A-Za-z0-9]*__c$")
BUILDABLE_TYPES = {"Text", "TextArea", "LongTextArea", "Number", "Currency", "Percent", "Checkbox", "Date",
                   "DateTime", "Email", "Phone", "Url", "Picklist"}


def _tag(name: str, value) -> str:
    if isinstance(value, bool):
        value = "true" if value else "false"
    return f"    <{name}>{escape(str(value))}</{name}>\n"


def buildable(spec: dict) -> bool:
    """Only new custom fields with a full definition, plus the permission set
    that grants them. Everything else needs Codex."""
    comps = spec.get("components") or []
    fields = [c for c in comps if c.get("type") == "CustomField"]
    if not fields:
        return False
    for c in comps:
        if c.get("type") == "PermissionSet" and c.get("api_name", "").split(".")[-1] == PERMISSION_SET:
            continue
        if c.get("type") != "CustomField" or c.get("action") != "create" or c.get("exists_in_org"):
            return False
        f = c.get("field") or {}
        if not API_NAME.match(c.get("api_name", "")) or f.get("data_type") not in BUILDABLE_TYPES \
                or not (f.get("label") or "").strip():
            return False
        if f["data_type"] == "Picklist" and not f.get("picklist_values"):
            return False
    return True


def field_xml(comp: dict) -> str:
    name = comp["api_name"].split(".", 1)[1]
    f = comp["field"]
    t = f["data_type"]
    out = ['<?xml version="1.0" encoding="UTF-8"?>\n', f'<CustomField xmlns="{NS}">\n', _tag("fullName", name)]
    if t == "Checkbox":
        out.append(_tag("defaultValue", (f.get("default_value") or "false").lower() == "true"))
    elif f.get("default_value"):
        out.append(_tag("defaultValue", f["default_value"]))
    out.append(_tag("description", comp.get("description") or f["label"]))
    out.append(_tag("inlineHelpText", f.get("help_text") or comp.get("description") or f["label"]))
    out.append(_tag("label", f["label"][:40]))
    if t in ("Text",):
        out.append(_tag("length", min(int(f.get("length") or 255), 255)))
    if t == "LongTextArea":
        out.append(_tag("length", min(int(f.get("length") or 32768), 131072)))
    if t in ("Number", "Currency", "Percent"):
        out.append(_tag("precision", int(f.get("precision") or 18)))
    if t != "Checkbox":
        out.append(_tag("required", bool(f.get("required"))))
    if t in ("Number", "Currency", "Percent"):
        out.append(_tag("scale", int(f.get("scale") if f.get("scale") is not None else (2 if t == "Currency" else 0))))
    out.append(_tag("type", t))
    if t == "LongTextArea":
        out.append(_tag("visibleLines", 3))
    if t == "Picklist":
        values = "".join(f"            <value>\n                <fullName>{escape(v)}</fullName>\n"
                         f"                <default>false</default>\n                <label>{escape(v)}</label>\n"
                         "            </value>\n" for v in f["picklist_values"])
        out.append("    <valueSet>\n        <restricted>true</restricted>\n        <valueSetDefinition>\n"
                   f"            <sorted>false</sorted>\n{values}        </valueSetDefinition>\n    </valueSet>\n")
    out.append("</CustomField>\n")
    return "".join(out)


def _field_permission(api_name: str) -> str:
    return ("    <fieldPermissions>\n        <editable>true</editable>\n"
            f"        <field>{escape(api_name)}</field>\n        <readable>true</readable>\n"
            "    </fieldPermissions>\n")


def permission_set_xml(existing: str | None, grant: list[str]) -> str:
    """Add field access to HarnessAgentAccess: merged into the copy retrieved
    from the org when there is one, so nothing it already grants is lost."""
    if existing and "</PermissionSet>" in existing:
        add = "".join(_field_permission(a) for a in grant if f"<field>{a}</field>" not in existing)
        if not add:
            return existing
        # Salesforce wants each element group together, groups in alphabetical
        # order: new access goes right after the existing fieldPermissions, or
        # before the first element that sorts after it (never simply at the end).
        last = existing.rfind("</fieldPermissions>")
        if last >= 0:
            at = existing.index("\n", last) + 1
        else:
            later = [m for m in re.finditer(r"^    <([A-Za-z]+)[ />]", existing, re.M) if m.group(1) > "fieldPermissions"]
            at = later[0].start() if later else existing.rindex("</PermissionSet>")
        return existing[:at] + add + existing[at:]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<PermissionSet xmlns="{NS}">\n'
            + _tag("description", "Access to what the Agentic Harness developer agent builds.")
            + "".join(_field_permission(a) for a in grant)
            + _tag("hasActivationRequired", False) + _tag("label", "Harness Agent Access")
            + "</PermissionSet>\n")


def build(ws: str, spec: dict) -> list[str]:
    """Write the fields and their access into the workspace. Returns the paths."""
    written, grant = [], []
    for comp in spec.get("components") or []:
        if comp.get("type") != "CustomField":
            continue
        obj, name = comp["api_name"].split(".", 1)
        rel = f"{SOURCE_ROOT}/objects/{obj}/fields/{name}.field-meta.xml"
        full = os.path.join(ws, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(field_xml(comp))
        written.append(rel)
        if not comp["field"].get("required"):  # Salesforce refuses access settings on required fields
            grant.append(comp["api_name"])
    if grant:
        full = os.path.join(ws, PERMISSION_SET_PATH)
        existing = None
        if os.path.exists(full):
            with open(full, encoding="utf-8") as fh:
                existing = fh.read()
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(permission_set_xml(existing, grant))
        written.append(PERMISSION_SET_PATH)
    return written
