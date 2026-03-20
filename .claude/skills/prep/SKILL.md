---
name: prep
description: Generate interview prep material for an upcoming interview. Researches the interviewer, generates likely questions, talking points, and questions to ask. Creates an interview file in kanban/interviews/ and updates the company hub.
---

# Interview Prep Generation

Generate targeted prep material when Greg has an upcoming interview. Reads existing hub context, researches the interviewer, and produces prep tailored to the interview type and the specific person.

## Prerequisites

- Company hub exists at `kanban/companies/{Company}.md` (created via `/analyze` + `/apply`)
- Greg provides: company name, interviewer name/title, interview date, interview type

## Instructions

### Step 1: Load Context

- Read WORKFLOW.md and CONTEXT.md if not already loaded this session
- Read `kanban/companies/{Company}.md` to pull:
  - `position:` from frontmatter
  - `score:` from frontmatter
  - `## Fit Assessment` section (score, green/red flags, gaps)
  - `## Experience to Highlight` section (the approved bullets from `/analyze`)
  - `## Company Research` section (funding, headcount, domain)
  - `## Job Description` section (the original posting)
  - `## Questions I Might Get Asked` section (if populated)
  - `## Questions to Ask` section (if populated)
  - `## Interviews` section (existing wikilinks — check for prior interview files)
- If the hub file does not exist, STOP and tell Greg to run `/analyze` and `/apply` first. Prep requires existing hub data.

### Step 2: Parse the Trigger

Extract from Greg's natural language input:

- **Company name** (required) — match to existing hub file
- **Interviewer name and title** (required) — e.g., "Thomas Roton, VP Engineering"
- **Interview date** (required) — resolve relative dates ("Thursday", "next Tuesday") to ISO date using today's date
- **Interview type** (required) — infer from context and map to a valid type: Phone Screen, Technical, System Design, Behavioral, Panel, Hiring Manager, Executive, Take-Home

If any field is ambiguous, ask Greg to clarify before proceeding.

### Step 3: Research the Interviewer

Use WebSearch to research the interviewer:

- LinkedIn profile — current role, tenure, career history
- Blog posts, conference talks, podcast appearances
- Open-source contributions (GitHub)
- Published articles or interviews
- Identify connection points with Greg's experience (shared domains, technologies, mutual interests)

Build a concise profile that gives Greg context on who they're talking to. If WebSearch returns nothing useful, say "No public profile found" plainly and focus on role-based preparation instead.

### Step 3.5: Apply the Staff/Principal Interview Framework

Every prep at this level must address the **Four Pillars** — the specific areas where Staff/Principal candidates most commonly fail interviews. These are based on direct recruiter feedback on rejection reasons and apply to all interview types, not just technical rounds.

**Pillar 1: Quantified Impact ("Own It")** — The #1 rejection reason. Every story Greg tells must connect technical work to hard business metrics: revenue impact, latency reduction (with numbers), efficiency multipliers, cost savings, team velocity improvements. "I don't know the numbers" or "we didn't formally measure it" is a major red flag at this level. When generating prep, pair every talking point with the specific metric from CONTEXT.md. If no metric exists for a story, flag it as a gap so Greg can either find the number or choose a different story.

**Pillar 2: Architectural Decision Making** — Greg must be able to walk through real ADRs: what trade-offs were considered (build vs. buy, monolith vs. federated, etc.), how he secured buy-in from other senior engineers or leadership, and long-term risks identified with mitigations. No hypotheticals — only concrete decisions he made and saw through to completion. When generating likely questions, include at least one ADR-style question.

**Pillar 3: Analytical Depth & Root Cause ("Dive Deep")** — When discussing incidents or failures, the expectation is a systematic elimination chain (rollback → log analysis → profiling → code trace), not heroics. Every incident story must include the architectural prevention: what changed so this *class* of error can't recur? If the root cause was simple, it's not a Staff/Principal-level story. When generating prep, ensure incident stories have both the investigation methodology and the systemic fix.

**Pillar 4: Executive Communication & Breadth** — Answers must be under 4 minutes using STAR format. If the interviewer has to accelerate the candidate, it counts as a negative signal for communication. Even specialized answers should be framed in terms of system-wide impact and end-user experience. Self-awareness about knowledge boundaries is expected — defensiveness when pushed on a weak answer is a red flag. When generating prep, include timing guidance and flag any stories that risk going long.

**Quick Checklist (include in every prep):**
1. Does every story have a hard number? (Pillar 1)
2. Is there at least one ADR walk-through ready? (Pillar 2)
3. Does every incident story have investigation methodology + systemic prevention? (Pillar 3)
4. Can each answer be delivered in under 4 minutes? (Pillar 4)

### Step 4: Generate Prep Material

Generate four sections, each tailored to the interview type and interviewer. Apply the Four Pillars framework to every section — ensure each talking point and answer includes quantified impact, and flag any gaps.

**1. Interviewer Background**
- Who they are, what they care about, their technical/business focus
- Connection points with Greg's experience
- Key insights for rapport building

