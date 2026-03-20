---
company: "Parloa"
interviewer: "Micaël Mbagira"
role: "Staff Software Engineer"
type: "Technical"
date: 2026-03-17
---

# Micaël Mbagira — Technical — 2026-03-17
**Company:** [[Parloa]]

## Prep Notes

### Interviewer Profile
- Staff Software Engineer at Parloa (promoted Dec 2025 from Senior, joined Jan 2024)
- Builds backend systems for conversational AI platform — infra design, scalability, reliability
- Deep expertise: Rust, TypeScript, cloud-native, edge computing
- Prior: TIER Mobility (2 yrs, IoT/edge, Rust/TS/Kafka), Advertima (4.5 yrs, real-time edge apps, computer vision)
- Education: IMT Atlantique MEng, French
- PSM I certification (Dec 2025)
- 7 mutual connections including Konstanty Sliwowski
### Interview Format
- 10-15 min live coding (Python, AI tools encouraged) + 30-45 min general technical questions
- VS Code with Claude Code as IDE
- python-scaffold project: ~/src/parloa-interview
- Key: they evaluate HOW you interact with AI tools, not raw coding ability
### Your Setup
1. Open ~/src/parloa-interview in VS Code
2. Terminal visible alongside editor, Claude Code accessible
3. Narrate intent before prompting AI — show you're driving, not delegating
4. Use AI for boilerplate/imports/tests, write core logic yourself
5. Ask Micaël questions, not just AI
### Four Pillars (Xcede rejection feedback)
1. Quantified Impact — every story needs hard numbers
2. Architectural Decision Making — real ADRs with trade-offs and buy-in
3. Analytical Depth — systematic root cause + prevention, not heroics
4. Executive Communication — STAR, under 4 minutes, systems thinking
### Likely Coding Task
- Event/message processing (Kafka/NATS patterns) — most likely
- Rate limiter (sliding window) — second most likely
- Async pipeline (STT/LLM/TTS chain) — outside chance
### Practice Scenarios
Scenario 1: Event Deduplicator — class EventProcessor: accepts events as dicts, deduplicates by id within configurable time window (default 60s), routes to handlers by type. Edge cases: no handler for type, malformed events.
Scenario 2: Rate Limiter — class RateLimiter(max_requests, window_seconds): allow(key) -> bool, get_usage(key) -> dict. Sliding window, independent per key, memory cleanup.
Scenario 3: Async Voice Pipeline — chain transcribe/generate_response/synthesize_speech with 2s total timeout, per-stage error handling with fallback, per-stage timing logs.
### Coding Playbook (15 min)
- Min 0-2: Read and clarify. Ask 2-3 questions before coding.
- Min 2-4: Design out loud. Sketch structure as comments.
- Min 4-5: Scaffold with Claude Code. Review and modify.
- Min 5-12: Implement core logic. Narrate. Handle key edge case.
- Min 12-15: Test and refine. Walk through test case verbally.
### Connection Points with Micaël
- Edge computing: his TIER/Advertima IoT work parallels Yara IoT gateway
- Cloud-native + Kubernetes: shared background
- Scalability: his platform work at Parloa maps to 1KOMMA5° and Mobimeo platform work
- Real-time systems: his edge computing parallels TradingScreen latency work
### General Technical Questions (30-45 min)
- System design thinking: TradingScreen latency, BuzzFeed 700K concurrent, Mobimeo Kafka
- Architecture trade-offs: Cloud Run vs K8s at 1KOMMA5°, centralized vs embedded SREs at Mobimeo
- AI tools in daily work: Solo Recon workflow — architecture is human, implementation is AI-assisted
- Complex codebases: Mobimeo 75 services no docs, 1KOMMA5° joining a moving org
- Reliability: 1KOMMA5° 95%→99.9%, Mobimeo MTTR -50%
- Cross-team influence: 1KOMMA5° golden paths (pulled not pushed), Mobimeo Platform Ops proposal
### Questions to Ask Micaël
- What's the biggest infrastructure challenge the backend team is tackling right now?
- How does the team handle edge vs cloud deployment decisions for latency-sensitive paths?
- What does on-call look like for the backend team?
- How do Staff engineers at Parloa influence technical direction across teams?
- What does a typical week look like for a Principal Engineer? Work-life balance?

## Debrief

## Transcript / Raw Notes
