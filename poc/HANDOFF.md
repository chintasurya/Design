# HANDOFF — AI Change Console POC

Everything a fresh conversation needs to continue this work without re-deriving
it. Written 2026-09-20, rewritten 2026-09-24 after a session that closed P1 and
P2, declared the pod, and fixed two false clearances.

- **Repo:** `chintasurya/Design`
- **Branch:** `claude/funny-babbage-t29499` (all work lives here, never on main)
- **Package root:** `poc/salesforce/`
- **Deployable artifact:** `poc/salesforce/AI_Change_Console_POC.zip`
- **Last commit at handoff:** `a2361a2`

---

## 1. The goal

Build a working POC, in a Salesforce **sandbox**, that answers this question
before anybody writes code:

> *"Does what I am about to ask for already exist, and what will it break?"*

A user types a plain-English change request into a Lightning Web Component. The
system searches a **pre-built knowledge graph** of the org's metadata, shows its
reading of the request and the evidence it found, and returns a verdict —
already exists / safe to create / impact assessed. Only **after a human
approves** does anything reach a model or a Jira ticket.

The point is reuse discipline and token economy: the graph answers most
questions for free, and an LLM is called only when the graph proves something
genuinely new is needed.

### The intended end-to-end arc

```
user types request
      ↓
graph search (free, no LLM, ~2s)
      ↓
verdict + evidence shown on ONE screen
      ↓
── APPROVAL GATE 1 (human) ──
      ↓
Jira ticket raised  (current sprint, or next sprint if the current one is closed)
      ↓
"do you want me to connect a model to generate the logic?"  ← model buttons appear HERE
      ↓
── APPROVAL GATE 2 (human) ──
      ↓
Codex / Claude / Gemini generates the metadata
      ↓
deploy to sandbox → run tests → Jira status moves to QA / Testing
```

### Scope of the POC

| In | Out |
|---|---|
| Salesforce sandbox only | Production, ever |
| The **Network Services** pod only | All other pods |
| Salesforce as the **read** source | Jira/Confluence as read sources |
| Jira + Confluence as **write** targets (ticket + page creation) | — |
| Objects, fields, record types, Apex classes, triggers, flows, LWC | — |
| Create new metadata **and** update existing metadata | — |

---

## 2. Rules of engagement (do not break these)

1. **Sandbox only.** Never suggest or perform anything against production.
2. **No credentials in chat, ever.** The user authenticates with their own
   browser/CLI. Claude produces a package in git; the user deploys it through
   Workbench. Atlassian creds come from environment variables
   (`ATLASSIAN_SITE`, `ATLASSIAN_EMAIL`, `ATLASSIAN_TOKEN`) and are never passed
   as command-line arguments or written to the repo.
3. **Knowledge graph, not live search.** The user rejected live keyword search
   explicitly, twice. Layer 5 is a persisted JSON document. Do not drift back.
4. **Never store the graph in custom object records.** This was tried and it
   filled 221 MB of sandbox data storage with 113,310 records, blocking the user
   from creating any record at all. The graph lives in a **Salesforce File
   (ContentVersion)** as JSON.
5. **Run `python3 tools/build.py` before shipping any package.** It has caught
   six distinct classes of deploy-killing fault. Four deploy cycles were burnt
   on compile errors before it existed.
6. **Don't build literally — build correctly.** The user said: *"dont stick to
   what i say you know the functionality build in that way."* Interpret intent.
7. Be honest about what is unverified. Claude has no access to the org and
   cannot confirm what Semantica ContextGraph does beyond the user's documents.

---

## 2a. The Network Services pod, as the pod owner defined it

Declared in `AINetworkServicesPod`, not inferred. The profile was never going
to express this: several of these objects are written only by automation, so
the pod profile has no create permission on them and they fell out of scope
while being what the questions are about.

**Objects.** The generation chain — Account (a child Account is an Account)
→ HealthcareProvider → HealthcareFacility → HealthcarePractitionerFacility
→ CareProviderFacilitySpecialty → ContractPaymentAgreement — plus
HealthcareFacilityNetwork (HFN), Lead, Contact, Opportunity, Task, Case and
Credentialing Application.

**Created by automation, never typed:** HFN, HealthcarePractitionerFacility,
CareProviderFacilitySpecialty, ContractPaymentAgreement.

**Record types:** `Network Services` and `Network Services TX CIN`, on Lead and
Account and on most pod objects. Matched on `networkservices`, not the bare
word `network`, which would also catch an unrelated Network Partner.

**Automation naming:** flows and Apex are prefixed `Network Services`, `NS` or
`AHC`. Entry triggers are `AHC_AccountTrigger` and `AHC_LeadTrigger`.

**HFN generation** is the question most often asked. It happens in Apex in some
scenarios and in Flow in others. The Apex half is readable today and its call
chains are now edges. **The Flow half is not readable at all without the
Tooling API** — see section 8, which is now the blocking item rather than a
nice-to-have.

