# Jobbing — Project Instructions

## Read These First

1. **WORKFLOW.md** — authoritative workflow. Step-by-step process, JSON schema, Notion queue system, naming conventions. If anything conflicts, WORKFLOW.md wins.
2. **CONTEXT.md** — Greg's profile, complete career timeline, technical skills, salary benchmarks, and writing style rules. This is your source of truth for all claims about Greg's experience.

Read both files at the start of every session before doing any work.

## What This Project Does

AI-assisted job application workflow. Greg pastes a job posting, Claude analyzes fit, generates tailored CV and cover letter content as JSON, renders PDFs, and updates a Notion tracker.

## Behavioral Directives

**Be concise.** No narration, no step-by-step commentary, no filler. Deliver completed work and brief explanations. If Greg needs details, he'll ask.

**Be critical.** Your job is to protect Greg from bad applications. Flag weak matches honestly. Call out red flags in postings: vague titles masking junior work, unrealistic scope, underpaying companies, poor Glassdoor sentiment. A skip is better than a wasted application.

**Be circumspect.** Verify before you claim. Check CONTEXT.md before asserting dates, titles, team sizes, or achievements. Cross-reference salary benchmarks. Research companies via web search — don't guess at funding stage, headcount, or culture. If you're unsure, say so.

**Be helpful.** When Greg decides to proceed, execute the full workflow autonomously: analysis → Notion entry → JSON → PDFs → tracker update. Don't stop to ask unless something is genuinely ambiguous.

## Skills

Project-level skills in `.claude/skills/`. In Claude Code CLI, invoke as `/analyze`, `/apply`, etc. In Cowork, skills load as background context — use natural language ("analyze this job posting", "help me apply").

- **analyze** — Fit assessment. Paste a job posting, get score, green/red flags, gaps, salary read, company intel, Experience to Highlight bullets. Always start here.
- **apply** — Full application workflow. Notion entry → tailored JSON → PDFs → ATS check. Run after analyze and Greg's go decision.
- **outreach** — LinkedIn contact research. Drafts connection request messages. Run after applying.
- **prep** — Interview prep generation. Researches interviewer, generates likely questions, talking points, and questions to ask. Run when an interview is scheduled.
- **debrief** — Post-interview debrief capture. Greg dumps raw thoughts, Claude structures them into the Interviews DB row. Run right after an interview.
- **followup** — Follow-up cadence monitor. Checks all "In Progress (Interviewing)" entries for staleness, surfaces stale conversations with suggested actions. Read-only, no auto-actions.
- **reassess** — Living Fit Assessment. Re-scores an application after interviews reveal new information. Reads existing score, debrief notes, and Greg's input. Writes via the existing `fit_assessment` queue command.
- **compare** — Decision comparison. Side-by-side weighted analysis of two or more active opportunities. Read-only, outputs Markdown.
- **track** — Tracker operations. Status updates, research, highlights, conclusions.
- **scoring** — Tunable scoring guidelines. Component weights, thresholds, domain/tech matching rules. Referenced by analyze, disaggregate, and scan.
- **scan** — Job board scanner. Python fetches boards, Claude extracts and scores postings in-conversation. No API key needed.
- **disaggregate** — Aggregator spam parser. Identifies original companies behind Jobgether/Lensa repostings, de-duplicates, quick-scores.

## Project Structure

