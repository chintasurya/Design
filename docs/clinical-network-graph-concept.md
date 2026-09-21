# Clinical Network Knowledge Graph: concept note

**Idea:** one knowledge graph over providers, facilities, service lines, credentials, geography and patient demand, so that the mismatches between them become computable instead of anecdotal.

**Status:** concept for discussion. Not a solution design.
**Deck:** `docs/clinical-network-graph-concept.pptx` (5 slides: nine layer architecture, scenario catalogue, appointments and extensibility, graph model, feasibility).
**Type:** Trenda IG Display and Trenda IG Text. The font files live at `deck/fonts/` on branch `claude/peaceful-mendel-76r18m`; they must be installed locally for the deck to render as designed.

---

## Why this is a graph problem

A gap is a missing path, not a missing row.

- **Demand path:** patient to geography to condition to service line.
- **Supply path:** facility offers service line, staffed by a credentialed provider holding the required specialty, reachable inside a drive time band.
- **A gap** is where the demand path exists and the supply path does not. The shape of the break says which gap it is.

A star schema answers "how many cardiologists are in this county". It cannot answer "which counties have demand for a service line whose required specialty has no privileged provider within thirty minutes, and which three existing providers could cover it with one added session". That is variable depth traversal across nine entity types where the answer is an absent edge.

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

### E. Appointments, added by the feature pack below

| # | Scenario | In the graph | Action |
|---|---|---|---|
| 13 | Idle slot recovery | Late cancellations whose slots never refill | Backfill from the waitlist, shorten the recovery window |
| 14 | Chronic no-show with open care gaps | Repeated non-attendance on a patient who also has overdue measures | Support outreach, never a downgraded slot |
| 15 | Clinic-initiated cancellation | The clinic is the cancelling party, through provider absence or template churn | Fix the template, and stop counting it against the patient |
| 16 | Lead time feedback loop | Long waits push bookings further out, longer lead times raise no-shows, no-shows lengthen waits | Break the loop at the template, not at the patient |
| 17 | Waitlist backfill matching | A freed slot, and the best fit waiting patient by specialty, urgency and drive time | Automated offer, ranked |
| 18 | Reminder channel lift | Which channel actually moves attendance | Measured against a holdout, then standardised |

Every scenario is the same query shape and returns the same four things: the evidence path, the patients affected, the recommended action, and a cohort ready to activate.

---

## Appointments: booking, cancellation and attendance risk

### A booking is a lifecycle, not a row

States: requested, scheduled, confirmed, reminded, arrived, completed. The exits are what carry the information, and they are not interchangeable:

| Exit | Why it is distinct |
|---|---|
| Cancelled by the patient | Lead time decides whether the slot is recoverable at all |
| Cancelled by the clinic | Provider absence or template churn. Frequently recorded as though the patient cancelled, which quietly blames the patient for the clinic's problem |
| Rescheduled | A new appointment against the same care intent. Not a second failure |
| No-show | The slot is gone and the care gap stays open |

**Care intent is the unit that matters.** One care intent can hold four bookings and three cancellations. Count appointments and the patient looks non-compliant. Count care intents and you see one person who eventually got seen, after three rounds of friction. Most reporting gets this wrong, and the bitemporal edges already in the model make the reschedule chain reconstructable.

### What the prediction actually predicts

**Define the target properly first.** Three outcomes, not two: attended, cancelled, no-show. And a cancellation three weeks out is a recovered slot, while a cancellation two hours out is a no-show with extra steps. So the model returns **attendance probability** and **slot recovery probability**, because those are the two numbers an operation can act on.

**Features the graph already holds:** lead time from booking to visit (usually the strongest single signal), patient history shrunk for low counts, drive time and travel burden (already an edge), reminder delivered and engaged with, the number of times the clinic previously cancelled on this patient, appointment type, specialty and slot time, open care gaps, coverage status.

