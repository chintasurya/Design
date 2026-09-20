# AI Change Console: Phase 1

Metadata API package for the Network Services POC. Deployable to a sandbox
today, with no backend service, because the graph layer ships with a stub.

**`AI_Change_Console_POC.zip`** is the Workbench-ready artifact.
**`mdapi/`** is the same content unzipped, and is the source of truth in git.

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

## Switching from stub to live service

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
