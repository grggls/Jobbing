---
company: "Filevine"
interviewer: "Jonáš Kratochvíl"
role: "VP, Machine Learning & AI Initiatives"
type: "Phone Screen"
date: 2026-03-14
---

# Jonáš Kratochvíl — Phone Screen — 2026-03-14
**Company:** [[Filevine]]

## Prep Notes

### Interviewer Background
Jonáš Kratochvíl — VP, Machine Learning & AI Initiatives at Filevine (May 2025–present, Prague, hybrid). Before Filevine, spent ~6 years at Parrot: IC ML Engineer → ML Lead → Manager of ML. Academic background in AI (Charles University, Master's in Artificial Intelligence) and Economics (Charles University, Bachelor's). Published NLP research — co-authored "Large Corpus of Czech Parliament Plenary Hearings" (ACL 2020) on building a 1200-hour speech corpus for ASR training. Also contributed to the ELITR (European Live Translator) project for simultaneous conference subtitling. Did speech recognition engineering at Charles University and interned at the US Embassy in Prague early career.
At Filevine, he's a peer VP and one of the key faces of LOIS (Legal Operating Intelligence System). Featured alongside CEO Ryan Anderson in the MedChron product announcement (June 2025) — an AI tool that automates medical chronology generation for injury cases. His team builds the AI features that the reliability org needs to keep running in production.
What he cares about: Building AI products with real-world legal domain impact. Model accuracy and reliability for high-stakes use cases (lawyers making case decisions based on AI output). Growing an ML org from IC-heavy to structured engineering function. He came up through the IC track — he'll respect technical depth.
Connection points:
- Both EU-based, working for US companies remotely — shared timezone reality. He's in Prague, you'd be in Berlin. His presence as a peer VP in Europe is a strong signal that global remote works at the VP level.
- His NLP/speech recognition background → your AtFarm satellite imagery ML infra at Yara, your 40TB/day EMR/Spark ML pipeline at FCA/Cloudreach. Different domains, same pattern: ML workloads with real-world consequences where reliability matters.
- He's building AI features that need robust infrastructure — you'd be the person making sure his models stay up in production.
- Both have academic research backgrounds (your Milan industrial research thesis on reconfigurable manufacturing, his Prague AI/speech recognition research).
### What This Call Is
Informal/exploratory peer chat, not a formal interview. Jonas reached out proactively after your LinkedIn message. He'll be assessing three things:
1. "Do I want this person as my infrastructure partner?" — Can you talk about AI workload reliability without hand-waving?
2. "Will this person slow us down or speed us up?" — He ships AI features fast and needs infra that enables, not gates.
3. "Is this person a cultural fit for distributed leadership?" — He's in Prague, you'd be in Berlin, reliability team is presumably US-based.
### Company Context
Filevine is a Legal AI company ($400M raised in 2025, ~$3B valuation, ~790 employees, ~6,000 customers). Their core AI product is LOIS (Legal Operating Intelligence System) — a RAG-based system where legal documents get embedded into a vector database, lawyers ask questions, and the system retrieves relevant chunks and generates answers with source citations. MedChron automates medical chronology generation. They acquired Pincites (AI contract redlining in Word) in Dec 2025. Compliance requirements include FedRAMP, SOC 2, CJIS, ISO.
Glassdoor warning: 2.8/5, 44% recommend, culture 2.4/5. Consistent reports of toxic culture, micromanagement, high turnover, burnout. Use this call to gauge Jonas's own experience — he joined May 2025, so he has ~10 months of direct observation.
### Likely Topics
"What do you know about Filevine / what interests you?"
Lead with the reliability transformation mandate — the posting describes shifting from bottleneck to force multiplier, which is exactly what you did at 1KOMMA5° and Mobimeo. Mention the AI-native architecture angle — supporting ML workloads at scale in a regulated environment (FedRAMP, SOC 2, CJIS) is a problem that interests you.
"What's your experience supporting ML/AI workloads in production?"
Two stories:
- Cloudreach/FCA: Led 10-12 engineers building an AWS data platform ingesting 40TB/day through EMR/Spark ML jobs for the UK Financial Conduct Authority. Data pipeline reliability at that volume — job failure handling, data integrity, throughput SLOs, audit requirements. Security controls so strong they couldn't bring their own laptops into the building.
- Yara Digital Farming: Kubernetes platform supporting AtFarm satellite imagery product — ML for crop health analysis via light refraction. Multi-region clusters (Germany, Singapore, Brazil), Istio service mesh. Reliability for a product where farmers made real decisions based on model output.
- Then be honest: "I haven't run model serving or vector search at Filevine's scale. What I bring is the operational discipline — SLOs, capacity planning, incident response, pipeline idempotency — and I'd learn the AI-specific domain from your team and the SRE leads."
"How do you think about the platform-ML team relationship?"
- I built self-service golden paths so product teams (including data teams) could deploy without platform bottleneck. The shift from "platform does it for you" to "platform enables you to do it yourself." Backstage golden paths came with observability baked in. Teams adopted SLOs not because you mandated it, but because the tooling made it obvious. "I try to be pragmatic, not dogmatic. At the end of the day, every engineer wants to do good work and ship good code.
- Team Topologies (Skelton & Pais) — The canonical model. Platform teams exist to reduce cognitive load on stream-aligned teams. For ML, that means the platform provides feature stores, model registries, experiment tracking, and inference serving as self-service products. ML teams own model lifecycle end-to-end; platform teams own the abstractions underneath. The decision criterion for what to centralize vs. delegate is always cognitive load — not organizational convenience.
- Platform-as-product — The 2024-2025 shift. Netflix, Stripe, Airbnb, DoorDash all evolved from "platform team runs infrastructure" to "platform team builds products for ML engineers." Stripe's Shepherd (feature platform adapted from Chronon) lets fraud teams ship models with 200+ features in weeks instead of months. Netflix's Metaflow provides configurable orchestration supporting hundreds of production models. The pattern: assign a product manager to the platform, run user research with ML engineers, measure adoption and satisfaction — not just uptime.
- Golden paths for ML — Spotify's golden paths / Netflix's paved roads, applied to model lifecycle. Opinionated, tested routes from experiment to production. Teams can deviate, but most follow the path. The benefit: eliminates debates about tooling, reduces time-to-production, and makes observability automatic (because it's baked into the path).
- Google's MLOps maturity model — Level 0 (manual notebooks), Level 1 (automated training pipelines), Level 2 (CI/CD for models with drift monitoring and rollback). Most orgs are stuck at Level 0-1. Getting to Level 2 requires dedicated platform investment — which is exactly the role Jonas is hiring for.
- The abstraction layer that matters — Feature stores (offline/online separation eliminates training-serving skew), model registries (MLflow as de facto standard — versioning, lineage, approval workflows), and managed inference serving (Ray Serve, Triton — so ML teams don't manage Kubernetes). Platform teams own infrastructure; ML teams consume via SDKs and APIs.
- Outcomes companies report: Airbnb cut model dev time from 8-12 weeks to 3-5 days. Stripe blocks $10M+/year in fraud through platform-enabled rapid model iteration. Vannevar Labs cut inference costs 45% with Ray + Karpenter abstraction. DORA's 2024 report found mature platforms amplify AI's positive effect on performance — immature platforms amplify dysfunction.
"How do you balance speed vs. reliability?"
Error budgets. When the budget is healthy, ship fast. When it's burned, fix reliability. Turns it into a data-driven conversation, not a political one. Jonas will resonate — his team ships AI features fast and doesn't want infra blocking releases. Also mention LaunchDarkly at Mobimeo — feature flags and canary deploys to decouple deployment from release.
### Talking Points
1KOMMA5° reliability transformation:
No SLOs, no real on-call discipline, 95% uptime at best — no real measurement either. Lots of angry customer calls. Mapped the org and tech — communication paths between branches, customer support, IT, engineering, management. Defined SLOs around customer-facing actions (not server health), introduced error budgets, designed on-call so a single engineer could cover all systems. Was incident commander and ran blameless postmortems personally for 6 months. Built a culture of autonomy, trust, and quality. Result: 99.9% uptime, deploy frequency +350%, change failure rate -90%.
Mobimeo platform consolidation:
Merger during pandemic doubled the engineering org — twice as many customers, systems, services, AWS accounts. CTO said fix the platform first. Mapped everything: people, processes, platforms. Ran two exercises — migrate onto theirs? Theirs onto ours? Both revealed tremendous tech debt. Chose a third path: greenfield platform, best from each side, all teams onboarded equitably. Three phases via RFC/ADR. 75 services integrated with zero downtime. Observability consolidated from fragmented Datadog/Prometheus/New Relic onto Prometheus, Grafana, Loki, Jaeger. OpenTelemetry tracing — every request got a trace ID at the API gateway. Eliminated €1M/year New Relic contract.
Developer empowerment, not gatekeeping:
"I moved from a bottleneck model to a force multiplier model. Platform provides guardrails and self-service, teams operate their own services." This is exactly what the posting describes and what Jonas needs from a reliability VP.
Compliance without slowing down:
SOC 2, FCA, Deutsche Bahn audits — all while maintaining delivery velocity. For Jonas: "I won't let FedRAMP/CJIS compliance become a reason your team can't ship."
### AI/ML Reliability — Concept Reference
These are the AI-specific reliability concepts most likely to come up. You don't need to be an expert — you need to ask the right questions and show you understand the problem space.
What LOIS is under the hood (educated guess from public sources):
A RAG (Retrieval-Augmented Generation) system. Legal documents go in → get converted to embeddings (numerical representations) → stored in a vector database. When a lawyer asks a question → question gets embedded → vector database finds the most similar document chunks → those chunks plus the question get sent to an LLM → LLM generates an answer with source citations. Intent-aware routing directs different query types (summarizing depositions, extracting facts, calculating deadlines) to different AI capabilities within LOIS.
Model serving reliability:
Model serving = running ML models in production to handle real-time inference requests. The reliability concerns: latency SLOs for inference (lawyers waiting for answers — if LOIS takes 30 seconds, they go back to manual), GPU capacity planning (inference is compute-intensive and bursty), fallback behavior when models are slow or down, and autoscaling for variable load.
Vector database and embedding index management:
A vector database stores embeddings — numerical representations of text. When new documents are added (case files, medical records), they need to be embedded and indexed. If the index gets stale (documents added but not indexed), lawyers get incomplete results. If the embedding model changes (upgrading to a better model), you may need to re-embed the entire corpus — potentially millions of documents. Keeping the vector index in sync with the source of truth is a data pipeline reliability problem. Key terms: index consistency (derived data store stays in sync with source), index rebuild (re-embedding entire corpus after model change), embedding drift (quality degradation over time).
Retrieval quality:
How good is the vector search at finding the right documents? Measured by precision (of documents returned, how many are relevant?) and recall (of all relevant documents, how many did we find?). Poor retrieval quality = LLM generates answers based on wrong context = wrong legal advice = malpractice risk. This is a data integrity problem, not a model problem. The reliability org owns the infrastructure that affects it — index freshness, database performance, embedding pipeline health.
Eval pipeline:
Automated testing of model output quality — like CI/CD for models. A set of test cases (input/expected output pairs), a runner that sends inputs to the model and collects outputs, a scoring function, and a gating layer that passes or fails the deployment. The platform team builds the pipeline infrastructure; the ML team defines test cases and scoring criteria. Continuous evals against production catch drift — models can degrade silently when a provider updates their model, the RAG index gets stale, or a prompt change has side effects.
Model deployment gating:
The mechanism deciding whether a new model version goes to production. Simplest: manual approval after reviewing eval results. Better: automated — eval pipeline runs, scores exceed threshold, deployment proceeds. Best: canary deployment for models — route 5% of traffic to new model, compare output quality against baseline, promote or rollback. This is LaunchDarkly for models.
AI-specific failure modes:
- Model timeouts and latency spikes: LLM inference is inherently variable. Simple query = 500ms, complex one = 30 seconds. External API calls (OpenAI, Anthropic) subject to their capacity/rate limits.
- Hallucination spikes: Model confidently returns wrong information. For legal, existential risk. Rates change when models are updated, retrieval quality degrades, or edge-case inputs hit the system.
- Context window limits: LLMs have max input size. A 500-page medical record can't fit in one call — needs chunking, and wrong chunking means missed information.
- Rate limits: External LLM APIs have requests-per-minute ceilings. Hit the limit and queries queue or fail.
- Cascade failures: If AI layer goes down, does the platform still work? Graceful degradation means lawyers can still access cases/documents/workflows without AI features.
Inference latency SLOs:
Same concept as any SLO, applied to model inference. "P95 inference latency for LOIS queries under 3 seconds." Tricky because latency depends on input length (more tokens = slower), model load, and external API variability. May need different SLOs for different query types.
Data pipeline idempotency:
If a document ingestion job runs twice (retry, crash recovery, duplicate event), result should be same as running once. Document appears once in vector index, not twice. Without idempotency: duplicate embeddings, corrupted search results, inflated storage. Standard data engineering — exactly-once semantics, deduplication keys, transactional writes. Maps directly to your FCA experience: 40TB/day through EMR/Spark.
Graceful degradation:
What happens when the AI layer fails. Can lawyers still access cases, documents, workflows? Or is LOIS a hard dependency? Design principle: AI features enhance the platform but shouldn't be a single point of failure. Circuit breakers, fallback paths, cached results.
AI cost management:
Three models: API-based (pay per token to OpenAI/Anthropic — simple, scales linearly, dependent on third party), self-hosted (own GPUs — higher upfront, lower marginal cost at scale, requires ML ops), hybrid (self-hosted for high-volume, API for experimental). Inference costs can surprise — a feature calling the LLM 3x per action at $0.05/call across 100K daily users = $15K/day. Traditional FinOps applies but unit is tokens, not instances.
### Strongest Framing for AI Reliability
"I haven't run model serving or vector search at Filevine's scale. What I have is 20 years of making production systems reliable under pressure — SLOs, error budgets, capacity planning, incident response. At Cloudreach I ran 40TB/day through ML pipelines for the FCA. At Yara I ran Kubernetes infrastructure supporting ML workloads for satellite imagery. The reliability principles are the same: pipeline idempotency, inference latency SLOs, graceful degradation when models fail, and observability that tells you when output quality is drifting — not just when a server is down. The domain specifics — vector database tuning, embedding index management, eval pipeline design — I'd learn from your team and the SRE leads. What I bring is the operational discipline and the org structure to make it all run reliably."
### Questions to Ask Jonas
1. What does your ML team's infrastructure look like today — model serving on EKS, managed services, or something else?
2. What's the biggest reliability pain point for the ML/AI team right now — model serving latency, data pipeline failures, deployment speed?
3. How does your team interact with the current reliability/platform org? Is there friction, or does it work well?
4. You're in Prague, the reliability team is presumably mostly US-based — how does the remote/distributed model work day-to-day for engineering leadership?
5. What does LOIS look like under the hood — vector databases, RAG pipelines, fine-tuned models, API orchestration?
6. How do you gate model deployments? Is there an eval pipeline, or is that more manual today?
7. What would you want from an ideal VP of Reliability as your infrastructure partner?
8. How is AI workload reliability handled today — dedicated ML infra team, or does the reliability org own that?
### Why Looking / Why Leave (if it comes up)
Solo Recon was a deliberate bet — wanted to go deep on hands-on engineering after several years of management. Built and shipped a full product solo in 6 months. Was finding product-market fit, then OpenAI released Aardvark (agentic cybersecurity) and Anthropic followed with Claude Code Security. Wound it down. "I learned a lot, proved I can still build, and now I want to apply that depth at an organization with real scale and real customers."
### First 90 Days (if it comes up)
First 30 days: listen and map. Understand how teams ship today, incident history, observability state, pain points, where the team's time goes. Meet every team that depends on platform. Read the postmortems. Weeks 4-8: identify highest-leverage gap — usually observability, deployment safety, or on-call burden. Identify toil. Pick one high-leverage project and ship a visible improvement. Weeks 8-12: propose a roadmap to engineering leadership with clear outcomes, not just projects. Earn trust through delivery before proposing big changes.

## Debrief

## Transcript / Raw Notes