```
Jobbing/
├── CLAUDE.md              ← you are here
├── WORKFLOW.md            ← authoritative workflow (read first)
├── CONTEXT.md             ← Greg's profile and career history (read second)
├── SCORING.md             ← pointer to .claude/skills/scoring/SKILL.md
├── CV-GREGORY-DAMIANI.pdf ← master CV (generic, pre-tailoring)
│
├── src/jobbing/           ← Python package
│   ├── cli.py             ← Unified CLI: jobbing track|queue|pdf|scan
│   ├── scanner.py         ← Bookmark parser + board fetcher (no API key)
│   ├── config.py          ← Config loading (env, .env, API keys)
│   ├── models.py          ← Domain models (Application, Contact, CVData, etc.)
│   ├── pdf.py             ← PDF generator (CV + cover letter)
│   └── tracker/
│       ├── __init__.py    ← TrackerBackend Protocol + factory
│       ├── notion.py      ← Notion API tracker
│       └── json_file.py   ← JSON file tracker (portable fallback)
│
├── .claude/skills/        ← Claude Code slash commands
│   ├── analyze/SKILL.md      ← /analyze — fit assessment
│   ├── apply/SKILL.md        ← /apply — full application workflow
│   ├── debrief/SKILL.md      ← /debrief — post-interview debrief
│   ├── disaggregate/SKILL.md ← /disaggregate — aggregator spam parser
│   ├── followup/SKILL.md     ← /followup — follow-up cadence monitor
│   ├── outreach/SKILL.md     ← /outreach — LinkedIn contact research
│   ├── prep/SKILL.md         ← /prep — interview prep generation
│   ├── reassess/SKILL.md     ← /reassess — living fit assessment
│   ├── compare/SKILL.md      ← /compare — decision comparison
│   ├── scan/SKILL.md         ← /scan — job board scanner
│   ├── scoring/SKILL.md      ← /scoring — tunable scoring guidelines
│   └── track/SKILL.md        ← /track — tracker operations
│
├── pyproject.toml         ← Package metadata, deps, CLI entry point
├── .env                   ← API keys (gitignored)
├── .venv/                 ← Python virtual environment
│
├── companies/             ← all company-specific content (gitignored)
│   └── {company}/
│       ├── {company}.json                    ← tailored CV + CL data
│       ├── {COMPANY}-CV.pdf                  ← generated CV
│       ├── {COMPANY}-CL.pdf                  ← generated cover letter
│       ├── {COMPANY}-APPLICATION-ANSWERS.md  ← application questions
│       ├── {COMPANY}-INTERVIEW-PREP.md       ← interview prep
│       └── (other company-specific docs)
│
├── docs/                  ← Architecture, decisions, design history
├── examples/              ← Anonymized templates
├── tests/
│
├── scan_results/          ← scan output JSON files
├── notion_queue/          ← transient queue files (launchd watches this)
└── notion_queue_results/  ← processed queue audit trail
```

## Workflow Summary

Full details in WORKFLOW.md. The short version:

1. **`/analyze`** — Greg pastes a job posting. Assess fit (score 0–100), green/red flags, gaps, salary read, company intel, Experience to Highlight bullets. Present the analysis and wait for Greg's go/skip decision.
2. **`/apply`** — Notion entry → tailored JSON → PDFs → ATS check. All in one flow.
3. **Application answers** — If the application has extra questions, draft `companies/{company}/{COMPANY}-APPLICATION-ANSWERS.md`.
4. **`/outreach`** — After applying, research LinkedIn contacts and draft messages.
5. **`/prep`** — Interview scheduled. Research interviewer, generate prep, write to Interviews DB.
6. **`/debrief`** — After interview. Capture what happened, structure into Interviews DB row.
7. **`/followup`** — Check for stale interview processes. Surfaces companies needing follow-up.
8. **`/reassess`** — After interviews change the picture. Re-scores with debrief data and Greg's input.
9. **`/compare`** — Multiple offers or finalists. Weighted side-by-side comparison, read-only.
10. **`/track`** — Status updates, research, highlights — all tracker operations.

## Critical Rules

**Chronology is sacred.** Solo Recon and Modern Electric are CURRENT roles (2024–present). "Most recently" always means these. Never lead with Mobimeo as most recent. Check CONTEXT.md timeline before writing.

**People management started mid-2017.** That's 8+ years as of 2026. Never write "6+ years."

**No AI tells.** Never write summative self-congratulatory sentences like "my experience aligns perfectly with this role." Show, don't tell. Let specifics speak for themselves. See the "Writing Style" section in CONTEXT.md.

**No fake metrics.** Don't invent percentages, time savings, or impact numbers that aren't in CONTEXT.md.

**Experience to Highlight is a checkpoint.** Present the bullets to Greg explicitly and wait for feedback before generating documents. Don't rubber-stamp.

## Commands

### Notion writes — queue only

The queue is the only reliable write path. Write JSON to `notion_queue/` and the launchd agent on Greg's Mac processes it automatically. Do not attempt Notion MCP writes — known Zod serialization bugs on every write tool.

The queue `create` command builds template-like scaffolding automatically: seven toggle heading_3 sections (Job Description, Fit Assessment, Company Research, Experience to Highlight, Outreach Contacts, Questions I Might Get Asked, Questions to Ask) plus an inline Interviews database. If `score` is included, it also sets the Score number property.

