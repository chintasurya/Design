# HANDOFF — AI Change Console POC

Everything a fresh conversation needs to continue this work without re-deriving
it. Written 2026-09-20.

- **Repo:** `chintasurya/Design`
- **Branch:** `claude/funny-babbage-t29499` (all work lives here, never on main)
- **Package root:** `poc/salesforce/`
- **Deployable artifact:** `poc/salesforce/AI_Change_Console_POC.zip`
- **Last commit at handoff:** `7676cce`

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

Six edge types are emitted today:
`SOBJECT_HAS_FIELD`, `SOBJECT_HAS_RECORDTYPE`, `SOBJECT_RELATES_TO_SOBJECT`,
`TRIGGER_FIRES_ON_SOBJECT`, `FLOW_UPDATES_SOBJECT`, `APEX_REFERENCES_SOBJECT`.

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
├── ARCHITECTURE.md              target-state nine-stage pipeline
├── HANDOFF.md                   this file
├── discovery/
│   ├── discover_scope.py        read-only org scope probe
│   └── check_atlassian.py       read-only Atlassian probe (env vars only)
└── salesforce/
    ├── AI_Change_Console_POC.zip   ← deploy this in Workbench
    ├── README.md                   deploy notes + failure triage
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
        └── probe_flow_missing.apex read-only diagnostic for the Account flow
```

### Apex classes

| Class | Role |
|---|---|
| `AIGraphDocument` | Layer 5 neutral contract + `combine()` |
| `AIGraphFileStore` | ContentVersion persistence; `save/load/describe`; 2.5 MB cap |
| `AIGraphMemory` | Layer 7 in-memory graph; `anchorObject`, `seeds`, `blastRadius`; measures heap |
| `AIGraphSalesforceExport` | Queueable exporter; caps at 220 objects / 200 fields each |
| `AINetworkServicesScope` | Pod footprint from profile object access + record types |
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
createRequest(text, type, model)
stepUnderstand(requestId)   ┐
stepScope(requestId)        │ progressive "thinking" pipeline,
stepSearch(requestId)       │ so the user sees what it is doing
stepAssess(requestId)       ┘
approveAnalysis / approveCode / rejectRequest / getView
```

### Custom objects

`AI_Change_Request__c`, `AI_Graph_Finding__c`, `AI_Generated_Artifact__c`,
`AI_Artifact_Chunk__c`, `AI_Test_Result__c`, `AI_Poc_Config__mdt`.

`Graph_Node__c` and `Graph_Edge__c` were **deleted** — that was the record-based
graph that filled the org.

`AI_Poc_Config__mdt` fields: `Use_Stub_Graph__c`, `Use_Remote_Graph__c`,
`Use_Live_Search__c`, `Context_Named_Credential__c`, `Context_Query_Path__c`,
`Pod_Profile_Name__c` (default `Network Services`), plus Jira/Confluence
credential fields reserved for the write services.

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

1. **No Flow is linked to Account**, so *"when an Account is created, create a
   HealthcareProvider and a HealthcareFacility"* still returns Safe to Create
   when a Flow already does exactly that. Three candidate causes, in order of
   suspicion — Account is outside the pod scope; the `LIMIT 200` cap on
   `FlowDefinitionView` (no `ORDER BY`) cut it; or it is a subflow with no
   trigger object. **`tools/probe_flow_missing.apex` diagnoses all three** and
   has not yet been run.
2. **The scope note reads "36 objects owned by Network Services (12 writable, 24
   with a Network record type) out of 18 readable."** Only 18 readable objects
   strongly suggests this org grants access through **Permission Sets, not the
   profile** — which would make the profile the wrong scope signal entirely.
   Unresolved.
3. The graph can see *that* a flow exists but not *what it does*. Reading
   `recordCreates` / `recordUpdates` needs the Tooling API (section 8).

---

## 7. Open work, in priority order

### P1 — Run the probe and fix the Account flow gap
`tools/probe_flow_missing.apex` in Developer Console → Execute Anonymous, with
Open Log ticked. Read-only. It prints the scope, the true active-flow count,
every active flow record-triggered on Account, what reached the graph, and
whether `FlowElementView` is describable (which might give flow internals with
plain SOQL and skip the Tooling API for this case).

