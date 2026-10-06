# Session log — September 2026

What happened in the conversation that produced commits `da1efbf..be91bee`, in
the order it happened, with the reasoning and the wrong turns kept in.

`HANDOFF.md` is the state: what the system is, what it does, what is left.
**Read that first.** This file is the history: how it got that way, which
defects were real, and which of my conclusions you should not take on trust.
A fix with no failure attached reads as a preference and gets undone; this is
where the failures are written down.

---

## 1. Where the session started

P1 and P2 from the previous handoff were open. The console could build a graph
and answer duplicate questions about fields, but *"when an Account is created,
create a HealthcareProvider and a HealthcareFacility"* returned **Safe to
Create** while a Flow already did exactly that.

The previous session had written `tools/probe_flow_missing.apex` to choose
between three candidate causes and never run it. **It is still worth knowing
that I cannot run anything against the org**: no credentials, by rule. Every
org fact in this project arrived as a screenshot or a pasted debug log, and
everything else is inference from code. That constraint shaped the whole
session — diagnostics became the deliverable, repeatedly.

---

## 2. The arc, in order

| # | What was asked | What it turned into |
|---|---|---|
| 1 | "Start with P1" | Fixed all three candidate causes rather than waiting for the probe, then found two further defects that would have kept the symptom alive anyway |
| 2 | "Start P2" | Type buttons removed, model choice moved behind the approval gate |
| 3 | "What are the scoped objects? Give me the list" | **There was no list.** The scope had only ever reported counts. Built `print_scope.apex` |
| 4 | Screenshots of the real pod model | Rewrote scoping entirely: the pod is now declared in code, not inferred from a profile |
| 5 | "What do you need to read Flow metadata?" | Tooling API runbook. Then four rounds of OAuth failures |
| 6 | "Update the PPT" | 13 slides appended to the architecture deck |
| 7 | "Content is overlapping" | A line-spacing bug of mine, and a checker of mine that hid it |
| 8 | "Summary… are we not capturing snapshot model?" | A fair challenge. We capture retention, not a snapshot model, and a code comment of mine had overclaimed it |
| 9 | "This field already exists but it says Safe to Create" | The most serious defect of the session |

---

## 3. Defects found and fixed, with root causes

The root cause matters more than the fix. Several of these look like matching
bugs and are not.

### Automation was dropped for its target's sake

A Flow record-triggered on Account resolved to nothing and **the whole Flow was
discarded**, because Account was outside the pod scope. The console was
answering a question about a Flow by not knowing the Flow existed.

→ Out-of-scope trigger objects now enter as **boundary nodes**: one node, no
fields, capped at 150. Automation may reach outside the pod; it is part of the
pod's behaviour regardless of where its target lives.

### An unsearched absence was reported as an absence

`AIReuseAnalyzer.behaviour()` returned Safe to Create on an empty findings
list. So *"the graph does not hold Account"* and *"nothing runs on Account"*
produced the identical verdict.

→ A clearance now requires the trigger object to appear in the evidence. If it
was never searched, the verdict says so and blocks.

### The traversal budget was spent on columns

`blastRadius` walked edges in storage order. An object with 200 fields has 200
structural edges against perhaps three pieces of automation, so with
`MAX_NODES = 60` the walk finished inside the field list and the Flow never
entered the result.

→ Edges are walked **behaviour before structure**, and a caller can exclude
node types from the walk outright. Filtering afterwards is too late: the budget
is already gone.

### One question returned fifty-five answers

*"Terminate HealthcareFacilityNetwork when due date is exceeded"* returned 55
components, every one reached via `-> sobj:account`. The walk passed **through**
Account, which connects to ~70 classes, and fanned out across all of them.

→ **A non-anchor object is a destination, not a corridor.** It is reported as a
finding and never expanded through. Triggers, flows and classes still expand —
that is what follows a call chain.

Three things conspired on that one request, and all three are fixed: the object
was never found (the parser only knew `on|in|for <Object>` phrasings), the verb
`terminate` was unknown so the action fell back to the widest possible search,
and the rows were unreadable. `objectsNamedIn()` now matches the request
against the graph's own object names.

### A field that existed cleared as Safe to Create

