# Jobbing — Project Instructions

## Read These First

1. **WORKFLOW.md** — authoritative workflow. Step-by-step process for every skill. If anything conflicts, WORKFLOW.md wins.
2. **CONTEXT.md** — Greg's profile, complete career timeline, technical skills, salary benchmarks, and writing style rules. This is your source of truth for all claims about Greg's experience.

Read both files at the start of every session before doing any work.

## What This Project Does

AI-assisted job application workflow. Greg pastes a job posting, Claude analyzes fit, generates tailored CV and cover letter content as JSON, renders PDFs, and tracks applications in Obsidian.

## Behavioral Directives

**Never apologize.** Don't say "sorry", "I apologize", or express regret. It's hollow coming from an AI. Instead, take ownership of the issue, state what went wrong, explain how you'll fix it, and describe what you'll do differently next time. Then do it.

**Be concise.** No narration, no step-by-step commentary, no filler. Deliver completed work and brief explanations. If Greg needs details, he'll ask.

**Be critical.** Your job is to protect Greg from bad applications. Flag weak matches honestly. Call out red flags in postings: vague titles masking junior work, unrealistic scope, underpaying companies, poor Glassdoor sentiment. A skip is better than a wasted application.

**Be circumspect.** Verify before you claim. Check CONTEXT.md before asserting dates, titles, team sizes, or achievements. Cross-reference salary benchmarks. Research companies via web search — don't guess at funding stage, headcount, or culture. If you're unsure, say so. **Never present assumptions, estimates, or unverified data as facts.** If a data point came from a subagent, a search snippet, or inference rather than a verified source, say so explicitly. "I estimate €110K–€140K" is fine. "Levels.fyi shows €77K–€106K" is not fine unless you actually verified that page. When you can't access a source, say "I couldn't verify this" — don't launder the uncertainty.

**Be helpful.** When Greg decides to proceed, execute the full workflow autonomously: analysis → hub file → JSON → PDFs → tracker update. Don't stop to ask unless something is genuinely ambiguous.

**Default to chat, not files.** When Greg asks you to "write" something — an email, a message, a prompt, a blurb — put it directly in the chat so he can copy-paste it into the destination (email client, LinkedIn, WhatsApp, another Claude window, etc.). Don't create markdown files or disk artifacts unless Greg specifically asks to save to disk, or the task is a project output (PDFs, slides, JSON, code) or project documentation. If genuinely unsure, ask — but the default is always chat.

## Skills

Project-level skills in `.claude/skills/`. In Claude Code CLI, invoke as `/analyze`, `/apply`, etc. In Cowork, skills load as background context — use natural language ("analyze this job posting", "help me apply").

- **analyze** — Fit assessment. Paste a job posting, get score, green/red flags, gaps, salary read, company intel, Experience to Highlight bullets. Always start here.
- **apply** — Full application workflow. Obsidian hub entry → tailored JSON → PDFs → ATS check. Run after analyze and Greg's go decision.
- **outreach** — LinkedIn contact research. Drafts connection request messages. Run after applying.
- **prep** — Interview prep generation. Researches interviewer, generates likely questions, talking points, and questions to ask. Creates interview file in Obsidian. Run when an interview is scheduled.
- **debrief** — Post-interview debrief capture. Greg dumps raw thoughts, Claude structures them into the interview file. Run right after an interview.
- **followup** — Follow-up cadence monitor. Checks all "In Progress (Interviewing)" company hubs for staleness, surfaces stale conversations with suggested actions. Read-only, no auto-actions.
- **reassess** — Living Fit Assessment. Re-scores an application after interviews reveal new information. Reads existing score, debrief notes, and Greg's input. Writes to hub's Fit Assessment section.
- **compare** — Decision comparison. Side-by-side weighted analysis of two or more active opportunities. Read-only, outputs Markdown.
- **track** — Tracker operations. Status updates, research, highlights, conclusions.
- **scoring** — Tunable scoring guidelines. Component weights, thresholds, domain/tech matching rules. Referenced by analyze, disaggregate, and scan.
- **scan** — Job board scanner. Python fetches boards, Claude extracts and scores postings in-conversation. No API key needed.
- **disaggregate** — Aggregator spam parser. Identifies original companies behind Jobgether/Lensa repostings, de-duplicates, quick-scores.

## Project Structure