### P2 — LWC restructure (user's point 3, agreed, not started)
- **Remove the "Change something that exists / Add something new" Type buttons.**
  The system now infers the shape itself; the person typing does not know
  whether their request is new or an update.
- **Move the three model buttons (Codex / Claude / Gemini)** so they appear only
  *after* approval, phrased as *"do you want me to connect a model to get the
  logic?"* — not on the entry screen.

### P3 — Resume-from-Jira-ticket (user's point 4, agreed, not started)
The console should open with two doors:
- **new request** — as today; or
- **enter a Jira ticket number** — rehydrate the stored analysis, evidence and
  approval from `AI_Change_Request__c` so the user does not re-answer
  everything and a second ticket is not created.

Status arc to implement: Ticket Created → In Progress → generate → deploy → QA.
If the ticket is not in the current sprint it goes to the next sprint.

### P4 — Tooling API connection
Unlocks flow internals, real dependency edges, validation rules, LWC bundles and
code coverage. Setup steps in section 8.

### P5 — Jira and Confluence write services
Ticket creation and page creation. Credential fields already exist on
`AI_Poc_Config__mdt`; the services do not exist yet.

---

## 8. Tooling API — what it takes and what it buys

All in the sandbox, ~15 minutes, needs Setup access.

1. **Connected App** (Setup → App Manager → New Connected App / External Client
   App). Enable OAuth. Scopes `api` and `refresh_token, offline_access`.
   Placeholder callback URL for now. Save, wait ~10 min, copy Consumer Key and
   Secret.
2. **Auth. Provider** (Setup → Auth. Providers → New → type **Salesforce**).
   Paste the key/secret. Authorize endpoint
   `https://<mydomain>.sandbox.my.salesforce.com/services/oauth2/authorize`,
   token endpoint `.../services/oauth2/token`, default scopes
   `api refresh_token`. Save, then copy its generated **Callback URL** back into
   the Connected App.
3. **Named Credential** (New Legacy). Name `AI_Tooling_API`, URL
   `https://<mydomain>.sandbox.my.salesforce.com`, Identity Type **Named
   Principal**, OAuth 2.0 with the Auth Provider, tick **Start Authentication
   Flow on Save** and **Generate Authorization Header**.
4. **Permissions** on that principal: API Enabled, View Setup and Configuration,
   View All Data (the Dependency API needs it).

Apex then calls `callout:AI_Tooling_API/services/data/v59.0/tooling/query?q=...`
with no Remote Site Setting needed.

| Query | What it gives |
|---|---|
| `Flow.Metadata` | what a flow **does** — `recordCreates`, `recordUpdates` and their targets. The real fix for the Account case |
| `MetadataComponentDependency` | real dependency edges, replacing the Apex text-scan heuristics |
| `ValidationRule`, `LightningComponentBundle` | two component types the graph cannot see at all today |
| `ApexCodeCoverageAggregate` | coverage, needed for the deploy gate later |

**Constraint to plan around:** Tooling API queries selecting `Metadata` or
`FullName` return **one record per call**. With ~200 active flows that is 200
callouts against a 100-per-transaction limit, so flow internals must be read in
a chained Queueable across several transactions. Confirm this on the first real
call rather than taking it on trust.

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
7676cce  Add a read-only probe for the missing Account flow
2df9f3d  Read the field name out of the request without swallowing "field"
b6b40f3  Fix a case-insensitive shadowing bug, and lint for the whole class of it
7829f98  Stop clearing behaviour requests the graph cannot actually vouch for
40379ca  Measure the heap the graph load actually uses, and trim the document
0d0199a  Match whole words, and anchor the search on the object that was named
bf30b66  Fix the empty scope that produced 350 orphan nodes and zero edges
ed9601f  Match the profile tolerantly, and stop hiding it in the diagnostic
c3adbfe  Move Layer 5 from records to a JSON file, per the original design
1ebd2b6  Replace live search with a real persisted knowledge graph
```
