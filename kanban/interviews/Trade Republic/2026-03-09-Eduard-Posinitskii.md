---
company: "Trade Republic"
interviewer: "Eduard Posinitskii"
role: "Staff Engineer, Application Platform"
date: 2026-03-09
vibe: 4
outcome: "Pending"
---

# Eduard Posinitskii — 2026-03-09
**Company:** [[Trade Republic]] · **Outcome:** Pending · **Vibe:** 4/5

## Prep Notes

## Debrief

### What Landed
- Observability migration story resonated strongly. Ed jumped in to supply "Mimir" when I was trying to remember the name — clearly a lived experience for him.
- Honesty about Cloud Run: "I wouldn't make that choice again" — delivered results and still formed a critical opinion. Staff-level judgment.
- TerraMate critique — called out unnecessary complexity from consultants building a product on our infra.
- Cross-account merger story at Mobimeo — directly relevant to Cloud Platform's networking responsibilities.
- BuzzFeed ECS platform story as a programming answer — pivoted to platform-as-a-service building, which is what they do.
### What Stumbled
- Programming question: "not much experience building apps" is honest but could be a flag. If next round expects Go or Kotlin live coding, that's a gap. But Ed said no coding challenges.
- Ran out of time — didn't get to ask about performance reviews (Glassdoor red flag), what drew Ed from DoubleCloud, or biggest reliability challenge.
### What You Learned
- Ed is on Application Platform, NOT Cloud Platform. Screening for a peer role on a sister team.
- 4 teams in Platform Engineering: Application Platform (messaging, runtime, secrets), Cloud Platform (networking, observability, incident mgmt), DevEx (CI/CD, code delivery, AI tools), Core (libraries, SDKs, gateways, auth)
- ~30+ people total in Platform Engineering, 8-10 per team. Cloud Platform is ~7-8.
- Total headcount ~300+ (Ed said "a bit over 300"), not 600 or 1,325.
- Cloud Platform's three branches: IAM integration (AWS IAM, Teleport, Okta), Networking (VPNs, BGPs, cross-account/cross-cloud), Observability (LGTM stack).
- K8s networking is Application Platform, not Cloud Platform. Cloud Platform handles VPCs/VPNs/external.
- Victoria Metrics also in use alongside Mimir/Prometheus — new info.
- Observability ingestion: couple TB/day with ongoing queuing/ingestion challenges.
- On-call: L1 (business hours) + L2 (24/7 pager), different engineers same week. Recently split back to per-team.
- ArgoCD AND FluxCD both in use. GitHub Actions for CI.
- No coding challenge. Next round is technical with team + management.
- Culture: speed is #1 priority. "Not a typical German company, more like US." Platform shields teams from catastrophic failures.
### Updated Read
Role is clearer: Cloud Platform owns networking, IAM integration, and observability. Strong match for Mobimeo experience. Programming question is the one watch item. No reassessment needed — fit is what we thought, possibly stronger given confirmed observability challenges at TB/day scale.
### Questions They Asked
- Tell me about your past experience
- Elaborate on 1KOMMA5° — cloud provider, stack, main challenges, what was the platform?
- Cross-account or cross-cloud networking experience?
- Observability experience — setting up the stack, challenges of high volume?
- Development experience — languages, scripting vs building apps?
### Questions I Asked
- What does the Cloud Platform team look like — how many engineers, engagement model?
- On-call structure?
- Cloud Platform interaction with security and compliance?
- How does 'Amp it Up' / 'Every Day is Day One' translate to infrastructure work?
- Specific CI/CD tooling?
### Follow-Up
Next round: technical interview with the team + management. No coding challenge. Wait for Ed's feedback via Elizaveta.

## Transcript / Raw Notes
