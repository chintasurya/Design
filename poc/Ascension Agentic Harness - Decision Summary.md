# Ascension Agentic Harness: proposal decision summary

What we decided for the Ascension proposal deck, end to end. The deck is **"Ascension Agentic Harness"** (30 slides, Insight Global template).

---

## 1. Positioning and naming

| Decision | Detail |
|---|---|
| Name | The proposal was first called **MAD (Multi-Agent Delivery)**. It is now **Agentic Harness** on every slide, in the speaker notes and in the design. |
| One-line pitch | An AI agent team, grounded in a knowledge graph of the Ascension org, takes a Jira story to a tested, deployable Salesforce change. People approve every step. |
| Core message | *"Codex is the engine. The Agentic Harness is everything around it."* Ascension already licenses Codex Enterprise. We build the harness that makes it grounded, governed and repeatable. |
| Lifecycle term | **ADLC (agentic development lifecycle)** replaces SDLC throughout. |
| Look | Insight Global PowerPoint template. Light slides for detail, black slides for the story (platform, harness engineering, future state, scorecard), and the evals slide on the template's blue glow background. The IG footer comes from the slide layouts, so it is fixed on every slide and cannot be dragged. |
| Original content | The client's original slide content was kept word for word, apart from the MAD → Agentic Harness rename. Only the theme changed. |

---

## 2. Final deck, slide by slide

| # | Slide | What it says |
|---|---|---|
| 1 | Title | Ascension Agentic Harness |
| 2 | Opener | "What if every change already knew everything Ascension has built?" Agenda, plus measured results: 2-4 days per Health Cloud change (was 1-2 weeks), 15-20 days per campaign (was ~90), 75-85% faster test preparation, and 20-25% lower run cost (planned). |
| 3 | One agent team | 7 agents reused by every pod |
| 4 | High-level architecture | Helios-style layers (Surface, Runtime, Registry, Context, Govern) on Ascension's own infrastructure. |
| 5 | Harness engineering | Five pillars: **Context, Action, Orchestration, Control, Feedback**. Operating rule: *when an agent struggles, fix the harness, not the prompt.* |
| 6 | Future state | From **Agentic Harness** (today, this proposal) to **dynamic self-harness**, which AGI (Artificial General Intelligence) would make possible. Includes "How we trust AGI" and "What never changes". |
| 7 | Evals are how we earn reliability | **Reliability = Observability + Evals, protected by Guardrails** across the top. Evals sit at the centre: agent output, traces, and the golden set with weekly samples go in; Pass, Retry (bounded loop, max 5 attempts, then a named owner) and Learn (closed loop: every miss becomes a new test) come out, all inside guardrails in and out. |
| 8 | Agent scorecard | Each agent scored on its own job, with a definition of pass@k. |
| 9-10 | Pod cases | Nudge campaign (90 → 15-20 days) and Network Services market onboarding (9 months → 10-12 weeks) |
| 11 | Operational efficiency | People supervise, agents build, around the clock |
| 12 | Business outcomes | Measured results so far, plus the **20-25% floor** we commit to |
| 13 | What it means for Ascension | All pods: $16M a year today; savings in the three years **after go-live** (section 7) |
| 14 | Timeline | 18 months; phase exits signed before the next phase starts |
| 15 | Phase exit criteria | For each phase: outcome, how success is measured, who signs, dependency |
| 16 | Risks and mitigations | Nine risks, each with likelihood, impact, mitigation, early warning and owner |
| 17 | Delivery team | 17 at peak, 10 roles, all offshore |
| 18 | Commercials | Fixed fee vs time and materials, plus the managed service |
| 19 | Thank you | |
| 20 | Ask us anything (back-up) | Every "what if" question mapped to the layer that answers it: guardrails, observability, evals, people |
| 21 | Change management (back-up) | Change Guardian across every pod |
| 22-30 | Appendix | Knowledge graph layers, Google Cloud deployment, target architecture, execution flow, network services architecture |

---

## 3. How the solution works (what the slides commit to)

- **Phase 1, knowledge graph.** One cited map of Jira, Confluence, Salesforce, Git, Copado and Google Drive, held in **Spanner Graph** (queried with GQL). The earlier proof of concept used an in-memory graph; we now propose Spanner Graph because Ascension runs on Google Cloud, so the graph store is native there with no separate database to buy or approve. Agents check what already exists, its impact and its owners before building.
- **Phase 2, agentic harness runtime on Google Cloud.**
  - Every story runs as a nine-step durable workflow.
  - Seven agents do the steps: Orchestrator, Requirements, Architect, Developer, Review, Test, Release.
  - People approve at the human gates **H1-H4 and CAB**.