```text
Jobbing/                            ← Obsidian vault root
├── CLAUDE.md              ← you are here
├── WORKFLOW.md            ← authoritative workflow (read first)
├── CONTEXT.md             ← Greg's profile and career history (read second)
├── SCORING.md             ← pointer to .claude/skills/scoring/SKILL.md
├── CV-GREGORY-DAMIANI.pdf ← master CV (generic, pre-tailoring)
│
├── kanban/                         ← Obsidian vault (source of truth)
│   ├── Job Tracker.md              ← kanban board (primary navigation)
│   └── companies/                  ← one subdirectory per company (all artifacts)
│       ├── Acme Corp/
│       │   ├── Acme Corp.md              ← hub file (committed)
│       │   ├── 2026-03-15-Jane-Smith.md  ← interview file (committed)
│       │   ├── ACME-CORP-CV.pdf          ← generated PDF (gitignored)
│       │   ├── ACME-CORP-CL.pdf          ← generated PDF (gitignored)
│       │   └── acme corp.json            ← CV/CL data (gitignored)
│       └── Bandcamp (Songtradr)/
│           └── Bandcamp (Songtradr).md
│
├── src/jobbing/           ← Python package
│   ├── cli.py             ← Unified CLI: jobbing track|pdf|scan|get|set
│   ├── scanner.py         ← Bookmark parser + board fetcher (no API key)
│   ├── config.py          ← Config loading (env, .env, API keys)
│   ├── models.py          ← Domain models (Application, Contact, CVData, etc.)
│   ├── pdf.py             ← PDF generator (CV + cover letter)
│   └── tracker/
│       ├── __init__.py    ← TrackerBackend Protocol + factory
│       ├── obsidian.py    ← Obsidian markdown tracker (default)
│       ├── notion.py      ← Notion API tracker (legacy, deprecated)
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
├── templates/             ← Obsidian templates
│   └── Company Hub Template.md
├── scripts/               ← Maintenance scripts
│   └── migrate_to_unified_dirs.py
├── docs/                  ← Architecture, decisions, design history
├── examples/              ← Anonymized templates
├── tests/
└── scan_results/          ← scan output JSON files
```

## Workflow Summary

Full details in WORKFLOW.md. The short version:

1. **`/analyze`** — Greg pastes a job posting. Assess fit (score 0–100), green/red flags, gaps, salary read, company intel, Experience to Highlight bullets. Present the analysis and wait for Greg's go/skip decision.
2. **`/apply`** — Create company hub in Obsidian → tailored JSON → PDFs → ATS check. All in one flow.
3. **Application answers** — If the application has extra questions, draft `kanban/companies/{Company}/{COMPANY}-APPLICATION-ANSWERS.md`.
4. **`/outreach`** — After applying, research LinkedIn contacts and draft messages.
5. **`/prep`** — Interview scheduled. Research interviewer, generate prep, create interview file in Obsidian.
6. **`/debrief`** — After interview. Capture what happened, structure into interview file.
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

## Obsidian Writes — Direct File Edits

Obsidian is the source of truth. Write directly to markdown files using Read/Edit/Write tools. No queue, no API, no launchd.

Use `jobbing get "{Company}"` to read all company data as structured JSON. Use `jobbing set "{Company}" --field status --value "Applied"` to update fields atomically. Prefer the API layer over direct markdown parsing to avoid context loss.

### Company hub: `kanban/companies/{Company}/{Company}.md`

```markdown
---
company: "Acme Corp"
position: "Staff Engineer"
status: "Targeted"
date: 2026-03-15
url: "https://acme.com/jobs/123"
environment: [Remote, Berlin]
salary: "€120K"
focus: [SaaS, DevTools]
score: 82
conclusion: ""
---

# Acme Corp
**Position:** Staff Engineer · **Status:** Targeted · **Score:** 82/100

## Documents
- [[ACME-CORP-CV|CV]] · [[ACME-CORP-CL|Cover Letter]]

## Interviews
- [[2026-03-15-Jane-Smith|Jane Smith — Phone Screen · Passed · Vibe 4/5]]

## Fit Assessment

## Company Research

## Experience to Highlight

## Job Description

## Outreach Contacts

## Questions I Might Get Asked

## Questions to Ask

## Conclusion
```

**Hub file rules:**

