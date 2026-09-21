# Patient and Provider Gap Intelligence: Solution Design

**Programme:** Solution 2 on the production knowledge graph
**Built on:** the Neo4j / TopQuadrant / GraphRAG / Agentforce estate described in the Insight Global case study one pager
**Status:** Feasibility investigation and layered design, for review
**Date:** 21 September 2026
**Source inputs:** `Insight_Global_Case_Study_OnePager_1.pptx` (Solution 1, seller agents grounded in a production knowledge graph), and the request to analyse patient and provider data, find the gaps between them, rank by highest patient inflow against lowest provider outcome, and drive a campaign from the result.

---

## 0. The question that was asked

> Analyse patient data and provider data, identify the gaps between them, find where patient inflow is highest and provider outcomes are lowest, and use that to run a campaign. Can we do it on the same knowledge graph model we are already using?

Short answer: **yes**, and the graph is the right shape for it rather than a workaround. Three conditions attach, and they are in section 1.

Two design principles govern everything below. They are the same two that govern the Provider Dues design in this repo, restated for a graph.

> **P1: The ontology is the source of truth.** Sources land unchanged at L0 and acquire meaning at L2. A corrected claims extract or a re-run roster replays through the graph rather than rewriting it.

> **P2: Every score is reachable by traversal.** A score stored as a flat attribute on a row is a report. A score reachable by traversal is an answer. This is exactly what the BDR and SDR signal migration proved in Solution 1, and it is the rule that makes agent latency budgets achievable here.

---

## 1. Feasibility verdict

### 1.1 Why the model transfers

The Solution 1 graph is an entity-relationship-signal graph with a retrieval layer on top. The domain classes change; the machinery does not.

| Solution 1 (sales) | Solution 2 (care delivery) |
|---|---|
| Account | Patient, and Population as the aggregate |
| Opportunity | Encounter, and Episode as the aggregate |
| Product | ServiceLine, and Procedure as the leaf |
| BDR and SDR scores promoted to traversals | Risk score, risk adjusted outcome index, capacity index, leakage index, promoted the same way |
| Conversation transcripts bridged from Data Cloud | Referral notes, clinical notes and call transcripts bridged the same way |
| Account POV agent | Market POV agent, Provider POV agent, Campaign planner agent |
| LLM as a judge gold set | The same harness, plus campaign lift measurement |

Unchanged: Neo4j and its index design, TopQuadrant and SHACL, SageMaker, Snowflake, Data Cloud, the MCP tool surface into Agentforce and Slack, and the evidence gated delivery model.

### 1.2 The three conditions

1. **Outcomes are not comparable until they are risk adjusted.** Ranking raw outcomes punishes the providers who take the sickest patients. The first clinician who reads such a list will say so, correctly, and the finding is dead. Risk adjustment, minimum denominators, shrinkage and confidence intervals belong in the build, not in a later refinement pass. This is the single largest difference from Solution 1, where a mis-scored account costs a wasted call and here it costs credibility.

2. **Activation needs a gate the seller build never had.** Consent state, channel permission, suppression and a minimum necessary check sit between the gap list and any send, with a named human approving each cohort. PHI does not enter a model prompt unless the endpoint is covered by a BAA.

3. **Identity resolution is the ceiling on every number.** A 92 percent provider match rate means up to 8 percent of what looks like a gap is a join failure. Match rate is published next to every gap, every time, or the gap list is not trustworthy.

### 1.3 What this is not

It does not make clinical decisions, and it does not publish a league table of individual clinicians. It ranks addressable gaps and names who can close them.

---

## 2. What a gap actually is

Six computable gaps, each with a defined trigger. The first five are business gaps; the sixth is the one Solution 1 already taught us to look for first.

| # | Gap | Definition | Triggers |
|---|---|---|---|
| 1 | Access | Demand against contracted, bookable capacity by geography and service line | Provider recruitment and contracting |
| 2 | Outcome | Risk adjusted outcome index against a like for like peer benchmark | Quality improvement campaign |
| 3 | Leakage | Attributed patients treated outside the network, traced along referral paths | In network capture campaign |
| 4 | Care | Open quality measures per patient: screening, chronic follow up, adherence | Patient outreach cohort |
| 5 | Adequacy | Time, distance and appointment wait standards by county and specialty | Network filing and expansion |
| 6 | Link | Entities that exist in the sources but are not related in the ontology | The graph backlog itself |

