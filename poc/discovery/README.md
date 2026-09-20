# POC Discovery

Read-only scripts that size the Network Services pod before any POC code is written.
Neither script writes to Salesforce, Jira or Confluence. Neither script accepts a
credential as an argument.

## 1. Salesforce scope

Scope is derived from the **Network Service profile's object permissions**, not a
hand-maintained list. That makes the inventory reproducible and defensible: the
answer to "why is this object in scope" is always "the pod's profile can read it".

```bash
sf org login web --alias ns-sandbox
python3 discover_scope.py --org ns-sandbox --profile "Network Service"
```

Options:

| Flag | Default | Purpose |
|---|---|---|
| `--org` | required | sf CLI alias or username |
| `--profile` | `Network Service` | profile whose access defines the scope |
| `--record-type-pattern` | `network` | case-insensitive regex for pod record types |

Writes `out/*.json` plus `out/summary.json`, which carries the node and edge
estimate for the Salesforce half of the graph.

### What it collects

| File | Source | Notes |
|---|---|---|
| `objects.json` | `ObjectPermissions` | readable set, with create/edit flags |
| `fields.json` | `FieldPermissions` | queried in batches of 20 objects |
| `record_types.json` | `RecordType` | filtered to the pod pattern |
| `triggers.json` | `ApexTrigger` (Tooling) | filtered by `TableEnumOrId` |
| `flows.json` | `FlowDefinitionView` | active only |
| `validation_rules.json` | `ValidationRule` (Tooling) | filtered by entity |
| `apex_classes.json` | `ApexClass` (Tooling) | unmanaged only |
| `dependencies.json` | `MetadataComponentDependency` | one query per object |

`MetadataComponentDependency` is Tooling-API only and caps out around 2000 rows
per query, which is why dependencies are pulled per object rather than in one go.

## 2. Atlassian access

Answers whether a single API token reaches both products.

```bash
export ATLASSIAN_SITE=your-site          # the part before .atlassian.net
export ATLASSIAN_EMAIL=svc-ai@example.com
export ATLASSIAN_TOKEN=...               # id.atlassian.com > Security > API tokens

python3 check_atlassian.py --project-key NSVC --space-key NSDOCS
```

A single token authenticates to both Jira and Confluence **only if** all three hold:

1. Both products are Atlassian **Cloud** on the same `*.atlassian.net` site.
2. The account holds a **Confluence licence**, not just Jira.
3. The account has **space permissions** on the pod's Confluence spaces.

Atlassian **Data Center / Server** is a different story: separate applications,
separate base URLs, separate personal access tokens. Two sets of credentials.

## 3. Handing results back

Share `out/summary.json` and the console output of the Atlassian check. Neither
contains credentials. `summary.json` contains object and component **names**, not
record data, so review it against the client's confidentiality terms before it
leaves the sandbox environment.
