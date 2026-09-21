# Clinical Network Knowledge Graph: concept note

**Idea:** one knowledge graph over providers, facilities, service lines, credentials, geography and patient demand, so that the mismatches between them become computable instead of anecdotal.

**Status:** concept for discussion. Not a solution design.
**Deck:** `docs/clinical-network-graph-concept.pptx` (3 slides: architecture, scenario catalogue, feasibility).

---

## Why this is a graph problem

A gap is a missing path, not a missing row.

- **Demand path:** patient to geography to condition to service line.
- **Supply path:** facility offers service line, staffed by a credentialed provider holding the required specialty, reachable inside a drive time band.
- **A gap** is where the demand path exists and the supply path does not. The shape of the break says which gap it is.

A star schema answers "how many cardiologists are in this county". It cannot answer "which counties have demand for a service line whose required specialty has no privileged provider within thirty minutes, and which three existing providers could cover it with one added session". That is variable depth traversal across seven entity types where the answer is an absent edge.

**The modelling decision that makes it work:** `(ServiceLine)-[:REQUIRES]->(Specialty | Capability)`. Once a service line declares what it needs, every facility, every credential and every patient flow can be tested against it automatically. Most provider data models never encode this, which is why gap analysis stays manual.

---

## The scenario catalogue

### A. Supply and demand mismatch

| # | Scenario | In the graph | Action |
|---|---|---|---|
| 1 | Demand without supply | Geography has inflow for a service line and no credentialed provider inside the drive time band | Recruit, locum, telehealth or a transfer agreement |
| 2 | Supply without demand | Sessions and slots exist, encounter volume in the bottom decile for the peer group | Redeploy sessions, re-market, resize the template |
| 3 | Capability and credential mismatch | The site holds the asset (cath lab, MRI, labour and delivery) with nobody privileged to use it, or the reverse | Privilege, credential, or move the asset |

### B. Network completeness

| # | Scenario | In the graph | Action |
|---|---|---|---|
| 4 | Incomplete service line | The line requires N specialties and the site has N minus one, so care finishes elsewhere | Close the one gap that unlocks the whole line |
| 5 | Single point of failure | One provider is the only path to a service line in a county | Succession and cross cover, with blast radius quantified |
| 6 | Volume below threshold | Complex procedures performed under the safe volume floor | Consolidate or refer, with the quality risk named |

### C. Patient flow

| # | Scenario | In the graph | Action |
|---|---|---|---|
| 7 | Referral leakage | Attributed patients treated out of network, traced along referral edges | Recapture campaign that fixes the reason, not the symptom |
| 8 | Bypass and travel burden | Patients repeatedly drive past a nearer site to reach a farther one | Isolates reputation against capability against access |
| 9 | Referral chain depth | Four hops to definitive care, every hop measurable in days | Shorten the path, open a direct access pathway |

### D. Access, quality and growth

| # | Scenario | In the graph | Action |
|---|---|---|---|
| 10 | Adequacy and access deserts | CMS time and distance failures by county and specialty | Filing evidence, and the fewest hires that fix the most counties (set cover) |
| 11 | Inflow high, outcome weak | Top decile volume with risk adjusted O over E above the peer benchmark | Quality campaign, and steer volume to the strong sites |
| 12 | Hire and site simulation | Insert a hypothetical provider or site, re-run every traversal, diff the result | Patients gaining access and leakage recaptured, before spending |

Every scenario is the same query shape and returns the same four things: the evidence path, the patients affected, the recommended action, and a cohort ready to activate.

---

## The eight layers

| Layer | Purpose |
|---|---|
| L1 Source systems | EHR, credentialing, provider directory, scheduling, claims, referrals, geography |
| L2 Source connectors | Read only, PHI safe at the boundary, hashed and replayable |
| L3 Ingestors and identity | EMPI for patients, NPI, TIN and CCN for providers and places, with provenance |
| L4 Domain model | CareNetworkContext: providers, facilities, service lines, demand, access, flows |
| L5 Graph storage | Vendor neutral JSON snapshot, versioned, de-identified by default |
| L6 Derived edge engine | SERVES, REQUIRES, COVERS, SUBSTITUTE_FOR, plus the dated indices |
| L7 Network ContextGraph | Traversals, network analytics, what-if simulation |
| L8 Gap engines and API | The twelve scenarios, the query surface, the output contract |

---

## The five hard problems

1. **Identity resolution is the ceiling on every number.** Roster, claims and NPPES disagree about who works where. Individual and organisational NPIs must never collapse into one node.
2. **Privileging data is usually the weakest source,** often a separate and stale system. Scenario 3 depends on it entirely.
3. **Bookable against booked supply.** If scheduling exposes only booked appointments, the capacity index degrades to a proxy and "no slots" cannot be separated from "bad template".
4. **Attribution.** Whose patient is it. One versioned rule per service line, agreed before build.
5. **PHI governance.** Three identities: de-identified analytic graph, limited data set under BAA for outreach, identified access role gated at the query layer.

None are blockers. All five are decisions to take in week one rather than discoveries to make in month three.

---

## Ninety day proof

| Weeks | Scope |
|---|---|
| 1 to 3 | One market, two service lines. Source inventory, attribution rule, required specialty map agreed |
| 4 to 7 | Identity resolution and the graph loaded. Match rate published as the first deliverable |
| 8 to 11 | Two gap engines live (scenarios 1 and 3), reviewed by a clinical SME |
| 12 to 13 | One what-if simulation, and a gap list that a clinical leader and a network leader both sign |

Rebuild the deck with `node scripts/build-clinical-network-deck.js docs/clinical-network-graph-concept.pptx` (requires `pptxgenjs`).