Gap 6 matters because an unlinked entity is indistinguishable from a business gap until someone checks. The case study challenge column named exactly this failure (Product, Account and Opportunity not formally linked in the ontology), so the design assumes it rather than discovering it.

### 2.1 The quadrant

The business question decomposes into four computable ones:

- **Q1 Demand.** Where do patients actually come from, by geography and service line, and is that volume growing?
- **Q2 Supply.** Who is contracted to serve them, with what bookable capacity and what panel status?
- **Q3 Performance.** How good is the outcome once adjusted for how sick the patients were?
- **Q4 Addressability.** Which gaps can an outreach actually move, and who is reachable and consented?

Plot the result on inflow (x) against risk adjusted outcome (y):

| | Low inflow | High inflow |
|---|---|---|
| **Strong outcome** | GROW: steer volume here | PROTECT: retain, contract, expand |
| **Weak outcome** | WATCH: monitor, small denominators | **PRIORITY: the campaign cohort** |

PRIORITY is the answer to the question as asked. GROW is where the steered volume goes. Both fall out of one query.

---

## 3. Architecture: eight layers

| Layer | Purpose | Stack |
|---|---|---|
| **L0** Source and ingestion | Land every system of record without changing what it means | Snowflake, Data Cloud, S3 |
| **L1** Identity resolution | One patient, one provider, one place, with evidence kept | EMPI, NPI and TIN, CCN, geocode |
| **L2** Ontology and graph | Make the relationship a first class object, validated on load | TopQuadrant, SHACL, Neo4j |
| **L3** Signal | Promote computed scores to native traversals under a latency SLA | SageMaker, graph projections |
| **L4** Gap analytics | Turn the graph into a ranked, defensible, lineage backed gap list | Neo4j GDS, Snowflake |
| **L5** GraphRAG and agents | Answer in natural language, grounded, with node level citations | GraphRAG, Agentforce, MCP |
| **L6** Campaign activation | Turn a gap into a governed outreach with a holdout | Health Cloud, Marketing Cloud |
| **L7** Evaluation and governance | Prove it is right, keep it legal, measure what it moved | LLM judge, holdouts, audit |

L0 to L3 are graph construction. L4 is the answer. L5 to L7 make it usable, governed and measurable.

---

## L0. Source and ingestion

| Source | Contributes | Grain | Latency |
|---|---|---|---|
| Claims, 837 and 835 | Utilisation, cost, outcome proxies, out of network activity | Claim line | Monthly, 30 to 90 day lag |
| EHR and FHIR, US Core | Diagnoses, procedures, labs, vitals, referrals | Encounter | Daily |
| Eligibility and attribution | Who is in the population and which provider owns them | Member month | Monthly |
| Provider directory, NPPES, CAQH, roster | Identity, specialty, location, contract status | Provider | Weekly |
| Scheduling and access | Bookable supply, wait time, panel open or closed | Slot | Daily |
| CRM and Health Cloud | Relationship, contacts, prior outreach, consent state | Account and contact | Near real time |
| Unstructured | Referral notes, clinical notes, call transcripts | Document | Streaming |
| Reference and geo | SNOMED, ICD-10, CPT, NUCC, census, drive time | Dimension | Quarterly |

Nothing acquires meaning here (P1). The unstructured feed reuses the Data Cloud bridge built in Solution 1, pointed at clinical and referral content instead of sales conversations.

---

## L1. Identity resolution

**Patient.** Deterministic first: source MRN, member id, and a composite of name, date of birth and last four of SSN. Probabilistic fallback on name, date of birth, address and phone, with a scored threshold and a manual review band between the auto-accept and auto-reject floors. Survivorship rules decide which attribute wins when sources disagree, and the losing value is retained. Cross source links are stored as evidence edges, not silent merges, so a bad link is reversible.