The declared names are logical, not API names: resolution ignores case, spaces,
underscores and a trailing `__c`. Anything that does not resolve is **named in
the scope note and in `tools/print_scope.apex`**, never dropped silently.

## 3. Architecture

### The eight layers (the agreed design)

| # | Layer | Where it lives today |
|---|---|---|
| 1 | **Sources** | Salesforce org metadata (Jira/Confluence are Phase 2 reads) |
| 2 | **Connectors** | `AIGraphSalesforceExport` — Describe + SOQL over ApexClass, ApexTrigger, FlowDefinitionView |
| 3 | **Ingestors** | same class — turns raw metadata into typed nodes |
| 4 | **Domain model** | `AIGraphDocument` — vendor-neutral node/edge contract |
| 5 | **Graph storage** | `AIGraphFileStore` — JSON in a ContentVersion file, versioned |
| 6 | **Graph exporter** | `AIGraphSalesforceExport` (Queueable) |
| 7 | **Semantica ContextGraph** | `AIGraphMemory` — in-memory adjacency + traversal |
| 8 | **Adapter API + model** | `AIContextGraphFile` → `AIReuseAnalyzer` → LWC |

`poc/ARCHITECTURE.md` holds the full nine-stage target-state diagram. The POC
is a compressed, in-org version of it.

### Why this is a knowledge graph and not Medallion

Asked directly by the user, for a client presentation. The agreed positions:

- **Medallion is a pipeline pattern** (bronze → silver → gold): it describes how
  data is *progressively refined*.
- **A knowledge graph is a data-model pattern**: entities and typed
  relationships, queried by traversal.
- This design is a **knowledge graph / metadata catalog** — the same shape as
  DataHub or Apache Atlas, but for delivery artifacts and consumed by an LLM.
  It *has* a refinement pipeline feeding it, which is why it looks Medallion-ish.
- **Do not say "Medallion is for data, knowledge graph is for metadata."** It is
  unsafe in front of a healthcare client — clinical knowledge graphs over
  patient data are common. The honest line is *pipeline pattern vs data-model
  pattern*.

### Layer 5 data contract

```apex
AIGraphDocument
  version, source (SALESFORCE|JIRA|CONFLUENCE|COMBINED), snapshotId,
  exportedAt, nodeCount, edgeCount, notes[]
  nodes[]         : id, nodeType, name, apiName, properties,
                    provenance, riskTier, sourceSystem
  relationships[] : id, edgeType, fromId, toId, origin, provenance, confidence
```

Field names are deliberate: `nodeType` not `type`, `fromId`/`toId` not
`from`/`to`, `sourceSystem` not `system` — all reserved words in Apex.

Eight edge types are emitted today:
`SOBJECT_HAS_FIELD`, `SOBJECT_HAS_RECORDTYPE`, `SOBJECT_RELATES_TO_SOBJECT`,
`TRIGGER_FIRES_ON_SOBJECT`, `FLOW_UPDATES_SOBJECT`, `APEX_REFERENCES_SOBJECT`,
`TRIGGER_CALLS_APEX`, `APEX_CALLS_APEX`.

The last two are what make a handler's handler reachable. A trigger body is two
lines that call a handler, so without them a question about what happens to an
Account returns the name of a file containing nothing.

Nodes with no edge are dropped — an unreachable node is noise.

### Storage decision, and the arithmetic behind it

| Option | Verdict |
|---|---|
| Custom object records | **Rejected.** 113,310 rows filled the sandbox |
| Static Resource | **Rejected.** Apex cannot write one without a Metadata API callout |
| Git, fetched at runtime | Rejected for the POC — needs a callout and a token |
| **ContentVersion (Salesforce File)** | **Chosen.** Apex-writable, versioned, counts against *file* storage not *data* storage |

Heap ceiling: peak usage is roughly **5.5× the JSON size** (blob + UTF-16 string
+ parsed object tree). Against the 12 MB async heap that puts the practical
ceiling near **1.7 MB of JSON ≈ 5,000 nodes**. `AIGraphFileStore.MAX_BYTES` is
set to 2,500,000 and `AIGraphMemory` reports actual measured heap, not an
estimate.

---

## 4. What exists today

### Repo map