```json
{"command": "create", "name": "Company", "position": "Role", "date": "2026-02-20", "job_description": "Full posting text...", ...}
{"command": "update", "page_id": "PAGE_ID", "status": "Applied"}
{"command": "update", "page_id": "PAGE_ID", "status": "Followed-Up"}
{"command": "update", "page_id": "PAGE_ID", "status": "In Progress (Interviewing)"}
{"command": "update", "page_id": "PAGE_ID", "status": "Done", "conclusion": "Outcome text"}
{"command": "highlights", "page_id": "PAGE_ID", "highlights": ["Bullet 1", "Bullet 2"]}
{"command": "research", "name": "Company", "research": ["Finding 1", "Finding 2"]}
{"command": "outreach", "name": "Company", "contacts": [{"name": "Jane Smith", "title": "VP Eng", "linkedin": "https://...", "note": "Leads Platform org, ex-Google SRE", "message": "Hi Jane — ..."}]}
{"command": "interview_questions", "name": "Company", "questions": [{"question": "Q1?", "answer": "A1"}]}
{"command": "questions_to_ask", "name": "Company", "questions": ["Q1?", "Q2?"]}
{"command": "fit_assessment", "name": "Company", "score": 75, "reasoning": "...", "green_flags": ["..."], "red_flags": ["..."], "gaps": ["..."], "keywords_missing": ["..."]}
{"command": "interview_prep", "name": "Company", "date": "2026-03-15", "interviewer": "Jane Smith — VP Eng", "interview_type": "Hiring Manager", "prep_notes": "## Key Topics\n- ...", "questions_to_ask": ["Q1?", "Q2?"]}
{"command": "debrief", "name": "Company", "date": "2026-03-15", "interviewer": "Jane Smith — VP Eng", "outcome": "Passed", "vibe": 4, "debrief": "Strong conversation...", "questions_they_asked": ["Q1?"], "questions_i_asked": ["Q2?"], "follow_up": "Next steps..."}
```

**Status updates are Greg's decision.** Do not auto-mark "Applied" or any other status. Greg will explicitly ask for status changes.

### PDF generation

```bash
jobbing pdf {company}
jobbing pdf {company} --cv-only
jobbing pdf {company} --cl-only
```

### CLI commands

After `pip install -e .`, the `jobbing` CLI is available:

```bash
jobbing track create --name "Company" --position "Role" --date "2026-02-22"
jobbing track update --page-id "PAGE_ID" --status "Applied"
jobbing track highlights --page-id "PAGE_ID" --highlights "Bullet 1" "Bullet 2"
jobbing track research --name "Company" --research "Finding 1" "Finding 2"
jobbing track outreach --name "Company" --contacts-json contacts.json
jobbing track followup                              # check stale interview processes
jobbing track followup --threshold 7 --save         # custom threshold + save report
jobbing queue   # process all pending queue files
jobbing pdf {company}
jobbing scan bookmarks                              # list all bookmarks by category
jobbing scan bookmarks --categories "Climate / Impact"  # list one category
jobbing scan existing                               # list companies already tracked
jobbing scan fetch                                  # fetch all boards (~30s)
jobbing scan fetch --categories "Startup / Tech"    # fetch one category
jobbing scan fetch --limit 5                        # fetch first 5 boards
```

All track commands support `--dry-run` for previewing without sending.

## Notion Integration Notes

- **Notion is the single source of truth** for all application tracking, company research, and outreach contacts.
- **Writes**: Queue-based only. Write JSON to `notion_queue/`, launchd picks it up.
- **Reads**: Notion MCP tools (`notion-fetch`, `notion-search`) work for verification.
- **DON'T USE NOTION MCP FOR WRITES.** Known Zod serialization bug on every write tool (`update-page`, `create-pages`). Both fail with "Expected object, received string" regardless of payload format. Use the queue system for all writes.
- **File uploads**: Not supported by Notion API for internal integrations. Greg uploads PDFs manually.
- **Database ID**: `734d746c43b149298993464f5ccc23e7`
- **Status values** (in order): `Targeted` → `Applied` → `Followed-Up` → `In Progress (Interviewing)` → `Done`. New entries default to **Targeted**. Do NOT invent new status values — Notion auto-creates select options for any string, so typos and made-up values silently pollute the database. Add a `Conclusion` when moving to `Done`.
- **Page layout** (canonical order, matches application chronology): Inline "Interviews" database, divider, then seven toggle heading_3 sections: "Job Description", "Fit Assessment", "Company Research", "Experience to Highlight", "Outreach Contacts", "Questions I Might Get Asked", "Questions to Ask". All sections scaffolded from creation with empty placeholders. On update-existing, existing section content is preserved for any section the new JSON doesn't include — safe to re-run without data loss. Section matching is case-insensitive with backward-compat aliases for renamed sections.
- **Score property**: Number property on the database. Set automatically when `fit_assessment` command runs or when `create` includes a `score` field.
- **Markdown in queue payloads**: The `_markdown_to_blocks()` parser handles `#`/`##`/`###` headings, `-` bullets (including nested/indented), `**bold**`/`*italic*` inline formatting, and blank-line-separated paragraphs. Other markdown (tables, links, code blocks) is not supported and will render as plain text. Keep queue payload markdown simple.