**Output contract:** a calibrated probability rather than a rank, reason codes traced back to graph evidence, the model version and validity window, and the score written back as a signal node so every layer above can read it. Calibration matters more than discrimination here: if the model says thirty percent and the truth is fifty, every overbooking decision taken on it is wrong.

> **The rule that keeps it defensible: use the score to add support, never to remove access.** A no-show model that downgrades a slot, refuses a booking or double-books aggressively will penalise the patients with the worst transport, the least flexible work and the most caring responsibilities. The same score, pointed the other way, buys them a phone call, a transport offer or a telehealth alternative. Choose that direction deliberately, and write it into the specification rather than leaving it to whoever builds the screen.

---

## Extending the framework: the feature pack

A new feature declares five things. The engine does not change.

| # | Declaration | Appointments as the worked example |
|---|---|---|
| 1 | **Entities and edges**, added to the ontology as shapes: bitemporal, evidence bearing | Appointment, CareIntent, Slot, Waitlist |
| 2 | **A specification**, what good looks like: targets, thresholds, windows | Utilisation target, recovery window, maximum lead time |
| 3 | **Signals**, computed indices promoted to traversals | No-show risk, recovery probability, utilisation |
| 4 | **Gap engines**, constraints that, unsatisfied, are gaps | `idle_slot_gap()`, `lead_time_gap()`, `churn_gap()` |
| 5 | **Cohorts and actions**, handed to the activation layer that already exists | Backfill list, support outreach, overbook policy |

What a feature pack never touches: identity resolution, the privacy boundary, storage, the traversal engine, the campaign machinery. Predictions plug in the same way, through a model registry: any model registers as *(entity type, target, horizon)* and returns a calibrated score with reason codes and a validity window, written back as a signal. Adding a prediction is registering a model, not rebuilding a pipeline.

This is what makes the difference between an application and a framework. Register the feature, and the gaps, the agent answers and the campaigns follow.

---

## The nine layers

| Layer | Purpose |
|---|---|
| L1 Source systems | EHR, credentialing, provider directory, booking and scheduling, claims, referrals, geography |
| L2 Source connectors | Read only, hashed, replayable. No writes anywhere |
| **L3 Trust and privacy boundary** | **De-identification at ingress, three data planes, keys, re-identification defence** |
| L4 Ingest and identity | EMPI for patients, NPI, TIN and CCN for providers and places, with provenance |
| L5 Domain model | CareNetworkContext: providers, facilities, service lines, appointments, care intents, demand, flows |
| L6 Graph storage | Bitemporal, content addressed, immutable snapshots |
| L7 Derived edge engine | SERVES, REQUIRES, COVERS, SUBSTITUTE_FOR, plus the dated indices |
| L8 Network ContextGraph | Traversals, vector plane, prediction plane, shadow graph, network analytics |
| L9 Gap engines and API | The scenario library, feature pack registration, the query surface, policy at query time |

### Layer 3 in detail: how patient and provider data stays safe

Security is a layer rather than a footnote, because the data is PHI and because a graph is a sharper re-identification instrument than a table.

| Control | What it does |
|---|---|
| De-identify at ingress | Safe Harbor identifiers removed, MRN replaced by an HMAC token per realm, dates shifted by a consistent per-patient offset, geography truncated to census tract |
| Three data planes | **Analytic**: tokenised and k-anonymous, the default. **Operational**: limited data set under BAA, for outreach only. **Identified**: enclave access, break glass, logged |
| Keys and crypto | Keys held in KMS or HSM and never in the application, envelope encryption per snapshot, salt rotated by market and period, TLS 1.3 in transit and AES-256 at rest |
| Re-identification defence | k-anonymity floor on every published cell, suppression where a rare specialty meets a small geography, differential privacy noise on published counts, a query budget per user |
| Policy at query time (L9) | Purpose of use required on every call, minimum necessary compiled into the query rather than filtered after, k-anonymity checked before the result is returned |
| Assurance | HIPAA, HITRUST and SOC 2 controls mapped, immutable WORM audit log, quarterly re-identification risk review |