The worst one, and structural rather than a matching bug. Healthcare Facility
has **135 fields and 17 automation components** against a budget of **60**, and
behaviour edges are walked first — so roughly **seven fields in ten never
entered the result**, and `exactMatches()` then searched the survivors. Which
fields survived depended on map iteration order, so **the verdict was luck**.

→ **A bounded walk can answer "here is what this touches". It can never answer
"this does not exist",** because absence from a sample says nothing about
absence from the org. Existence now has its own lookup,
`AIGraphMemory.attachedMatches()`, which scans the anchor's own edges —
complete by construction, no budget near it — and matches across spellings.
Matches are added as Direct evidence *before* the traversal runs.

### Apex was read with `contains()`

`body.contains('Account')` is true of a class that only mentions
`AccountingCode` — the same substring fault as `"UPDATE".contains("DATE")`.

→ Bodies are split into identifier tokens once and matched whole. Cheaper too:
one tokenise per class instead of one `contains()` per object per class.

### A handler's handler was unreachable

A trigger body is two lines that call a handler. Without call edges, *"what
happens when an Account is saved"* returned the name of a file containing
nothing.

→ `TRIGGER_CALLS_APEX` and `APEX_CALLS_APEX` edges, with bodies fetched in
chunks of 25 and the scan stopping on a CPU/heap budget that reports how far it
got.

### Scope was inferred from the wrong signal

Several pod objects are written **only by automation**, so the profile has no
create permission on them. `HealthcareFacilityNetwork` — the object most
questions are about — was invisible for exactly that reason.

→ `AINetworkServicesPod` declares the pod in code. Measured: **49 objects in
scope, 13 declared (all 13 names resolved), 12 profile-writable, 24 carrying a
pod record type.** The obvious alternative was measured too and rejected:
permission sets grant write on **1,319 objects**, which is most of the org.

---

## 4. Things I got wrong in this session

Read this before trusting any conclusion in the handoff that is not backed by a
log you have seen.

| What I did | Why it mattered |
|---|---|
| Told you to use **"New Legacy"** for the Named Credential | Right for the authorization-code flow, wrong once PKCE turned out to be locked. Cost a rebuild of the credential |
| Gave `test.salesforce.com` as the **client credentials token endpoint** | Correct for auth-code, wrong here. Client credentials is only served by My Domain. Produced `invalid_grant · request not supported on this domain` |
| Said snapshot diffing "comes for free" in a code comment | Versioning makes it *buildable*, not *built*. You caught it. Comment corrected and the gap recorded |
| Emitted `1250` for a 1.25 line multiple in the deck generator | `spcPct` is thousandths of a percent — 100% is `100000`. Every wrapped paragraph stacked on one line |
| Wrote a geometry checker that clamped `max(line, 1.0)` | It read the bad value and **normalised the defect out of existence**, then reported a clean bill of health over broken slides. Worse than not checking |

The last two are the same failure twice: **a check that silently repairs its
input is not a check.** The clamp is gone, and spacing under 50% is now an
error in its own right.

---

## 5. Diagnostics, and what each one established

All read-only unless noted. All in `poc/salesforce/tools/`.

| Script | Established |
|---|---|
| `print_scope.apex` | The scoped object list with the reason each qualified. Built because the scope had only ever reported counts, which nobody could check |
| `probe_flow_missing.apex` | The Account flow gap, scope signals, whether the flow view can be filtered |
| `build_graph.apex` | **Writes** (the graph file only). Enqueues the export, then reports the job and the graph's own notes |
| `verify_tooling_api.apex` | Whether the Named Credential works. Still returning an error — see below |
| `verify_tooling_session.apex` | **The one that paid off.** Bypasses OAuth with `UserInfo.getSessionId()` + a Remote Site Setting |

That last one is the lesson worth keeping: when the credential fought back for
four rounds, decoupling *"is this data worth having"* from *"is the OAuth
config right"* answered every design question while Setup was still being
argued with. It is a **diagnostic only** — `getSessionId()` does not reliably
return an API-enabled session in async Apex, and the export is a Queueable.

**What it proved**, so none of it needs rediscovering:

- `Flow.Metadata` is readable, carrying `recordCreates`, `recordUpdates`,
  `recordLookups` **and `subflows`**
