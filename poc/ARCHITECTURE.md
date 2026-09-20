# POC Architecture: the pipeline, mapped to Salesforce

The nine-stage Engineering Context pipeline, annotated with the Salesforce
objects and Apex classes that exist in the Phase 1 package.

**The one thing to take from this page:** Salesforce appears **twice** and the
two appearances have nothing to do with each other. In Zone A it is a *source
system*, read-only, one of six. In Zone C it is the *consumption layer*, where
the console and the audit trail live. Stages 2 through 8 contain **no Salesforce
objects at all**.

```text
╔══════════════════════════════════════════════════════════════════════════════════════╗
║  ZONE A  ·  SYSTEMS OF RECORD                     read-only · authority never moves  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

  ┌────────────┐┌────────────┐┌────────────┐┌────────────┐┌────────────┐┌────────────┐
  │ Jira       ││ Confluence ││ Salesforce ││ Git        ││ Copado     ││ Drive      │
  │ issues     ││ pages      ││ metadata   ││ source     ││ releases   ││ docs       │
  └────────────┘└────────────┘└────────────┘└────────────┘└────────────┘└────────────┘
  └────────────── POC SCOPE ───────────────┘└─────────────── PHASE 2 ────────────────┘

      ┌──────────────────────────────────────────────────────────────────────────┐
      │ Salesforce appears HERE as a source, and again in Zone C as the          │
      │ consumption layer. Same org, two unrelated roles. Read path is           │
      │ Tooling + Metadata + Dependency API, scoped by the Network Service       │
      │ profile and the NetworkService / Network Services TX CIN record types.   │
      └──────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │  one read-only connector per system
                                            ▼

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  ZONE B  ·  GOOGLE CLOUD                          zero Salesforce objects live here  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

              ┌──────────────────────────────────────────────────────────┐
              │ Source Connectors                                        │
              │ per-source auth · delta pull · no write scope            │
              └──────────────────────────────────────────────────────────┘
                                            │
                                            ▼
              ┌──────────────────────────────────────────────────────────┐
              │ SourceArtifact                                           │
              │ raw bytes + metadata + SHA-256 + retrievedAt             │
              └──────────────────────────────────────────────────────────┘
                                            │
                                            ▼
              ┌──────────────────────────────────────────────────────────┐
              │ Source-specific Ingestors                                │
              │ ADF · HTML · Flow XML · Apex · sheet parsing             │
              └──────────────────────────────────────────────────────────┘
                                            │
                                            ▼
              ┌──────────────────────────────────────────────────────────┐
              │ Extensible Engineering Context                           │
              │ thin core model + domain / project extensions            │
              └──────────────────────────────────────────────────────────┘
                                            │
                                            ▼
              ┌──────────────────────────────────────────────────────────┐
              │ Neutral Graph JSON                                       │
              │ nodes + edges + provenance  →  archived in Git           │
              └──────────────────────────────────────────────────────────┘
                                            │
                                            ▼
              ┌──────────────────────────────────────────────────────────┐
              │ Semantica ContextGraph                                   │
              │ in-memory traversal · blast radius · reuse · risk        │
              └──────────────────────────────────────────────────────────┘

╔──────────────────────────────────────────────────────────────────────────────────────╗
║  THE SEAM  ·  GRAPH QUERY API                      GCP JSON becomes Salesforce rows  ║
╚──────────────────────────────────────────────────────────────────────────────────────╝

      ┌──────────────────────────────────────────────────────────────────────────┐
      │ POST  callout:Semantica_Context_Service/v1/context/query                 │
      │                                                                          │
      │ Salesforce side of the boundary, all of it:                              │
      │    AI_Poc_Config__mdt.Default     named credential + stub switch         │
      │    AIServiceFactory               picks stub or live                     │
      │    AIContextGraphService          the interface Semantica sits behind    │
      │    AIContextGraphHttp             the live client                        │
      │    AIContextSlice                 the DTO the JSON deserializes into     │
      └──────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │  AIContextSlice.toRecords(requestId)
                                            ▼

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  ZONE C  ·  SALESFORCE                               everything we built in Phase 1  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

         ┌────────────────────────────────────────────────────────────────────┐
         │ aiChangeConsole  (LWC)                                             │
         │ request entry · Codex | Claude | Gemini · both approval gates      │
         └────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
         ┌────────────────────────────────────────────────────────────────────┐
         │ AIChangeRequestController      @AuraEnabled surface, thin          │
         │ AIChangeRequestService         state machine, gates enforced here  │
         └────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
      ┌──────────────────────────────────────────────────────────────────────────┐
      │ AI_Change_Request__c        the ask, the status, both approval stamps    │
      │ AI_Graph_Finding__c         ONE ROW PER NODE the graph returned          │
      │ AI_Generated_Artifact__c    one row per proposed metadata change         │
      │ AI_Artifact_Chunk__c        overflow past 131,072 characters             │
      │ AI_Test_Result__c           one row per test method executed             │
      └──────────────────────────────────────────────────────────────────────────┘

         ┌────────────────────────────────────────────────────────────────────┐
         │ The graph slice lands as ROWS, never as a JSON blob in a field.    │
         │ That is why the approval screen, the Jira ticket and the audit     │
         │ report can all read the same records.                              │
         └────────────────────────────────────────────────────────────────────┘
                                            │
                                            │  approve gate 2  →  write back
                                            ▼

╔══════════════════════════════════════════════════════════════════════════════════════╗
║  ZONE D  ·  RETURN PATH                             sandbox only · never production  ║
╚══════════════════════════════════════════════════════════════════════════════════════╝

                ┌──────────────────────────────────────────────────────┐
                │ Tooling API deploy                                   │
                │ MetadataContainer → ApexClassMember                  │
                └──────────────────────────────────────────────────────┘
                                            │
                                            ▼
                ┌──────────────────────────────────────────────────────┐
                │ Tooling API test run                                 │
                │ runTestsAsynchronous → ApexTestResult                │
                └──────────────────────────────────────────────────────┘
                                            │
                                            ▼
                ┌──────────────────────────────────────────────────────┐
                │ Jira status update                                   │
                │ ticket moves to Testing, results attached            │
                └──────────────────────────────────────────────────────┘

        ┌──────────────────────────────────────────────────────────────────────┐
        │ And this closes the loop. The deployed change and the updated Jira   │
        │ ticket are themselves Zone A sources, so the next sync re-ingests    │
        │ them. The pipeline is drawn as a line but it runs as a cycle.        │
        └──────────────────────────────────────────────────────────────────────┘
```