**The threat model, with the control for each.** Re-identification from rare attribute combinations: k-anonymity at the query compiler. Insider browsing: purpose of use required per query. PHI reaching a model endpoint: aggregates only unless the endpoint is BAA covered. Vendor sprawl through copies: no copies leave the boundary.

---

## Seven decisions that make the graph model more than a directory

1. **Bitemporal by default.** Every edge carries two clocks: when it was true in the world, and when we learned it. Claims arrive ninety days late and credentials move, so without both clocks a real change cannot be told apart from a late arrival. It lets you ask what was true in March, and separately what we believed in March.
2. **Relationships are nodes.** Affiliation, Privilege and Coverage are objects rather than plain edges, so each carries its own dates, confidence, evidence and scope, and other edges can point at them. A coverage claim disputed by claims data keeps both sides.
3. **Assertion plane and evidence plane.** Every assertion resolves to evidence nodes: source, extract, row, hash. No evidence path means no publication, enforced by the engine rather than by habit.
4. **Capability algebra.** A service line is a specification: required specialties, required capabilities, coverage window, minimum volume. Gap detection becomes constraint satisfaction over the graph instead of a library of hand written queries, so a new service line is a specification row rather than new code.
5. **Symbolic plus vector.** Typed traversal handles the hard constraints, embeddings handle likeness: who could substitute, which site is comparable. Anchor symbolically and rank by vector, never the reverse, so similarity never overrules a credential.
6. **Shadow graph for counterfactuals.** Hypothetical providers and sites are written into a copy on write namespace. Traversals run against base plus shadow and the diff is the answer. The base graph never mutates, so the hire can be simulated before it is funded.
7. **Private by construction.** Patient nodes are tokenised and degree limited, and the cohort is the queryable unit. A graph is itself a re-identification vector: a rare specialty plus a rare condition plus a small geography identifies a person. k-anonymity belongs in the query compiler, not the dashboard.

Each is cheap to build in at the start and expensive to retrofit. Bitemporality in particular cannot be added after the fact, because the second clock was never recorded.

---

## The five hard problems

1. **Identity resolution is the ceiling on every number.** Roster, claims and NPPES disagree about who works where. Individual and organisational NPIs must never collapse into one node.
2. **Privileging data is usually the weakest source,** often a separate and stale system. Scenario 3 depends on it entirely.
3. **Bookable against booked supply.** If scheduling exposes only booked appointments, the capacity index degrades to a proxy and "no slots" cannot be separated from "bad template".
4. **Attribution.** Whose patient is it. One versioned rule per service line, agreed before build.
5. **Re-identification risk is a design constraint, not a review step.** It decides what the graph is allowed to hold, which is why Layer 3 exists before the graph is built rather than after.

None are blockers. All five are decisions to take in week one rather than discoveries to make in month three.

---

## Ninety day proof

| Weeks | Scope |
|---|---|
| 1 to 3 | One market, two service lines. Source inventory, attribution rule, required specialty map, privacy boundary design |
| 4 to 7 | Privacy boundary and identity resolution live. Match rate and k-anonymity floor published as the first deliverable |
| 8 to 11 | Two gap engines live (scenarios 1 and 3), reviewed by a clinical SME |
| 12 to 13 | One what-if simulation, and a gap list that a clinical leader and a network leader both sign |

Rebuild the deck with `node scripts/build-clinical-network-deck.js docs/clinical-network-graph-concept.pptx` (requires `pptxgenjs`).

The poster slide sizes itself: `scripts/trenda-widths.json` holds real Trenda advance widths and line heights, and the generator wraps every string against them to pick the largest uniform type size at which all nine columns still fit. It currently settles on 7.25pt body with 8.25pt section headings. Change the content and the size re-solves on the next build.
