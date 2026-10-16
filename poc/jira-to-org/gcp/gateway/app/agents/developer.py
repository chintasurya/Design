"""Developer agent: turns an approved requirement spec into deployed metadata.

    prepare SFDX workspace -> retrieve what the spec modifies -> Codex writes code
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

from ..codex import LEAN_CODING, CodexConnection, run_codex
from ..config import Settings
from ..graph.model import Edge, Node
from ..graph.store import GraphService
from ..jira import JiraClient
from ..runs import RunContext
from ..salesforce import SalesforceClient

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

You are implementing one Jira ticket in a Salesforce DX project. The spec is in
SPEC.md. The gateway that runs you validates and deploys your work; you have no
org access, so do not run `sf` or make network calls.

- Write Salesforce source format under `force-app/main/default/` only.
- Use API version {api} in every `-meta.xml`.
- Never delete files. Never create profiles, settings, named or external
  credentials, remote site settings, connected apps or destructive changes.
- Reuse what the spec says exists. Never create a field or class that the spec
  marks `exists_in_org: true`; modify the retrieved copy instead.
- Apex: `with sharing`, bulkified, no SOQL or DML inside loops.
- Every Apex class or trigger you create or change needs a test class named
  `<Name>Test` with `@isTest`, real assertions, and at least 85% coverage.
- Custom fields go in `objects/<Object>/fields/<Field>.field-meta.xml` with a
  description. A new custom object needs `<Object>.object-meta.xml` with
  `deploymentStatus` Deployed, `sharingModel` and a `nameField`.
- LWC bundles need `.js`, `.html` and `.js-meta.xml` (`isExposed`, `targets`).
- Grant field-level security for new fields in a permission set, never a
  profile: `permissionsets/Jira_Agent_Access.permissionset-meta.xml`.
- Keep the change as small as the acceptance criteria allow.
- When you finish, reply with a short summary: files changed and why.
"""


# Replaces Codex's long built-in coding prompt (see codex.LEAN_CODING): a short
# brief plus the workspace rules, so each turn re-sends far less.
DEVELOPER_INSTRUCTIONS = """\
You are a Salesforce developer agent. The current directory is a Salesforce DX
project. SPEC.md says what to build; the rules below say how. Work efficiently:
read only the files you need (SPEC.md first, then any retrieved file you must
change), make the edits with apply_patch, and do not explore the repository
broadly or re-read files. Do not use the network and do not run `sf`.

"""


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
    return {"success": success, "id": result.get("id"), "status": result.get("status"),
            "components_deployed": result.get("numberComponentsDeployed"),
            "tests_run": tests.get("numTestsRun") or result.get("numberTestsCompleted"),
            "errors": errors[:40]}


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
                 codex_runner: Callable[..., dict] = run_codex):
        self.s = settings
        self.codex = codex
        self.cli = cli
        self.jira = jira
        self.graphs = graphs
        self.codex_runner = codex_runner

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
            fh.write(".sf/\n.sfdx/\n.codex-last-message.txt\n")

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
    def _prompt(self, spec: dict, errors: list[str] | None) -> str:
        if not errors:
            return (f"Implement Jira ticket {spec.get('ticket_key')} as described in SPEC.md, following AGENTS.md. "
                    "Meet every acceptance criterion. Reply with a short summary when done.")
        return ("The Salesforce validation of your change failed. Fix exactly these problems, keep everything "
                "else as it is, and follow AGENTS.md:\n- " + "\n- ".join(errors))

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
        for attempt in range(1, self.s.max_fix_attempts + 2):
            ctx.step(f"Codex attempt {attempt}", "running")
            before = plan_usage() if plan_usage else None
            out = self.codex_runner(self.codex, ws, self._prompt(spec, errors), lambda line: ctx.step(line),
                                    home=codex_home,
                                    instructions=DEVELOPER_INSTRUCTIONS + AGENTS_MD.format(api=self.s.sf_api_version),
                                    extra_args=LEAN_CODING)
            if plan_usage:
                ctx.plan_usage(before, plan_usage())
            if after_codex:
                after_codex()
            summary = out.get("final_message") or summary
            u = out.get("usage") or {}
            if u:
                model = self.s.codex_model or ("codex (your ChatGPT sign-in)" if codex_home else "codex-cli default")
                ctx.add_usage("developer", model, u.get("input_tokens", 0),
                              u.get("output_tokens", 0), u.get("cached_input_tokens", 0), 0, key)
            if out.get("exit_code") not in (0, None):
                ctx.step("Codex exited with an error", "error", out.get("log_tail", "")[-1500:])
            kept, problems = self.guard(ws, self.changes(ws))
            if problems:
                ctx.step("Change set refused by the guard", "error", "\n".join(problems))
                errors = problems
                continue
            tests = self.test_classes(ws, kept)
            targets = sorted({component_root(c["path"]) for c in kept})
            ctx.step("Validating in Salesforce (check-only deploy)", "running",
                     f"{len(targets)} components · tests: {', '.join(tests) or 'none (NoTestRun)'}")
            validation = deploy_outcome(self.cli.deploy(ws, targets, tests, dry_run=True))
            if validation["success"]:
                ctx.step("Validation passed", detail=f"tests run: {validation.get('tests_run') or 0}")
                break
            ctx.step("Validation failed", "error", "\n".join(validation["errors"]))
            errors = validation["errors"]
        else:
            raise DeveloperError(f"no valid change after {self.s.max_fix_attempts + 1} Codex attempts: "
                                 + "; ".join((errors or [])[:5]))

        files, diff = self.snapshot_files(ws, kept)
        result = {"ticket_key": key, "ticket_url": spec.get("ticket_url"), "files": files, "diff": diff,
                  "deploy_targets": sorted({component_root(c["path"]) for c in kept}), "tests": tests,
                  "validation": validation, "codex_summary": summary[:4000]}
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
