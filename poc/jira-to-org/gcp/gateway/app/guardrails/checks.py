"""Automated guardrail checks on a Developer agent change set. No model involved.

Each check is named by a rule's `check` field in the pack; the pack decides
whether a finding blocks the deploy or only warns. A finding names the rule,
the file and what to fix, so it can go straight back to Codex.
"""
from __future__ import annotations

import os
import re
import xml.etree.ElementTree as ET
from typing import Callable, Iterable

SOURCE = "force-app/main/default/"
MD = "{http://soap.sforce.com/2006/04/metadata}"

ID_PREFIXES = ("001", "003", "005", "006", "00Q", "500", "00G", "012", "00D", "00e", "00T", "00U", "01I",
               "01p", "0WO", "701", "800", "801", "02i", "00N", "00O", "015", "069", "068")
HARDCODED_ID = re.compile(r"""['"]((?:%s)[0-9A-Za-z]{12}(?:[0-9A-Za-z]{3})?)['"]""" % "|".join(ID_PREFIXES))
SOQL = re.compile(r"\[\s*(SELECT|FIND)\b|Database\.(query|getQueryLocator)\s*\(", re.I)
DML = re.compile(r"\b(insert|update|upsert|delete|undelete|merge)\s+[A-Za-z_(\[]|"
                 r"Database\.(insert|update|upsert|delete|undelete|merge)\s*\(", re.I)
RECORD_ELEMENTS = ("recordCreates", "recordUpdates", "recordDeletes", "recordLookups")
SUFFIX_FOR = (("Database.Batchable", "Batch"), ("Schedulable", "Scheduler"), ("Queueable", "Queueable"))


class Change:
    def __init__(self, path: str, content: str, added: bool):
        self.path = path
        self.content = content
        self.added = added
        self.rel = path[len(SOURCE):] if path.startswith(SOURCE) else path
        self.name = os.path.basename(path)


def finding(rule: str, path: str, message: str) -> dict:
    return {"rule": rule, "file": path, "message": message}


# -- apex text helpers ---------------------------------------------------------
def strip_apex(src: str) -> str:
    """Remove comments and string contents (keeping quotes and line breaks), so
    keywords inside them never count."""
    out, i, n = [], 0, len(src)
    while i < n:
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            seg = src[i:(n if j < 0 else j + 2)]
            out.append("\n" * seg.count("\n"))
            i = n if j < 0 else j + 2
        elif src[i] == "'":
            j = i + 1
            while j < n and src[j] != "'":
                j += 2 if src[j] == "\\" else 1
            out.append("''")
            i = j + 1
        else:
            out.append(src[i])
            i += 1
    return "".join(out)


def _block_end(code: str, start: int) -> int:
    """Index after the statement or {block} that starts at `start`."""
    i = start
    while i < len(code) and code[i].isspace():
        i += 1
    if i < len(code) and code[i] == "{":
        depth = 0
        for j in range(i, len(code)):
            if code[j] == "{":
                depth += 1
            elif code[j] == "}":
                depth -= 1
                if depth == 0:
                    return j + 1
        return len(code)
    j = code.find(";", i)
    return len(code) if j < 0 else j + 1


def _paren_end(code: str, open_idx: int) -> int:
    depth = 0
    for j in range(open_idx, len(code)):
        if code[j] == "(":
            depth += 1
        elif code[j] == ")":
            depth -= 1
            if depth == 0:
                return j + 1
    return len(code)


def loop_bodies(code: str) -> list[str]:
    """Bodies of for/while/do loops. A SOQL for-loop's own query sits in the
    header, which is the recommended pattern, so only bodies are returned."""
    bodies = []
    for m in re.finditer(r"\b(for|while)\s*\(", code):
        header_end = _paren_end(code, m.end() - 1)
        bodies.append(code[header_end:_block_end(code, header_end)])
    for m in re.finditer(r"\bdo\s*\{", code):
        bodies.append(code[m.end() - 1:_block_end(code, m.end() - 1)])
    return bodies


