# AI Change Console: Phase 1

Metadata API package for the Network Services POC. Deployable to a sandbox
today, with no backend service, because the graph layer ships with a stub.

**`AI_Change_Console_POC.zip`** is the Workbench-ready artifact.
**`mdapi/`** is the same content unzipped, and is the source of truth in git.

## If the deploy fails

`UNKNOWN_EXCEPTION` with **0 component errors and 0 components deployed** means
the package failed while being parsed, before any component was examined. It is
a packaging fault, not a metadata fault. Two were found and fixed in the first
build:

- Custom metadata type fields were missing `<fieldManageability>`, which is
  mandatory on every CMT field.
- `AI_Poc_Config.Default.md` used the `xsd:` prefix without declaring the
  namespace. A namespace-aware parser rejects the file outright.

A second round then failed on Apex compilation, with two root causes and
eight cascade errors hiding behind them:

- `AIServiceFactory.override_` ended in an underscore, which Apex forbids
  outright, and `override` is a reserved word besides.
- `AIContextGraphStub.build()` took a parameter named `system`, which is
  reserved.

`tools/lint_apex.py` now catches both, plus exception classes that do not end
in `Exception` or that shadow a System exception. Run `python3 tools/build.py`
before shipping a package: it lints, parses every XML file with namespaces
enabled, checks package.xml against the files actually present, and only then
writes the zips.

If the main package still fails, deploy `stage/01-schema.zip`, then
`stage/02-code.zip`, then `stage/03-config.zip` in that order. Whichever stage
fails names the problem area.

The custom metadata **record** is deliberately not in the main package.
`AIServiceFactory.config()` falls back to sane defaults when the record is
absent, so the console runs without it. Deploy `03-config.zip` only if you want
the record present, or create it by hand in Setup.

## Deploy via Workbench

1. Log in to Workbench against the sandbox (`https://test.salesforce.com`).
2. **migration > Deploy**.
3. Choose `AI_Change_Console_POC.zip`.
4. Tick **Rollback on Error** and **Single Package**.
5. Test level: `RunSpecifiedTests` with
   `AIChangeRequestServiceTest,AIChangeRequestControllerTest,AIServiceFactoryTest`,
   or `NoTestRun` for a first smoke deploy.
6. Deploy, then assign the **AI Change Console User** permission set.
7. Drop the **AI Change Console** component on a Lightning App or Home page.

## Deploy via CLI instead

```bash
sf project deploy start --metadata-dir mdapi --target-org ns-sandbox --wait 20
sf org assign permset --name AI_Change_Console_User --target-org ns-sandbox
```

To work in SFDX source format in VS Code:

```bash
sf project convert mdapi --metadata-dir mdapi --output-dir force-app
```

## What is in it

| Component | Purpose |
|---|---|
| `AI_Change_Request__c` | One request, with the status machine and both approval stamps |
| `AI_Graph_Finding__c` | One row per node the graph returned, with provenance |
| `AI_Generated_Artifact__c` | One row per proposed metadata change |
| `AI_Artifact_Chunk__c` | Overflow for bodies past the 131,072 character field cap |
| `AI_Test_Result__c` | One row per test method executed |
| `AI_Poc_Config__mdt` | Stub-versus-live switch and the named credential to use |
| `AIChangeRequestService` | The state machine, including gate enforcement |
| `AIContextGraphService` | Interface the graph layer sits behind |
| `AIContextGraphStub` | Canned findings so the console runs with no backend |
| `AIContextGraphHttp` | Live implementation, via named credential |
| `aiChangeConsole` | LWC: request entry, three model buttons, both approval gates |

Findings are **rows, not a JSON blob**, so the approval screen, the Jira ticket
and any audit report all read the same records. No field in this package ever
holds a whole graph.

## What the console actually concludes

Four real Apex round trips, shown as they complete. Each line appears because
work behind it finished, not on a timer.

```
1  Reading the request        Create a Field named "Provider NPI" on Account
2  Resolving the scope        34 objects readable by "Network Service", 12 writable
3  Searching live metadata    9 connected components identified
4  Assessing reuse            Field "Provider NPI" already exists
```

### Asking for something that already exists

This is the rule the architecture exists to enforce: modify what is there,
create new only when genuinely needed. `AIReuseAnalyzer` returns one of four
outcomes:

| Outcome | When | What the console does |
|---|---|---|
| **Already Exists** | Create request, exact match found | Blocks, cites the existing component, tells you to reuse it |
| **Safe to Create** | Create request, no match | Allows, lists near misses, warns about automation needing regression |
| **Impact Assessed** | Update or delete | Reports the blast radius, direct vs one hop, how many are high risk |
| **Needs Clarification** | Nothing matched | Asks you to name the component rather than guessing |

Name matching normalises across spellings, so `Provider NPI`,
`Provider_NPI__c` and `providernpi` are recognised as the same field. Asking to
create a field that is already there returns the existing field with its real
type and provenance, and refuses to duplicate it.

### What it reads, with no configuration

Scope comes from the pod's profile, so "why is this in scope" always has the
answer "the Network Service profile can read it".

| Component | Source | Available |
|---|---|---|
| Objects | `Schema.describe()` | yes |
| Fields, formulas, lookups | `Schema.describe()` | yes |
| Record types | `getRecordTypeInfos()` | yes |
| Apex classes | SOQL `ApexClass` | yes |
| Triggers | SOQL `ApexTrigger` by `TableEnumOrId` | yes |
| Flows | SOQL `FlowDefinitionView` | yes |
| Lightning components | Tooling API only | not yet |
| Validation rules | Tooling API only | not yet |

The last two are unreachable from Apex without the Tooling API. The search says
so in its notes rather than omitting them silently.

### Jira and Confluence

Not read sources. They are write targets for this POC: a ticket raised on
analysis approval, a page written on completion. The config fields are in
place; the write services are Phase 2.

### What live mode is not

Name matching against live metadata, not graph traversal. It resolves what a
change touches directly and one hop out. Multi-hop blast radius, reuse across
capabilities and cross-source edges need precomputed typed relationships, which
is the graph layer's job. Nothing above `AIContextGraphService` changes when it
arrives.

## Switching to the remote graph service

Edit **Custom Metadata Types > AI POC Config > Default**:

| Field | Stub | Live |
|---|---|---|
| Use Stub Graph | checked | unchecked |
| Context Named Credential | | `Semantica_Context_Service` |
| Context Query Path | | `/v1/context/query` |

Then create the Named Credential of that name pointing at the Semantica
service. No redeploy is needed to flip between them.

The service must return JSON matching `AIContextSlice`:

```json
{
  "snapshotId": "b7f1c2e4-...",
  "summary": "12 connected components across 3 sources",
  "findings": [
    {
      "nodeId": "sobj:HFN__c",
      "nodeType": "SObject",
      "nodeName": "HFN",
      "relationshipPath": "Direct target of the request",
      "impact": "Direct",
      "riskTier": "High",
      "sourceSystem": "Salesforce",
      "provenance": "SALESFORCE_METADATA objects/HFN__c.object-meta.xml",
      "artifactHash": "sha256:9f2b...c41d",
      "confidence": 1.0
    }
  ]
}
```

## State machine

```
Draft ──▶ Analyzing ──▶ Awaiting Analysis Approval ──▶ Ticket Created
                                                            │
                                                            ▼
Complete ◀── Testing ◀── Deploying ◀── Awaiting Code Approval ◀── Generating
```

`Rejected` and `Failed` are reachable from anywhere. Every other transition is
whitelisted in `AIChangeRequestService.ALLOWED`, and an illegal jump throws
rather than silently succeeding. `approvalGatesCannotBeSkipped` in the test
class asserts that a Draft request cannot be deployed.

## Not in Phase 1

Deliberately deferred until the discovery output lands and the service endpoint
is agreed:

- Jira ticket creation on analysis approval
- The prompt builder and the model callout
- Tooling API deploy of generated metadata
- Tooling API test execution and result capture
- Platform Event push so the LWC updates without a refresh

Phase 1 is the skeleton those hang off, and it is demonstrable on its own:
type a request, watch the graph answer, approve or reject at the gate.

## Before demoing

Replace the fixtures in `AIContextGraphStub` with real node ids from the
discovery run. Stub findings currently reference `sobj:HFN__c`,
`flow:HFN_Generation` and `NS-1234`, which are placeholders.