**Provider and place.** Individual NPI is the person key, TIN plus NPI the practice key, CCN the facility key. Individual and organisational NPIs are never collapsed into one node. NUCC taxonomy supplies specialty. Address geocodes to census tract for drive time and adequacy work. Affiliation is time bounded, so a provider who left a practice in March does not distort the year.

**Published with every gap:** patient match rate, provider match rate, and the share of encounters that failed to resolve. See section 9, risk 5.

---

## L2. Ontology and graph model

Core triples, governed in TopQuadrant and enforced by SHACL on load. An unlinked entity fails the load rather than quietly becoming a gap.

```
(Patient)   -[:RESIDES_IN]->       (Geography)
(Patient)   -[:HAD_ENCOUNTER]->    (Encounter)
(Patient)   -[:ATTRIBUTED_TO]->    (Provider)        // time bounded
(Patient)   -[:HAS_OPEN_MEASURE]-> (Measure)
(Encounter) -[:PERFORMED_BY]->     (Provider)
(Encounter) -[:AT_FACILITY]->      (Facility)
(Encounter) -[:FOR_CONDITION]->    (Condition)
(Condition) -[:MAPS_TO]->          (ServiceLine)
(Provider)  -[:AFFILIATED_WITH]->  (Practice)        // time bounded
(Provider)  -[:HAS_TAXONOMY]->     (Specialty)
(Provider)  -[:REFERRED_TO]->      (Provider)
(Provider)  -[:SCORED_ON]->        (OutcomeIndex)    // dated, versioned
(Cohort)    -[:TARGETS]->          (Provider|Patient)
(Campaign)  -[:SENT]->             (Touch)
(Touch)     -[:RESULTED_IN]->      (Response)
```

Three rules the ontology enforces:

- **R1** Every score is reachable by traversal (P2).
- **R2** Every edge that can change over time carries validity dates. Affiliation, attribution and contract status all move, and a gap computed across a move is a false gap.
- **R3** Every derived node carries lineage back to the source rows that produced it, or it cannot be published.

**Scale.** The production estate already runs 511,000 plus nodes and 894,000 plus relationships with a scaled index design. The care delivery subgraph is additive to that estate rather than a second graph. Index design is reviewed at M1 against the traversal patterns L4 actually issues, not against the model on paper.

---

## L3. Signal

| Signal | Meaning | Method | Refresh | SLA |
|---|---|---|---|---|
| Patient risk score | Expected acuity and utilisation for the next period | HCC or CDPS, or an internal model on SageMaker | Monthly | 50ms |
| Risk adjusted outcome index (RAOI) | Observed over expected for a provider and service line | O/E with hierarchical shrinkage | Monthly | 50ms |
| Inflow index | Patient volume by geography and service line, trended | Graph aggregation and projection | Weekly | 50ms |
| Capacity index | Bookable supply against modelled demand | Scheduling feed plus panel status | Daily | 50ms |
| Leakage index | Share of attributed patients treated out of network | Bounded path query on referral edges | Monthly | 50ms |
| Contactability state | Reachable or not, and on which permitted channel | CRM plus consent store | Real time | 50ms |

Three properties of this layer:

- **Written where it is read.** Indices land on the Provider, Patient and Geography nodes, so retrieval needs no second system.
- **Versioned, never overwritten.** Each refresh writes a dated index, so last quarter's gap list reproduces exactly.
- **Confidence travels with the value.** Every index carries n, its interval and its peer group. L4 refuses to rank without them.

The 50ms traversal budget is inherited from Solution 1 and is what makes an agent reply feel instant rather than batched.

---

## L4. Gap analytics

### 4.1 The computation chain

1. **Demand.** Inflow index by geography and service line, trended over the attribution window.
2. **Supply.** Capacity index across contracted providers in the same geography and service line.
3. **Performance.** RAOI against the matched peer benchmark.
4. **Gap score.** A weighted function of demand, supply deficit, outcome deficit and addressability. Weights are configuration, not code, and are versioned per service line.
5. **Quadrant.** Rank, place on the inflow against outcome plane, attach the evidence.

### 4.2 Statistical guardrails

These are what make the list survive its first review:

