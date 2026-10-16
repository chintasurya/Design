# Jira to Org — two agents, one knowledge graph, POC

You open a Lightning Web Component in your Salesforce org, it asks you to
**connect to Codex** first, then you talk to a **Requirement agent** about Jira
tickets. It reads the ticket, checks the org's **knowledge graph on GCP**, and
writes a development-ready spec. You send that spec to the **Developer agent**,
which has Codex write the metadata, validates it against the org, waits for
your approval, deploys, updates the Jira ticket, and writes what it built back
into the graph.

```
 Salesforce org (Developer Edition)                 GCP project
 ┌───────────────────────────────┐          ┌──────────────────────────────────────────────┐
 │ LWC  agentConsole             │          │ Cloud Run  agent-gateway (FastAPI)           │
 │  1 Connect to Codex           │  Apex +  │                                              │
 │  2 Chat: Requirement agent    │  Named   │  Requirement agent ── OpenAI Responses API   │
 │  3 Spec  → Developer agent    │  Cred.   │     tools: Jira, knowledge graph             │
 │  4 Review → Deploy            ├─────────►│  Developer agent ──── Codex CLI (codex exec) │
 │                               │  X-Gate- │     sf CLI: retrieve, check-only, deploy ────┼──► Salesforce
 │ AgentConsoleController (Apex) │  way-Key │                                              │    Metadata API
 └───────────────────────────────┘          │  Secret Manager  OpenAI key, Jira token,     │
                                            │                  SF client id/secret, gw key │
            Jira Cloud (KAN) ◄──────────────┤  BigQuery  agent_kg: nodes, edges,           │
            read, comment, transition       │            agent_nodes, agent_edges, snapshots│
                                            │  Firestore agent_runs, agent_conversations   │
                                            └──────────────────────────────────────────────┘
```

## Rules of engagement (from the owner, 2026-10-16)

The Jira site, the Salesforce Developer Edition org and the GCP project
`jira-to-org-poc-2610` are **new instances created for this POC**. The owner
has authorized Claude to log in to all three and make any change needed to
build, deploy and test the POC, within these limits:

1. **No personal information.** Do not read, export or change personal
   details in Jira, Salesforce or GCP (user profiles, contact details,
   account settings).
2. **No billing, banking or payment details.** Never open, read or change
   GCP Billing, Salesforce billing or Atlassian billing. Anything that
   touches billing or personal settings needs the owner's approval first;
   ask and wait.
3. **Credentials never go into the repo.** They come from the environment
   settings (`GCP_SA_KEY_JSON`, `GCP_PROJECT`, `GCP_REGION`, `JIRA_*`,
   `SF_AUTH_URL`, `SF_CLIENT_ID`, `SF_CLIENT_SECRET`) or, where the owner
   chooses, from chat (the Jira token was given that way on 2026-10-16).
   Inside a session they live only in the scratchpad; on GCP only in Secret
   Manager. Anything given in chat is rotated by the owner when the POC ends.
4. **Stay in this POC.** Jira project `KAN`, the org
   `orgfarm-0054ddc238-dev-ed`, the GCP project `jira-to-org-poc-2610`.

## Live POC (deployed 2026-10-16)

| | |
|---|---|
| Salesforce app | **Agentic Harness** (App Launcher; API name `Jira_to_Org`), org `orgfarm-0054ddc238-dev-ed` |
| Gateway | Cloud Run `agent-gateway`, `https://agent-gateway-6y7zlyimaa-uc.a.run.app`, project `jira-to-org-poc-2610`, `us-central1` |
| Knowledge graph | BigQuery `jira-to-org-poc-2610.agent_kg`; first snapshot `8314ed7b9897`, 828 nodes · 991 edges |
| Runs, conversations, token usage | Firestore `agent_runs`, `agent_conversations` |
| Jira | `chintasuryateja.atlassian.net`, project `KAN` |

### The app's three tabs

1. **Agent Console.** **Connect to Codex** signs *you* in to *your own*
   Codex account (your ChatGPT plan or company workspace, your limits):
   click **Sign in to Codex** (the normal OpenAI sign-in page, so SSO
   works), and when your browser lands on a `localhost:1455` page it cannot
   open, paste that address into the console. Then chat with the Requirement agent, send its
   spec to the Developer agent, review the files, and approve the deploy.
   Both agents run on your Codex session; **Sign out of Codex** ends it.
2. **Knowledge Graph.** A read-only reference. The opening view is the
   graph by kind: one circle per kind of component (size = how many), one
   arrow per kind of relationship (number = how many). Search for any
   object, field, class, flow, LWC or ticket to see its direct connections;
   click a neighbour to move to it. Hover shows the detail; a table view and
   the snapshot's coverage notes sit below.