- **Safety by design.**
  - No agent holds a production credential.
  - Three identities: read, develop, release.
  - Every tool call goes through a gateway with an allow list.
  - The Change Guardian checks every design, commit and promotion against the ownership graph.
  - A change passport records every step and approval.
- **Guardrails, six layers.**
  - Codex Enterprise baseline.
  - Intake checks.
  - Input guardrails: moderation, injection rules, data loss prevention (DLP) for patient data.
  - Understand-and-confirm.
  - Action guardrails.
  - Output guardrails.
- **Bounded loops.** An agent retries a step until its checks pass, **at most 5 attempts**. Then the step stops, nothing is released, and a named owner gets every attempt in Jira. Budgets and timeouts can stop it sooner.
- **Run report.** Every run is logged and reported:
  - pass@1 to pass@5;
  - time per step and end to end;
  - re-run time and cost;
  - waiting time at gates;
  - agent scores;
  - escaped defects;
  - stopped runs.
- **Closed-loop evals.** Golden set → offline gate → guarded run → weekly blind sample re-reviewed by Ascension experts → diagnose → tune and re-test. Agents cannot edit tests or the evaluation set, a held-out set is never shown to agents, and any change that weakens a test is blocked.
- **pass@k.** The share of steps that pass all checks within k attempts. pass@1 means right first time; pass@5 means right by the last attempt.
- **Entropy management.** A weekly, *read-only* org health report to each pod (unused fields, duplicate Flows, stale Confluence pages). Nothing is cleaned automatically; owners decide what to fix.
- **AGENTS.md.** A short map file in each Git repo that Codex reads first. Access follows Ascension's existing repo permissions.

### Proven patterns we reference
- OpenAI's "Harness engineering" (Codex team, Feb 2026) and Martin Fowler's notes on it, for the harness engineering framing.
- Uber Eats' closed-loop evals for its food-photo agent (AI Engineer World's Fair 2026): golden sets, pass@k, QA gate, human labels on production samples, diagnoser. Our evals slide follows the same pattern.

---

## 4. Future state (slide 6)

- **Today, this proposal: Agentic Harness.** Agents work inside a harness we design and propose improvements; people approve every change.
- **Future state, AGI: dynamic self-harness.** The harness tunes itself inside limits Ascension sets.
- **How we trust AGI.**
  - Autonomy is earned step by step, with evidence.
  - Every action is on record.
  - Hard limits it cannot change.
  - People can always stop it.
- **What never changes.** Ascension sets the goals and limits, keeps the final say on production, and can see and stop any run.
- **Not in the price.** The AGI column is a direction, not a commitment, and is not part of the price.

---

## 5. Timeline, phase exits and risks (slides 14-16)

18 months, seven phases. Each phase starts only after the previous phase's exit is signed, and the fixed fee for a phase is invoiced only at that signature.

| Phase | Months | Exit (outcome signed) |
|---|---|---|
| 0 Mobilise | M1 | Access, environments, approvers and pilot-pod baselines signed |
| 1 Knowledge graph | M2-M5 | Graph proven on 10-15 past changes (≥90% agreement with architects) |
| 2 Harness pilot | M6-M9 | Two pilot pods (Network Services, Nudge) measured against baseline |
| 3 Harden | M10-M11 | Production use authorised (security + CAB) |
| 4 Scale wave 1 | M12-M14 | 5 pods live and measured |
| 5 Scale wave 2 | M15-M17 | All 9-10 pods live and measured |
| 6 Handover | M18 | Run team operating; handover signed |

The thresholds are proposed targets, confirmed with Ascension at the Phase 0 exit. During the build, each pod is measured against its own Phase 0 baseline at the phase exits; the savings figures on slide 13 start after go-live.

**Risks and mitigations (slide 16).**

| Risk | Likelihood · impact | Mitigation (in short) |
|---|---|---|
| Access and environments arrive late | Med · High | Access is the Phase 0 exit; Phase 1 starts only after it is signed |
| Experts have no time to label evals | High · High | Hours agreed per pod at Phase 0; agents pre-label, experts confirm |
| Codex policy blocks plugins or MCP | Med · High | Confirmed with Codex admins in Phase 0; fallback: harness runs headless on Cloud Run |
| Patient data or secrets reach a model | Low · High | Graph holds metadata only; DLP in and out; OpenAI BAA and zero retention confirmed; pen test |
| Graph facts are incomplete or stale | Med · High | Phase 1 exit at ≥90% agreement; freshness checks; nightly drift watch |
| Agent quality drifts, or a new model behaves differently | Med · Med | Evals gate every change; model pinned and changed only by config after passing evals |
| A change breaks another pod's process | Med · High | Change Guardian at design, commit and promotion; CAB unchanged; rollback plan |
| Pods keep working the old way | Med · High | Two pilot pods prove it first; onboarding waves with training; dashboard per pod |
| Agent run cost grows faster than planned | Med · Med | Token budgets per step and run; cost in every run report, reviewed monthly |

