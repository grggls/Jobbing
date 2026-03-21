---
company: "Parloa"
interviewer: "Thomas Dobbie"
role: "Outside Recruiter (Xcede)"
type: "Phone Screen"
date: 2026-02-17
vibe: 4
outcome: "Passed"
---

# Thomas Dobbie — Phone Screen · 2026-02-17
**Company:** [[Parloa]] · **Outcome:** Passed · **Vibe:** 4/5

## Prep Notes

## Debrief
- Parloa building a high-achieving engineering culture. Almost all staff and principal engineers (inverted pyramid).
- Reliability and latency for voice-AI is a huge topic, something they're hiring for.
- Discussed strategies for improving latency for voice-to-text, LLM, text-to-speech cycles to reduce wait times to human-native (200-800ms):
  - Measurement, log aggregation and standardization, distributed tracing — you can't improve what you can't measure
  - Caching of frequently returned values
  - Ensuring LLMs are loaded in memory at all times, minimizing memory pressure on nodes running LLMs, and keeping LLMs "warm"
  - Database optimization - caching, indexing, stored subroutines, minimizing disk read operations
  - Reducing network distance between communicating services
- Interview process is 5 steps: peer interview → live coding → system design → leadership/writing → bar raiser
- Thomas shared resources: Series D press release ($350M, $3B valuation), culture docs, technical interview guide
- Ambitions: F2000 vendor of choice, top 3 Gartner Magic Quadrant, 4x annual revenue YoY 2025-2028

## Transcript / Raw Notes
