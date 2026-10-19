"""Developer agent: turns an approved requirement spec into deployed metadata.

    prepare SFDX workspace -> retrieve what the spec modifies
    -> new fields only: the gateway writes them from the spec (no model call)
    -> otherwise one Codex call per attempt, no tools: it gets the spec and the
       files, and answers with complete files that the gateway writes
    -> guard the change set -> validate (check-only deploy + tests)
    -> on failure, hand the errors back to Codex (bounded) -> wait for approval
    -> deploy -> comment + transition the Jira ticket -> write facts to the graph

Codex never holds a Salesforce credential. The gateway logs the Salesforce CLI
in with a short-lived access token only for the retrieve and deploy commands,
in a throwaway home directory that is deleted straight after.
"""
from __future__ import annotations

import contextlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from typing import Callable, Iterator

from ..codex import LEAN_NO_TOOLS, CodexConnection, run_codex
from ..config import Settings
from ..graph.model import Edge, Node
from ..graph.store import GraphService
from ..guardrails import GuardrailService, areas_for_components
from ..guardrails.checks import run_checks
from ..jira import JiraClient
from ..runs import RunContext
from ..salesforce import SalesforceClient
from . import builder

SOURCE_ROOT = "force-app/main/default"
MAX_FILES = 60
MAX_FILE_BYTES = 200_000
MAX_STORED_BYTES = 500_000  # Firestore documents stop at 1 MiB; diff and steps ride along
FORBIDDEN_DIRS = ("profiles", "settings", "connectedApps", "externalClientApps", "namedCredentials",
                  "externalCredentials", "remoteSiteSettings", "cspTrustedSites", "authproviders",
                  "sites", "networks", "permissionsetgroups", "samlssoconfigs")

RETRIEVE_TYPES = {
    "ApexClass": "ApexClass", "ApexTrigger": "ApexTrigger", "LWC": "LightningComponentBundle",
    "CustomObject": "CustomObject", "CustomField": "CustomField", "Flow": "Flow",
    "ValidationRule": "ValidationRule", "PermissionSet": "PermissionSet", "Layout": "Layout",
}

AGENTS_MD = """\
# Rules for this workspace

You are implementing one Jira ticket in a Salesforce DX project. The spec and
the existing files are in the message. The gateway validates and deploys your
work; you have no org access.

- Write Salesforce source format under `force-app/main/default/` only.
- Use API version {api} in every `-meta.xml`.
- Never delete files. Never create profiles, settings, named or external
  credentials, remote site settings, connected apps or destructive changes.
- Reuse what the spec says exists. Never create a field or class that the spec
  marks `exists_in_org: true`; modify the retrieved copy instead.
- Build with the approach the spec chose (`approach.build_with`): declarative
  first.
- Flow: `flows/<NameInCamelCase>.flow-meta.xml`, status Active, a `start`
  element with the object and trigger type (RecordBeforeSave for field
  updates on the same record, RecordAfterSave for related records), a
  `description`, and a `faultConnector` on every record element leading to an
  error-handling element. Record changes at the end.
- Trigger: `triggers/<ObjectName>.trigger` containing only
  `new <ObjectName>TriggerHandler().run();`, and
  `classes/<ObjectName>TriggerHandler.cls` that `extends TriggerHandler` and
  overrides beforeInsert/afterInsert/beforeUpdate/afterUpdate/... The
  `TriggerHandler` framework already exists in the org: never create it. If
  the object already has a trigger, call the handler from that trigger
  instead of adding a second one.
- Tests: `<ClassName>Test` with `@TestSetup` data, positive, negative and
  200-record bulk cases, real assertions, at least 90% coverage.
- Custom fields: `objects/<Object>/fields/<Field>.field-meta.xml` with a
  `description` and `inlineHelpText`. A new custom object needs
  `<Object>.object-meta.xml` with a description, `deploymentStatus` Deployed,
  `sharingModel` and a `nameField`.
- LWC bundles need `.js`, `.html` and `.js-meta.xml` (`isExposed`, `targets`).
- Field access goes in a permission set, never a profile:
  `permissionsets/HarnessAgentAccess.permissionset-meta.xml` (label Harness
  Agent Access, with a description).
- The gateway checks the standards below automatically before anything
  reaches the org; a broken blocking rule comes back to you to fix.
- Keep the change as small as the acceptance criteria allow.
"""


