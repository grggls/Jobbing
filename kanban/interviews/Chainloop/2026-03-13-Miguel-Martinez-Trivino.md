---
company: "Chainloop"
interviewer: "Miguel Martinez Trivino"
role: "Co-Founder & CTO"
type: "Hiring Manager"
date: 2026-03-13
---

# Miguel Martinez Trivino — Hiring Manager — 2026-03-13
**Company:** [[Chainloop]]

## Prep Notes

### Interviewer Background
Miguel Martinez Trivino — Co-Founder & CTO, Chainloop (Dec 2022–present)
Based in Seville, Spain. Remote. BS Computer Science, Universidad de Sevilla. Y Combinator W11.
Serial co-founder and deep Go/Kubernetes engineer. Started with Beecoder (web dev agency, Seville, 2009–2011), then co-founded Beetailer (YC W11, e-commerce SaaS on Rails, 10K customers, 70M end users, 2011–2014). Joined Bitnami in 2014 as Senior Software Engineer — led Kubeapps, Monocular (engine behind Helm Hub), and was a founding member of the Helm 2 core team. Rose to Team Lead, then Staff Engineer at VMware Tanzu (2019–2022) where he designed and operated the secure software supply chain powering the Bitnami Catalog — thousands of container images, VMs, and K8s manifests built, tested, and released daily. This is where the Chainloop idea was born.
Technical identity: Go is his primary language. Kubernetes-native. CKA certified (2017). Open source DNA — Helm, Kubeapps, Chainloop itself (Apache 2.0). Technical CTO who writes code and designs systems.
Current focus: Recent LinkedIn posts emphasize "AI Factory Governance" and "agentic policies and workflows." Chainloop shipped a release with agentic policy support, new UI/UX, and security features. He and Daniel Liszka (CEO) are doing an NYC/SF roadshow Mar 16–26 (RSAC, BSidesSF, Chainguard's Assemble). Company is actively pivoting messaging toward AI-generated code governance.
Connection points:
- Both have founding experience — he'll respect the Solo Recon story
- He built the supply chain; Greg has been the buyer/operator of supply chain tooling. Complementary perspectives.
- Both deeply Kubernetes-native (CKA vs production EKS/GKE)
- Both value async-first remote work
- He coached engineers at Bitnami (iteration planning, code reviews, design docs, postmortems) — knows what good engineering management looks like
- Bitnami→VMware acquisition arc parallels Greg's Mobimeo/Deutsche Bahn merger experience
- His YC experience (W11 with Beetailer) was consumer SaaS — Chainloop is his deep-tech bet. He'll appreciate that Greg chose to build Solo Recon rather than just manage.
### Supply Chain Security — Domain Primer
Modern software is mostly assembled, not written. A typical application pulls in hundreds of open-source dependencies, runs through CI/CD pipelines, produces container images, and deploys to production. At every step, someone could tamper with the code, inject malicious dependencies, or compromise the build environment. SolarWinds (2020) and Log4Shell (2021) made this a board-level concern.
Key concepts:
- SBOM (Software Bill of Materials): Machine-readable inventory of every component in a piece of software. Two standards: SPDX (Linux Foundation) and CycloneDX (OWASP). Regulatory frameworks (US EO 14028, EU Cyber Resilience Act) are starting to require SBOMs.
- Attestation: A signed statement that says "X happened during the build process." Uses in-toto format — JSON envelope with subject (what you're attesting about), predicate (what you're claiming), and signature (who's claiming it).
- Provenance: Chain of evidence showing where software came from and how it was built. SLSA defines four levels of maturity.
- SLSA (Supply-chain Levels for Software Artifacts): Google-led framework defining increasing levels of build integrity. Level 1 = documented build; Level 2 = hosted build service; Level 3 = hardened builds with provenance. Most orgs at Level 1-2.
- Signing: Cryptographically signing artifacts so consumers can verify they haven't been tampered with. Sigstore makes this easier with keyless signing via OIDC. Cosign = CLI tool; Fulcio = certificate authority; Rekor = transparency log.
- Policy engines: Rules that say "this artifact can't be deployed unless it has a valid signature, an SBOM, no critical CVEs, and was built on an approved CI system." OPA and Kyverno are common tools. Chainloop uses Rego (OPA's language).
- VEX (Vulnerability Exploitability eXchange): Format for communicating whether a known CVE actually affects a specific product. Reduces alert fatigue.
The workflow: Code committed → CI pipeline runs → SBOM generated (Syft/Trivy) → artifacts built and signed (Cosign/Sigstore) → attestations created → policies check requirements → artifacts deployed. Chainloop sits at the orchestration layer.
### Chainloop Workflow Contracts and Attestation Layer — ELI5
Workflow Contract: A checklist that your security team writes for your CI/CD pipeline. It says: "Before you can ship this software, your build must produce: (a) a container image, (b) an SBOM, (c) a SARIF scan result, and (d) a signature. And it must run on GitHub Actions, not someone's laptop." Written in YAML/JSON/CUE. The Chainloop CLI guides developers through it: initialize, add evidence, push. If something's missing, the push fails. Pre-flight checklist for software releases.
Attestation Layer: The signed record of everything that happened. Like a notarized receipt: "On March 11, 2026, CI pipeline #4821 built container image sha256:abc123 from commit def456, produced SBOM xyz789, scanned with Trivy (0 critical CVEs), and signed with Cosign keyless." Immutable, tamper-proof, stored in Chainloop's evidence store. When auditors ask "how do you know this image is safe?" — point at the attestation.
The "layer" means it sits on top of existing CI/CD without replacing it. GitHub Actions, GitLab CI, Azure DevOps, Jenkins — Chainloop doesn't care. It collects evidence and enforces policies in one place.
### Competitive Landscape
Commercial competitors:
- Xygeni — Software supply chain security / ASPM platform
- OX Security — Active ASPM: application security, SBOM management, policy enforcement
- Chainguard — Hardened container images and Sigstore-based signing infra. Adjacent, not direct competitor. Chainloop integrates with their ecosystem.
- Snyk — Broader AppSec platform with SBOM capabilities
- Kusari — Supply chain security, builds GUAC (Graph for Understanding Artifact Composition)
- TestifySec — Builds Witness, an attestation framework
Open source alternatives / adjacent:
- Sigstore (Cosign, Fulcio, Rekor) — Keyless signing/transparency log. Chainloop uses Sigstore; it's a layer below.
- in-toto — Framework for supply chain attestations. Chainloop builds on top of in-toto format.
- SLSA — Google-led security level framework. Chainloop helps achieve SLSA compliance.
- Witness (TestifySec) — Open-source attestation framework. Closest OSS alternative to Chainloop's core.
- GUAC (Google/Kusari) — Software supply chain knowledge graph. Overlaps with evidence graph concept.
- Dependency-Track (OWASP) — SBOM analysis and vulnerability monitoring. Chainloop sends SBOMs to it.
- Syft/Grype (Anchore) — SBOM generation and vulnerability scanning. Feed into Chainloop.
Chainloop's positioning: Not competing with Sigstore, in-toto, or SLSA — it's the orchestration and governance layer on top of them. Competes with the manual glue scripts teams write to wire these standards together, and with commercial platforms like OX Security and Xygeni.
### FDE Feedback Loop — Explained
The JD describes the EM as "the glue that connects our Core, Frontend, and Forward Deployed functions." FDEs (Forward Deployed Engineers) work directly with customers — deploying, integrating, customizing. They hear customer pain points firsthand: "this policy doesn't cover our use case," "the attestation CLI is clunky for Azure DevOps."
The FDE feedback loop is how those customer-facing insights flow back to the Core product team. In a 5-person startup this is probably informal today. The EM's job: make it systematic — ensure FDE learnings become backlog items, product improvements, or documentation, not just one-off fixes. The risk in any FDE model is customer work diverging from the product roadmap (custom integrations that never get generalized). The EM prevents that.
The JD says "occasional flexibility with your schedule" — this is about timezone flexibility, not travel. FDEs handle customer-facing work. Worth asking Miguel: "How much customer-facing or travel time should I expect?"
### Likely Questions
"Tell me about yourself / walk me through your career"
Open with the connecting thread: platforms, developer tooling, and reliability. Hit Solo Recon (founding, hands-on, cybersecurity/supply chain adjacency), 1KOMMA5° (IDP, SOC 2, player-coach with 7 engineers), Mobimeo (scaled 8→23, owned security function, Deutsche Bahn audits). Close with: "I've been the buyer of supply chain security tooling for years — I know the pain points your customers have." Keep it under 3 minutes.
"Why Chainloop? Why this role?"
The honest story: you've been on the operator side of the problem Chainloop solves. SBOM pipelines, provenance tracking, policy guardrails, audit evidence — you've built and maintained this at Mobimeo (Deutsche Bahn audits) and 1KOMMA5° (SOC 2). The founding EM role is the intersection of what you do best: hands-on technical depth + building small teams. The AI governance angle is where the market is going — you saw it firsthand building an AI-native product at Solo Recon.
"How would you approach the first 30/60/90 days?"
First 30: ship something hands-on. Earn technical respect. Meet every engineer 1:1. Understand delivery rhythm, pain points, on-call. Map the Go backend and attestation pipeline. Days 30–60: establish lightweight process. Start hiring pipeline for the first 2 roles. Identify highest-leverage eng investment. Days 60–90: own engineering execution end-to-end. Propose delivery rhythm and roadmap cadence to Miguel. Have 2 hires in pipeline or closed. Reference the 1KOMMA5° story — walked in, mapped the org and tech, defined SLOs, shipped visible improvements, earned trust before proposing big changes.
"Your Go experience — how deep is it?"
Be honest: Go isn't your primary language. Python and TypeScript are. But you've read and debugged Go codebases, understand the ecosystem (modules, goroutines, interfaces, testing patterns), and operated Go-based infrastructure (ArgoCD, Helm controllers, K8s operators). At this level, the value is architecture, code review, and unblocking — not writing features solo. Deep K8s/CI/CD/supply-chain context means you understand the domain the code operates in. Don't oversell. He's a Go purist (Helm core, Kubeapps, Chainloop — all Go). Frame it as a weeks-not-months ramp.
"Tell me about a time you were a player-coach"
1KOMMA5°: 7 engineers, stayed hands-on with architecture decisions, production debugging (TypeScript/Node.js), designed CI/CD golden paths in Backstage. Reserved 2–3 days/week for technical work. Paired with engineers on complex problems rather than taking over. At Chainloop's size (~5 engineers), you'd be deeply technical — that's the sweet spot. Mobimeo taught where player-coach breaks down (~12-15 directs).
"How do you manage remote, async-first teams?"
BuzzFeed (3.5 years remote), Mobimeo and 1KOMMA5° (distributed time zones), Yara (Germany, Singapore, Brazil). Practices: strong written communication (RFCs, ADRs, async standup updates), clear ownership, protected focus time, minimal sync meetings, 1:1s as primary relationship tool. He'll care — Chainloop is fully remote with engineers in Seville, Poland, and potentially Berlin.
"How do you think about scaling from 5 to 10 engineers quickly?"
Mobimeo: 8→23 over 3 years (larger scale). For fast hiring: define clear role profiles and leveling rubrics upfront, structured interviews with diverse panels, source through network. Onboarding at pace: documentation-first, pairing buddies, first-week shipping target. JD says hire 2 in first 3 months, 5 in first 6 months.
"What's your experience with software supply chain security?"
Strongest answer you have. 1KOMMA5° (SOC 2 via Vanta, artifact management, CI/CD standardization). Mobimeo (Deutsche Bahn audits every 6 months, security function ownership, policy guardrails, secrets management, vulnerability scanning). Cloudreach/FCA (40TB/day under strict audit controls). Solo Recon (cybersecurity SaaS, CVE ingestion, vulnerability data). Frame it: "I've been the person who has to produce the attestation evidence and pass the audits. I know where the friction is."
"Why did Solo Recon wind down?"
Straightforward: was finding PMF, then OpenAI released Aardvark and Anthropic followed with Claude Code Security. Competitive landscape shifted decisively against a solo founder. Wound it down, learned a lot, proved you can still build. He'll respect the honesty — he's been through a startup that didn't survive (Beetailer).
"What salary range are you looking for?"
Posting says $140K–$170K + equity. Floor is EUR 135K. Don't anchor first — ask about full comp picture (equity structure, vesting, last valuation). If pressed: "I'm targeting the upper end of your posted range and would want to understand the equity component in context of stage and valuation."
### Talking Points
- Supply chain buyer's perspective: "I've implemented SBOM pipelines, Kyverno policies, OPA guardrails, Trivy scanning, and managed the compliance evidence lifecycle across multiple regulated environments. I know where the tooling creates friction — that's the perspective I'd bring to product decisions."
- Founding experience: "At Solo Recon I built and shipped a full product solo in 6 months — architecture to production. That's the founding muscle this role needs. Comfortable with ambiguity, full ownership, decisions without a playbook."
- IDP builder → Chainloop fit: "At 1KOMMA5° I built a developer platform from scratch — Backstage golden paths, CI/CD templates, artifact management. Chainloop's Workflow Contracts are the same concept: declarative expectations for what CI/CD must produce. The difference is Chainloop does it at the attestation layer."
- Scaling teams under pressure: "Mobimeo merger during COVID. Org doubled — redundant systems, fragmented AWS accounts. Mapped everything, picked a third path (greenfield platform, best from each side), unified 75 services with zero downtime. That's the kind of complexity I can navigate while hiring at pace."
- AI governance angle: "Built an AI-native product at Solo Recon — LLM reliability, inference latency, RAG pipeline freshness. When AI agents are writing and shipping code, the attestation and evidence trail becomes even more critical."
- FDE feedback loop: "I've run platform-as-a-product with internal customers at Mobimeo and 1KOMMA5°. Making the FDE→Core feedback loop systematic — turning customer learnings into backlog items instead of one-off fixes — is the same discipline."
### Questions to Ask Miguel
1. What does the Go codebase look like today — how's it organized, and what's the biggest area of tech debt? (Shows you're thinking about the code, not just the org chart.)
2. How do you split time between open-source community work and the commercial product? Where's the tension? (Directly relevant to his Helm/Kubeapps/Bitnami OSS background.)
3. I saw the changelog on AI-driven policy authoring with Claude Code and the debug mode for Rego policies, and your recent post about agentic policies in the latest release. How is that direction evolving? What does the roadmap look like for AI-assisted governance? (Shows you've read their announcements. Connects to the strategic direction. Ref: https://chainloop.dev/blog/changelog-ai-policy-authoring-product-compliance/)
4. What does the FDE function look like today — how much of their work feeds back into core product vs. custom integrations? And how much customer-facing or travel time should I expect in this role? (You'll own the FDE→Core glue. Important to understand boundaries.)
5. What's the biggest hiring challenge — finding people with supply chain domain expertise, or is Go/cloud-native talent the bottleneck? (You'll own hiring. Shows you're already thinking about it.)
6. How do you envision your relationship with the Engineering Manager day-to-day? Where do you want to stay hands-on, and where do you want to hand off? (Essential to understand the CTO↔EM dynamic before joining.)
7. What's the current funding runway, and when do you expect to raise next? (Reasonable for a founding role.)

## Debrief

## Transcript / Raw Notes