```
poc/
├── Ascension Network Services Knowledge Graph.pptx
│                                slides 1-8 the target architecture,
│                                9-21 generated, what the POC actually does
├── deck/                        generator for slides 9-21; re-runnable,
│                                idempotent, with a geometry checker
├── ARCHITECTURE.md              target-state nine-stage pipeline
├── HANDOFF.md                   this file
├── discovery/
│   ├── discover_scope.py        read-only org scope probe
│   └── check_atlassian.py       read-only Atlassian probe (env vars only)
└── salesforce/
    ├── AI_Change_Console_POC.zip   ← deploy this in Workbench
    ├── README.md                   deploy notes + failure triage
    ├── TOOLING_API_SETUP.md        External Client App → Auth Provider →
    │                               Named Credential, sandbox, step by step
    ├── mdapi/                      source of truth (MDAPI format)
    │   ├── package.xml
    │   ├── classes/    (23 Apex classes)
    │   ├── objects/    (6)
    │   ├── lwc/aiChangeConsole/
    │   ├── permissionsets/         GENERATED — never hand-edit
    │   └── customMetadata/
    ├── stage/                      01-schema, 02-code, 03-config — deploy in
    │                               order if the main package fails
    └── tools/
        ├── build.py                5-stage gate; ALWAYS run before shipping
        ├── lint_apex.py            6 rules, each from a real failed deploy
        ├── gen_permset.py          derives the permission set from the metadata
        ├── emergency_purge.apex    hard-delete graph records (LIMIT 4000)
        ├── build_graph.apex        enqueue the export, then check the job and
        │                           print the notes, node and edge type counts
        ├── print_scope.apex        read-only: the scoped object list, with the
        │                           reason each one qualified
        ├── verify_tooling_api.apex read-only: does the Named Credential work,
        │                           and is Flow.Metadata really one per call
        └── probe_flow_missing.apex read-only diagnostic for the Account flow
```

### Apex classes

| Class | Role |
|---|---|
| `AIGraphDocument` | Layer 5 neutral contract + `combine()` |
| `AIGraphFileStore` | ContentVersion persistence; `save/load/describe`; 2.5 MB cap |
| `AIGraphMemory` | Layer 7 in-memory graph; `anchorObject`, `seeds`, `blastRadius`; measures heap |
| `AIGraphSalesforceExport` | Queueable exporter; caps at 220 objects / 200 fields each |
| `AINetworkServicesPod` | **The pod, declared.** Objects, record type tokens, automation name prefixes, entry triggers. The authority |
| `AINetworkServicesScope` | Resolves the declared pod against the org, with the profile and record types as corroboration |
| `AIRequestIntent` | Rule-based request parser (action, type, name, object, data type, shape) |
| `AIReuseAnalyzer` | Verdicts: Already Exists / Safe to Create / Impact Assessed / Needs Clarification / Likely Already Handled / Needs Review |
| `AIContextGraphFile` | Layer 8 adapter — object-anchored seeding, keyword fallback |
| `AIContextSlice` | Bounded evidence package (findings, never raw bodies) |
| `AIChangeRequestController` | LWC entry points (below) |
| `AIChangeRequestService` | Request state machine |
| `AIServiceFactory` | Chooses graph implementation from custom metadata |
| `AIContextGraphService/Stub/Http/Live` | Graph strategy interface + implementations |
| `AISalesforceMetadataSource` | The old live-search path (superseded, still present) |
| `*Test` × 6 | Includes `AIRequestIntentTest`, which pins real sandbox sentences |

### LWC entry points (`AIChangeRequestController`)

```
buildGraph()                → kicks off the Queueable export
graphStatus()               → node/edge/KB counts for the status bar
listProfiles()              → all profiles, alphabetical, filterable
createRequest(text)           → the sentence and nothing else
stepUnderstand(requestId)   ┐
stepScope(requestId)        │ progressive "thinking" pipeline,
stepSearch(requestId)       │ so the user sees what it is doing
stepAssess(requestId)       ┘
approveAnalysis / approveCode / rejectRequest / getView
chooseModel(requestId, model)  → recorded only after gate 1
```

### Custom objects

`AI_Change_Request__c`, `AI_Graph_Finding__c`, `AI_Generated_Artifact__c`,
`AI_Artifact_Chunk__c`, `AI_Test_Result__c`, `AI_Poc_Config__mdt`.

`Graph_Node__c` and `Graph_Edge__c` were **deleted** — that was the record-based
graph that filled the org.

`AI_Poc_Config__mdt` fields: `Use_Stub_Graph__c`, `Use_Remote_Graph__c`,
`Use_Live_Search__c`, `Context_Named_Credential__c`, `Context_Query_Path__c`,
`Pod_Profile_Name__c` (default `Network Services`), `Tooling_Named_Credential__c`,
plus Jira/Confluence credential fields reserved for the write services.

---

## 5. Build and deploy

```bash
cd poc/salesforce
python3 tools/build.py          # lint → permset → xml → contiguity → package
```

Five stages, all must pass:

1. **apex naming** — the six linter rules
2. **permission set** — regenerated from the `.object` and `.cls` files
3. **namespace-aware xml** — every file parsed with namespaces enabled
4. **contiguous element groups** — MDAPI rejects split same-named elements
5. **packaging** — writes the main zip plus the three staged zips

Then: Workbench → Migration → Deploy → upload `AI_Change_Console_POC.zip`,
tick *Single Package*, run tests as preferred. If the main package fails, deploy
`stage/01-schema.zip`, `stage/02-code.zip`, `stage/03-config.zip` in order —
whichever stage fails names the problem area.

After deploying, in the org: run **Build Graph** from the console once, wait for
the Queueable, then the status bar shows node/edge/KB counts.

---

## 6. Current state in the sandbox

