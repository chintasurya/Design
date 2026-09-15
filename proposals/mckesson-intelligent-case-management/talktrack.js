/**
 * Talk track for McKesson_Intelligent_Case_Management.pptx.
 * Single source of truth: deck.js writes `say` into the slide's speaker notes,
 * and talktrack-doc.js renders the same content as the presenter handout.
 *
 *   title   what the slide is called, for the handout
 *   secs    rough spoken length, for pacing the run through
 *   purpose one line on why the slide exists
 *   say     what to actually say, in the room
 *   ask     the question this slide usually attracts, and the answer
 */
module.exports = [
{
  n: 1, title: 'Cover', secs: 20,
  purpose: 'Set the frame before any detail.',
  say: "We were asked to take on Extended Care email. What we are proposing is not more people pointed at the same queue, it is the queue itself working differently. Everything that happens to a case before an agent sees it, reading it, classifying it, prioritising it, routing it, drafting the reply, moves into Salesforce. The agent's job becomes judgement.",
  ask: "If asked what is different from the original proposal: the operating model and the commercials are unchanged. This is how the work gets done inside them.",
},
{
  n: 2, title: 'What this proposal covers', secs: 25,
  purpose: 'Give the shape of the next thirty minutes.',
  say: "Six sections. We start with where the effort actually goes today, then the solution itself, then classification, priority and SLA, then the drafting and summarising that reduces workload, then trust and phasing, and we close on business value and what we need from you. If you only want two, take section one and section six.",
},
{
  n: 3, title: 'The solution on one page', secs: 60,
  purpose: 'The executive slide. Everything in one picture.',
  say: "This is the whole design on one page. Email arrives and becomes a Salesforce case. A single record triggered Flow then does three things: it understands the email using a Prompt Template, which reads the thread and pulls out the category, the order numbers, the sentiment and a summary. It decides, using deterministic rules, what priority this is, which queue and skill it needs, which SLA clock applies and when to escalate. And it assists, drafting the reply grounded in your Knowledge articles. The agent reviews that draft, corrects it and sends. Underneath it all sits Omni Channel routing, Entitlements for SLA, Knowledge, and the Einstein Trust Layer for PHI masking and audit. On the right: what it is worth, what it runs on, and how it lands in three phases. The one line I would take away is at the bottom left. Anything involving money, PHI or a judgement call always stops with a person.",
  ask: "This is the slide to leave up if the conversation goes long. If an executive joins late, restart here.",
},
{
  n: 4, title: 'Where the effort goes today', secs: 45,
  purpose: 'Build the case for change from their own numbers.',
  say: "Thirty three thousand cases a month, and the blended handling time is eight fifteen. But look at the split: credits and disputes run at eleven twenty five against six forty for order placement, so a quarter of your volume is consuming a disproportionate share of the effort. On the left is what happens to every one of those cases today. Six manual steps, and only the last one, composing the reply, actually needs the expertise you hired for. The other five are administration that follows rules a system can apply.",
  ask: "If they push on the two minutes of triage: it is our estimate, and we validate it against real cases in the baseline period. The point stands either way.",
},
{
  n: 5, title: 'From a manual queue to intelligent case management', secs: 40,
  purpose: 'Show the before and after without going into mechanism.',
  say: "Do not read this line by line. The shape is what matters. Every row moves work from the agent to the platform. Case creation, classification, priority, assignment, SLA, the response itself, the handover. And every item in the right hand column is standard Salesforce behaviour, not something exotic we are inventing for you.",
},
{
  n: 6, title: 'Six stages, one automated case lifecycle', secs: 35,
  purpose: 'Name the six stages used for the rest of the deck.',
  say: "Six stages: capture, understand, route, time, assist, learn. We use this frame for the rest of the deck, so if you lose the thread at any point, ask which stage we are in. Worth noting now: stages one, three, four and six need no new licensing at all. Stages two and five are where Prompt Templates come in, and that is the only part with a licensing question attached.",
},
{
  n: 7, title: 'How it works inside McKesson Salesforce', secs: 50,
  purpose: 'The architecture, for the technical audience.',
  say: "This is the same story with the Salesforce components named. The important architectural point is that one Flow is the spine. The Prompt Templates are called by the Flow, they do not own the process. That matters because it means the policy, what priority something gets, whether it can be automated, stays deterministic and auditable. A model is interpreting language. It is not deciding how your cases are handled. Underneath, the Einstein Trust Layer gives us zero data retention, PHI masking, prompt injection defence and a full audit trail on every generated output.",
  ask: "Security will ask where the data goes. Answer: it runs in McKesson tenancy, PHI is masked before the prompt leaves the org, and nothing is retained or trained on.",
},
{
  n: 8, title: 'Capture the email, then understand it', secs: 45,
  purpose: 'Show the eight values everything downstream depends on.',
  say: "Capture is Email to Case, with thread matching so a reply appends to the existing case instead of creating a duplicate, and an acknowledgement going back to the customer within seconds. Understand is the triage template. The eight fields at the bottom are the whole point of this slide, because routing, SLA, drafting and reporting all key off them. And note the third bullet on the right: deterministic Flow rules sit over the top. Where policy is unambiguous, the rule wins, not the model.",
},
{
  n: 9, title: 'A case taxonomy built for customer service', secs: 35,
  purpose: 'Replace software terminology with service categories.',
  say: "An earlier draft of this used terms like story and defect. Those are engineering words and they would confuse a customer service agent. These six categories describe what an Extended Care customer is actually asking for, and they map cleanly onto how the work gets handled. Category tells you what kind of work it is. The service family field on the right tells you which part of the operation owns it. Routing, reporting and knowledge all key off the pair.",
},
{
  n: 10, title: 'Priority is derived, not guessed', secs: 40,
  purpose: 'Show priority as a formula with controls, not a judgement call.',
  say: "Category alone does not tell you how urgent something is. Priority comes from four inputs: business impact, urgency, customer criticality, and regulatory or financial risk. The four tiers are on the slide, but the controls along the bottom matter more than the tiers. Priority is never left blank. An agent can change it only with a recorded reason. Downgrading a P1 or P2 needs Shift Lead approval, and every change is in the audit history. Without those controls priority drifts and the SLA numbers stop meaning anything.",
},
{
  n: 11, title: 'Routed to the right team', secs: 30,
  purpose: 'Assignment on skill and capacity, not next free hands.',
  say: "Omni Channel takes the category, family and priority and pushes the case to someone who has the skill and the capacity to work it now. Six inputs decide it: queue, skill, capacity, priority, coverage and a fallback so nothing sits unowned. The practical effect is on the right: complex credits reach senior agents, and a P1 never sits behind a routine status request. This is all included in Service Cloud. No AI licensing needed.",
},
{
  n: 12, title: 'Two SLA clocks, enforced by the platform', secs: 45,
  purpose: 'SLA as live records, not month-end reporting.',
  say: "Entitlements and Milestones run the SLA inside Salesforce against your business hours. Two clocks: first meaningful response, and resolution. The clock is a record, not a report, which means we can act on it while it is still running rather than explain it afterwards. One design decision to flag: the resolution clock keeps running while we wait on an internal McKesson team. We could pause it and our numbers would look better, but it would hide the real customer experience. Instead we measure dependency time separately so you can see what is ours and what is yours.",
  ask: "Expect pushback on that decision. It is deliberate and we think it is the honest choice. The four way time split is the answer.",
},
{
  n: 13, title: 'Escalation fires on percentage of SLA consumed', secs: 35,
  purpose: 'Explain why proportional beats a fixed rule.',
  say: "A fixed one hour escalation rule is too slow for a P1 and pure noise on a seventy two hour credit. So escalation fires on percentage of the clock consumed. Fifty percent notifies the owner, seventy brings in the Shift Lead, eighty five escalates and flags on the dashboard, a hundred goes to the Operations Manager. On a P1 that first prompt lands at seven and a half minutes. On a credit case it lands at thirty six hours. The escalation load scales with actual risk, so people are interrupted when it matters.",
},
{
  n: 14, title: 'The draft is waiting when the agent opens the case', secs: 50,
  purpose: 'The workload reduction, and the boundary that makes it safe.',
  say: "If you take one slide from this deck, take this one. The agent stops composing from a blank box and starts reviewing, correcting and sending. The draft is written in your approved tone, grounded on the case, the customer, the Knowledge article and the order record. The summary means a second agent can pick up a case without reading every reply. And the third column is what makes this safe to say yes to: every credit, return, pricing adjustment, account hold and billing dispute stays with a person, as does anything PHI sensitive or where the data is missing or conflicting. In Phase 2 nothing generated reaches a customer without an agent approving it.",
},
{
  n: 15, title: 'Knowledge articles are what make the answer correct', secs: 35,
  purpose: 'Answer the accuracy objection.',
  say: "The obvious objection to generated replies is that they might be wrong. This is the answer. Every draft is grounded in your own approved Knowledge articles, and the article used is attached to the case so it can be checked in seconds. When an agent finds no article fits, they raise a gap in one click and it becomes a backlog item with an owner. So the knowledge base gets better rather than drifting. Today a good answer helps one customer. Under this model a good answer is written once and grounds every future reply on that case type.",
},
{
  n: 16, title: 'Standard statuses, and what each does to the clock', secs: 30,
  purpose: 'Remove ambiguity from SLA reporting.',
  say: "Ambiguous statuses are how SLA reporting loses credibility. Ten statuses, each with one meaning and a defined effect on both clocks, configured in the Entitlement Process. The row to look at is Pending Internal Team, which is the decision we just discussed. We measure four times on every case: end to end closure, our controllable time, dependency time waiting on a McKesson team, and customer wait time.",
},
{
  n: 17, title: 'Built for a PHI sensitive environment', secs: 40,
  purpose: 'The security conversation, pre-empted.',
  say: "Everything generative runs through the Einstein Trust Layer inside McKesson tenancy. Nothing is trained on your data and nothing is retained by a model provider. PHI and PII are masked before the prompt leaves the org and rehydrated in the response. Instructions embedded in an inbound customer email are treated as content, not as commands to the system. And every prompt, response, agent edit and send is retained, so any reply a customer received can be reconstructed. The band along the bottom is the list that never becomes autonomous, at any phase, whatever the confidence score.",
  ask: "If security wants detail, this is the slide to slow down on. Phase 1 uses no generative capability at all, so it introduces no new data handling surface.",
},
{
  n: 18, title: 'Three phases, and value before any new licence', secs: 40,
  purpose: 'De-risk the licensing question.',
  say: "This is the commercial point without talking commercials. Phase 1 is built entirely from capability you already own in Service Cloud: routing, SLA, escalation, the response library, the dashboards. No new licensing, so you can start without resolving the Agentforce question first. Phase 2 adds the Prompt Templates and needs Einstein or Agentforce licensing. Phase 3 is a controlled pilot on a narrow list of case types. Each phase is gated on readiness, not on a date.",
},
{
  n: 19, title: 'What McKesson and the team can see, live', secs: 30,
  purpose: 'Show that structured data makes real reporting possible.',
  say: "Because classification, priority and SLA are now structured fields rather than judgement calls, they can be reported on reliably. Two views: an operations control tower for the leads and for you, and an individual view for each agent. Note the automation coverage metrics, which is how we prove the AI is actually helping. Draft acceptance rate is a coaching signal about the templates, never a target for the agent. And shift reports are generated from case fields, not typed by agents at the end of a shift.",
},
{
  n: 20, title: 'Every closed case feeds the next one', secs: 25,
  purpose: 'Improvement as a managed process.',
  say: "A short survey on closure, linked back to the originating case. Negative feedback automatically raises a service recovery action. QA determines whether the cause is the agent, the process, the article, the system, a dependency or the policy, and the fix goes to the right place. The difference from today is that the signal is captured automatically at the point of work rather than depending on someone remembering.",
},
{
  n: 21, title: 'Where the minutes actually come from', secs: 45,
  purpose: 'Show the arithmetic rather than assert a percentage.',
  say: "Handling time does not fall because we ask agents to work faster. It falls because we remove steps that do not need a person and shorten the ones that do. Here is the decomposition of the eight fifteen, step by step, with what we think each becomes. It totals six fifteen, about a twenty four percent reduction. The row I would defend hardest is classify, prioritise and assign, because that one is fully automated rather than assisted. Across your volume that is over three hundred and seventy hours a month on its own. These are modelled numbers and we have labelled them as such. We validate them in the baseline period before anyone commits to them.",
  ask: "If challenged on the compose row, note it only saves twenty five seconds because we assume the agent reads and edits every draft. We have been deliberately conservative.",
},
{
  n: 22, title: 'Efficiency and response time, the two targets', secs: 40,
  purpose: 'The number the sponsor remembers.',
  say: "Two targets. Efficiency is the twenty four percent, roughly eleven hundred hours a month returned as capacity. Response time improves further, and for a different reason: today first response is mostly queue wait, because a case is only understood when an agent reaches it. Under this model it is understood in seconds, so an urgent case is surfaced immediately rather than on discovery. And every customer gets an acknowledgement with a case number within seconds, which is itself a response time improvement. The right hand column is what this is worth beyond the numbers, and consistency is the one I would underline.",
},
{
  n: 23, title: 'What we need from McKesson to build this', secs: 30,
  purpose: 'Close on the ask.',
  say: "Four things. Access and environment, so we can configure and test. The licensing decision, which is the only genuinely open question and which Phase 1 does not wait on. Data and systems, including your existing articles and templates. And people and decisions, primarily sign off on the taxonomy, the priority rules and the SLA targets. Our proposed next step is a joint design workshop on those definitions, run alongside a technical discovery session on your Salesforce configuration and current Einstein entitlement.",
},
{
  n: 24, title: 'Close', secs: 15,
  purpose: 'One line to leave in the room.',
  say: "Salesforce reads, classifies, prioritises, routes, times, summarises and drafts. Insight Global owns the operation, the quality and the outcome. And agents spend their time on the cases that need judgement. Thank you.",
},
];