- **Minimum denominator.** No provider is ranked below the agreed encounter count for that service line.
- **Shrinkage.** Small volume providers are pulled toward the peer mean by empirical Bayes before ranking.
- **Confidence intervals.** Published with every index. Overlapping intervals are reported as not different, in those words.
- **Peer groups.** Defined by specialty, care setting and case mix, never by geography alone.
- **Attribution.** One rule per service line, agreed before build, versioned, and stated on every answer.
- **Lineage.** Every gap resolves back to the source rows that produced it, or it is not published.

A gap that cannot be defended in front of the provider it names is not a gap, it is a complaint.

---

## L5. GraphRAG and agents

**Retrieval pipeline:** question, entity anchor, subgraph expansion, signal read, rerank and assemble, grounded answer. County, specialty and provider names resolve to graph identifiers first; expansion runs along typed edges within a bounded hop budget; indices are read from the nodes they already sit on; evidence is assembled before the model writes a word.

**Agents:**

| Agent | Question it takes | What it returns |
|---|---|---|
| Market POV | "Where is our biggest access gap this quarter?" | County, service line, gap score and the practices behind it, each traceable to its evidence |
| Provider POV | "Why is this practice flagged?" | The O/E, the peer group, the interval, the volume and the encounters that produced it |
| Campaign planner | "Build me the cohort." | Cohort definition, projected reach and the approvals required. It drafts. It does not send. |

**Guardrails:** no PHI in a prompt unless the endpoint is covered by a BAA; de-identified aggregates by default; every claim cites the nodes it came from; a refusal path when evidence falls below threshold; full prompt and response audit retained.

---

## L6. Campaign activation

| Step | What happens | Output |
|---|---|---|
| 1 Cohort build | Drawn from the quadrant and the gap score, with the target metric named up front | Cohort definition |
| 2 Consent gate | Opt in state, channel permission, suppression list, minimum necessary check | Eligible list |
| 3 Human review | Clinical and compliance approval, versioned, approver recorded | Approval record |
| 4 Channel routing | Provider: field task, contracting outreach, quality packet. Patient: SMS, email, call list, care manager | Channel plan |
| 5 Holdout and send | Randomised control held back at cohort build, ten percent by default | Test and control |
| 6 Write back | Campaign, Touch and Response land on the graph | Graph nodes |

Steps 2 and 3 are the gate. Nothing reaches a channel without passing both, and the agent layer can draft a cohort but cannot open the gate.

Two rules:

- **The holdout is defined before the send**, or the lift number is a story rather than a measurement.
- **The write back closes the loop.** Campaign, Touch and Response become graph nodes, so the next cycle's targeting trains on what actually worked rather than on what was planned.

---

## L7. Evaluation and governance

**Is the answer right?** Gold set of 100 plus SME labelled questions, the method carried straight from Solution 1. LLM as a judge scoring with a human spot audit on a fixed sample. Clinical SME review of flagged providers before any gap is published. Match rate and coverage dashboards, read before the gap list is read. Before and after agent accuracy on the same gold set.

**Did the campaign move anything?** Holdout lift on one primary metric named at cohort build. Guardrail metrics alongside it: opt out rate, complaint rate, provider abrasion. Attribution window fixed in advance and not adjusted once the result is known. A scorecard per cohort, kept whether the result was good or bad.

**Is it legal and audited?** HIPAA minimum necessary enforced at the query layer rather than by convention. Role based access to subgraphs. De-identification for analytic use, re-identification only through a controlled path. Lineage from every published gap back to source rows. Retention and purge aligned to policy, and every agent prompt and response retained for audit.

The evaluation framework is the reusable asset. Solution 1 built it for seller agents, Solution 2 inherits it and adds campaign lift, and Solution 3 will inherit both.

---

## 8. Worked example

Illustrative. The shape is real, the figures are placeholders until the source inventory at M0.