**2. Likely Questions** (tailored by interview type)
- **Phone Screen:** motivation, career narrative, culture fit, salary expectations
- **Technical:** architecture decisions, debugging stories, system design, tech stack specifics
- **System Design:** scalability, trade-offs, real-world system examples
- **Behavioral:** leadership scenarios, conflict resolution, team scaling, cross-functional work
- **Panel:** mix of technical and behavioral, tailored to each panelist's focus
- **Hiring Manager:** team vision, role expectations, management philosophy, org dynamics
- **Executive:** strategy, business impact, organizational leadership
- **Take-Home:** clarification questions, scope management, documentation approach

For each question, include bullet-point answer guidance drawn from CONTEXT.md and Experience to Highlight. Where interviewer research reveals specific interests, tune the answer framing accordingly.

**3. Talking Points** (drawn from Experience to Highlight, reframed for interview type)
- Technical screens: architecture stories, production incidents, scale numbers, infrastructure decisions
- Behavioral rounds: leadership examples, team scaling, cross-functional alignment, coaching moments
- Hiring Manager: org building, hiring strategy, delivery track record
- Each talking point references specific roles and concrete outcomes from CONTEXT.md

**4. Questions to Ask This Interviewer**

Start by reading the `## Questions to Ask` section from the hub file. These are Greg's accumulated questions about the company — technical, organizational, business, cultural. Filter them:

- **Include** questions this interviewer can actually answer given their role and domain knowledge
- **Exclude** questions outside their scope (don't ask a recruiter about architecture decisions; don't ask a Staff Engineer about comp structure)
- **Add** new questions specific to this person — based on interviewer research, their seniority, and their likely knowledge domain

The result should be a short, prioritized list (5–8 questions) that Greg can realistically ask in one conversation. Each question should make sense only for this specific interviewer — not a generic dump of everything Greg wants to know about the company.

### Step 5: Present for Review — CHECKPOINT

Present the full prep material organized in the four sections above. This is a mandatory review checkpoint — wait for Greg's feedback before writing any files. Greg may:

- Correct factual errors about the interviewer
- Add or remove talking points
- Adjust emphasis based on inside knowledge
- Refine the questions to ask

### Step 6: Write Files

After Greg approves:

**a) Create the interview file**

Derive the file path:
- `kanban/interviews/{Company}/{date}-{FirstName-LastName}.md`
- Example: `kanban/interviews/Bandcamp/2026-03-15-Thomas-Roton.md`

Create the directory if it doesn't exist. Write the interview file:

```markdown
---
company: "Company Name"
interviewer: "Thomas Roton"
role: "VP Engineering"
type: "Hiring Manager"
date: 2026-03-15
vibe: —
outcome: "Pending"
---

# Thomas Roton — Hiring Manager · 2026-03-15
**Company:** [[Company Name]] · **Outcome:** Pending · **Vibe:** —

## Prep Notes

[Full prep content here — all four sections]

## Debrief

## Transcript / Raw Notes
```

**b) Update the hub Interviews section**

In `kanban/companies/{Company}.md`, append a wikilink to the `## Interviews` section:

```
- [[2026-03-15-Thomas-Roton|Thomas Roton — Hiring Manager · Pending · Vibe —]]
```

Use the Edit tool to append this line.

**c) Auto-populate Questions I Might Get Asked (conditional)**

If the `## Questions I Might Get Asked` section in the hub file is empty or contains only placeholder text, populate it with the Likely Questions from this prep run. Use the Edit tool to replace the placeholder content with the questions and answer guidance.

Do NOT overwrite this section if it already has substantive content from a previous `/prep` run or manual entry.

## Critical Rules

- Check CONTEXT.md before every assertion about Greg's experience — dates, team sizes, achievements must be accurate
- Chronology is sacred — Solo Recon and Modern Electric are current roles (2024-present). "Most recently" always means these.
- People management started mid-2017 — that's 8+ years as of 2026
- Interviewer research must be real — if you can't find information, say so. Do not fabricate LinkedIn profiles, conference talks, or blog posts.
- Prep notes are for Greg's eyes only — they can be more direct and strategic than external-facing documents
- No AI tells — no "aligns perfectly", "uniquely positioned", "proven track record"
- No fake metrics — only use numbers that appear in CONTEXT.md
- No marketing superlatives — no "world-class", "cutting-edge", "unparalleled"
- Do not describe Solo Recon as having customers, revenue, or traction — it's a solo effort with ~12 users

## Do Not

- Skip the review checkpoint — present prep to Greg and wait for feedback before writing any files
- Generate prep without reading the company hub first — prep must build on existing hub context
- Fabricate interviewer information — no public profile found is an honest answer
- Write generic prep that could apply to any company — every section must reference the specific company, role, and interviewer
- Auto-populate "Questions I Might Get Asked" without checking whether it already has content
- Use the same question set for every interview type — Phone Screen prep is fundamentally different from System Design prep
- Create prep for a company not yet tracked in Obsidian — tell Greg to run `/analyze` + `/apply` first
- Invent mutual connections between Greg and the interviewer
- Run without knowing the interview date — date is required for the interview filename

## Related Skills

- `/analyze` — Fit assessment (must be run before `/prep`)
- `/apply` — Full application workflow (must be run before `/prep`)
- `/outreach` — LinkedIn contact research (may provide interviewer context)
- `/debrief` — Post-interview debrief capture (run after the interview)
