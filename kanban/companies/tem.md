---
company: "tem"
position: "Senior Staff Engineer"
status: "In Progress (Interviewing)"
date: 2026-03-20
url: ""
environment: [Remote, Berlin]
salary: "€150K (Senior Staff) / €185K (Principal) + share options"
focus: [Energy, CleanTech, ML/AI, Distributed Systems]
score:
conclusion: ""
---

# tem
**Position:** Senior Staff Engineer · **Status:** In Progress (Interviewing)

## Documents

## Interviews

- [[2026-03-20-Luke-Victor|Luke Victor — Recruiter Screen · Passed · Vibe 4/5]]
- [[2026-03-23-Bhartich|Bhartich (CTO) — Hiring Manager · Pending · Vibe —]]

## Fit Assessment

## Experience to Highlight
-

## Company Research
- Series B: $75M (Feb 2026), led by Lightspeed. Total raised ~$94M. Valued at $300M+.
- Product: Tendering/pricing engine (core IP) that bypasses the wholesale energy market entirely. Uses ML to match buy side and sell side directly, predicting energy usage, weather patterns, and pricing based on actual cost of production. Automatic discounting balances buy/sell sides.
- Growth: Started 2025 with 35 people / 300 customers / £7M ARR target. Hit ARR target in March (9 months early). Ended 2025 with 85 people / 4,000 customers. Now ~110, planning 160–170.
- B2B only (commercial customers). Typically saves customers 30–40% on energy bills. Customers include Boohoo, Fever-Tree, Silverstone, Newcastle United FC.
- Expansion: Texas first (similar market structure, deregulated), then NE US, Australia, India, Germany.
- UK P442 regulation coming — affects matching requirements. Will add complexity to the engine.
- Originally tried to sell the pricing engine to incumbent utilities — none interested. Pivoted to building their own neo-utility front end (RED), went live 2024.
- Tech stack: Python, TypeScript, AWS serverless (Lambda, API Gateway, DynamoDB), microservices, event-driven architecture.
- Tendering engine team: 5 SWEs + 4 MLEs. Principal MLE already in place on modeling side. Hiring senior staff/principal engineer as systems/architecture counterpart.
- Fully remote, distributed across Europe. London HQ. EOR for international hires, always perm. Haven't hired in Germany before but willing.
- Comp: €150K Senior Staff / €185K Principal, plus share options. Equity structure TBD. (Per Luke Victor, recruiter screen 2026-03-20.)
- Interview process: Recruiter screen → CTO call (Bhartich, cofounder) → 2 technical stages (system design + hands-on discussion) → culture add with other cofounders.
- Glassdoor: Mostly positive — mission-driven, remote-first, good benefits. One pointed critique about leadership transparency. 3-stage interview rated 63.6% positive.
- Source: Inbound LinkedIn from Luke Victor (Talent Lead) 2026-03-12. Recruiter screen 2026-03-20.

### Luke Victor Call Notes (2026-03-20)

Recruiter screen. Luke gave a detailed company overview — tem built a tendering/pricing engine (core IP) that bypasses the wholesale energy market, matching buy side and sell side directly using ML predictions. Started 2025 with 35 people and 300 customers, hit their £7M ARR target in March (was supposed to be EOY), ended year with 85 people and 4,000 customers. Now ~110, planning to grow to 160–170.

The Senior Staff role sits on the tendering engine team: 5 SWEs + 4 MLEs. There's already a Principal MLE on the modeling side — they want a senior staff/principal engineer as the counterpart on the systems/architecture side. Core challenges: scaling for 10K+ new customers, international expansion (Texas first, then NE US, Australia, India, Germany), hedging correctness, forecasting accuracy, automated pricing/discounting, and upcoming UK P442 regulation (matching requirements).

Comp: €150K for Senior Staff, €185K for Principal, plus share options. Always perm, EOR for international hires. Haven't hired in Germany before but willing. I flagged the Scheinselbständigkeit risk early and they confirmed they do EOR, not contractor arrangements.

Luke was personable, knowledgeable about the product, and moved quickly. Good energy.

**Questions they asked:** Current work situation; what I'm looking for; walk through recent projects (Solo Recon, Modern Electric, 1KOMMA5°); based in Germany?; availability to start; salary expectations.

**Questions I asked:** Engineering challenges coming down the pike; growth story and team evolution for Texas expansion; have you hired in Germany before (flagged Scheinselbständigkeit risk); interview process overview.

**Next step:** CTO call with Bhartich (cofounder) — Monday Mar 23, 10:00 GMT / 11:00 CET.

## Job Description
Inbound recruiter outreach from Luke Victor (Talent Lead). Two Senior Staff Engineer roles: (1) scaling distributed pricing & transaction platform (Rosso), (2) building production foundations for AI agents automating real-world energy workflows. Tech: stateful distributed systems, serverless AWS, event-driven architectures, ML/LLM integration. Strong influence across engineering and product. Series B ($75M, Feb 2026), ~90 people, fully remote, London HQ.

## Outreach Contacts
-

## Questions I Might Get Asked
- Walk me through how you'd approach scaling a stateful distributed system for international expansion
- How have you collaborated with ML/data science teams? What does a good interface between ML pipelines and application code look like?
- Tell me about a time you inherited a system that needed to scale 10x — what did you do?
- How do you think about failure modes in financial/transactional systems?
- What's your approach to observability and incident response in serverless architectures?
- Describe your experience with event-driven architectures — what patterns work, what doesn't?
- How do you balance architectural purity with startup speed?
- What drew you to the energy sector?

## Questions to Ask

### For Bhartich (CTO) — Monday Mar 23

- What's your technical vision for the tendering engine over the next 12–18 months?
- How tightly coupled is the ML pipeline to the transaction engine? What does the interface between the two look like?
- What's the biggest scaling bottleneck right now — compute, data, architecture, or organizational?
- When a forecast is wrong and you're exposed on a hedge, what happens? How mature is that failure mode handling?
- What does deployment look like — release cadence, observability, incident response maturity?
- What does success in this role look like at 6 months?
- How do you see the Senior Staff role's authority — can they make architectural decisions, or is that consensus-driven?
- With Texas expansion, are you rebuilding for ERCOT or adapting the UK engine? How different are the market mechanics?
- What's the equity structure like — option pool size, vesting, strike price relative to the Series B valuation?
- How do you and the other cofounders divide technical leadership?

### Already Answered by Luke

- ~~Which of the two roles is more urgent?~~ → Role is on tendering engine team (5 SWEs + 4 MLEs)
- ~~Comp range?~~ → €150K Senior Staff / €185K Principal + share options
- ~~Hired in Germany before?~~ → No, but willing via EOR. Always perm.
- ~~Interview process?~~ → CTO call → 2 technical stages (system design + hands-on) → culture add with cofounders
- ~~Australia and Texas expansion?~~ → Texas first (similar market), then NE US, Australia, India, Germany

## Conclusion