| Layer | What happens |
|---|---|
| L0, L1 | 128,000 attributed patients and 41 contracted cardiologists in the county resolve at 96 percent patient match and 94 percent provider match. Both rates are published with the result. |
| L2 | Patients, encounters, providers, practices, facilities and the cardiology service line are linked and SHACL validated. Twelve practices and seven facilities carry the volume. |
| L3 | Inflow index for the county sits in the top decile. RAOI is 1.18 observed over expected, and the interval excludes 1.0, so the difference is real. |
| L4 | Supply deficit is seven full time equivalents. Leakage is 23 percent of referrals leaving the network. The county lands in PRIORITY and ranks first on gap score. |
| L5 | The Market POV agent answers the quarterly question with the county, the twelve practices, the interval and a link back to the encounters behind every number. |
| L6 | Two cohorts leave the gate: twelve practices for contracting and quality outreach, and 4,100 patients with open measures, ten percent held back as control. |
| L7 | Lift measured against the holdout at ninety days. SME sign off recorded before send. The whole chain replays from the source rows on request. |

---

## 9. What would make this wrong

| # | Risk | What stops it |
|---|---|---|
| 1 | Confounding: outcome differences that are really case mix differences | Risk adjustment, matched peer groups, published intervals |
| 2 | Small denominators: a provider with two patients looks catastrophic or perfect | Minimum volume floor plus empirical Bayes shrinkage |
| 3 | Data lag: claims run 30 to 90 days behind, so a gap may already be closed | Dated indices, and the lag stated on every answer |
| 4 | Attribution disputes: two parties both claim, or both disclaim, the same patient | One versioned rule per service line, agreed before build |
| 5 | Identity failure that looks exactly like a business gap | Match rate published next to every gap, every time |
| 6 | Provider abrasion and the legal exposure of naming clinicians | Internal only ranking, review gate, no public league table |
| 7 | PHI reaching a model endpoint or an unapproved channel | BAA covered endpoints, de-identified by default, consent gate |
| 8 | Campaign fatigue: the same cohort contacted by three teams in one month | Suppression list and contact frequency caps held in the graph |

Each of these is a design decision taken before build, not a caveat added after the first review.

---

## 10. Delivery plan

Four months, five evidence gates, the same milestone gated shape that de-risked the first engagement.

| Milestone | Weeks | Scope | Gate |
|---|---|---|---|
| **M0** Foundation | 1 to 3 | Source inventory, attribution and peer group rules agreed, ontology draft, identity baseline | Match rate at or above the agreed floor, attribution rule signed |
| **M1** Graph and signals | 4 to 7 | Ontology loaded with SHACL, care subgraph at production scale, indices as traversals | Index parity with the analytics team's own numbers, inside tolerance |
| **M2** Gap engines | 8 to 11 | Six gap engines, the quadrant, statistical guardrails, lineage | Clinical SME review of a flagged sample, shrinkage and intervals validated |
| **M3** Agents and eval | 12 to 14 | GraphRAG retrieval, three agents in Agentforce and Slack via MCP, gold set baseline | Accuracy at or above the agreed baseline on the gold set |
| **M4** Activation | 15 to 17 | Cohort builder, consent gate, holdout design, write back, first campaign in flight | Holdout defined pre send, compliance sign off, scorecard live |

A gate that cannot be evidenced moves the date rather than the standard.

---

## 11. Open questions for week one

1. Who owns the attribution rule, and by when?
2. Risk model: buy the standard grouper or build internally?
3. Which model endpoints are BAA covered today?
4. Which system is the consent store of record?
5. Who signs off a cohort before it is sent?
6. What is the policy on naming individual clinicians internally?
7. Which market or region is the pilot, and which service lines are in scope for M0?
8. Does the scheduling feed expose bookable supply, or only booked appointments? The capacity index degrades to a proxy if it is the latter.

---

## 12. Artefacts in this repo

| File | What it is |
|---|---|
| `docs/patient-provider-gap-intelligence-design.md` | This document |
| `docs/patient-provider-gap-intelligence.pptx` | The layered solution deck, 18 slides, Insight Global case study styling |
| `scripts/build-gap-intelligence-deck.js` | Generator for the deck, so it rebuilds from source rather than being hand edited |

Rebuild the deck with `node scripts/build-gap-intelligence-deck.js docs/patient-provider-gap-intelligence.pptx` (requires `pptxgenjs`).
