# Universal Gap Intelligence Framework: does the pattern travel?

**Question asked:** we have built two knowledge graphs, one for engineering delivery and one for providers and patients. Is this a universal solution, independent of industry and of technology?

**Deck:** `docs/universal-gap-framework.pptx` (3 slides: core and pack, the four industry mapping, fit and limits).

**Short answer:** the pattern travels, the claim needs bounding. Roughly seven parts in ten never change. What changes is a five part declaration. It does not fit everything, and the places it does not are predictable in advance, which is more useful than a yes.

---

## 1. What is actually universal

Strip the domain out of both graphs we have built and the same sentence is left:

> **A gap is a missing path between demand and a supply that satisfies a declared capability, reachable inside a constraint.**

That sentence contains no industry. Ten abstract primitives carry it:

| # | Primitive | Role |
|---|---|---|
| 1 | **Party** | The demand side. Who wants something |
| 2 | **Resource** | The supply side. Who or what can serve it |
| 3 | **Capability** | What the resource is actually able and permitted to do |
| 4 | **Offering** | The thing demanded, which **declares what it requires** |
| 5 | **Place and reachability** | Where, and the metric that decides whether supply is reachable |
| 6 | **Interaction** | The event where demand meets supply |
| 7 | **Commitment** | The booking, order or subscription, with a lifecycle and exits |
| 8 | **Flow** | Movement between suppliers, and therefore leakage |
| 9 | **Signal** | A computed index attached to a node |
| 10 | **Evidence** | Provenance on every assertion |

Primitive 4 is the load bearing one. Once an offering declares what it requires, gap detection is constraint satisfaction rather than a library of hand written queries, and that is what makes the engine domain neutral.

---

## 2. The mapping, worked rather than asserted

| Abstract | Healthcare | Telecom | Automotive | Engineering delivery |
|---|---|---|---|---|
| Party | Patient | Subscriber | Owner or buyer | Requirement or request |
| Resource | Provider, facility | Cell site, sector, field engineer | Dealer, bay, technician | Component, service, team |
| Capability | Specialty plus privilege | Band, capacity, backhaul | Brand and EV certification, diagnostic rig | Language, framework, API |
| Offering | Service line | Plan or product, such as fixed wireless | Sale, warranty repair, EV service | Feature or change |
| Place, reachability | County, drive time | Coverage polygon, signal strength | Territory, drive time | Repo and domain boundary |
| Interaction | Encounter | Session, care call, truck roll | Service visit, test drive | Deployment, incident |
| Commitment | Appointment | Subscription | Order, service booking | Work item |
| Flow | Referral out of network | Port out to a competitor | Defection to independents | Dependency across teams |
| Adequacy rule | CMS time and distance | Regulator coverage obligation | OEM network standard | Architecture standard or SLA |
| Identity spine | NPI, TIN, CCN, EMPI | MSISDN, IMSI, account | VIN, dealer code | Repo and service id |

### The scenarios survive the translation

**Scenario 1, demand without supply.** A county with inflow and no credentialed cardiologist inside the drive time band. A postcode with demand and no site carrying the required band. A territory with a growing electric parc and no high voltage certified technician. A requirement with no component that implements it.

**Scenario 3, capability and credential mismatch.** A cath lab with nobody privileged to use it. A 5G radio with no fibre backhaul behind it. A dealer holding the EV diagnostic rig with no certified technician. All three are the same query, and all three are expensive assets earning nothing.

**Scenario 10, adequacy.** CMS time and distance standards in healthcare are structurally identical to regulator coverage obligations in telecom and to OEM network standards in automotive. Same traversal, same set cover problem when you ask which additions fix the most territories.

**The appointment pack** transfers with no modification: healthcare appointments, telecom installation and truck roll slots, automotive service bookings. No-show prediction becomes churn prediction in telecom and defection prediction in automotive, all with the same target shape and the same output contract.

---

## 3. Core against pack

| Layer | Core or pack | What varies |
|---|---|---|
| L1 Source systems | Pack | Whatever the systems of record are, in any vendor |
| L2 Source connectors | Pack | One connector per system. The contract itself is core |
| L3 Trust and privacy boundary | Both | Mechanics are core. HIPAA, GDPR or PCI is the pack |
| L4 Ingest and identity | Both | Resolution machinery is core. The identity spine is the pack |
| L5 Domain model | Pack | The classes change. Bitemporal and evidence rules do not |
| L6 Graph storage | Core | Content addressed, immutable, vendor neutral |
| L7 Derived edge engine | Both | The engine is core. Reachability and thresholds are the pack |
| L8 Graph runtime | Core | Traversal, vectors, shadow graph, analytics |
| L9 Gap engines and API | Core | The scenarios are already domain neutral |

**A new industry declares five things:** ontology classes and identity spine, the reachability metric, the capability specification, the regulatory profile, and the connectors plus action catalogue. Nothing else moves.

We have already built two packs without calling them packs. The engineering delivery graph and the clinical network graph share all nine layers and differ only in those five declarations.

---

## 4. Where it weakens

Being specific about this is worth more than a universal claim.