- Company identifier = company name = directory name = hub filename (e.g. `kanban/companies/Acme Corp/Acme Corp.md`)
- Obsidian resolves `[[ACME-CORP-CV]]` to the PDF in the same directory by shortest unique filename
- Documents section written by `jobbing pdf {company}` after PDF generation
- Interviews section grows as prep and debrief files are created (append, don't replace)
- Status values (in order): `Targeted` → `Applied` → `Followed-Up` → `In Progress (Interviewing)` → `Done`

### Interview file: `kanban/companies/{Company}/{date}-{slug}.md`

```markdown
---
company: "Acme Corp"
interviewer: "Jane Smith"
role: "VP Engineering"
type: "Phone Screen"
date: 2026-03-15
vibe: 4
outcome: "Passed"
---

# Jane Smith — Phone Screen · 2026-03-15
**Company:** [[Acme Corp]] · **Outcome:** Passed · **Vibe:** 4/5

## Prep Notes

## Debrief

## Transcript / Raw Notes
```

**Interview file rules:**

- Filename: `{date}-{FirstName}-{LastName}.md` (e.g. `2026-03-15-Jane-Smith.md`)
- `[[Acme Corp]]` links back to the hub — Obsidian's backlinks panel shows all interviews for a company
- `/prep` creates the file and writes Prep Notes; `/debrief` fills Debrief and outcome
- One file per interviewer per interview slot; duplicate dates append `-2`, `-3`

### Board card format: `kanban/Job Tracker.md`

```text
- [ ] [[Acme Corp|Acme Corp]] — Staff Engineer
  Score: 82 · 2026-03-15
```

Board card updated when status changes. Card moves between lanes: Targeted → Applied → Followed-Up → In Progress (Interviewing) → Done.

## CLI Commands

After `pip install -e .`, the `jobbing` CLI is available:

```bash
jobbing track create --name "Company" --position "Role" --date "2026-02-22"
jobbing track update --name "Company" --status "Applied"
jobbing track highlights --name "Company" --highlights "Bullet 1" "Bullet 2"
jobbing track research --name "Company" --research "Finding 1" "Finding 2"
jobbing track outreach --name "Company" --contacts-json contacts.json
jobbing track followup                              # check stale interview processes
jobbing track followup --threshold 7 --save         # custom threshold + save report
jobbing track validate                              # check all hubs for integrity issues
jobbing track sync                                  # reconcile board with hub frontmatter
jobbing pdf {company}
jobbing pdf {company} --cv-only
jobbing pdf {company} --cl-only
jobbing get "{company}"                             # all company data as JSON
jobbing get "{company}" --field status              # single frontmatter field
jobbing get "{company}" --section "Fit Assessment"  # single section content
jobbing set "{company}" --field status --value "Applied"
jobbing set "{company}" --section "Fit Assessment" --content "..."
jobbing scan bookmarks                              # list all bookmarks by category
jobbing scan bookmarks --categories "Climate / Impact"  # list one category
jobbing scan existing                               # list companies already tracked
jobbing scan fetch                                  # fetch all boards (~30s)
jobbing scan fetch --categories "Startup / Tech"    # fetch one category
jobbing scan fetch --limit 5                        # fetch first 5 boards
```

All track commands support `--dry-run` for previewing without writing.

## Obsidian Integration Notes

- **Source of truth**: `kanban/companies/{Company}/{Company}.md` (hub file) and `kanban/companies/{Company}/{date}-{Name}.md` (interview files)
- **All company artifacts** live in one directory: `kanban/companies/{Company}/` — hub, interviews, PDFs, JSON
- **API layer**: `jobbing get "{Company}"` returns all hub data as JSON. `jobbing set "{Company}" --field|--section` updates atomically. Prefer these over direct markdown parsing.
- **Board**: `kanban/Job Tracker.md` — updated when status changes
- **Reads**: Use `jobbing get` first. Fall back to Read tool on markdown files if you need raw content.
- **Writes**: Use `jobbing set` for fields and sections. Use Edit/Write for structural changes. No queue, no API, no launchd.
- **PDFs**: `jobbing pdf {company}` generates PDFs into the company dir and updates `## Documents` in the hub
- **Status values** (in order): `Targeted` → `Applied` → `Followed-Up` → `In Progress (Interviewing)` → `Done`. New entries default to **Targeted**. Do NOT invent new status values.
- **Company identifier** = company name = directory name = hub filename (no page_id concept)
- **Score**: `score:` field in YAML frontmatter. Set when Fit Assessment runs.

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
- Auto-mark "Applied" or any other status — status updates are Greg's decision
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

### Job Postings and Research

- Try to fetch job postings via web search/fetch tools — LinkedIn, Greenhouse, Lever, SmartRecruiters, Workable, and most job boards are blocked. **Always use Greg's Chrome browser** (Claude in Chrome MCP tools) to read job postings. This is the only reliable path.
- Score roles based on title and company name alone — always fetch and read the actual JD before scoring
- Present unverified data as sourced facts — if a data point came from a search snippet or subagent and you didn't read the source page yourself, say so

### Technical

- Create files outside `kanban/companies/{Company}/` for company-specific content (CVs, CLs, JSON, interviews, application answers)
- Leave TODO comments or placeholder content in JSON files
- Claim you included something in the JSON that you didn't actually include — verify your own work before reporting

### Ethical

- Apply to defense contractors, military technology, weapons systems, or companies whose primary customer is military/intelligence — this is a firm exclusion, non-negotiable
- Misrepresent Greg's work authorization — US citizen (no sponsorship needed for US), German permanent residency (no sponsorship needed for EU/DE)