3. **Agent Dashboard.** Model tokens per agent: totals, input/output and
   cached input, tokens per day (stacked: Requirement, Developer), tokens
   per Jira ticket, and the latest runs with their status. The Requirement
   agent's count is every Responses API call in a turn; the Developer
   agent's is every `codex exec` attempt, retries included.

### How "Connect to Codex" works (per developer)

```
Agent Console ──► Apex (sends your Salesforce username) ──► gateway
                                                             │ codex login, in a Codex home for you alone,
                                                             │ waiting for its redirect on 127.0.0.1:1455
   you ◄── "Sign in to Codex" link ◄─────────────────────────┘
   you sign in at auth.openai.com with your own account (SSO)
   browser → http://localhost:1455/auth/callback?code=… ("can't be reached": expected)
   you paste that address ──► Apex ──► gateway replays it to the waiting CLI
                                                             │ CLI exchanges the code (PKCE) → auth.json
                                                             │ → Secret Manager (codex-sessions)
Requirement agent ─► codex exec --output-schema, read-only, as you
Developer agent   ─► codex exec in the SFDX workspace, as you
```

- Nobody shares a key. Each developer's usage lands on their own Codex plan
  or workspace credits, and the dashboard shows tokens per developer.
- Sessions are kept in one Secret Manager secret, `codex-sessions`, keyed by a
  hash of the Salesforce username, so they survive Cloud Run restarts. Each
  save destroys the previous version. **Sign out of Codex** deletes yours.
- In this mode the Requirement agent cannot call live tools mid-answer (a
  Codex session only works through the Codex CLI), so the gateway looks up
  the tickets and the graph first and hands Codex the facts. Field existence
  is still re-checked against the graph afterwards.
- The pasted address carries a one-time code that is useless without the
  waiting CLI's PKCE verifier, and Apex and the gateway accept only a
  `localhost`/`127.0.0.1` `/auth/callback` address. The CLI owns port 1455,
  so one developer signs in at a time; a second sees "try again in a minute".
- `CODEX_LOGIN_FLOW=device` switches to a one-time code instead (needs
  device-code sign-in enabled on the ChatGPT account).
- `CODEX_AUTH_MODE=apikey` on the gateway switches back to one shared
  OpenAI API key for everyone.
- Known limit: the gateway trusts the username Apex sends, because only your
  org's named credential holds the gateway key. Production would have
  Salesforce sign the identity per user (per-user principals or JWT).

### Token budget: why reading a ticket costs nothing

Measured live: one Requirement agent call through Codex was 15.7k input
tokens, of which the gateway's own context (ticket, graph matches and
relationships, instructions) was about 2.7k. The other ~13k was Codex's
built-in coding-agent instructions, tool definitions and environment block,
sent on every call. So the agents now take the cheapest path first:

| Ask | Path | Model tokens |
|---|---|---|
| "Read KAN-6", "KAN-6", "status of KAN-8", "list my open tickets" | answered from Jira and the knowledge graph | **0** |
| "Analyze KAN-6" for a ticket analysed before whose summary, description and acceptance criteria are unchanged | its analysis, stored in the knowledge graph as a `RequirementSpec` node (`ticket --analysed as--> spec`), is returned; comments and status changes do not make it stale | **0** |
| "Analyze KAN-6" (new or changed), "what could break if…" | lean Codex: own short instructions (`model_instructions_file`), no tools, no environment block, low reasoning, trimmed graph context | target 2–4k |
| Developer agent | lean Codex coding run: short brief + workspace rules instead of Codex's prompt; no web search, apps, plugins or sub-agents | multi-turn; measured on the dashboard |