# Replaces Codex's long built-in coding prompt. One call, no tools: everything
# Codex needs is in the message, so there are no read-the-file turns that each
# re-send the whole context (that cost ~45k tokens per attempt).
DEVELOPER_INSTRUCTIONS = """\
You are a Salesforce developer agent. The message holds the requirement spec,
the knowledge graph context and the current content of every relevant file.
Do not run commands or open files: you have no tools. Answer with JSON only:
`files` lists every file you create or change, each with its path under
force-app/main/default/ and its COMPLETE new content (never a diff, never a
partial file; files you leave unchanged are not listed); `summary` is at most
3 one-line bullets. Include the -meta.xml file for every new Apex class or
trigger. Output is paid for per token: no comments beyond what the standards
require, no unused code.

"""

CODE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "files": {"type": "array", "items": {
            "type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"], "additionalProperties": False}},
    },
    "required": ["summary", "files"],
    "additionalProperties": False,
}
PROMPT_FILE_CHARS = 20_000   # one file in the message
PROMPT_FILES_CHARS = 60_000  # all files in the message


class DeveloperError(RuntimeError):
    pass


def _run(cmd: list[str], cwd: str | None = None, env: dict | None = None, timeout: int = 900,
         stdin: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, env=env, input=stdin, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _json_out(text: str) -> dict:
    start = text.find("{")
    if start < 0:
        return {}
    try:
        return json.loads(text[start:])
    except json.JSONDecodeError:
        return {}


class SalesforceCli:
    def __init__(self, settings: Settings, sf: SalesforceClient,
                 runner: Callable[..., tuple[int, str]] = _run):
        self.settings = settings
        self.sf = sf
        self.runner = runner

    @contextlib.contextmanager
    def _session(self) -> Iterator[dict]:
        token, instance = self.sf.session()
        home = tempfile.mkdtemp(prefix="sf-home-")
        env = {"PATH": os.environ.get("PATH", ""), "HOME": home, "SF_ACCESS_TOKEN": token,
               "SF_USE_GENERIC_UNIX_KEYCHAIN": "true", "SF_DISABLE_TELEMETRY": "true",
               "SF_AUTOUPDATE_DISABLE": "true", "SF_SKIP_NEW_VERSION_CHECK": "true", "LANG": "C.UTF-8"}
        try:
            code, out = self.runner([self.settings.sf_bin, "org", "login", "access-token", "--instance-url",
                                     instance, "--no-prompt", "--alias", "agent-org", "--json"], env=env, timeout=120)
            if code != 0:
                raise DeveloperError(f"sf login failed: {out[-500:]}")
            yield env
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def retrieve(self, workspace: str, metadata: list[str]) -> dict:
        if not metadata:
            return {}
        cmd = [self.settings.sf_bin, "project", "retrieve", "start", "--target-org", "agent-org", "--json",
               "--ignore-conflicts", "--wait", "10"]
        for m in metadata:
            cmd += ["--metadata", m]
        with self._session() as env:
            _, out = self.runner(cmd, cwd=workspace, env=env, timeout=900)
        return _json_out(out)

    def deploy(self, workspace: str, source_paths: list[str], tests: list[str], dry_run: bool) -> dict:
        cmd = [self.settings.sf_bin, "project", "deploy", "start", "--target-org", "agent-org", "--json",
               "--wait", "30", "--ignore-conflicts"]
        for p in source_paths:
            cmd += ["--source-dir", p]
        if tests:
            cmd += ["--test-level", "RunSpecifiedTests"]
            for t in tests:
                cmd += ["--tests", t]
        else:
            cmd += ["--test-level", "NoTestRun"]  # allowed in Developer Edition and sandboxes
        if dry_run:
            cmd.append("--dry-run")
        with self._session() as env:
            _, out = self.runner(cmd, cwd=workspace, env=env, timeout=2400)
        return _json_out(out) or {"status": 1, "message": out[-2000:]}


def deploy_outcome(out: dict) -> dict:
    """Normalise `sf project deploy start --json` into success + readable errors."""
    result = out.get("result") or out.get("data") or {}
    details = result.get("details") or {}
    failures = details.get("componentFailures") or []
    if isinstance(failures, dict):
        failures = [failures]
    tests = details.get("runTestResult") or {}
    test_failures = tests.get("failures") or []
    if isinstance(test_failures, dict):
        test_failures = [test_failures]
    warnings = tests.get("codeCoverageWarnings") or []
    if isinstance(warnings, dict):
        warnings = [warnings]
    errors = [f"{f.get('componentType')} {f.get('fullName')}: {f.get('problem')}"
              + (f" (line {f.get('lineNumber')})" if f.get("lineNumber") else "") for f in failures]
    errors += [f"test {f.get('name')}.{f.get('methodName')}: {f.get('message')}" for f in test_failures]
    errors += [f"coverage {w.get('name') or ''}: {w.get('message')}" for w in warnings]
    success = bool(result.get("success")) and out.get("status", 0) == 0 and not errors
    if not success and not errors:
        errors.append(str(out.get("message") or result.get("errorMessage") or "deploy failed without detail")[:1000])
    coverage = {}
    entries = tests.get("codeCoverage") or []
    for c in [entries] if isinstance(entries, dict) else entries:
        total = int(c.get("numLocations") or 0)
        if c.get("name") and total:
            coverage[c["name"]] = round(100.0 * (total - int(c.get("numLocationsNotCovered") or 0)) / total, 1)
    return {"success": success, "id": result.get("id"), "status": result.get("status"),
            "components_deployed": result.get("numberComponentsDeployed"),
            "tests_run": tests.get("numTestsRun") or result.get("numberTestsCompleted"),
            "coverage": coverage, "errors": errors[:40]}


def component_root(path: str) -> str:
    """The path the CLI should deploy for a changed file."""
    rel = path[len(SOURCE_ROOT) + 1:] if path.startswith(SOURCE_ROOT + "/") else path
    parts = rel.split("/")
    if parts[0] in {"lwc", "aura", "staticresources"} and len(parts) > 2:
        return f"{SOURCE_ROOT}/{parts[0]}/{parts[1]}"
    if path.endswith("-meta.xml"):
        base = path[: -len("-meta.xml")]
        if base.endswith((".cls", ".trigger", ".page", ".component")):
            return base
    return path


def node_for_path(path: str) -> tuple[Node, Edge | None] | None:
    """The graph node a deployed file stands for, plus its structural edge."""
    rel = path[len(SOURCE_ROOT) + 1:] if path.startswith(SOURCE_ROOT + "/") else path
    p = rel.split("/")
    name = os.path.basename(rel)
    if p[0] == "classes" and name.endswith(".cls"):
        n = name[:-4]
        return Node(f"apex:{n.lower()}", "ApexClass", n, n), None
    if p[0] == "triggers" and name.endswith(".trigger"):
        n = name[:-8]
        return Node(f"trigger:{n.lower()}", "ApexTrigger", n, n), None
    if p[0] == "lwc" and len(p) > 2:
        return Node(f"lwc:{p[1].lower()}", "LWC", p[1], p[1]), None
    if p[0] == "flows" and name.endswith(".flow-meta.xml"):
        n = name[: -len(".flow-meta.xml")]
        return Node(f"flow:{n.lower()}", "Flow", n, n), None
    if p[0] == "objects" and len(p) >= 3:
        obj = p[1]
        if p[2] == "fields" and name.endswith(".field-meta.xml"):
            f = name[: -len(".field-meta.xml")]
            node = Node(f"field:{obj.lower()}.{f.lower()}", "Field", f, f"{obj}.{f}")
            return node, Edge("SOBJECT_HAS_FIELD", f"sobj:{obj.lower()}", node.id, origin="developer-agent")
        if name == f"{obj}.object-meta.xml":
            return Node(f"sobj:{obj.lower()}", "SObject", obj, obj, properties={"label": obj}), None
        if p[2] == "validationRules" and name.endswith(".validationRule-meta.xml"):
            v = name[: -len(".validationRule-meta.xml")]
            node = Node(f"vr:{obj.lower()}.{v.lower()}", "ValidationRule", v, f"{obj}.{v}")
            return node, Edge("VALIDATES_SOBJECT", node.id, f"sobj:{obj.lower()}", origin="developer-agent")
    return None


class DeveloperAgent:
    def __init__(self, settings: Settings, codex: CodexConnection, cli: SalesforceCli,
                 jira: JiraClient | None, graphs: GraphService,
                 codex_runner: Callable[..., dict] = run_codex, guardrails: GuardrailService | None = None):
        self.s = settings
        self.codex = codex
        self.cli = cli
        self.jira = jira
        self.graphs = graphs
        self.codex_runner = codex_runner
        self.guardrails = guardrails or GuardrailService()

    # -- workspace -------------------------------------------------------------
    def workspace(self, run_id: str) -> str:
        return os.path.join(self.s.workspace_root, run_id)

    def _git(self, ws: str, *args: str) -> str:
        env = {"PATH": os.environ.get("PATH", ""), "HOME": ws, "GIT_AUTHOR_NAME": "developer-agent",
               "GIT_AUTHOR_EMAIL": "agent@localhost", "GIT_COMMITTER_NAME": "developer-agent",
               "GIT_COMMITTER_EMAIL": "agent@localhost"}
        code, out = _run(["git", *args], cwd=ws, env=env, timeout=120)
        if code != 0:
            raise DeveloperError(f"git {' '.join(args)} failed: {out[-300:]}")
        return out

    def _scaffold(self, ws: str) -> None:
        os.makedirs(os.path.join(ws, SOURCE_ROOT), exist_ok=True)
        with open(os.path.join(ws, "sfdx-project.json"), "w", encoding="utf-8") as fh:
            json.dump({"packageDirectories": [{"path": "force-app", "default": True}], "namespace": "",
                       "sourceApiVersion": self.s.sf_api_version}, fh, indent=2)
        with open(os.path.join(ws, ".gitignore"), "w", encoding="utf-8") as fh:
            fh.write(".sf/\n.sfdx/\n.codex-last-message.txt\n.codex-output-schema.json\n")

    def prepare(self, run_id: str, spec: dict, ctx: RunContext) -> str:
        ws = self.workspace(run_id)
        shutil.rmtree(ws, ignore_errors=True)
        self._scaffold(ws)
        with open(os.path.join(ws, "AGENTS.md"), "w", encoding="utf-8") as fh:
            fh.write(AGENTS_MD.format(api=self.s.sf_api_version))
        context = self.graphs.graph().context_slice(
            " ".join([spec.get("title", ""), spec.get("summary", "")]
                     + [c.get("api_name", "") for c in spec.get("components", [])]))
        with open(os.path.join(ws, "SPEC.md"), "w", encoding="utf-8") as fh:
            fh.write(f"# {spec.get('ticket_key')}: {spec.get('title')}\n\n")
            fh.write("## Requirement spec (from the Requirement agent)\n\n```json\n")
            fh.write(json.dumps({k: v for k, v in spec.items() if k != "ticket"}, indent=2))
            fh.write("\n```\n\n## Jira ticket\n\n")
            fh.write((spec.get("ticket") or {}).get("description") or "(description not captured)")
            fh.write("\n\n## Knowledge graph context\n\n")
            fh.write("\n".join(f"- {line}" for line in context["related"][:80]) or "- (nothing related found)")
            fh.write("\n")
        self._git(ws, "init", "-q")
        metadata = []
        for comp in spec.get("components", []):
            kind = RETRIEVE_TYPES.get(comp.get("type", ""))
            if kind and comp.get("exists_in_org") and comp.get("api_name"):
                name = comp["api_name"]
                if kind in {"ApexClass", "ApexTrigger", "LightningComponentBundle", "Flow", "PermissionSet"}:
                    name = name.split(".")[-1]
                metadata.append(f"{kind}:{name}")
        grants_fields = any(c.get("type") == "CustomField" and c.get("action") == "create"
                            for c in spec.get("components", []))
        perm = f"PermissionSet:{builder.PERMISSION_SET}"
        if grants_fields and perm not in metadata:
            metadata.append(perm)  # new field access is merged into the org's copy, never replaces it
        if metadata:
            out = self.cli.retrieve(ws, metadata)
            files = (out.get("result") or {}).get("files") or []
            ctx.step(f"Retrieved {len(files)} existing files from the org", detail=", ".join(metadata))
        self._git(ws, "add", "-A")
        self._git(ws, "commit", "-q", "-m", "baseline", "--allow-empty")
        return ws

    # -- change set ------------------------------------------------------------
    def changes(self, ws: str) -> list[dict]:
        self._git(ws, "add", "-A")
        out = self._git(ws, "diff", "--cached", "--name-status", "--no-renames")
        changes = []
        for line in out.splitlines():
            if "\t" in line:
                status, path = line.split("\t", 1)
                changes.append({"status": status.strip(), "path": path.strip()})
        return changes

    def guard(self, ws: str, changes: list[dict]) -> tuple[list[dict], list[str]]:
        """Keep source changes, refuse anything that widens access or deletes."""
        problems: list[str] = []
        kept: list[dict] = []
        for c in changes:
            path = c["path"]
            if not path.startswith(SOURCE_ROOT + "/"):
                continue  # SPEC.md, AGENTS.md, scratch files: never deployed
            sub = path[len(SOURCE_ROOT) + 1:].split("/")[0]
            if c["status"].startswith("D"):
                problems.append(f"{path}: deleting metadata is not allowed")
            elif sub in FORBIDDEN_DIRS or "destructiveChanges" in path:
                problems.append(f"{path}: {sub} is outside what the agent may change")
            elif os.path.getsize(os.path.join(ws, path)) > MAX_FILE_BYTES:
                problems.append(f"{path}: larger than {MAX_FILE_BYTES} bytes")
            else:
                kept.append(c)
        if len(kept) > MAX_FILES:
            problems.append(f"{len(kept)} files changed; the limit is {MAX_FILES}")
        if not kept:
            problems.append("Codex made no change under force-app/main/default")
        apex = [c["path"] for c in kept if c["path"].endswith((".cls", ".trigger"))]
        if apex and not self.test_classes(ws, kept):
            problems.append("Apex changed but no @isTest class was written")
        return kept, problems

    @staticmethod
    def test_classes(ws: str, kept: list[dict]) -> list[str]:
        tests = []
        for c in kept:
            if c["path"].endswith(".cls"):
                with open(os.path.join(ws, c["path"]), encoding="utf-8", errors="replace") as fh:
                    if re.search(r"@isTest", fh.read(), re.I):
                        tests.append(os.path.basename(c["path"])[:-4])
        return sorted(tests)

    def snapshot_files(self, ws: str, kept: list[dict]) -> tuple[list[dict], str]:
        files, total = [], 0
        for c in kept:
            with open(os.path.join(ws, c["path"]), encoding="utf-8", errors="replace") as fh:
                content = fh.read()
            total += len(content)
            files.append({"path": c["path"], "status": "added" if c["status"].startswith("A") else "modified",
                          "content": content})
        if total > MAX_STORED_BYTES:
            raise DeveloperError(f"change set is {total} bytes; the stored limit is {MAX_STORED_BYTES}")
        diff = self._git(ws, "diff", "--cached", "--no-color", "--", SOURCE_ROOT)
        return files, diff[:150_000]

    # -- the run -----------------------------------------------------------------
    def _instructions(self, spec: dict) -> str:
        """Brief + workspace rules + only the standards this change touches."""
        areas = areas_for_components(spec.get("components") or [])
        if any(c.get("type") in ("ApexClass", "ApexTrigger") for c in spec.get("components") or []):
            areas = sorted(set(areas) | {"Test"})
        pack = self.guardrails.pack()
        return (DEVELOPER_INSTRUCTIONS + AGENTS_MD.format(api=self.s.sf_api_version)
                + f"\n# Development standards: {pack.get('name')} (apply to this change)\n\n"
                + self.guardrails.brief(areas) + "\n")

    def _files(self, ws: str, kept: list[dict]) -> list[dict]:
        out = []
        for c in kept:
            with open(os.path.join(ws, c["path"]), encoding="utf-8", errors="replace") as fh:
                out.append({"path": c["path"], "content": fh.read(),
                            "status": "added" if c["status"].startswith("A") else "modified"})
        return out

    def scorecard(self, ws: str, kept: list[dict], coverage: dict | None = None) -> dict:
        pack = self.guardrails.pack()
        card = run_checks(self.guardrails.rules(), self._files(ws, kept), graph=self.graphs.graph(),
                          coverage=coverage)
        return {**card, "pack": pack.get("name"), "version": pack.get("version")}

    @staticmethod
    def as_errors(card: dict) -> list[str]:
        return [f"[{f['rule']} {f['title']}] {f['file'].replace(SOURCE_ROOT + '/', '')}: {f['message']}"
                for f in card["blocked"]]

    def _workspace_files(self, ws: str) -> str:
        """Every source file in the workspace (retrieved from the org, or written
        by an earlier attempt), for the message."""
        parts, total = [], 0
        root = os.path.join(ws, SOURCE_ROOT)
        for dirpath, _, names in sorted(os.walk(root)):
            for name in sorted(names):
                full = os.path.join(dirpath, name)
                with open(full, encoding="utf-8", errors="replace") as fh:
                    content = fh.read()[:PROMPT_FILE_CHARS]
                if total + len(content) > PROMPT_FILES_CHARS:
                    parts.append(f"=== {os.path.relpath(full, ws)} === (omitted: message size limit)")
                    continue
                total += len(content)
                parts.append(f"=== {os.path.relpath(full, ws)} ===\n{content}")
        return "\n\n".join(parts) or "(none: everything is new)"

    def _prompt(self, ws: str, spec: dict, errors: list[str] | None) -> str:
        # what the build needs; the Requirement agent's notes on reuse and impact are already in components
        brief = {k: v for k, v in spec.items() if k in ("ticket_key", "title", "summary", "acceptance_criteria",
                                                         "approach", "components", "test_plan")}
        context = self.graphs.graph().context_slice(
            " ".join([spec.get("title", ""), spec.get("summary", "")]
                     + [c.get("api_name", "") for c in spec.get("components", [])]))
        description = ((spec.get("ticket") or {}).get("description") or "")[:4000]
        task = (f"Implement Jira ticket {spec.get('ticket_key')}. Meet every acceptance criterion."
                if not errors else
                "Your previous change (the files above) failed these checks. Fix exactly these problems and "
                "return every file you change, complete:\n- " + "\n- ".join(errors))
        return ("SPEC:\n" + json.dumps(brief, separators=(",", ":"))
                + ("\n\nJIRA DESCRIPTION:\n" + description if description else "")
                + "\n\nKNOWLEDGE GRAPH:\n" + ("\n".join(f"- {line}" for line in context["related"][:25]) or "- none")
                + "\n\nFILES:\n" + self._workspace_files(ws)
                + "\n\nTASK:\n" + task)

    @staticmethod
    def _write_answer(ws: str, answer: dict) -> list[str]:
        """Write the files Codex answered with. Paths outside the source tree
        are refused here; the guard checks the rest."""
        problems = []
        for f in answer.get("files") or []:
            rel = os.path.normpath((f.get("path") or "").strip().lstrip("/"))
            if not rel.startswith(SOURCE_ROOT + "/") or ".." in rel.split(os.sep):
                problems.append(f"{f.get('path')}: files must be under {SOURCE_ROOT}/")
                continue
            full = os.path.join(ws, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(f.get("content") or "")
        return problems

    def develop(self, run_id: str, spec: dict, ctx: RunContext, codex_home: str | None = None,
                after_codex: Callable[[], None] | None = None,
                plan_usage: Callable[[], dict | None] | None = None) -> dict:
        """`codex_home` is the developer's own signed-in Codex (ChatGPT sign-in
        mode); `after_codex` saves its refreshed tokens after each attempt."""
        key = spec.get("ticket_key", "")
        if self.jira and key:
            reached = self.jira.transition(key, self.s.jira_start_transition)
            ctx.step(f"Jira {key} -> {reached}" if reached else f"Jira {key}: no '{self.s.jira_start_transition}' transition")
        ws = self.prepare(run_id, spec, ctx)
        ctx.step("Workspace ready", detail="SFDX project, AGENTS.md rules, SPEC.md with graph context")

        errors: list[str] | None = None
        summary = ""
        validation: dict = {}
        kept: list[dict] = []
        tests: list[str] = []
        use_builder = builder.buildable(spec)
        for attempt in range(1, self.s.max_fix_attempts + 2):
            write_problems: list[str] = []
            if attempt == 1 and use_builder:
                written = builder.build(ws, spec)
                summary = "Built by the gateway from the requirement spec (no model call):\n" + \
                          "\n".join(f"- {p.replace(SOURCE_ROOT + '/', '')}" for p in written)
                ctx.add_usage("developer", "gateway builder (no model call)", 0, 0, 0, 0, key, calls=0)
                ctx.step("Built from the spec by the gateway (no model call)", detail=summary)
            else:
                ctx.step(f"Codex attempt {attempt} (one call, no tools)", "running")
                before = plan_usage() if plan_usage else None
                out = self.codex_runner(self.codex, ws, self._prompt(ws, spec, errors), lambda line: ctx.step(line),
                                        home=codex_home, sandbox="read-only", output_schema=CODE_OUTPUT_SCHEMA,
                                        instructions=self._instructions(spec), extra_args=LEAN_NO_TOOLS)
                if plan_usage:
                    ctx.plan_usage(before, plan_usage())
                if after_codex:
                    after_codex()
                u = out.get("usage") or {}
                if u:
                    model = self.s.codex_model or ("codex (your ChatGPT sign-in)" if codex_home else "codex-cli default")
                    ctx.add_usage("developer", model, u.get("input_tokens", 0),
                                  u.get("output_tokens", 0), u.get("cached_input_tokens", 0), 0, key)
                if out.get("exit_code") not in (0, None):
                    ctx.step("Codex exited with an error", "error", out.get("log_tail", "")[-1500:])
                try:
                    answer = json.loads(out.get("final_message") or "{}")
                except json.JSONDecodeError:
                    answer = {}
                summary = answer.get("summary") or summary
                write_problems = self._write_answer(ws, answer)
            kept, problems = self.guard(ws, self.changes(ws))
            problems = write_problems + problems
            if problems:
                ctx.step("Change set refused by the guard", "error", "\n".join(problems))
                errors = problems
                continue
            card = self.scorecard(ws, kept)
            if card["blocked"]:
                ctx.step(f"Guardrails: {len(card['blocked'])} blocking findings", "error",
                         "\n".join(self.as_errors(card)))
                errors = self.as_errors(card)
                continue
            ctx.step(f"Guardrails passed: {len(card['passed'])} rules checked",
                     detail=f"{len(card['warnings'])} warnings · {card['pack']} v{card['version']}")
            tests = self.test_classes(ws, kept)
            targets = sorted({component_root(c["path"]) for c in kept})
            ctx.step("Validating in Salesforce (check-only deploy)", "running",
                     f"{len(targets)} components · tests: {', '.join(tests) or 'none (NoTestRun)'}")
            validation = deploy_outcome(self.cli.deploy(ws, targets, tests, dry_run=True))
            if validation["success"]:
                ctx.step("Validation passed", detail=f"tests run: {validation.get('tests_run') or 0}")
                card = self.scorecard(ws, kept, coverage=validation.get("coverage") or {})
                if card["blocked"]:  # TST-01: coverage is only known once the org has run the tests
                    ctx.step("Guardrails: coverage below the standard", "error", "\n".join(self.as_errors(card)))
                    errors = self.as_errors(card)
                    continue
                break
            ctx.step("Validation failed", "error", "\n".join(validation["errors"]))
            errors = validation["errors"]
        else:
            raise DeveloperError(f"no valid change after {self.s.max_fix_attempts + 1} Codex attempts: "
                                 + "; ".join((errors or [])[:5]))

        files, diff = self.snapshot_files(ws, kept)
        result = {"ticket_key": key, "ticket_url": spec.get("ticket_url"), "files": files, "diff": diff,
                  "deploy_targets": sorted({component_root(c["path"]) for c in kept}), "tests": tests,
                  "validation": validation, "codex_summary": summary[:4000], "guardrails": card}
        if self.s.auto_deploy:
            ctx.status("running", result=result)
            return self.deploy(run_id, result, ctx)
        ctx.step("Waiting for approval to deploy", "waiting")
        ctx.status("waiting_approval", result=result)
        return result

    def materialize(self, run_id: str, result: dict) -> str:
        """Rebuild the workspace from the stored change set if this instance
        no longer has it (restart, scale-down)."""
        ws = self.workspace(run_id)
        if all(os.path.exists(os.path.join(ws, f["path"])) for f in result["files"]):
            return ws
        shutil.rmtree(ws, ignore_errors=True)
        self._scaffold(ws)
        for f in result["files"]:
            full = os.path.join(ws, f["path"])
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(f["content"])
        return ws

    def deploy(self, run_id: str, result: dict, ctx: RunContext) -> dict:
        ws = self.materialize(run_id, result)
        ctx.step("Deploying to Salesforce", "running", ", ".join(result["deploy_targets"]))
        outcome = deploy_outcome(self.cli.deploy(ws, result["deploy_targets"], result["tests"], dry_run=False))
        result = {**result, "deployment": outcome}
        if not outcome["success"]:
            ctx.step("Deployment failed", "error", "\n".join(outcome["errors"]))
            ctx.status("failed", result=result, error="deployment failed")
            return result
        ctx.step("Deployed", detail=f"deploy id {outcome.get('id')} · {outcome.get('components_deployed')} components")
        key = result.get("ticket_key")
        if self.jira and key:
            comment = (f"Deployed to Salesforce by the Developer agent.\n\nDeploy id: {outcome.get('id')}\n"
                       f"Components:\n" + "\n".join(f"- {t}" for t in result["deploy_targets"])
                       + f"\n\nTests: {', '.join(result['tests']) or 'none (no Apex changed)'}"
                       + (f"\n\nSummary from Codex:\n{result['codex_summary'][:2500]}" if result.get("codex_summary") else ""))
            self.jira.add_comment(key, comment)
            reached = self.jira.transition(key, self.s.jira_done_transition)
            ctx.step(f"Jira {key} commented" + (f" and moved to {reached}" if reached else ""))
        self.record(result)
        ctx.step("Knowledge graph updated", detail="ticket -> implemented-by edges written")
        ctx.status("succeeded", result=result)
        return result

    def record(self, result: dict) -> None:
        key = (result.get("ticket_key") or "").upper()
        nodes: list[Node] = []
        edges: list[Edge] = []
        tid = f"ticket:{key.lower()}"
        if key:
            nodes.append(Node(tid, "JiraTicket", key, key, source_system="JIRA",
                              properties={"url": result.get("ticket_url"), "status": "Deployed"}))
        for f in result["files"]:
            hit = node_for_path(f["path"])
            if not hit:
                continue
            node, structural = hit
            node.properties["deployed_by"] = "developer-agent"
            node.properties["deploy_id"] = (result.get("deployment") or {}).get("id")
            nodes.append(node)
            if structural:
                edges.append(structural)
            if key:
                edges.append(Edge("TICKET_IMPLEMENTED_BY", tid, node.id, origin="developer-agent"))
        self.graphs.record(nodes, edges)
