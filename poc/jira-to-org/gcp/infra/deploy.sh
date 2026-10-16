#!/usr/bin/env bash
# Build and deploy the agent gateway to Cloud Run from source.
#
#   export GCP_PROJECT=my-project GCP_REGION=us-central1
#   export JIRA_BASE_URL=https://<site>.atlassian.net JIRA_EMAIL=you@example.com JIRA_PROJECT_KEY=KAN
#   export SF_LOGIN_URL=https://<mydomain>.my.salesforce.com
#   ./deploy.sh
set -euo pipefail

: "${GCP_PROJECT:?set GCP_PROJECT}"
: "${JIRA_BASE_URL:?set JIRA_BASE_URL}"
: "${JIRA_EMAIL:?set JIRA_EMAIL}"
: "${SF_LOGIN_URL:?set SF_LOGIN_URL (the org My Domain, not login.salesforce.com)}"
# Salesforce login: secret sf-auth-url (SFDX auth URL) if set, else sf-client-id/secret
GCP_REGION="${GCP_REGION:-us-central1}"
SERVICE="${SERVICE:-agent-gateway}"
SA="agent-gateway@${GCP_PROJECT}.iam.gserviceaccount.com"
HERE="$(cd "$(dirname "$0")" && pwd)"

# Env vars go through a YAML file: values such as the Jira email contain
# characters that break gcloud's inline KEY=VALUE list syntax.
ENV_FILE="$(mktemp --suffix .yaml)"
trap 'rm -f "$ENV_FILE"' EXIT
python3 - "$ENV_FILE" <<'PY'
import json, os, sys
keys = {
    "GCP_PROJECT": os.environ["GCP_PROJECT"], "BQ_DATASET": os.environ.get("BQ_DATASET", "agent_kg"),
    "GRAPH_STORE": "bigquery", "RUN_STORE": "firestore",
    "JIRA_BASE_URL": os.environ["JIRA_BASE_URL"], "JIRA_EMAIL": os.environ["JIRA_EMAIL"],
    "JIRA_PROJECT_KEY": os.environ.get("JIRA_PROJECT_KEY", "KAN"),
    "JIRA_START_TRANSITION": os.environ.get("JIRA_START_TRANSITION", "In Progress"),
    "JIRA_DONE_TRANSITION": os.environ.get("JIRA_DONE_TRANSITION", "Done"),
    "SF_LOGIN_URL": os.environ["SF_LOGIN_URL"], "SF_API_VERSION": os.environ.get("SF_API_VERSION", "62.0"),
    "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", ""), "CODEX_MODEL": os.environ.get("CODEX_MODEL", ""),
    "CODEX_SANDBOX": os.environ.get("CODEX_SANDBOX", "workspace-write"),
    "AUTO_DEPLOY": os.environ.get("AUTO_DEPLOY", "false"),
    # chatgpt: every developer signs in to their own Codex | apikey: one OpenAI key on the gateway
    "CODEX_AUTH_MODE": os.environ.get("CODEX_AUTH_MODE", "chatgpt"),
    # browser: normal Codex sign-in page (SSO), paste back the redirect | device: one-time code
    "CODEX_LOGIN_FLOW": os.environ.get("CODEX_LOGIN_FLOW", "browser"),
}
with open(sys.argv[1], "w") as fh:
    for k, v in keys.items():
        fh.write(f"{k}: {json.dumps(v)}\n")  # JSON strings are valid YAML scalars
PY

SECRETS="OPENAI_API_KEY=openai-api-key:latest,JIRA_API_TOKEN=jira-api-token:latest"
SECRETS+=",SF_AUTH_URL=sf-auth-url:latest,SF_CLIENT_ID=sf-client-id:latest,SF_CLIENT_SECRET=sf-client-secret:latest"
SECRETS+=",GATEWAY_API_KEY=gateway-api-key:latest"

# --no-cpu-throttling + one instance: agent runs are background threads that
# must keep CPU after the request that started them returns, and the
# workspace between "validated" and "deploy" lives on that instance.
# gen2: the Codex CLI sandbox needs a full Linux kernel surface.
gcloud run deploy "$SERVICE" \
  --project "$GCP_PROJECT" --region "$GCP_REGION" \
  --source "$HERE/../gateway" \
  --service-account "$SA" \
  --allow-unauthenticated \
  --execution-environment gen2 \
  --no-cpu-throttling --min-instances 0 --max-instances 1 --concurrency 20 \
  --cpu 2 --memory 4Gi --timeout 3600 \
  --env-vars-file "$ENV_FILE" \
  --set-secrets "$SECRETS"

URL="$(gcloud run services describe "$SERVICE" --project "$GCP_PROJECT" --region "$GCP_REGION" --format 'value(status.url)')"
echo
echo "Gateway URL: $URL"
echo "Smoke test:  curl -s $URL/healthz"
echo "Next: set this URL on the Salesforce Named Credential (salesforce/scripts/set-gateway-url.sh $URL)"