**Working:**
- Package deploys clean.
- Graph builds: last reported **2,177 nodes · 2,786 edges · 1,427 KB JSON**.
- Duplicate detection works — asking for a field that exists returns the
  existing field and refuses to duplicate it.
- Pod scoping works, with tolerant profile matching (exact → case-insensitive →
  prefix) that reports any substitution it made.
- Whole-word / camelCase matching stopped the substring accidents (`"UPDATE"
  contains "DATE"` was returning six unrelated Account flows).
- The analysis stays on one screen with a visible step-by-step pipeline.

**Known broken or suspect:**

1. **The Account flow gap is addressed in code but unconfirmed in the org.**
   All three candidate causes were fixed without waiting for the probe, because
   each fix is cheap and correct on its own terms:
   - *Account outside the pod scope* — a flow is no longer dropped when its
     trigger object is outside the pod. The object enters as a **boundary
     node**: one node, no fields, enough to hang the automation off. Trigger
     labels now resolve against the whole org, not just the scoped set.
   - *The `LIMIT 200` cap* — the read now asks for record-triggered flows
     first, ordered, so screen flows cannot displace the ones that can produce
     an edge. The cap itself cannot be raised; `FlowDefinitionView` rejects
     `queryMore()`. When the batch fills, the notes say so.
   - *A subflow with no trigger object* — still needs the Tooling API (P4). The
     probe now reports whether `FlowElementView` is queryable and dumps its
     fields, which decides whether P4 is needed for this case at all.

   Two further defects were found while fixing it, both of which would have
   kept the symptom alive after the export was correct. See section 9.

   **Still to do: run `tools/probe_flow_missing.apex` and report the output.**
   It confirms which cause was real and whether the fix took.
2. **Scope resolved, and the declared pod was the right call.** Measured
   2026-09-21: **49 objects in scope — 13 declared, 12 writable on the
   "Network Services" profile, 24 carrying a Network Services record type.**
   All **13 declared objects resolved**, so the API names in
   `AINetworkServicesPod` are correct as written. Account, HealthcareProvider
   and HealthcareFacility are all in scope.

   The permission-set diagnostic settles the old argument in the opposite
   direction to the one expected: permission sets assigned to that profile's
   users grant write on **1,319 objects**. That is not a pod, it is most of the
   org, and scoping from it would blow the 220-object export guard instantly.
   Permission sets are the wrong scope signal here, not the right one — the
   declared pod is what makes this work, and using it is not a shortcut.

3. **The scope note is now measured rather than suspected.** Every resolve also
   counts the objects writable through **permission sets assigned to the
   profile's users**, and the note prints it next to the profile's own numbers.
   If permission sets grant more than the profile does, the note says outright
   that the profile is the narrower signal and may be the wrong one. The old
   note's apparent contradiction ("36 owned out of 18 readable") was real but
   not a bug: `owned` is the *union* of writable and record-type objects, and
   record types are not filtered by profile readability. The note now says that.
   When the profile grants nothing at all, the scope falls back to the
   permission-set objects rather than to every readable object.
4. **Nobody has ever seen the scoped object list.** The scope reported counts
   and never names, which is why "is Account in scope?" could not be answered
   from anything in the repo. `tools/print_scope.apex` prints the list with the
   reason each object qualified, and the exporter now writes the names into the
   graph notes so every graph file says what it covered. Neither is a
   substitute for running it: the scope is live org state.
5. **There is no snapshot model, only snapshot retention.** Saving to an
   existing `ContentDocumentId` keeps every prior build as a ContentVersion,
   and each build stamps a `snapshotId` and `exportedAt` that
   `AI_Change_Request__c.Snapshot_Id__c` records, so any past answer can be
   tied to the graph state it was given for. Nothing is built on top of that:
   `load()` always takes `IsLatest = true`, no code reads an earlier version,
   nothing diffs two builds, and no node or edge carries a `validFrom` or
   `validTo`. So the questions a snapshot model exists to answer — what
   changed since the last sync, when did this component appear, what did the
   graph hold when that decision was approved — cannot be asked. The target
   architecture names snapshot diffing and temporal retraction as Layer 7
   capabilities; the POC has neither. `AIGraphFileStore`'s header used to
   claim diffing "comes for free"; it does not, and the comment now says so.
   The cheapest first step is a diff between two ContentVersions of the same
   file, which needs no schema change at all.
6. The graph can see *that* a flow exists but not *what it does*. Reading
   `recordCreates` / `recordUpdates` needs the Tooling API (section 8).

---

## 7. Open work, in priority order

Re-ranked 2026-09-24. P1 and P2 are done and verified in the org; what was P4
is now the blocker.

### P1 — Finish the Tooling API credential  ·  BLOCKING

Everything else of value is behind this. Flow internals are unreadable without
it, and "how is an HFN generated" is answered half in Apex (working) and half
in Flow (invisible).

**Where it got to.** PKCE is locked on in this org — the External Client App
shows *"To change this required setting, contact Support"* — so the
authorization code flow is impossible and **client credentials is the only
path**. Appendix A of `salesforce/TOOLING_API_SETUP.md` is the runbook. Three
errors were worked through in order, each one progress:

