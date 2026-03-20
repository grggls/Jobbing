---
company: "Golem / Arkiv"
position: "Head of Platform - Arkiv"
status: "Done"
score: 74
date: 2026-01-26
url: "https://golem.network/careers"
focus: [Blockchain]
conclusion: "Withdrew before Round 2. B2B contract (not employment), no platform team, aggressive September mainnet deadline, and crypto market uncertainty made this a poor fit relative to stronger opportunities in pipeline. Two offers in hand (Acto, ReflexAI) at the time of withdrawal."

---

# Golem / Arkiv
**Position:** Head of Platform - Arkiv

**Score:** 74/100 · **Status:** Done · **Date:** 2026-01-26 · **Focus:** Blockchain

[Job Posting](https://golem.network/careers)

## Fit Assessment
Score: 74/100
Strong technical match on infrastructure stack (K8s, Terraform, Prometheus, ArgoCD, GitOps) and leadership scope (team building, SRE culture, vendor management). Seniority and scope align well. Main gaps: no blockchain/Web3 experience (JD says OK), mixed company signals (Glassdoor 3.0/5, ICO-funded, board friction). B2B contract rather than full-time employment adds uncertainty.
Green flags:
- Infrastructure stack maps directly: Kubernetes, Terraform, Prometheus, Grafana, ArgoCD
- SRE philosophy in JD matches Greg's operating model: SLOs, blameless postmortems, ownership culture
- Team-building mandate mirrors Mobimeo 8-to-23 trajectory
- Hands-on leadership explicitly required
- Remote-first, EU-based
- JD explicitly says blockchain experience not required
- Pre-mainnet timing means greenfield infrastructure decisions
Red flags:
- B2B contract, not full-time employment — discovered during Round 1
- No platform team hired yet — Greg would be first, with September mainnet deadline
- Glassdoor 3.0/5 with chaotic management and board friction in reviews
- ICO-funded ($8.6M in 2016), no subsequent VC — reliant on Foundation endowment in volatile crypto
- Scope extremely broad for one person: L3 infra, monitoring, website, Bridge UI, explorer, docs, partner pilots, AND team building
- Arkiv not a separate legal entity — governance ambiguity
- Existing Terraform from 3rd-party consultancy — takeover with unknown code quality
Gaps:
- No blockchain/Web3 infrastructure experience
- No Rust experience (part of tech stack)
- No Go experience (part of tech stack)
- No bare metal Kubernetes experience (listed as strong plus)
Keywords to weave in:
- blockchain infrastructure
- L3
- bridge operations
- node operations
- Web3
- Rust
- Go
- bare metal Kubernetes
- Blockscout

## Experience to Highlight
- At 1KOMMA5°, standardized on-call/incident response and introduced SLO practices across engineering — uptime improved from 95% to 99.9%, change failure rate dropped 90%
- Built Mobimeo's platform organization from 8 to 23 engineers spanning Platform, SRE, Security, and Data Engineering — direct experience standing up and scaling the exact function Arkiv needs
- Improved MTTR 50% at Mobimeo through documentation and operational discipline; governed €4M/year cloud spend + €1M/year SaaS tooling including vendor management
- At BuzzFeed, maintained 99.99% SLOs serving ~700,000 concurrent users; built "Rig," a homegrown Docker PaaS on ECS that scaled to hundreds of deployments per day
- Operated production Kubernetes platforms at Yara (multi-region EKS with Istio), 1KOMMA5° (GKE/Cloud Run), and Solo Recon (GKE with Crossplane and ArgoCD) — deep hands-on K8s across cloud providers
- At TradingScreen, managed latency-sensitive global trading infrastructure across 4 POPs connected to London, Tokyo, Singapore — systems where downtime has real financial consequences
- Implemented LaunchDarkly at Mobimeo for feature flags and canary deploys; built CI/CD golden paths at 1KOMMA5° using Backstage templates — progressive delivery and developer enablement
- Mentored 4 engineers into leadership roles at Mobimeo; structured hiring and onboarding practices that enabled scaling from startup-sized team to full org
- At Solo Recon, built and shipped a full-stack SaaS product end-to-end as sole engineer — demonstrates the hands-on technical depth this role demands
- Operated under Deutsche Bahn biannual audits (Mobimeo), FCA regulation (Cloudreach), and financial services compliance (JP Morgan) — experienced in high-stakes environments where production reliability is non-negotiable

## Job Description
**Head of Platform**
**About Arkiv**
Blockchain data is hard to use. Developers store data on-chain, then immediately need indexers, subgraphs, and custom infrastructure just to query it back. We think that's broken.
Arkiv is fixing it at the protocol layer - a blockchain with queryable storage built in. SQL queries against on-chain data, no external indexing required. It's a different architecture, and it doesn't exist anywhere else yet.
We're a small, focused team preparing for mainnet launch. If you want to run foundational Web3 infrastructure and own the experience developers have when they interact with Arkiv, this is the moment.
**The Role**
You might come from fintech, gaming, or high-scale SaaS — or you might already be deep in blockchain infrastructure. What matters is that you run systems where downtime has real consequences.
You will own everything that runs Arkiv in production and everything users interact with: L3 infrastructure, monitoring, the website, dashboards, Bridge UI, explorer, and developer onboarding.
**Developers, users, and partners are why we exist — their success is our success.**
This is a **hands-on leadership role**. You will build and own the infrastructure that keeps Arkiv running - and you'll own the surfaces where developers experience it: the explorer, the Bridge UI, the docs, the getting started guides. You'll debug production issues, design monitoring systems, and be on-call. You will also shape how we operate, mentor engineers, and help define what the platform team looks like as we grow.
**Our philosophy: We own production. When it breaks, we learn. Our goal is fewer pages, faster recovery, and systems that let us sleep.**
You collaborate closely with the CTO on reliability and infrastructure strategy, and with the Protocol team who builds what you operate. You lead a small team today, with a mandate to grow and shape it.
You'll also be the technical face of Arkiv for prospective partners — supporting pilots, answering integration questions, and making sure their first experience with Arkiv is excellent. For deep protocol questions, you'll pull in the CTO or Protocol team — but day-to-day partner enablement is yours.
**What You'll Own
**The Head of Platform will be responsible for several critical domains across the production environment and user-facing applications.
Domain Scope
**Who You Are**
**Character and drive matter more than your CV.**
- You are genuinely curious - but your curiosity has a specific flavor: you need to understand how things *fail*. Not just well enough to deploy, but well enough to debug when others normally sleep and make sure it doesn't happen again.
- You are hands-on. You've led teams, but you haven't stopped doing the work. You believe the best infrastructure leaders stay close to production. You can run a planning meeting, but you're equally comfortable in a terminal session during an incident.
- You are data-driven. SLOs, MTTR, incident frequency - you measure what matters and use data to prioritize. "I think it's reliable" isn't good enough; you want to know.
- You collaborate well. You're demanding and you have high standards - but you're also approachable, and hopefully humorous. People want to work with you, not just for you. You make the team better by being in it.
- You see beyond your lane. When something is broken or could be better, you notice - even if it's not strictly your responsibility. Production issues don't respect org charts, and neither do you.
- You have an inner drive to improve. The current state is never good enough. You're always looking for what's more reliable, more observable, more automated.
- You stay calm under pressure. Incidents happen. You set the tone: clear thinking, structured response, blameless postmortems that drive improvement.
- You've done this before. You have a track record running demanding production systems - ideally at scale, ideally with real consequences for downtime. You've grown engineers. You've been responsible for both the systems and the people operating them.

**What We Expect**
- **Stay hands-on:** This is not a "meetings and dashboards" role - you debug, deploy, and build
- **Own production:** Reliability is your responsibility; you set SLOs and hold the team to them
- **Lead by example:** Set the standard for operational excellence, quality, and collaboration
- **Mentor and grow:** Help engineers reach senior level; give direct, useful feedback
- **Partner with Protocol:** Work closely with the protocol team who builds what you operate - shared ownership of reliability and success
- **Shape the team:** Help define roles, hiring priorities, and team structure as we scale
**Technical Requirements**
We are looking for a leader with significant hands-on technical depth, as detailed in the table below.
**Strong Plus:**
- Track record in open source projects or significant internal platform/tooling work
- Incident commander experience
- Vendor/SLA management experience
- Experience with bare metal Kubernetes deployments or cost-optimized infrastructure setups

We know this list is demanding - covering all of it is rare. If you're a strong technical leader and most of these requirements resonate, we encourage you to apply.

**How We Work**
- **Ownership:** See a problem, own it - follow through or escalate.
- **Direct feedback:** We challenge ideas openly and say what we mean.
- **Ship fast, learn faster:** Simple solutions, quick iterations, mistakes are data.
- **Stay close to users:** Decisions grounded in real signals from customers and the larger Web3 community, not assumptions.

**Location & Compensation**
Remote first
Competitive salary, commensurate with experience
*Arkiv is building infrastructure for a more open internet. If this sounds like you, we'd love to talk.*

## Questions I Might Get Asked
- How would you approach taking over infrastructure from a third-party consultancy?
- How would you design a deployment pipeline for blockchain L3 nodes?
- Describe your observability philosophy.
- How do you think about the Platform-Protocol team boundary?
- You don't have blockchain experience. How would you ramp up?
- How would you prioritize with broad scope and a September deadline?
- Tell me about building a team from scratch.
- What's your incident response process?

## Conclusion
Withdrew before Round 2. B2B contract (not employment), no platform team, aggressive September mainnet deadline, and crypto market uncertainty made this a poor fit relative to stronger opportunities in pipeline. Two offers in hand (Acto, ReflexAI) at the time of withdrawal.