## Stage by stage

| # | Pipeline stage | Runs where | Salesforce artifact |
|---|---|---|---|
| 1 | Six systems of record | External + the org itself | Salesforce is a **source**: Tooling, Metadata and Dependency API, scoped by the Network Service profile |
| 2 | Source Connectors | Python service on GCP | none |
| 3 | SourceArtifact | Python service, in flight | none |
| 4 | Source-specific Ingestors | Python service | none |
| 5 | Extensible Engineering Context | Python service | none |
| 6 | Neutral Graph JSON | Git archive + GCS | none |
| 7 | Semantica ContextGraph | Cloud Run, in memory | none |
| 8 | Graph Query API | Cloud Run endpoint | `AIContextGraphHttp`, `AIContextSlice`, `AIServiceFactory`, `AI_Poc_Config__mdt`, Named Credential |
| 9 | Salesforce UI / AI agent / users | Salesforce | `aiChangeConsole`, `AIChangeRequestController`, `AIChangeRequestService`, all five custom objects |

Stage 8 is the only line in the whole pipeline that crosses the boundary. That
is deliberate: if Semantica is ever replaced, `AIContextGraphHttp` is the single
class that changes, because everything downstream depends on `AIContextSlice`
rather than on the graph runtime.

## What gets written, and when

| Status | Written by | Records created |
|---|---|---|
| `Draft` | `AIChangeRequestService.create` | `AI_Change_Request__c` with a correlation id |
| `Analyzing` | `analyze()` | none yet, the graph call is in flight |
| `Awaiting Analysis Approval` | `analyze()` | one `AI_Graph_Finding__c` per node returned, plus snapshot id and summary on the parent |
| `Ticket Created` | `approveAnalysis()` | approval stamped; Jira issue key written (Phase 2) |
| `Generating` | Phase 2 | none |
| `Awaiting Code Approval` | Phase 2 | `AI_Generated_Artifact__c` per proposed change, `AI_Artifact_Chunk__c` only past 131,072 characters |
| `Deploying` | `approveCode()` | second approval stamped |
| `Testing` | Phase 2 | `AI_Test_Result__c` per test method |
| `Complete` | Phase 2 | Jira moved to Testing with results attached |
| `Rejected` / `Failed` | any state | reason written to `Error_Message__c` |

## Why findings are rows

`AI_Graph_Finding__c` holds **one record per node** the graph returned, not a
JSON document in a field. That choice is what makes the rest work:

- The approval screen renders a datatable straight off the records.
- The Jira ticket is built from the same rows, so the evidence in the ticket and
  the evidence on screen cannot drift.
- An auditor can query findings by risk tier across every request ever raised.
- No field in the package ever holds a whole graph, so the 6 MB synchronous heap
  limit is never in play.

Node **properties and provenance** are stored. Raw artifact bodies are not. The
graph carries `artifactPath` and `artifactHash`, and the model fetches source on
demand for the two or three components in the change plan.

## Technology decisions

Reviewed against the platform recommendation from engineering leadership.
Most of it matches what is already built; two rows are worth arguing.