## Location Logic

- **European roles**: "Berlin, Germany • EU-based • Remote"
- **US roles**: "New York, NY • Berlin, Germany • Remote"
- **Global/ambiguous**: "Berlin, Germany • New York, NY • Remote"

## Do Not

### Process
- Skip `/analyze` and go straight to document generation — analysis is always step one
- Skip the Experience to Highlight checkpoint — present bullets to Greg and wait for feedback
- Skip the tailoring plan checkpoint in `/apply` — present the strategy and wait for approval
- Generate the JSON before Greg approves the tailoring plan
- Auto-mark "Applied" or any other Notion status — status updates are Greg's decision
- Proceed without reading WORKFLOW.md and CONTEXT.md at the start of each session
- Proceed without reading `examples/example_company.json` as the structural template before generating JSON
- Inflate fit scores to be encouraging — be honest, a skip is better than a wasted application
- Guess at company info (headcount, funding, culture) — web search or say "not found"

### Writing — CV and Cover Letter
- Use AI tells or summative self-congratulatory language. Banned phrases include:
  - "aligns perfectly", "uniquely positioned", "proven track record"
  - "passionate about", "thrilled to", "excited to bring"
  - "This maps directly to...", "My experience is directly applicable..."
  - "...making me an ideal candidate for this role"
  - Any sentence whose purpose is to restate the obvious connection between Greg's experience and the role — the reader can connect the dots
- Use marketing superlatives: "blazingly fast", "world-class", "cutting-edge", "unparalleled"
- Invent metrics, percentages, time savings, or impact numbers not in CONTEXT.md
- Write "6+ years of people management" — it's 8+ years (started mid-2017)
- Lead with Mobimeo as "most recent" — Solo Recon and Modern Electric are current (2024–present)
- Present German language ability as a qualification — it's A2, not useful
- Claim Greg has experience he doesn't have (check CONTEXT.md before every assertion)
- Write in first person in the CV (CVs are third-person implied; cover letters are first person)
- Add filler paragraphs or pad content to seem longer — be concise and substantive
- Use the same generic cover letter structure for every role — each one must be tailored
- Describe Solo Recon as having customers, revenue, or traction — it's a solo effort with ~12 users, no funding, no sales
- Say "led a team of 23" for any role other than Mobimeo — check CONTEXT.md team sizes per role
- Claim direct reports or management responsibility at roles where Greg was IC (e.g., BuzzFeed, Yara, TradingScreen)

### Outreach Messages
- Write messages over 300 characters (LinkedIn connection request limit)
- Leave the company name implied — always name the company explicitly
- End with "Happy to connect" or "Would welcome a conversation" — end with curiosity about their work
- Write generic messages that could apply to any company — tailor to the specific contact's role and domain
- Use stiff, transactional language — write like a peer, not a candidate pitching

### Notion and Technical
- Use Notion MCP `update-page` — Zod serialization bug, use the queue for all updates
- Create files outside `companies/{company}/` for company-specific content
- Leave TODO comments or placeholder content in JSON files
- Claim you included something in the JSON that you didn't actually include — verify your own work before reporting
- Write to Notion directly from Cowork — use the queue system for all writes except template-based page creation

### Ethical
- Apply to defense contractors, military technology, weapons systems, or companies whose primary customer is military/intelligence — this is a firm exclusion, non-negotiable
- Misrepresent Greg's work authorization — US citizen (no sponsorship needed for US), German permanent residency (no sponsorship needed for EU/DE)
