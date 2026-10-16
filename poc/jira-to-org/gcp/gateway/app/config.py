"""Gateway settings. Everything comes from the environment.

On Cloud Run the secrets (OpenAI key, Jira token, Salesforce client secret,
gateway key) are mounted from Secret Manager as environment variables by
`infra/deploy.sh`, so nothing here ever reads a secret from disk or the repo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

UNSET = {"", "unset", "none", "changeme"}


def env(name: str, default: str = "") -> str:
    value = os.environ.get(name, default)
    return value.strip() if value else default


def secret(name: str) -> str:
    """A secret env var, with the setup script's placeholder treated as absent."""
    value = env(name)
    return "" if value.lower() in UNSET else value


def flag(name: str, default: bool = False) -> bool:
    return env(name, "1" if default else "0").lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # GCP
    gcp_project: str
    bq_dataset: str
    graph_store: str          # bigquery | local
    local_graph_path: str
    run_store: str            # firestore | memory

    # Jira
    jira_base_url: str
    jira_email: str
    jira_project_key: str
    jira_start_transition: str
    jira_done_transition: str

    # Salesforce
    sf_login_url: str
    sf_api_version: str
    kg_standard_objects: tuple[str, ...]
    kg_flow_metadata_max: int

    # Codex / OpenAI
    openai_model: str         # empty = pick the best available at connect time
    codex_model: str          # empty = Codex CLI's own default
    codex_bin: str
    codex_home: str
    codex_sandbox: str
    codex_timeout_s: int

    # Developer agent
    sf_bin: str
    workspace_root: str
    max_fix_attempts: int
    auto_deploy: bool

    @property
    def jira_configured(self) -> bool:
        return bool(self.jira_base_url and self.jira_email and secret("JIRA_API_TOKEN"))

    @property
    def salesforce_configured(self) -> bool:
        return bool(self.sf_login_url and secret("SF_CLIENT_ID") and secret("SF_CLIENT_SECRET"))


def load() -> Settings:
    return Settings(
        gcp_project=env("GCP_PROJECT", env("GOOGLE_CLOUD_PROJECT")),
        bq_dataset=env("BQ_DATASET", "agent_kg"),
        graph_store=env("GRAPH_STORE", "bigquery"),
        local_graph_path=env("LOCAL_GRAPH_PATH", "/tmp/agent-kg.json"),
        run_store=env("RUN_STORE", "firestore"),
        jira_base_url=env("JIRA_BASE_URL").rstrip("/"),
        jira_email=env("JIRA_EMAIL"),
        jira_project_key=env("JIRA_PROJECT_KEY", "KAN"),
        jira_start_transition=env("JIRA_START_TRANSITION", "In Progress"),
        jira_done_transition=env("JIRA_DONE_TRANSITION", "Done"),
        sf_login_url=env("SF_LOGIN_URL").rstrip("/"),
        sf_api_version=env("SF_API_VERSION", "62.0"),
        kg_standard_objects=tuple(
            o.strip() for o in env(
                "KG_STANDARD_OBJECTS",
                "Account,Contact,Lead,Opportunity,Case,Task,Event,Campaign,Product2,"
                "Pricebook2,Order,Contract,Quote,User",
            ).split(",") if o.strip()
        ),
        kg_flow_metadata_max=int(env("KG_FLOW_METADATA_MAX", "100")),
        openai_model=env("OPENAI_MODEL"),
        codex_model=env("CODEX_MODEL"),
        codex_bin=env("CODEX_BIN", "codex"),
        codex_home=env("CODEX_HOME_DIR", "/srv/codex-home"),
        codex_sandbox=env("CODEX_SANDBOX", "workspace-write"),
        codex_timeout_s=int(env("CODEX_TIMEOUT_S", "900")),
        sf_bin=env("SF_BIN", "sf"),
        workspace_root=env("WORKSPACE_ROOT", "/tmp/agent-runs"),
        max_fix_attempts=int(env("MAX_FIX_ATTEMPTS", "2")),
        auto_deploy=flag("AUTO_DEPLOY", False),
    )
