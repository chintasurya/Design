#!/usr/bin/env bash
# One-time GCP setup for the Jira-to-Org agents. Idempotent: safe to re-run.
#
# Reads secrets from YOUR shell environment and writes them to Secret Manager.
# Nothing is written to disk or to the repo. Usage:
#
#   export GCP_PROJECT=my-project GCP_REGION=us-central1
#   export JIRA_API_TOKEN=...            # required
#   export SF_AUTH_URL=force://...       # the org login (sfdxAuthUrl); or, instead:
#   export SF_CLIENT_ID=... SF_CLIENT_SECRET=...   # an External Client App with Run As
#   export OPENAI_API_KEY=...            # optional: or paste it in the LWC on first connect
#   ./setup.sh
set -euo pipefail

: "${GCP_PROJECT:?set GCP_PROJECT}"
GCP_REGION="${GCP_REGION:-us-central1}"
BQ_LOCATION="${BQ_LOCATION:-US}"
BQ_DATASET="${BQ_DATASET:-agent_kg}"
SA_NAME=agent-gateway
SA="${SA_NAME}@${GCP_PROJECT}.iam.gserviceaccount.com"

gcloud config set project "$GCP_PROJECT" >/dev/null

echo "== enabling APIs"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  secretmanager.googleapis.com bigquery.googleapis.com firestore.googleapis.com

echo "== service account $SA"
gcloud iam service-accounts describe "$SA" >/dev/null 2>&1 \
  || gcloud iam service-accounts create "$SA_NAME" --display-name "Jira-to-Org agent gateway"

# put_secret NAME VALUE: create if missing; add a version only when a value is supplied
put_secret() {
  local name="$1" value="${2:-}"
  if ! gcloud secrets describe "$name" >/dev/null 2>&1; then
    gcloud secrets create "$name" --replication-policy=automatic >/dev/null
    printf '%s' "${value:-unset}" | gcloud secrets versions add "$name" --data-file=- >/dev/null
    echo "   created $name"
  elif [ -n "$value" ]; then
    printf '%s' "$value" | gcloud secrets versions add "$name" --data-file=- >/dev/null
    echo "   updated $name"
  else
    echo "   kept    $name"
  fi
  gcloud secrets add-iam-policy-binding "$name" --member "serviceAccount:$SA" \
    --role roles/secretmanager.secretAccessor >/dev/null
}

echo "== secrets"
put_secret jira-api-token "${JIRA_API_TOKEN:-}"
put_secret sf-auth-url "${SF_AUTH_URL:-}"
put_secret sf-client-id "${SF_CLIENT_ID:-}"
put_secret sf-client-secret "${SF_CLIENT_SECRET:-}"
put_secret openai-api-key "${OPENAI_API_KEY:-}"
# each developer's own Codex sign-in (ChatGPT mode): one secret holding a map keyed by a
# hash of the Salesforce username. The gateway adds a version per save and destroys the
# previous one, so it needs version management on this secret only.
if ! gcloud secrets describe codex-sessions >/dev/null 2>&1; then
  gcloud secrets create codex-sessions --replication-policy=automatic >/dev/null
  printf '{}' | gcloud secrets versions add codex-sessions --data-file=- >/dev/null
  echo "   created codex-sessions"
fi
for role in roles/secretmanager.secretAccessor roles/secretmanager.secretVersionManager; do
  gcloud secrets add-iam-policy-binding codex-sessions --member "serviceAccount:$SA" --role "$role" >/dev/null
done
# the LWC can submit a new OpenAI key at connect time (API-key mode); stored as a new version
gcloud secrets add-iam-policy-binding openai-api-key --member "serviceAccount:$SA" \
  --role roles/secretmanager.secretVersionAdder >/dev/null
if ! gcloud secrets describe gateway-api-key >/dev/null 2>&1; then
  put_secret gateway-api-key "$(openssl rand -hex 32)"
else
  put_secret gateway-api-key ""
fi

echo "== BigQuery dataset $BQ_DATASET (the knowledge graph)"
bq --location="$BQ_LOCATION" show "$GCP_PROJECT:$BQ_DATASET" >/dev/null 2>&1 \
  || bq --location="$BQ_LOCATION" mk --dataset --description "Jira-to-Org knowledge graph" "$GCP_PROJECT:$BQ_DATASET"
gcloud projects add-iam-policy-binding "$GCP_PROJECT" --member "serviceAccount:$SA" \
  --role roles/bigquery.jobUser --condition=None >/dev/null
# dataset-level IAM bindings need allowlisting, so grant WRITER through the dataset's access list
ACL="$(mktemp)"
bq show --format=prettyjson "$GCP_PROJECT:$BQ_DATASET" > "$ACL"
python3 - "$ACL" "$SA" <<'PY'
import json, sys
path, sa = sys.argv[1], sys.argv[2]
ds = json.load(open(path))
if not any(a.get("userByEmail") == sa for a in ds.get("access", [])):
    ds.setdefault("access", []).append({"role": "WRITER", "userByEmail": sa})
json.dump({"access": ds["access"]}, open(path, "w"))
PY
bq update --source "$ACL" "$GCP_PROJECT:$BQ_DATASET" >/dev/null
rm -f "$ACL"

echo "== Firestore (agent runs and conversations)"
gcloud firestore databases describe --database="(default)" >/dev/null 2>&1 \
  || gcloud firestore databases create --location="$GCP_REGION" --type=firestore-native
gcloud projects add-iam-policy-binding "$GCP_PROJECT" --member "serviceAccount:$SA" \
  --role roles/datastore.user --condition=None >/dev/null

echo
echo "Done. Next: ./deploy.sh"
echo "The Salesforce Named Credential needs the gateway key. Copy it with:"
echo "  gcloud secrets versions access latest --secret gateway-api-key"
