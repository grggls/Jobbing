---
company: "Filevine"
interviewer: "J.R. Jasperson"
role: "CTO (hiring manager)"
type: "Hiring Manager"
date: 2026-03-19
---

# J.R. Jasperson — Hiring Manager — 2026-03-19
**Company:** [[Filevine]]

## Prep Notes

### Interviewer Background
J.R. Jasperson, CTO at Filevine since 2022. Based in Denver, CO.
Career path: DBA at AOL (8yr) -> Data Architect at GoDaddy -> Dir Enterprise Architecture / Chief Architect at SendGrid -> Chief Architect at Twilio (post-acquisition) -> Chief Architect at Coursera -> CTO at Filevine.
Signature work: Led SendGrid's full cloud-native rearchitecture — eliminated stateful components, decoupled for independent scaling, solved distributed queuing/deduplication at scale. O'Reilly talk: 'Rearchitecting for Cloud Native; Or, All We Changed Was Everything.'
Leadership style: Servant leader. Uses Kurt Lewin's force-field analysis — focuses on removing hindering forces rather than pushing positive motivators. Colleagues say: 'culture of deeper engineering excellence driven by thoughtful architectural vision.' Easy to work with, deep listener, thorough investigator.
### Context from Ryan CEO Call (Mar 18)
Ryan said 'I don't get called into too many of these — only when the team says we really, really want this person.' Multiple execs advocated for Greg. Ryan closed with 'we'd love to have you on board.' This means J.R. already likes you — this round is about technical depth and working relationship, not gatekeeping.
Ryan confirmed: ~50% microservices (deploy anytime), ~50% monolith (nightly deploys). He framed the core tension as 'innovation velocity vs reliability' and said he expects to interact with VP Reliability frequently, possibly daily. He's 'highly convinceable' but needs clear explanations.
Ryan was particularly struck by framing SRE as encompassing AI response reliability — accuracy, retrieval quality, graceful degradation. Asked about LLM failover when Claude goes down. This is clearly top-of-mind for the exec team.
### J.R.'s O'Reilly Talk — Key Insights
SendGrid context: 50B+ emails/month, 1B+/day, reached half of all email users on earth every 90 days.
Problems he solved:
- Unbounded failure domains from monolithic scale-up architecture -> bounded failure domains via bulkhead pattern (multiple mail pipelines vs one big pipeline)
- Width thrashing: MTA processes spending more time deciding what to do next than doing work, leading to death spirals -> fixed width via constrained pipelines
- Stateful compute tied to local spool storage (fault intolerant, can't scale independently) -> stateless compute with durable object storage (Ceph on-prem, S3 in AWS)
- Tight coupling between mail processors and MTAs -> decoupled via shared object store, independent scaling
- Push-based load balancing (least connections, causes hotspots) -> pull-based model (workers request work when ready)
- Dogpile data architecture (single logical DB, implicit latency assumptions) -> teased apart based on write-latency intolerance
His key phrases (mirror naturally):
- 'Bounded failure domains' (not blast radius)
- 'Width thrashing' (decision overhead exceeding work output)
- 'Parameters to constrain architectural decisions' (thinks in constraints, not open possibilities)
- 'Reconciling opposing considerations' (CFO wants margins, eng wants velocity, 'not everyone gets their cupcake')
- 'Dogpile data architecture' (his term for single-DB antipattern in fast-growing companies)
- 'Write-latency intolerance' (the hard constraint forcing Big Bang vs incremental migration)
- 'Build measure learn cycle' (agile, iterative, anti-Big Bang)
- 'Replacing an engine while the plane is in flight' (used unironically, this was his reality)
His leadership tells:
- Aligns stakeholders by making competing priorities explicit
- Pragmatic on lift-and-shift vs cloud-native: 'false dichotomy, depends on business drivers'
- Optimizes for velocity first, cost later: 'get stuff out to customers first, circle back and optimize'
- Thinks in transition plans, not end states: 'trails don't go straight up the mountain'
- Anti-Big Bang: 'we were not on-premise Tuesday and in Amazon on Wednesday'
Greg's bridges:
- Mobimeo: Two AWS environments post-merger, consolidation while keeping services running, teasing apart coupled systems, migrating incrementally. Same pattern as SendGrid rearchitecture.
- FCA: 40TB/day through ML pipelines. Data contracts, pipeline idempotency, exactly-once semantics. Maps to J.R.'s data migration concerns around write-latency intolerance.
- 1KOMMA5: Bounded failure domains via SLOs and error budgets. Pull-based developer platform (golden paths, self-service) vs push-based mandates. Same philosophy.
### Temporal Deep Dive
Filevine is a heavy Temporal user, building majority of workflows in it including LOIS agentic orchestration.
What it is: Durable execution platform. Workflows survive crashes, infrastructure failures, restarts via event-sourced deterministic replay. Guarantees exactly-once execution of workflow logic.
Core concepts:
- Workflows: stateful orchestration logic, deterministic, can run seconds to years
- Activities: individual tasks (API calls, LLM invocations, DB queries), may fail transiently, wrapped with retry policies
- Workers: processes that execute code, horizontally scalable, poll task queues for work
- Task Queues: lightweight, dynamically allocated, persist across worker failures
- Event History: immutable log of every action, enables deterministic replay on failure
The Agentic AI Pattern — Why Temporal Matters for LOIS:
An agentic system has two fundamentally different types of work:
1. Orchestration logic (deterministic): 'retrieve documents, summarize them, check summary against original, if confidence low retry, if three retries fail escalate to human.' Given the same inputs, the same decisions should happen. This is the Temporal workflow.
2. LLM calls (non-deterministic): 'here is a prompt and 50 pages of legal documents, give me a summary.' Same prompt can produce different outputs. Model might timeout, hallucinate, return garbage. These are Temporal activities.
Temporal enforces this separation architecturally. Workflows are replayed deterministically from event history — they cannot contain non-deterministic work. All LLM calls, tool invocations, and external API calls must be wrapped as activities.
What this gives you:
- Resumability: worker crashes after 3rd LLM call in a 5-step agent loop -> Temporal replays, sees steps 1-3 completed, picks up at step 4. No lost work, no duplicate LLM calls.
- Auditability: every LLM call, tool invocation, decision point recorded in event history. For legal: 'why did the AI flag this witness?' -> replay the exact sequence of document retrieval, prompting, response, comparison.
- Cost control: activities individually tracked -> see exactly how many LLM calls per workflow, tokens consumed, retries. At 20-30M pages/day, this prevents runaway API costs.
- Failure isolation: LLM timeout doesn't crash the workflow. Activity fails, Temporal retries with exponential backoff. Model down entirely -> workflow pauses durably, resumes when model returns. No data loss.
- Testing: replay workflows with mocked activities. Swap in deterministic fake LLM responses, verify orchestration logic independent of model behavior.
Analogy for J.R.: This is exactly what he did at SendGrid — separating stateful email processing from stateless compute, pulling state into durable storage so components could fail independently. Temporal does the same for agent systems: pulls state into durable event history so LLM calls can fail independently without losing the workflow.
### Competitive Landscape
Harvey AI ($11B valuation, $190M ARR) and Legora ($5.55B, March 2026) compete in BigLaw AI research/drafting. Filevine ($3B, ~$200M ARR, 6000 customers) competes in case management — different category. Ryan confirmed in bake-offs against AI-native competitors Filevine does 'incredibly well' because competitors lack platform depth. Filevine's moat: workflow data, daily usage, network effects from depositions. Direct competitors: Clio ($1B acquisition of vLex), Litify, MyCase, CloudLex.
### Open Questions for J.R.
These are unresolved from the Jonáš call, Ryan call, application research, and interview prep. Prioritized by importance.
### Role & Org Structure
- What does the reliability org look like today? Is there an existing team, or is this a build-from-scratch hire?
- What's the team size and hiring plan for the reliability org?
- Who carries the pager today? What does incident management look like?
- Does this role report directly to you?
- How does the VP Reliability role partner with Jonáš's ML teams day-to-day? Is it embedded, consultative, or shared-service?
- Ryan said he expects to interact with VP Reliability frequently, possibly daily. What does that relationship look like from your side?
### Technical Architecture
- Ryan said roughly 50/50 microservices vs monolith. What's the monolith stack? (.NET confirmed by Jonáš — what version, what DB, what hosting?)
- How are you thinking about the monolith decomposition timeline — multi-year migration or are there forcing functions?
- You led the SendGrid rearchitecture — what lessons from that are you applying to Filevine's transformation?
- What's the current observability stack? Datadog, Grafana, something else?
- Where are you in the Temporal adoption journey — everything on Temporal or mixed orchestration?
- What cloud provider(s)? AWS, Azure, GCP, hybrid?
- What does the CI/CD pipeline look like today? The nightly monolith deploy — is that automated or manual?
### Reliability & Scale
- What's the biggest reliability risk you're losing sleep over right now?
- 3B+ pages OCR'd/vectorized this quarter, 20-30M pages/day — where are the bottlenecks?
- Ryan asked about LLM failover when Claude goes down. Is there a multi-model strategy today, or is that aspirational?
- How do you think about SLOs/SLAs today? Are they formalized or informal?
- What does the on-call rotation look like? Is there follow-the-sun, or is it US-hours only?
### Platform & Culture
- How do you think about the balance between platform standardization and team autonomy?
- Ryan's philosophy is 'all problems are product problems.' How does that translate to how you run the eng org?
- What's the engineering culture around reliability — is it owned by a central team, or distributed across product teams?
- What compliance/security frameworks are in place? SOC 2, FedRAMP, CJIS? (Government customers: LAPD, DAs, public defenders)
### EU-Remote & Logistics
- Is EU-remote confirmed for this role? Jonáš and Pavlina are in Prague, but is there a preference for US-based?
- What are the core collaboration hours expected?
- Compensation — is this benchmarked to US or adjusted for location?
### Process
- What are the remaining interview steps after this conversation?
- Timeline to decision?

## Debrief

## Transcript / Raw Notes