| Error | Cause | Fixed by |
|---|---|---|
| `missing required code challenge` | PKCE locked on, auth code flow unusable | switching to client credentials |
| `request not supported on this domain` | token endpoint was `test.salesforce.com` | **client credentials is only served by My Domain** |
| `no client credentials user enabled` | **the app has no Run As user** | ← **this is where it stopped** |

**Next action:** External Client App Manager → Policies → **Edit** (the tab
opens read-only, which looks identical to a disabled feature) → tick *Enable
Client Credentials Flow* → the **Run As** field appears only after that tick →
choose an integration user with **API Enabled** and **View Setup and
Configuration** → Save → re-run `tools/verify_tooling_api.apex`. If the error
survives, the consumer key on the External Credential principal belongs to a
different app than the one carrying Run As.

**Already proved, using `tools/verify_tooling_session.apex`** (which bypasses
OAuth with `UserInfo.getSessionId()` and a Remote Site Setting — a diagnostic
only, since that does not work in async Apex):

- `Flow.Metadata` **is readable** and carries `recordCreates`, `recordUpdates`,
  `recordLookups` **and `subflows`**
- **495 active flows**, all 495 ids returned in **one** call — the Tooling API
  removes the 200-row `FlowDefinitionView` cap as a side effect
- `SELECT Id, Metadata ... LIMIT 5` returns `MALFORMED_QUERY`, so **one record
  per call is confirmed**: 495 retrieves against 100 callouts per transaction
  means a **chained Queueable across 5+ transactions**, keeping only extracted
  facts (a body is ~8 KB; 495 of them is ~4 MB, which the heap will not hold)
- `MetadataComponentDependency` answers, so **real dependency edges are
  available** and the Apex body text-scan heuristic can be retired

### P2 — Build the flow reader, once P1 is green

Design is settled by the measurements above. Chained Queueable, progress
persisted between transactions, extract and discard per flow. Emits
`FLOW_CREATES_SOBJECT` / `FLOW_UPDATES_FIELD` style edges and
`FLOW_CALLS_SUBFLOW`, which is the flow equivalent of the Apex call chains that
already work. This is what finally answers HFN generation end to end.

### P3 — Resume from a ticket number  ·  agreed, not started

The console opens with two doors: a new request, or a ticket number that
rehydrates the stored analysis, evidence and approval from
`AI_Change_Request__c`, so nothing is re-answered and no second ticket is
raised. Status arc: Ticket Created → In Progress → generate → deploy → QA, and
into the next sprint if the current one is closed.

### P4 — Snapshot model  ·  a gap against the design, see section 6 item 5

Versions are retained; nothing reads or compares them. Cheapest first step is a
diff between two ContentVersions of the same file — no schema change needed.

### P5 — Jira and Confluence write services

Ticket creation and page creation. Credential fields exist on
`AI_Poc_Config__mdt`; the services do not.

### Done this session, with the defect each one fixed

| Was | Now |
|---|---|
| Flows on out-of-pod objects dropped entirely | boundary nodes; automation is never lost for its target's sake |
| A behaviour cleared because the object was never searched | a clearance must show the trigger object was in the evidence |
| Pod scope inferred from a profile that cannot see automation-written objects | `AINetworkServicesPod` declares it; 13/13 names resolved |
| Apex read with `contains()`, so `Account` matched `AccountingCode` | whole-identifier token matching |
| Trigger → handler → handler invisible | `TRIGGER_CALLS_APEX` and `APEX_CALLS_APEX` edges |
| Type and model asked for on the entry screen | type derived; model asked only after gate 1 |
| One question about HFN returned 55 rows, all via `sobj:account` | a non-anchor object is a destination, not a corridor |
| Rows read as `apex:X -[EDGE]-> sobj:y` | rows read as sentences, ordered automation first |
| **A field that existed cleared as Safe to Create** | **existence has its own budget-free lookup** |
| A column change listed 30 classes that merely mention the object | schema changes show the object and what runs on it |

---

## 8. Tooling API — what it takes and what it buys

All in the sandbox, ~15 minutes, needs Setup access.

**Full runbook: `poc/salesforce/TOOLING_API_SETUP.md`.** Summary:

1. **External Client App** (Setup → App Manager → New External Client App).
   Connected Apps are superseded; the Auth. Provider and Named Credential steps
   are unchanged. Distribution State **Local**, Enable OAuth, scopes `api` and
   `refresh_token, offline_access`, PKCE **off**, placeholder callback. Then
   **Policies → Edit** and enable OAuth there too — policies are a separate
   screen and an app whose policies were never saved refuses to authorize,
   which is the most common failure. Copy Consumer Key and Secret, wait ~10 min.
2. **Auth. Provider** (New → type **Salesforce**). Paste the key/secret.
   Authorize `https://test.salesforce.com/services/oauth2/authorize`, token
   `https://test.salesforce.com/services/oauth2/token`, scopes
   `api refresh_token`. Save, copy its generated **Callback URL** back into the
   app.