def try_ranges(code: str) -> list[tuple[int, int]]:
    ranges = []
    for m in re.finditer(r"\btry\s*\{", code):
        ranges.append((m.end() - 1, _block_end(code, m.end() - 1)))
    return ranges


def is_test(code: str) -> bool:
    return bool(re.search(r"@isTest\b", code, re.I))


def class_name(code: str) -> str | None:
    m = re.search(r"\b(class|interface)\s+([A-Za-z_]\w*)", code)
    return m.group(2) if m else None


def _upper_camel(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", name))


def _xml(content: str) -> ET.Element | None:
    try:
        return ET.fromstring(content)
    except ET.ParseError:
        return None


def _text(root: ET.Element, tag: str) -> str:
    el = root.find(MD + tag)
    return (el.text or "").strip() if el is not None else ""


# -- checks ----------------------------------------------------------------------
def no_hardcoded_ids(changes, ctx):
    for c in changes:
        if c.name.endswith((".cls", ".trigger", ".flow-meta.xml", ".js")):
            for m in HARDCODED_ID.finditer(c.content):
                yield finding("GEN-02", c.path, f"Hardcoded record ID {m.group(1)}; use Custom Metadata, a Custom "
                                                "Label or a query instead")


def no_profiles(changes, ctx):
    for c in changes:
        if c.rel.startswith("profiles/"):
            yield finding("GEN-04", c.path, "Profiles must not be changed; grant access in a permission set")


def object_naming(changes, ctx):
    for c in changes:
        if c.added and c.name.endswith(".object-meta.xml"):
            api = c.name[: -len(".object-meta.xml")]
            if "_" in api.removesuffix("__c"):
                yield finding("NAM-01", c.path, f"Object {api}: no underscores in the name (e.g. SalesCampaign__c)")
            root = _xml(c.content)
            if root is not None and not _text(root, "description"):
                yield finding("NAM-01", c.path, f"Object {api} has no description")


def field_naming(changes, ctx):
    for c in changes:
        if c.added and c.name.endswith(".field-meta.xml"):
            api = c.name[: -len(".field-meta.xml")]
            base = api.removesuffix("__c")
            if "_" in base:
                yield finding("NAM-02", c.path, f"Field {api}: no underscores in the name "
                                                f"(e.g. {base.replace('_', '')}__c)")
            root = _xml(c.content)
            if root is not None:
                if not _text(root, "description"):
                    yield finding("NAM-02", c.path, f"Field {api} needs a description")
                if not _text(root, "inlineHelpText"):
                    yield finding("NAM-02", c.path, f"Field {api} needs help text (inlineHelpText)")


def permission_set_naming(changes, ctx):
    for c in changes:
        if c.added and c.name.endswith(".permissionset-meta.xml"):
            root = _xml(c.content)
            if root is None:
                continue
            if "_" in _text(root, "label"):
                yield finding("NAM-05", c.path, "Permission set label must not contain underscores")
            if not _text(root, "description"):
                yield finding("NAM-05", c.path, "Permission set needs a description")


def validation_rule_naming(changes, ctx):
    for c in changes:
        if c.added and c.name.endswith(".validationRule-meta.xml"):
            root = _xml(c.content)
            if root is None:
                continue
            name = c.name[: -len(".validationRule-meta.xml")]
            if len(re.findall(r"[A-Z][a-z0-9]*|[a-z0-9]+", name.replace("_", " "))) < 3:
                yield finding("NAM-06", c.path, f"Validation rule {name}: name it [Field Label] [rule applied], "
                                                "e.g. Contact_First_Name_Cannot_Be_Null")
            if not _text(root, "description"):
                yield finding("NAM-06", c.path, f"Validation rule {name} needs a description")
            if not _text(root, "errorMessage"):
                yield finding("NAM-06", c.path, f"Validation rule {name} needs an error message")


def flow_naming(changes, ctx):
    for c in changes:
        if not c.name.endswith(".flow-meta.xml"):
            continue
        root = _xml(c.content)
        if root is None:
            yield finding("FLW-01", c.path, "Flow XML does not parse")
            continue
        api = c.name[: -len(".flow-meta.xml")]
        label = _text(root, "label")
        if c.added and "_" in api:
            yield finding("FLW-01", c.path, f"Flow {api}: no underscores in the name (e.g. UpdateRelatedContactRecord)")
        if "_" in label:
            yield finding("FLW-01", c.path, f"Flow label '{label}' must not contain underscores")
        if re.search(r"\bflow$", label, re.I):
            yield finding("FLW-01", c.path, f"Flow label '{label}' must not end with 'Flow'")
        if not _text(root, "description"):
            yield finding("FLW-01", c.path, f"Flow {api} needs a description of what it does")
        for var in root.findall(MD + "variables"):
            vname = _text(var, "name")
            if vname and not re.fullmatch(r"[a-z][A-Za-z0-9]*", vname):
                yield finding("FLW-01", c.path, f"Flow variable {vname}: use camelCase (e.g. firstName)")


def flow_fault_paths(changes, ctx):
    for c in changes:
        if not c.name.endswith(".flow-meta.xml"):
            continue
        root = _xml(c.content)
        if root is None:
            continue
        for kind in RECORD_ELEMENTS:
            for el in root.findall(MD + kind):
                if el.find(MD + "faultConnector") is None:
                    yield finding("FLW-02", c.path, f"{kind[:-1]} element '{_text(el, 'name')}' has no fault path; "
                                                    "connect it to an error handler")


def one_automation_per_object(changes, ctx):
    graph = ctx.get("graph")
    if graph is None:
        return
    for c in changes:
        obj = None
        if c.added and c.name.endswith(".trigger"):
            m = re.search(r"\btrigger\s+\w+\s+on\s+(\w+)", strip_apex(c.content))
            obj = m.group(1) if m else None
        elif c.added and c.name.endswith(".flow-meta.xml"):
            root = _xml(c.content)
            start = root.find(MD + "start") if root is not None else None
            obj = _text(start, "object") if start is not None else None
        if not obj:
            continue
        existing = [n.api_name for n in graph.nodes.values()
                    if (n.properties.get("trigger_object") or "").lower() == obj.lower()
                    and (n.node_type == "ApexTrigger"
                         or (n.node_type == "Flow" and n.properties.get("trigger_type")))]
        if existing:
            yield finding("FLW-04", c.path, f"{obj} already has automation: {', '.join(sorted(existing)[:5])}. "
                                            "Extend it where possible instead of adding another.")


def apex_naming(changes, ctx):
    for c in changes:
        if not c.name.endswith(".cls"):
            continue
        code = strip_apex(c.content)
        name = class_name(code) or c.name[:-4]
        if not _upper_camel(name):
            yield finding("APX-01", c.path, f"Class {name}: UpperCamelCase, whole words, no underscores")
        if is_test(code) and not name.endswith("Test"):
            yield finding("APX-01", c.path, f"Test class {name} must be named <ClassName>Test")
        for marker, suffix in SUFFIX_FOR:
            if re.search(r"implements[^{]*\b" + re.escape(marker), code) and not name.endswith(suffix):
                yield finding("APX-01", c.path, f"{name} implements {marker}; name it <Name>{suffix}")
        if re.search(r"\binterface\s+" + re.escape(name), code) and not name.startswith("Interface"):
            yield finding("APX-01", c.path, f"Interface {name} must be named Interface<Name>")
        for m in re.finditer(r"\b(?:public|private|protected|global)\s+(?:static\s+|override\s+|virtual\s+)*"
                             r"[\w<>,.\[\]\s]+?\s+(\w+)\s*\(", code):
            method = m.group(1)
            if method != name and method[0].isupper():
                yield finding("APX-01", c.path, f"Method {method} in {name}: use lowerCamelCase")


def apex_sharing(changes, ctx):
    for c in changes:
        if c.name.endswith(".cls"):
            code = strip_apex(c.content)
            if is_test(code) or re.search(r"\binterface\s", code[:400]):
                continue
            head = code[: code.find("{")] if "{" in code else code
            if not re.search(r"\b(with|without|inherited)\s+sharing\b", head):
                yield finding("APX-02", c.path, f"{class_name(code) or c.name}: declare 'with sharing'")


def no_soql_in_loops(changes, ctx):
    for c in changes:
        if c.name.endswith((".cls", ".trigger")):
            for body in loop_bodies(strip_apex(c.content)):
                if SOQL.search(body):
                    yield finding("APX-03", c.path, "SOQL inside a loop; query once before the loop and use a Map/Set")
                    break


def no_dml_in_loops(changes, ctx):
    for c in changes:
        if c.name.endswith((".cls", ".trigger")):
            for body in loop_bodies(strip_apex(c.content)):
                if DML.search(body):
                    yield finding("APX-04", c.path, "DML inside a loop; add records to a List and do one DML after")
                    break


def no_single_record_trigger(changes, ctx):
    for c in changes:
        if c.name.endswith((".cls", ".trigger")) and re.search(r"Trigger\.(new|old)\s*\[\s*0\s*\]",
                                                               strip_apex(c.content), re.I):
            yield finding("APX-05", c.path, "Trigger.new[0] handles only one record; iterate the whole collection")


def dml_in_try(changes, ctx):
    for c in changes:
        if not c.name.endswith(".cls"):
            continue
        code = strip_apex(c.content)
        if is_test(code):
            continue
        ranges = try_ranges(code)
        for m in DML.finditer(code):
            if not any(a <= m.start() < b for a, b in ranges):
                yield finding("APX-06", c.path, "DML outside try/catch; handle the exception gracefully")
                break


def apex_formatting(changes, ctx):
    for c in changes:
        if c.name.endswith((".cls", ".trigger")):
            long_lines = [i + 1 for i, line in enumerate(c.content.splitlines()) if len(line.expandtabs(4)) > 120]
            if long_lines:
                yield finding("APX-09", c.path, f"{len(long_lines)} lines over 120 characters (first: line "
                                                f"{long_lines[0]})")
            if c.name.endswith(".cls") and "/**" not in c.content.split("class", 1)[0]:
                yield finding("APX-09", c.path, "Add a JavaDoc comment on the class")


def trigger_per_object(changes, ctx):
    graph = ctx.get("graph")
    for c in changes:
        if not c.name.endswith(".trigger"):
            continue
        m = re.search(r"\btrigger\s+(\w+)\s+on\s+(\w+)", strip_apex(c.content))
        if not m:
            continue
        name, obj = m.groups()
        # an existing trigger cannot be renamed without deleting it, so naming applies to new ones
        if c.added and name not in (obj, obj.removesuffix("__c")):
            yield finding("TRG-01", c.path, f"Trigger {name} must be named after its object: trigger "
                                            f"{obj.removesuffix('__c')} on {obj}")
        if graph is not None and c.added:
            others = [n.api_name for n in graph.nodes.values() if n.node_type == "ApexTrigger"
                      and (n.properties.get("trigger_object") or "").lower() == obj.lower()
                      and n.api_name.lower() != name.lower()]
            if others:
                yield finding("TRG-01", c.path, f"{obj} already has trigger {', '.join(others)}; one trigger per "
                                                f"object: call {obj.removesuffix('__c')}TriggerHandler from it instead")


def trigger_handler(changes, ctx):
    names = {c.name[:-4] for c in changes if c.name.endswith(".cls")}
    sources = {c.name[:-4]: strip_apex(c.content) for c in changes if c.name.endswith(".cls")}
    graph = ctx.get("graph")
    for c in changes:
        if not c.name.endswith(".trigger"):
            continue
        code = strip_apex(c.content)
        m = re.search(r"\btrigger\s+\w+\s+on\s+(\w+)", code)
        obj = m.group(1).removesuffix("__c") if m else "Object"
        body = code[code.find("{") + 1: code.rfind("}")] if "{" in code else ""
        statements = [s for s in body.split(";") if s.strip()]
        handler = f"{obj}TriggerHandler"
        if len(statements) > 1 or not re.search(r"new\s+\w*TriggerHandler\s*\(\s*\)\s*\.\s*run\s*\(", body):
            yield finding("TRG-02", c.path, f"The trigger must hold no logic: only `new {handler}().run();`")
        in_org = graph is not None and f"apex:{handler.lower()}" in graph.nodes
        if handler not in names and not in_org:
            yield finding("TRG-02", c.path, f"Missing {handler}, the handler this trigger must call")
        if handler in sources and not re.search(r"extends\s+TriggerHandler\b", sources[handler]):
            yield finding("TRG-02", f"{SOURCE}classes/{handler}.cls", f"{handler} must extend TriggerHandler")


def test_quality(changes, ctx):
    graph = ctx.get("graph")
    classes = {c.name[:-4]: strip_apex(c.content) for c in changes if c.name.endswith(".cls")}
    tests = {n: code for n, code in classes.items() if is_test(code)}
    for name, code in classes.items():
        if name in tests or re.search(r"\binterface\s", code[:400]):
            continue
        has_test = f"{name}Test" in tests or (graph is not None and f"apex:{name.lower()}test" in graph.nodes)
        if not has_test:
            yield finding("TST-02", f"{SOURCE}classes/{name}.cls", f"{name} needs a test class {name}Test")
    for name, code in tests.items():
        path = f"{SOURCE}classes/{name}.cls"
        if not re.search(r"\b(System\.assert\w*|Assert\.\w+)\s*\(", code):
            yield finding("TST-02", path, f"{name} has no assertions; assert the behaviour, not just coverage")
        if re.search(r"SeeAllData\s*=\s*true", code, re.I):
            yield finding("TST-02", path, f"{name} uses SeeAllData=true; create test data instead")


def lwc_practice(changes, ctx):
    for c in changes:
        if c.rel.startswith("lwc/") and c.name.endswith(".js") and "ShowToastEvent" in c.content \
                and re.search(r"variant\s*:\s*['\"]error", c.content):
            yield finding("LWC-01", c.path, "Show errors inline in the component rather than as toasts")


CHECKS: dict[str, Callable] = {f.__name__: f for f in (
    no_hardcoded_ids, no_profiles, object_naming, field_naming, permission_set_naming, validation_rule_naming,
    flow_naming, flow_fault_paths, one_automation_per_object, apex_naming, apex_sharing, no_soql_in_loops,
    no_dml_in_loops, no_single_record_trigger, dml_in_try, apex_formatting, trigger_per_object, trigger_handler,
    test_quality, lwc_practice)}


def coverage_findings(coverage: dict[str, float], changed: Iterable[str], minimum: float = 90.0) -> list[dict]:
    """TST-01 from the org's own validation run: every changed class or trigger at 90%."""
    out = []
    for path in changed:
        name = os.path.basename(path).rsplit(".", 1)[0]
        if path.endswith((".cls", ".trigger")) and name in coverage and coverage[name] < minimum:
            out.append(finding("TST-01", path, f"{name} is at {coverage[name]:.0f}% coverage; it needs "
                                               f"{minimum:.0f}%. Add tests for the uncovered paths"))
    return out


def run_checks(pack_rules: list[dict], files: list[dict], graph=None, coverage: dict[str, float] | None = None) -> dict:
    """Scorecard for a change set. `files`: [{path, content, status}]."""
    changes = [Change(f["path"], f["content"], f.get("status", "added") == "added") for f in files]
    rules = {r["id"]: r for r in pack_rules if r.get("severity") != "off"}
    findings: list[dict] = []
    ran: set[str] = set()
    ctx = {"graph": graph}
    for r in rules.values():
        check = CHECKS.get(r.get("check") or "")
        if check:
            ran.add(r["id"])
            findings.extend(check(changes, ctx))
    if coverage is not None and "TST-01" in rules:
        ran.add("TST-01")
        findings.extend(coverage_findings(coverage, [c.path for c in changes]))
    for f in findings:
        f["severity"] = rules.get(f["rule"], {}).get("severity", "warn")
        f["title"] = rules.get(f["rule"], {}).get("title", f["rule"])
    blocked = [f for f in findings if f["severity"] == "block"]
    warnings = [f for f in findings if f["severity"] == "warn"]
    failed = {f["rule"] for f in findings}
    return {"checked": sorted(ran), "passed": sorted(ran - failed), "blocked": blocked, "warnings": warnings}