The **Agent Dashboard** shows tokens and, for a ChatGPT sign-in, the Codex
plan itself: % of the 5-hour and weekly limits used and the credits balance
(read from the same endpoint Codex's `/status` uses), plus per run how many
limit points and credits it used, and how many answers needed no model.

### For testers

- An admin assigns the **Agent Console User** permission set to each
  tester (Setup → Users → the user → Permission Set Assignments). It grants
  the app, the three tabs, the Apex controller and the gateway credential.
- Open **Agentic Harness** → **Agent Console** → **Connect to Codex** →
  **Sign in to Codex**, sign in with your own account, then paste the
  `localhost:1455/...` address your browser shows into the console.
- Try: *"List my open tickets"*, *"Analyze KAN-1"*, or create a new story in
  `KAN` (e.g. *"Add a Next Step Date field on Opportunity"*), then
  *"Analyze KAN-6"* → **Send to Developer agent** → review → **Deploy to org**.
- Every run shows up on the Agent Dashboard within a refresh.
- Known in this org: Opportunity `Priority__c`, `Region__c` and
  `RenewalDate__c` (KAN-2..4) exist but nobody has field-level security on
  them, so no user can see them. The graph knows they exist and the
  Requirement agent will propose granting access rather than creating them
  again.

## What each piece does

| Piece | Where | Job |
|---|---|---|
| `agentConsole` LWC | `salesforce/force-app/.../lwc` | Connect screen first, every time it opens. Then chat, ticket picker, spec card, developer timeline, file review, Deploy / Reject, graph rebuild |
| `AgentConsoleController` | `salesforce/.../classes` | One Apex method per gateway route, through `callout:Agent_Gateway`. Validates run ids and ticket keys before any callout. No generic proxy |
| `Agent_Gateway` named + external credential | `salesforce/.../namedCredentials`, `externalCredentials` | Holds the Cloud Run URL and injects `X-Gateway-Key`. The key never reaches the browser |
| Gateway | `gcp/gateway/app/main.py` | The HTTP API; every agent turn is a background **run** the LWC polls, because Apex callouts stop at 120 s and Codex takes minutes |
| Codex connection | `app/codex.py` | Verifies the OpenAI key, picks a Codex model the key can use, logs the Codex CLI in. A key pasted in the LWC is verified, then stored as a new Secret Manager version |
| Requirement agent | `app/agents/requirement.py` | Responses API tool loop: `list_jira_tickets`, `search_jira`, `get_jira_ticket`, `query_knowledge_graph`, `check_field_exists`, `submit_requirement_spec`. Re-checks every "create field" against the graph so a field that exists is never duplicated |
| Developer agent | `app/agents/developer.py` | SFDX workspace → retrieve what the spec modifies → `codex exec` → guard → check-only deploy with the tests Codex wrote → errors back to Codex (bounded, 3 attempts) → **wait for approval** → deploy → Jira comment + transition → graph write-back |
| Knowledge graph | `app/graph/` | Ingests objects, fields, record types, Apex, triggers, flows (including what they create/update and which subflows/Apex they call), LWC, validation rules, the Dependency API, and Jira tickets. Stored in BigQuery; traversed in memory |

### The safety rails, and why each exists

- **Connect first.** Nothing reads Jira or touches the org until Codex is
  connected in this session of the console.
- **Codex never holds a Salesforce credential.** Its process gets `PATH` and
  its own home, nothing else. The gateway logs the `sf` CLI in with a
  short-lived token only for retrieve and deploy, in a home directory deleted
  straight after.
- **A guard sits between Codex and the org.** It refuses deletions, profiles,
  settings, credentials, remote sites, connected apps, files over 200 KB, more
  than 60 files, and Apex without an `@isTest` class.
- **Check-only first, then a human.** Every change is validated with
  `sf project deploy start --dry-run` and the tests Codex wrote. The real
  deploy happens only when you press **Deploy to org** (set `AUTO_DEPLOY=true`
  on the gateway to skip the gate; not recommended — ticket text is an
  untrusted prompt).
- **The graph decides existence, not the model.** `check_field_exists` is an
  exact lookup, never inferred from a bounded search, and an object the graph
  does not hold reports *unknown*, not *absent*.

---

## Setup runbook

You need: the Salesforce org (`orgfarm-0054ddc238-dev-ed`), a GCP project with
billing, the Jira site `chintasuryateja.atlassian.net` (project `KAN`), and an
OpenAI API key with Codex model access. Run the GCP steps from Cloud Shell or
any machine with `gcloud` and `bq`; run the Salesforce steps with the `sf` CLI
or Workbench.

### 0. Rotate the Jira token

The token was pasted into a chat, so treat it as exposed. Create a new one at
<https://id.atlassian.com/manage-profile/security/api-tokens>, revoke the old
one, and use the new one in step 2. It goes into Secret Manager and nowhere
else.

### 1. Salesforce: how the gateway logs in

**What the POC uses: the org login (`SF_AUTH_URL`).** The owner approved a
Salesforce CLI login in the browser; its SFDX auth URL
(`force://PlatformCLI::<refresh token>@<my domain>`) goes into Secret Manager
as `sf-auth-url`, and the gateway refreshes its own access tokens from it.
Nothing to create in Setup. Revoke it any time under Setup → Connected Apps
OAuth Usage → Salesforce CLI.

**Alternative: an External Client App with client credentials**, so the
gateway holds no refresh token. Only needed if you prefer it:

1. Setup → **External Client App Manager** → **New External Client App**.
   Name `Agent Gateway`, distribution **Local**.
2. **Enable OAuth**. Callback URL `https://login.salesforce.com/services/oauth2/success`
   (unused, but required). Scopes: **Manage user data via APIs (api)**.
   Tick **Enable Client Credentials Flow**. Save.
3. **Policies** tab → **Edit** (it opens read-only, which looks like a
   disabled feature) → OAuth Policies → **Enable Client Credentials Flow** →
   **Run As**: your admin user. Save.
4. **Settings** tab → OAuth Settings → **Consumer Key and Secret**. Copy both
   (Salesforce asks for a verification code).

Token endpoint is your **My Domain**, not `login.salesforce.com` — the login
hosts reject this flow with *request not supported on this domain*:

```
SF_LOGIN_URL=https://orgfarm-0054ddc238-dev-ed.develop.my.salesforce.com
```

### 2. GCP: secrets, BigQuery, Firestore, service account

```bash
cd poc/jira-to-org/gcp/infra
export GCP_PROJECT=<your-project-id> GCP_REGION=us-central1
export JIRA_API_TOKEN=<the new token>
export SF_AUTH_URL=<force://... org login>   # or SF_CLIENT_ID + SF_CLIENT_SECRET
export OPENAI_API_KEY=<optional; you can paste it in the LWC instead>
./setup.sh
```

Enables Run, Cloud Build, Artifact Registry, Secret Manager, BigQuery and
Firestore; creates the `agent-gateway` service account with only the roles it
needs; creates the five secrets (a random `gateway-api-key` included); the
`agent_kg` dataset; and the Firestore database. Re-running is safe.

### 3. GCP: deploy the gateway to Cloud Run

```bash
export JIRA_BASE_URL=https://chintasuryateja.atlassian.net
export JIRA_EMAIL=chinta.suryateja@gmail.com JIRA_PROJECT_KEY=KAN
export SF_LOGIN_URL=https://orgfarm-0054ddc238-dev-ed.develop.my.salesforce.com
./deploy.sh
```

It prints the service URL. Check it: `curl -s <URL>/healthz` → `{"ok":true}`.

One instance with CPU always allocated (`--no-cpu-throttling --max-instances 1`):
agent runs are background threads, and the validated workspace waits on that
instance for your approval. If the instance is recycled the deploy step
rebuilds the workspace from the change set stored on the run.

Optional settings (env vars on `deploy.sh`): `OPENAI_MODEL` (Requirement
agent; default: the first of `gpt-5.3-codex`, `gpt-5.2-codex`,
`gpt-5.1-codex-max`, … the key can use), `CODEX_MODEL` (Developer agent;
default: the Codex CLI's own), `JIRA_START_TRANSITION` (`In Progress`),
`JIRA_DONE_TRANSITION` (`Done`), `CODEX_SANDBOX` (`workspace-write`; see
Troubleshooting).

### 4. Salesforce: deploy the console

```bash
cd poc/jira-to-org/salesforce
./scripts/set-gateway-url.sh https://<your-service>.run.app
sf org login web --alias jira-poc --instance-url https://orgfarm-0054ddc238-dev-ed.develop.my.salesforce.com
sf project deploy start --source-dir force-app --target-org jira-poc --test-level RunSpecifiedTests --tests AgentConsoleControllerTest
sf org assign permset --name Agent_Console_User --target-org jira-poc
```

No CLI? Run `./scripts/build-zip.sh` (or use the committed
`Agent_Console.zip`, whose URL is a placeholder you then fix in Setup →
Named Credentials) and deploy it in Workbench → Migration → Deploy.

Then give the named credential its key, once:

1. Copy it: `gcloud secrets versions access latest --secret gateway-api-key`
2. Setup → **Named Credentials** → **External Credentials** → **Agent Gateway**
   → Principals → **GatewayPrincipal** → Edit → **Add** an authentication
   parameter named **`ApiKey`** with that value. Save.

### 5. Use it

1. App Launcher → **Agent Console**.
2. **Connect to Codex.** Click **Sign in to Codex**, sign in with your own
   account (SSO), and paste back the `localhost:1455` address your browser
   lands on. (With
   `CODEX_AUTH_MODE=apikey` it asks for an OpenAI API key instead.)
3. **Rebuild knowledge graph** (bottom bar), once, and after big org changes.
4. Pick a ticket on the left, or ask: *"Analyze KAN-3"*, *"which tickets are
   ready?"*, *"what does the org already have on Account?"*. The agent's tool
   calls stream in as steps.
5. The spec card shows what will be created vs modified, what already exists
   (with graph evidence), what could be affected, the test plan, and open
   questions. **Send to Developer agent.**
6. Watch the timeline: workspace, retrieve, Codex, guard, validation. When it
   says **Waiting for your approval**, open the files, then **Deploy to org**
   or **Reject**.
7. After deploy the Jira ticket gets a comment and moves to Done, and the
   graph links the ticket to every component it built.

---

## Run and test locally

```bash
cd poc/jira-to-org/gcp/gateway
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q                      # 26 tests, no network, no cloud

# a local gateway against your real Jira / org, graph in a JSON file:
export GATEWAY_API_KEY=dev GRAPH_STORE=local RUN_STORE=memory
export JIRA_BASE_URL=... JIRA_EMAIL=... JIRA_API_TOKEN=... SF_LOGIN_URL=... SF_CLIENT_ID=... SF_CLIENT_SECRET=...
export CODEX_HOME_DIR=$HOME/.agent-codex WORKSPACE_ROOT=$HOME/.agent-runs
uvicorn app.main:app --port 8080
curl -s -H 'X-Gateway-Key: dev' localhost:8080/v1/status
```

The local gateway needs `npm i -g @openai/codex@0.163.0 @salesforce/cli` and `git` on `PATH`.

## API

All routes but `/healthz` need `X-Gateway-Key`.

| Method | Path | Body / result |
|---|---|---|
| GET | `/v1/status` | Codex, Jira, Salesforce, graph |
| POST | `/v1/codex/connect` | `{apiKey?}` → `{connected, model, needsKey, message}` |
| GET | `/v1/jira/tickets?only_open=true` | ticket list |
| POST | `/v1/requirements/chat` | `{message, conversationId?}` → `{runId, conversationId}` |
| POST | `/v1/developer/runs` | `{ticketKey, spec, override?}` → `{runId}` |
| GET | `/v1/runs/{id}` | `status`: queued · running · waiting_approval · succeeded · failed · rejected, plus `steps` and `result` |
| POST | `/v1/runs/{id}/deploy` · `/reject` | the approval gate |
| POST | `/v1/graph/rebuild` | `{runId}` |
| GET | `/v1/graph/stats` · `/v1/graph/search?q=` | inspect the graph |

Query the graph directly in BigQuery:

```sql
-- what does the org run on Account?
SELECT e.edge_type, n.node_type, n.api_name
FROM `agent_kg.edges` e JOIN `agent_kg.nodes` n ON n.id = e.from_id
WHERE e.to_id = 'sobj:account' AND e.edge_type != 'SOBJECT_HAS_FIELD';

-- what did the Developer agent build for each ticket?
SELECT from_id AS ticket, to_id AS component, written_at
FROM `agent_kg.agent_edges` WHERE edge_type = 'TICKET_IMPLEMENTED_BY' ORDER BY written_at DESC;
```

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| LWC: *Could not reach the agent gateway* | Named Credential URL still the placeholder, or Cloud Run not deployed |
| LWC: *The gateway rejected the key* | `ApiKey` on the GatewayPrincipal is missing or differs from `gateway-api-key` |
| `We couldn't access the credential(s)` | The user lacks **Agent Console User** (it grants the principal) |
| Salesforce *token request failed … request not supported on this domain* | `SF_LOGIN_URL` must be the My Domain |
| *… no client credentials user enabled* | External Client App Policies → Run As not set (step 1.3) |
| Connect: *None of the Codex-capable models are available* | Set `OPENAI_MODEL` to a model your key has, then redeploy |
| Codex steps fail with sandbox / landlock errors on Cloud Run | Redeploy with `CODEX_SANDBOX=danger-full-access`. The container is the boundary, and Codex holds no Salesforce or Jira credential either way |
| Jira step says *no 'In Progress' transition* | The board's workflow names differ; set `JIRA_START_TRANSITION` / `JIRA_DONE_TRANSITION` |

## What is verified and what is not

Verified here: the 26 gateway tests (agents, guard, fix loop, approval gate,
graph ingestion and traversal, Jira client, API end to end) against fakes; the
gateway booting from env config; the Codex CLI 0.163.0 accepting the exact
`exec` flags and config overrides used, and its JSONL event format; the
Salesforce package converting cleanly with `sf` 2.154.4; the LWC compiling
with `@lwc/compiler`; and the Apex passing the repo's `lint_apex.py`.

**Not verified:** nothing has run against the real Jira, Salesforce org,
OpenAI or GCP. This build environment's network policy blocks all four, so
the first live run is yours. The likeliest first-run snags are the
External/Named Credential metadata (if the deploy rejects them, create the
two in Setup by hand with the names above and deploy the rest), the Codex
sandbox on Cloud Run (see Troubleshooting), and Jira transition names.