---

## 6. Team (slide 17)

**17 people at peak, 10 roles, 100% offshore** (16.5 FTE at peak, 247.5 FTE-months).

| Role | Peak | Note |
|---|---|---|
| Engagement lead / project manager | 1 | Also covers business analysis (no separate BA) |
| Solution architect | 1 | |
| AI harness architect | 1 | Was "AI architect" |
| Harness engineers | 3 | Were "forward deployed AI engineers" |
| Knowledge graph engineers | 2 | |
| Cloud and DevOps engineers | 2 | Cover the former SRE role |
| Salesforce Health Cloud developers | 2 | Build the skill packs the agents follow and review agent code in the pilots; they do not build pod features |
| Marketing / Data Cloud developer | 1 | Same role, for Marketing and Data Cloud |
| QA automation engineers | 3 | |
| Cloud security engineer (HIPAA) | 1 | Half-time |

**After month 18**, a run team of 4, offshore.

---

## 7. Commercials and value (slides 13, 18)

### Price
| Option | Amount |
|---|---|
| **A. Fixed fee by gate (recommended)** | **$4.79M** over 18 months, invoiced only when each phase exit is signed |
| B. Time and materials | $5.50M |
| C. Managed service, from month 19 | ~$83K/month team + ~$20K/month platform ≈ **$103K/month ($1.24M a year)** |
| Platform usage | Passed through at cost (~$0.23M over 18 months) |

- **Why fixed is lower than T&M.** We price the outcome and bring work already built, and Insight Global carries the delivery risk. The fixed fee is 13% below T&M.
- **Negotiation levers** (if Ascension pushes toward ~$3.5M). Trade scope, not rates:
  - Contract scale wave 2 later: about $3.90M.
  - Also fold the handover into the managed service: about $3.76M.
- **Rates are assumed.** Blended ~$139/h offshore, ranging $100-195/h by role. **Replace with the IG rate card before the commercials go to the client.** The commercials slide carries no speaker notes, by decision.

### Value (slide 13: all pods, in the three years after go-live)
Years 1-3 start once the 18-month implementation is done (month 19 on) and every pod is live. The build period is not in these numbers.

| | Today | With the harness | Saved |
|---|---|---|---|
| Year 1 | $16M | $7M | $9M (56%) |
| Year 2 | $16M | $5M | $11M (69%) |
| Year 3 | $16M | $3M | $13M (81%) |
| **3 years** | **$48M** | **$15M** | **$33M (69%)** |

- **Return:** about **7x the $4.79M fixed fee**, paid back within the first year after go-live.
- **How it works:** in every pod, a squad of 4-5 developers plus a QA becomes 1 developer directing the harness agent, plus 1 QA.
- **Floor vs target:** slide 12's 20-25% lower net run cost is the commitment. Slide 13 is the target.

---

## 8. Client Q&A preparation (highlights)

| Likely question | Answer |
|---|---|
| Why do we need this if we have Codex? | Codex doesn't know Ascension's org, rules or approvals. The harness does. |
| Can AI change production? | No. No agent holds a production credential; owning teams deploy after CAB. |
| What if it makes a mistake? | Tests, Code Analyzer, Change Guardian and human gates catch it before release. Every change has a rollback plan. |
| Is patient data safe? | DLP redacts it; agents get only a bounded context slice. |
| Will people lose jobs? | Ascension chooses: redeploy, attrition, or keep the team and deliver more. Reviewed quarterly. |
| Is the saving guaranteed? | The 20-25% floor and the phase exits are the commitment; slide 13 is the target. |
| What if a phase fails? | It extends and the next phase does not start. On the fixed fee, IG carries the overrun. |
| What if a better model comes out? | The model is set by configuration in the agent runtime, and the tools stay the same because they sit behind MCP. Any new model must pass the evaluation set first. |
| What about AGI? | A direction, not in the price. Autonomy grows only with evidence and Ascension's approval. |

---

## 9. Open items and risks before the client meeting

1. **Rates.** Replace the assumed bill rates with the IG rate card (commercials, slide 18).
2. **Savings ambition.** The three years on slide 13 start after go-live. Present slide 13 as the target and slide 12 as the floor. Year 3 at $3M includes ~$1.24M for the managed service.
3. **Client effort.** Ascension's experts label the golden set and the weekly samples (a few hours a week). This should be added to the team slide's "Ascension provides" list.
4. **Codex set-up.** Confirm with Ascension's Codex Enterprise admins that custom plugins and MCP servers are allowed.
5. **Architecture slide.** Optional "Stops after 5 attempts" differentiator tag on the target architecture slide (slide 27, pending).
6. **Pod baselines.** All per-pod figures are confirmed against each pod's Phase 0 baseline.