- **495 active flows**, all ids in **one** call — Tooling removes the 200-row
  `FlowDefinitionView` cap as a side effect
- `SELECT Id, Metadata ... LIMIT 5` → `MALFORMED_QUERY`. **One record per call
  is confirmed**, so the reader must be a chained Queueable across 5+
  transactions, keeping extracted facts rather than bodies (~8 KB each, 495 of
  them ≈ 4 MB)
- `MetadataComponentDependency` answers — real dependency edges are available
  and the Apex text-scan heuristic can be retired

---

## 6. The Tooling API credential, where it stands

PKCE is **locked on** in this org — *"To change this required setting, contact
Support"* — so the authorization code flow is impossible and **client
credentials is the only path**. Appendix A of `TOOLING_API_SETUP.md`.

Four errors, in order, each one progress:

1. `missing required code challenge` → PKCE locked; switch to client credentials
2. `INVALID_SESSION_ID` → the External Credential principal was never granted
   to a user through a permission set
3. `invalid_grant · request not supported on this domain` → **my error**; token
   endpoint must be My Domain, not `test.salesforce.com`
4. `invalid_grant · no client credentials user enabled` → **where it stopped.**
   The app has no **Run As** user

**Next action.** External Client App Manager → Policies → **Edit** (the tab
opens read-only, which looks identical to a disabled feature — this cost a
round) → tick *Enable Client Credentials Flow* → the **Run As** field appears
only after that tick → pick an integration user with **API Enabled** and **View
Setup and Configuration** → Save → re-run `verify_tooling_api.apex`. If the
error survives, the consumer key on the External Credential principal belongs
to a different app than the one carrying Run As.

---

## 7. The deck

`Ascension Network Services Knowledge Graph.pptx`. Slides **1–8 are yours**,
untouched. Slides **9–21 are generated** by `deck/add_poc_slides.py` and
describe what the POC actually does.

Design was read out of the file rather than guessed: the `F4F7FC` ground,
`12233B` navy, your categorical accents, Trenda IG type, and the title block at
exactly the offsets slides 2–8 use. Body copy is 8–9.5pt rather than your 5–7pt
because these carry explanation, not reference diagrams.

The generator is idempotent — each generated slide carries a marker and a run
strips its own previous slides before appending, so re-running cannot leave two
copies.

**These slides have never been rendered.** LibreOffice could not load any file
in that environment, including a freshly generated empty one, so
`deck/check_geometry.py` is an arithmetic stand-in: off-slide shapes,
overlapping text boxes, broken margins, collapsed line spacing, text too big
for its box. It cannot judge whether a slide *looks* right. `Fonts.zip` holds
Trenda IG — install it before judging spacing, or PowerPoint substitutes and
the overflow you see is not real.

---

## 8. Open threads

1. **The Tooling API credential** — section 6. Blocking everything else.
2. **The flow reader** — design is settled by the measurements in section 5;
   build it once the credential is green. This is what finally answers HFN
   generation end to end.
3. **Verify the false-clearance fix in the org.** The last package was
   deployed but the field-creation request was not re-run. It should now return
   **Already Exists** citing `Effective_From_Date__c`. If it still clears, the
   field is not attached to the object in the graph — a different problem, and
   I would want the export notes for it.
4. **Look at deck slides 9–21.** Never seen by anyone at the time of writing.
5. **Snapshot model** — retention exists, nothing reads or compares it.
   Cheapest first step is a diff between two ContentVersions, no schema change.
6. **Resume from a ticket number** — agreed long ago, not started.

---

## 9. Rules that did not change, and should not

- **Sandbox only.** No phase of this holds a production credential.
- **No credentials in chat, ever.** I produce a package; you deploy it in
  Workbench. Consumer keys never leave Setup.
- **Always run `python3 tools/build.py`** from `poc/salesforce` before shipping
  a package. It has caught six distinct classes of deploy-killing fault.
- **A knowledge graph, not live search.** Layer 5 is a persisted JSON document.
  This was rejected as live search twice; do not drift back.
- **Never store the graph in records.** 113,310 rows, 221 MB, filled a sandbox.
- **Build correctly, not literally.** Interpret the intent of a request.
- **Be honest about what is unverified.** Most of this project's org facts
  arrived as screenshots. Where something has not been measured, say so.