| Capability | Recommended | What we built | Verdict |
|---|---|---|---|
| Salesforce UI | LWC | `aiChangeConsole` | Agreed, shipped |
| Salesforce integration layer | Apex | `AIChangeRequestController`, `AIChangeRequestService` | Agreed, shipped |
| Call GCP from Salesforce | Named Credential / OAuth | `Semantica_Context_Service` + `AI_Poc_Config__mdt` | Agreed, shipped |
| Source ingestion | Cloud Run Jobs | Cloud Run Jobs | Agreed, and a better call than a long-running service |
| Scheduling | Cloud Scheduler | Cloud Scheduler | Agreed, fills a gap we had left open |
| Transformation / context generation | Cloud Run | Cloud Run | Agreed |
| Intermediate snapshot | Cloud Storage | Cloud Storage **+ Git** | Add Git for readable snapshot diffs |
| **Graph DB** | **Spanner Graph** | **Semantica now, Spanner as the destination** | **Defer, see below** |
| Graph API | Cloud Run service | Cloud Run service | Agreed |
| Secrets | Secret Manager | Secret Manager | Agreed, fills a gap |
| **Audit / analytics** | **BigQuery / Cloud Logging** | **Audit in Salesforce, analytics in BigQuery** | **Split the row, see below** |
| Graph visualization | Spanner Studio initially | Contingent on the graph DB call | Contingent |
| Business-facing visualization | Custom LWC later | Agreed | Agreed |

Rows the platform table does not cover, which the flow needs:

| Capability | Where it belongs | Why |
|---|---|---|
| LLM provider gateway | Cloud Run, not Apex | Apex caps a callout at 120s with no streaming; one abstraction beats three Named Credentials and three response parsers |
| Approval workflow and state | Salesforce, `AI_Change_Request__c` | The gates are the governance story; they belong where the approver works |
| Metadata write-back | Apex, Tooling API | Must originate in-org |
| Test execution and results | Apex, Tooling API | Must originate in-org |
| Jira write-back | Cloud Run or Apex | Either; Apex keeps the audit chain in one place |

### Graph DB: the choice is deferrable

Spanner Graph is a defensible destination and the instinct behind it is right.
Durable, managed, ACID, IAM-governed, and it removes the "who maintains this
library" question at an architecture review. The Engineering Memory scaling
notes already call for durable graph persistence at enterprise level.

The reasons not to adopt it for the POC:

- One pod's graph is roughly 3,000 to 6,000 nodes, about a megabyte. Spanner is
  built for petabyte-scale distributed OLTP, and it carries a real monthly floor
  even at minimum provisioning. Price it before committing.
- Semantica already exists, already holds the analysis functions, and is already
  Layer 7 in the client deck.
- An in-memory traversal answers in under 10 ms with no network hop.

The reason this is not urgent: **Salesforce has no opinion about it.**
`AIContextGraphService` is an interface, and everything downstream depends on
`AIContextSlice` rather than on a graph runtime. Moving from Semantica to
Spanner Graph changes the Cloud Run Graph API and nothing else. No Apex, no LWC,
no objects, no redeploy.

One thing to prove before committing either way: express `blast_radius` with a
runtime-variable hop count, `reuse_candidates` and `coverage_gap` in GQL against
a representative subgraph. If Spanner Graph handles those cleanly, the migration
is genuinely a swap. Note also that adopting Spanner shrinks Semantica's role to
ingestion and context generation, since the analysis functions become GQL plus
application logic in the Graph API.

### Audit and analytics are two different rows

They have different readers and belong in different places.

**Audit belongs in Salesforce.** Who asked, what the graph found, who approved,
what deployed, what the tests said. This is evidence attached to a governed
decision, and the approver has to see it in the same place they approved. For a
healthcare client, the audit trail living where the governance lives is the
point. `AI_Change_Request__c` and its children already hold it, queryable by
delivery leads without a data engineer in the loop.

**Analytics belongs in BigQuery.** Sync durations, node and edge counts over
time, graph growth per pod, model usage. Aggregate measurement over time is a
warehouse job, and Salesforce is the wrong tool for it.

**Cloud Logging is neither.** It is service telemetry, useful for debugging a
failed sync, not an audit trail and not analytics.

Putting the audit in BigQuery means the approver cannot see the evidence behind
the decision they are being asked to make.

## The return path

The original diagram ends at consumption. The POC does not: it writes back, and
the write-back lands in systems that are themselves Zone A sources.

```
Zone C approval  →  Tooling API deploy  →  Tooling API test run
                                              │
                          Jira ticket updated ┘
                                              │
                    next sync re-ingests it ──┘  →  back to Zone A
```

Drawn as a line, run as a cycle. Worth saying out loud in the room, because it
is the difference between a read-only assistant and a delivery loop.

Sandbox only. No phase of this design holds a production credential.
