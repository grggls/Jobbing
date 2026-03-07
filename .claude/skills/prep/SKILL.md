---
name: prep
description: Generate interview prep material for an upcoming interview. Researches the interviewer, generates likely questions, talking points, and questions to ask. Writes prep notes to the Interviews DB via the queue system.
---

# Interview Prep Generation

Generate targeted prep material when Greg has an upcoming interview. Reads existing tracker context, researches the interviewer, and produces prep tailored to the interview type and the specific person.

## Prerequisites

- Company is tracked in Notion (created via `/analyze` + `/apply`)
- Greg provides: company name, interviewer name/title, interview date, interview type

## Instructions

### Step 1: Load Context

- Read WORKFLOW.md and CONTEXT.md if not already loaded this session
- Look up the company page in Notion via `notion-search` (by company name)
- Read the company page via `notion-fetch` to pull:
  - Experience to Highlight (the approved bullets from `/analyze`)
  - Company Research (funding, headcount, domain)
  - Fit Assessment (score, green/red flags, gaps)
  - Job Description (the original posting)
  - Questions I Might Get Asked (if populated)
  - Questions to Ask (if populated)
- If the company does not exist in the tracker, STOP and tell Greg to run `/analyze` and `/apply` first. Prep requires existing tracker data.

### Step 2: Parse the Trigger

Extract from Greg's natural language input:

- **Company name** (required) — match to existing tracker entry
- **Interviewer name and title** (required) — e.g., "Thomas Roton, VP Engineering"
- **Interview date** (required) — resolve relative dates ("Thursday", "next Tuesday") to ISO date using today's date
- **Interview type** (required) — infer from context and map to a valid Notion select value: Phone Screen, Technical, System Design, Behavioral, Panel, Hiring Manager, Executive, Take-Home

If any field is ambiguous, ask Greg to clarify before proceeding.

### Step 3: Research the Interviewer

Use WebSearch to research the interviewer:

- LinkedIn profile — current role, tenure, career history
- Blog posts, conference talks, podcast appearances
- Open-source contributions (GitHub)
- Published articles or interviews
- Identify connection points with Greg's experience (shared domains, technologies, mutual interests)

Build a concise profile that gives Greg context on who they're talking to. If WebSearch returns nothing useful, say "No public profile found" plainly and focus on role-based preparation instead.

### Step 4: Generate Prep Material

Generate four sections, each tailored to the interview type and interviewer:

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

Start by reading the existing "Questions to Ask" section from the Notion page. These are Greg's accumulated questions about the company — technical, organizational, business, cultural. Filter them:

- **Include** questions this interviewer can actually answer given their role and domain knowledge
- **Exclude** questions outside their scope (don't ask a recruiter about architecture decisions; don't ask a Staff Engineer about comp structure)
- **Add** new questions specific to this person — based on interviewer research, their seniority, and their likely knowledge domain

The result should be a short, prioritized list (5–8 questions) that Greg can realistically ask in one conversation. Each question should make sense only for this specific interviewer — not a generic dump of everything Greg wants to know about the company.

### Step 5: Present for Review — CHECKPOINT

Present the full prep material organized in the four sections above. This is a mandatory review checkpoint — wait for Greg's feedback before writing anything to Notion. Greg may:

- Correct factual errors about the interviewer
- Add or remove talking points
- Adjust emphasis based on inside knowledge
- Refine the questions to ask

### Step 6: Write to Notion

After Greg approves, write to `notion_queue/`:

**a) Interview prep** — the prep notes to the Interviews DB row:

```json
{
  "command": "interview_prep",
  "name": "CompanyName",
  "date": "2026-03-15",
  "interviewer": "Jane Smith — VP Engineering",
  "interview_type": "Hiring Manager",
  "prep_notes": "## Interviewer Background\n...\n\n## Likely Questions\n...\n\n## Talking Points\n...\n\n## Questions to Ask\n...",
  "questions_to_ask": ["Q1?", "Q2?"]
}
```

Queue file naming: `YYYYMMDD_companyname_interview_prep.json`

**b) Questions I Might Get Asked** (conditional) — if this section on the Notion page is empty or contains only placeholder bullets, auto-populate it from the Likely Questions output:

```json
{
  "command": "interview_questions",
  "name": "CompanyName",
  "questions": [
    {"question": "How did you scale the platform org?", "answer": "Mobimeo: 8 to 23 engineers across Platform, SRE, Security, Data..."},
    {"question": "Tell me about a production incident", "answer": "1KOMMA5°: uptime was 95% when I joined. Standardized on-call, SLOs..."}
  ]
}
```

Do NOT write this if "Questions I Might Get Asked" already has substantive content from a previous `/prep` run or manual entry.

## Critical Rules

- Check CONTEXT.md before every assertion about Greg's experience — dates, team sizes, achievements must be accurate
- Chronology is sacred — Solo Recon and Modern Electric are current roles (2024-present). "Most recently" always means these.
- People management started mid-2017 — that's 8+ years as of 2026
- Interviewer research must be real — if you can't find information, say so. Do not fabricate LinkedIn profiles, conference talks, or blog posts.
- Interview type must be one of the 8 valid Notion select values — do not invent new ones
- Prep notes are for Greg's eyes only — they can be more direct and strategic than external-facing documents
- No AI tells — no "aligns perfectly", "uniquely positioned", "proven track record"
- No fake metrics — only use numbers that appear in CONTEXT.md
- No marketing superlatives — no "world-class", "cutting-edge", "unparalleled"
- Do not describe Solo Recon as having customers, revenue, or traction — it's a solo effort with ~12 users

## Do Not

- Skip the review checkpoint — present prep to Greg and wait for feedback before writing to Notion
- Generate prep without reading the company's Notion page first — prep must build on existing tracker context
- Fabricate interviewer information — no public profile found is an honest answer
- Write generic prep that could apply to any company — every section must reference the specific company, role, and interviewer
- Auto-populate "Questions I Might Get Asked" without checking whether it already has content
- Use the same question set for every interview type — Phone Screen prep is fundamentally different from System Design prep
- Create prep for a company not yet tracked in Notion — tell Greg to run `/analyze` + `/apply` first
- Invent mutual connections between Greg and the interviewer
- Run without knowing the interview date — date is required for the Interviews DB row
- Use Notion MCP write tools — queue system only for all writes

## Related Skills

- `/analyze` — Fit assessment (must be run before `/prep`)
- `/apply` — Full application workflow (must be run before `/prep`)
- `/track` — Manual interview prep and debrief via queue commands
- `/outreach` — LinkedIn contact research (may provide interviewer context)
- `/debrief` — Post-interview debrief capture (run after the interview)