3. **Named Credential** (New Legacy). Name `AI_Tooling_API`, Identity Type
   **Named Principal**, OAuth 2.0 with that Auth. Provider, **Start
   Authentication Flow on Save** and **Generate Authorization Header** ticked.
   URL is **the My Domain sandbox URL**, `https://<mydomain>--<sandbox>.sandbox.my.salesforce.com`.
4. **Permissions** on that principal: API Enabled, View Setup and Configuration,
   View All Data (the Dependency API needs it; flow internals do not).
5. **`AI_Poc_Config__mdt.Default.Tooling_Named_Credential__c`** = `AI_Tooling_API`.
6. **Verify with `tools/verify_tooling_api.apex`** before building anything on
   it. Read-only, four callouts.

**This org locks PKCE on** (*"To change this required setting, contact
Support"*), so the authorization code flow is unavailable: a Salesforce-type
Auth. Provider sends no `code_challenge` and saving the Named Credential fails
with `missing required code challenge`. **Use Appendix A of
TOOLING_API_SETUP.md, the client credentials flow**, which never redirects a
browser, has no refresh token to rotate, and works in asynchronous Apex — which
the Queueable export needs regardless. It was the better destination anyway.

**`test.salesforce.com` is a login host, not an API host.** It is correct for
the Auth. Provider endpoints and wrong for the Named Credential URL: a callout
there returns a login page, so the failure looks like an HTML body or a 302
rather than an auth error. The verify script calls this out by name.

Apex then calls `callout:AI_Tooling_API/services/data/v59.0/tooling/query?q=...`
with no Remote Site Setting needed.

### Measured against the org, 2026-09-21, not assumed

Everything below came back from `tools/verify_tooling_session.apex` against the
sandbox. It replaces the guesses this section used to carry.

| Question | Answer |
|---|---|
| Is `Flow.Metadata` readable? | **Yes.** A retrieve of one flow returned 8,445 characters carrying `recordCreates`, `recordUpdates`, `recordLookups` **and** `subflows`. Flow internals and flow-to-subflow chains are both reachable. |
| How many active flows? | **495.** `FlowDefinitionView` caps at 200 in one batch and cannot page, so the current exporter sees at most 40% of them. |
| Can Tooling read all 495 ids at once? | **Yes**, `SELECT Id FROM Flow WHERE Status = 'Active'` returned `totalSize: 495, done: true` in a single call. The Tooling API removes the 200-flow cap as a side effect. |
| Is `Metadata` one record per call? | **Confirmed.** `SELECT Id, Metadata ... LIMIT 5` returns HTTP 400 `MALFORMED_QUERY`: *"the query qualifications must specify no more than one row for retrieval"*. So 495 retrieves against a 100-callout limit per transaction: **a chained Queueable across at least five transactions**, persisting progress between them. |
| Is `MetadataComponentDependency` available? | **Yes**, HTTP 200. Real dependency edges are on the table, replacing the Apex body text scan. |

**The client credentials token endpoint must be My Domain**, not
`test.salesforce.com`. The login host rejects the flow with `invalid_grant` and
*request not supported on this domain*, which reads like a bad client id and is
not one.

| Query | What it gives |
|---|---|
| `Flow.Metadata` | what a flow **does** — `recordCreates`, `recordUpdates` and their targets. The real fix for the Account case |
| `MetadataComponentDependency` | real dependency edges, replacing the Apex text-scan heuristics |
| `ValidationRule`, `LightningComponentBundle` | two component types the graph cannot see at all today |
| `ApexCodeCoverageAggregate` | coverage, needed for the deploy gate later |

**Constraint, now confirmed rather than assumed:** Tooling API queries selecting
`Metadata` or `FullName` return **one record per call**. With 495 active flows
that is 495 callouts against a 100-per-transaction limit, so flow internals must
be read in a chained Queueable across at least five transactions, persisting
progress between them. Only the extracted facts can be kept — a flow body is
~8 KB, and 495 of them is roughly 4 MB before parsing, which the heap will not
hold.

---

## 9. Traps already paid for — do not rediscover these

### Apex compile traps (all six are now linter rules in `tools/lint_apex.py`)

1. Identifiers may not end in `_` (`override_` failed).
2. Reserved words as **parameter** names: `system`, `type`, `any`, `like`, `on`,
   `list`, `global`, `override`.
3. Reserved words as **local variable** names — same list. `List<...> any` and
   `List<...> on` both shipped before the rule existed.
4. Exception classes must end in `Exception` and must not shadow a System
   exception (an inner `CalloutException` failed).
5. **Inner enum values referenced unqualified** fail with the misleading *"Static
   field cannot be referenced from a non static context"*. Replaced with String
   constants.
6. **Apex identifiers are case-insensitive**, so a local `automation` shadows a
   static `AUTOMATION` and produces *"void contains(String) from the type
   List<...>"*. Three real instances existed.

### Governor and platform traps

- **`FlowDefinitionView` rejects `queryMore()`.** A SOQL for-loop always opens a
  cursor regardless of `LIMIT`, so it must be a **list assignment** with an
  explicit `LIMIT`. Four for-loops had to be converted.
- **`Database.emptyRecycleBin()` counts against the same DML row governor as the
  delete.** 9,000 + 9,000 blew the 10,000 limit; the purge uses `LIMIT 4000`.
- A plain delete frees **no storage for 15 days** — hard delete is required.
- Static Resources **cannot** be written from Apex without a Metadata API callout.
- ContentVersion counts against **file** storage, not data storage; setting
  `ContentDocumentId` creates a new version rather than a new file.
- **A picklist default is applied on insert, so "not choosing" becomes a
  choice.** `Model__c` was `required` with `Codex` defaulted. Simply leaving it
  out of the insert would have written Codex anyway, and the console would have
  shown a model nobody picked. Deferring a field means clearing `required`
  **and** removing the `<default>` from its value set.
- A **required** field is implicitly editable, so `gen_permset.py` leaves it out
  of the permission set. Making one optional adds it — that is why the field
  count moves when a `required` flag changes.
- Apex `Map` key order is **not** guaranteed — the data-type scan needs an
  explicit ordered list so `DATETIME` is tried before `DATE` and `TEXTAREA`
  before `TEXT`.

### MDAPI packaging traps

- `UNKNOWN_EXCEPTION` with **0 component errors and 0 deployed** means the
  package failed at **parse**, before any component was examined. It is a
  packaging fault, not a metadata fault.
- Custom Metadata Type fields require `<fieldManageability>` on every field.
- A `.md` custom metadata record using an `xsd:` prefix without declaring the
  namespace kills the whole package. The XML check must be **namespace-aware**;
  `minidom` without namespaces passes it happily.
- PermissionSet XML requires same-named elements to be **contiguous**. Hence
  `gen_permset.py` — never hand-append to a permission set.
- API version is pinned at **59.0** (62.0 was tried and lowered).

### Graph and traversal traps

- **A node budget spent on columns never reaches the automation.** `blastRadius`
  walked edges in storage order, and an object with 200 fields has 200
  `SOBJECT_HAS_FIELD` edges against perhaps three pieces of automation. With
  `MAX_NODES = 60` the walk finished inside the field list and the Flow that
  answered the question never entered the result. Edges are now walked
  **behaviour before structure**, and a caller can exclude node types from the
  traversal outright — filtering the result afterwards is too late, the budget
  is already gone.
- **An unsearched absence is not an absence.** `AIReuseAnalyzer.behaviour()`
  returned Safe to Create on an empty finding list, which meant "the graph does
  not hold Account" and "nothing runs on Account" produced the same verdict.
  A clearance now requires the trigger object to appear in the evidence: if it
  was never searched, the verdict says so and blocks. This is the single most
  important rule in the analyzer — the whole POC exists to stop a confident
  answer that nothing checked.
- **Automation is allowed to reach outside the pod.** A Flow record-triggered
  on Account is part of the pod's behaviour even when Account is not a pod
  object. Dropping it because its target was out of scope was how the console
  came to answer a question about a Flow by not knowing the Flow existed.
  Out-of-scope trigger objects now enter as **boundary nodes**, capped at 150,
  carrying `{"boundary":true}` and a provenance line that says why they are
  there.
- **Resolving a label needs the whole org, not the scope.** `labelToApi` was
  built only from scoped objects, so any reference outside the pod resolved to
  null regardless of the cause. The org index is built from
  `getGlobalDescribe().keySet()` — **keys only**, no `getDescribe()` calls,
  because describing ~1,400 objects to read their labels would spend the CPU
  budget the export needs.
- **A view object may refuse a filter or a sort, and a static SOQL that tries
  it fails to compile.** The record-triggered-first flow read is `Database.query`
  inside a try/catch for exactly this reason: an org that will not filter
  `FlowDefinitionView` on `TriggerObjectOrEventLabel` falls back to the plain
  read and writes a note, instead of taking the whole class down at deploy.

### Search relevance traps

- **A second object is a destination, not a corridor.** *"Terminate
  HealthcareFacilityNetwork when due date is exceeded"* returned **55
  components**, every one of them reached via `-> sobj:account`. The walk
  passed **through** Account, which carries ~70 `APEX_REFERENCES_SOBJECT`
  edges, and fanned out across all of them. An SObject that is not what the
  request named is now reported as a finding but **never expanded through**.
  Triggers, flows and classes still expand, which is what follows a call chain.
- **The parser only finds objects in phrasings it was taught.** `OBJECT_CLAUSE`
  wants `on|in|to|for <Object>` at the end of the sentence. "terminate
  HealthcareFacilityNetwork when due date is exceeded" names its object
  plainly and matches none of those, so the anchor was empty and the search
  fell back to keywords, where "due" and "date" pulled in half the org.
  `AIGraphMemory.objectsNamedIn()` now matches the text against the graph's own
  SObject nodes — including labels written with spaces and custom objects
  without `__c` — which works for every object in the pod without a rule per
  phrasing.
- **An unknown verb is the widest possible search.** `terminate` was not in
  `ACTIONS`, so the action fell back to `Analyze`, which traverses three hops
  and produces a directory rather than an answer. The pod's real vocabulary is
  now listed: terminate, expire, deactivate, close, cancel, archive, suspend,
  renew, generate, populate, prevent and friends.
- **Existence must never be inferred from a bounded sample.** *"Create
  Effective From Date field in Healthcarefacility object"* returned **Safe to
  Create** for a field that was in the graph. `blastRadius` stops at
  `MAX_NODES = 60`; HealthcareFacility has **135 fields and 17 automation
  components**, and behaviour edges are walked first, so roughly **seven fields
  in ten never entered the result** — and `exactMatches()` then searched the
  survivors. Which fields survived depended on map iteration order, so the
  verdict was effectively luck. A bounded walk can support *"here is what this
  touches"*; it can never support *"this does not exist"*, because absence from
  a sample says nothing about absence from the org. Existence now has its own
  lookup: `AIGraphMemory.attachedMatches()` scans the anchor's own edges,
  complete by construction, with no budget anywhere near it.
- **Adding a column is not a code change.** The same request listed 32
  components, most of them Apex classes that merely mention the object
  somewhere in their body. For a Field or RecordType request the blast radius
  that matters is the object and the automation that **runs on** it, which is
  what needs regression; a class that references the object is a step further
  away than the question reaches. Those rows are dropped for schema changes,
  and the recommendation counts flows and triggers rather than everything, so
  the number in the sentence matches the list underneath it.
- **Rows are read by both audiences.**
  `apex:AHC_TestDataFactory -[APEX_REFERENCES_SOBJECT]-> sobj:account` is
  legible to whoever wrote the exporter and to nobody else. Findings now carry
  a sentence — *"Apex that reads or writes Healthcare Facility Network"*,
  *"Called by the trigger AHC_AccountTrigger"* — and are ordered automation
  first, then code it calls, then the object and its columns, so the answer
  reads top down instead of in adjacency-map order.

### Matching and parsing traps

- `"UPDATE".contains("DATE")` is true. Substring matching returned six unrelated
  Account flows for a HealthcareFacility request. Whole-word/camelCase matching
  is now mandatory.
- Case-sensitive `Set` comparison between `ObjectPermissions.SobjectType` and
  `getGlobalDescribe().keySet()` produced an **empty scope**, which produced 350
  orphan nodes and 0 edges. Scope matching is lowercase on both sides, an empty
  scope now **refuses** to export, and orphan nodes are dropped.
- `FlowDefinitionView.TriggerObjectOrEventLabel` is a **label**, not an API name.
  It must be resolved through a label→API map, or only `Account` ever matches.
- A trailing component noun is not part of a name: *"create effective from date
  field"* means a field called *"effective from date"*, not *"effective from
  date field"*. Fixed in commit `2df9f3d`, pinned by `AIRequestIntentTest`.
- Node_Type__c is a **restricted picklist** — any new node type must be added to
  it, and `AIContextSlice` maps unknown types to `Other` so one new type cannot
  fail an entire insert.

---

## 10. Recent commits worth knowing

```
a2361a2 Stop deciding whether something exists from a truncated sample
4831623 Correct a claim about snapshot diffing, and record the gap it was hiding
186bfb1 Fix line spacing that stacked every wrapped paragraph on one line
914ec5b Add thirteen slides to the deck describing what the POC actually does
08a804d Add files via upload
3aa10b4 Stop walking through one object to reach everything that touches another
e85360a Document the no-client-credentials-user error and what it rules in
bbdd7a6 Replace the Tooling API guesses with what the org actually returned
6b88c14 Make the graph rebuild a script like everything else
10cb19d Spell out that the external credential and the named credential are two objects
8720f55 Distinguish New from New Legacy, and say a legacy credential must be replaced
77ba7d0 Explain an authentication status stuck at Pending under client credentials
89b1996 Give a certain test for a missing principal, and point at the org's own examples
023b583 Explain an empty External Credential Principal Access list
2be3010 Take the client credentials warning at face value and say how to contain it
703b724 Say that the Policies tab opens read-only, and how to tell that from a locked setting
2f9a31f Say which of the two External Client App screens holds Run As
f7c22c4 Promote client credentials to the primary path, because this org locks PKCE on
6933e4d Explain the PKCE failure, including the org-wide switch that overrides the app
2b575a2 Diagnose the 401, and stop the Tooling API questions waiting on the OAuth config
89bd324 Say plainly what steps 6 and 7 do, and stop the verify script failing five times over
448d641 Write the Tooling API setup runbook for External Client Apps, and a way to verify it
2b5c799 Declare the Network Services pod instead of inferring it from a profile
9f8a7f5 Print the scoped object list, and write the names into the graph notes
```