| Limit | Why |
|---|---|
| **Elastic supply** | If capacity appears on demand, the gap closes itself. Commodity cloud does not need this. Credentialed, licensed or capital bound supply does. This is the decisive test |
| **No reachability constraint** | A purely digital good delivered instantly everywhere loses the strongest gap type. Latency, language or jurisdiction can stand in, but the edge is weaker |
| **The specification cannot be written** | Capability algebra needs someone to state what an offering requires. When nobody can, that is a business knowledge problem, and it is usually the hardest workshop in the engagement |
| **No identity spine** | Anonymous consumer markets still support geography level aggregates, but person level flow and leakage are lost |
| **Small scale** | Twelve suppliers and three sites is a spreadsheet. The graph earns its keep on heterogeneity and volume |

### The six question fit test

1. Can demand be located, by geography, segment or jurisdiction?
2. **Is supply lumpy, licensed or slow to add?** This one carries the most weight.
3. Can someone write down what an offering requires?
4. Is there an identity spine on both sides?
5. Does value flow between suppliers, and can it leak?
6. Is there a commitment with a lifecycle and exits?

Four or more yes is a strong fit. Healthcare, telecom, automotive aftersales, field service, energy networks, logistics and utilities all score five or six. Commodity software and pure digital distribution score two or three, and should be declined rather than forced.

---

## 5. Technology independence, honestly

**Swappable without redesign**, because the layering isolates them:

- CRM: Salesforce, Dynamics, ServiceNow, SAP. It is a connector.
- System of record: Epic, Cerner, Amdocs, a dealer management system.
- Graph store: Neo4j, TigerGraph, Neptune, Memgraph.
- Cloud and model endpoints, behind the same contract.

**Genuinely coupled**, so decide early:

- **Graph engine class.** Variable depth traversal and path queries are native in a property graph and hand rolled in SQL, where they hurt beyond about three hops. Any technology, yes. Any technology equally well, no.
- **The identity spine.** Per industry, and not equal in quality. A VIN is a better key than anything healthcare has, which makes automotive resolution materially cheaper than clinical resolution.
- **The regulatory regime.** HIPAA, GDPR and ePrivacy, or right to repair. The privacy boundary layer stays in place; the rules inside it are a pack concern. Telecom location data under GDPR is at least as sensitive as PHI.

---

## 6. The commercial shape

Build the core once, sell the pack per industry. A new market is a five part declaration plus a set of connectors, not a new build. That is what turns a delivered project into a repeatable practice, and it is the reason to spend the extra effort now on keeping L6 to L9 free of any domain vocabulary.

Rebuild the deck with `node scripts/build-universal-deck.js docs/universal-gap-framework.pptx` (requires `pptxgenjs`, and `scripts/trenda-widths.json` for text measurement).

---

## 7. The combined deck, and the questions that follow it

`docs/universal-gap-framework-combined.pptx` is the presentation order: the three universal slides, a transition, the two worked architectures, and a closing slide on platform and technology.

| # | Slide |
|---|---|
| 1 | Core and pack: what stays the same, what every industry declares |
| 2 | The same model, four industries |
| 3 | Fit, limits and technology |
| 4 | **Transition:** one framework, two solutions, for reference |
| 5 | Sample architecture: engineering delivery |
| 6 | Sample architecture: clinical network |
| 7 | **Platform:** where it runs, what it is written in, which model |

### Slide 7, in text

**Where does it run?** Any cloud or none: AWS, Azure, GCP, private cloud or on premise. Packaged as containers, so it lands in whatever is already operated. Batch on a schedule rebuilds the graph, an API service answers queries. No managed service is assumed anywhere in the design. *If it runs Python and containers, it runs this.*

**Where does the data live?** Object storage (S3, Azure Blob, Google Cloud Storage), graph store (Neo4j, TigerGraph, Neptune, Memgraph), warehouse (Snowflake, BigQuery, Databricks, Synapse), or Postgres where the graph is small enough to sit there. *The snapshot is vendor neutral JSON, so the store is a swap, not a rewrite.*

**What is it written in?** Python is the core: ingestion, identity resolution, derived edges and the gap engines. Standard libraries and open packages, no proprietary runtime. Orchestrated by whatever is already running, from Airflow to cron. Configuration is data, so ontology shapes, specifications and thresholds are files rather than code. *A new industry ships as configuration and connectors, not a new codebase.*

**Which AI model?** Claude, Gemini, GPT and Codex, or an open weights model, behind one adapter. The model turns a question into a traversal and evidence into a sentence. It does not decide the answer: the traversal computes it and the citation proves it. Model choice can differ per environment and per sensitivity rule. *Swap the model and the answers do not change. That is the test.*

### Three things required of any choice

1. **A store that can traverse**, or every hop is paid for in hand written SQL.
2. **An endpoint under the right agreement** where regulated data is in play, or the model sees aggregates only.
3. **Reproducibility from a snapshot id**, so any answer replays at a date whatever the stack underneath.

The framework is open by construction. Every vendor named is an example, not a dependency.

Rebuild the combined deck with `python3 scripts/extend_combined_deck.py <merged-source.pptx> docs/universal-gap-framework-combined.pptx`. It fills the transition slide and appends the platform slide, leaving the two architecture posters untouched.
