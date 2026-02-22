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

## Project Structure

```
Jobbing/
├── CLAUDE.md              ← you are here
├── WORKFLOW.md            ← authoritative workflow (read first)
├── CONTEXT.md             ← Greg's profile and career history (read second)
├── CV-GREGORY-DAMIANI.pdf ← master CV (generic, pre-tailoring)
├── job-scan-*.md          ← periodic job market scan notes
│
├── generate_pdfs.py       ← PDF generator script
├── notion_update.py       ← Notion API client
├── notion_queue_runner.sh ← launchd queue processor
├── pyproject.toml         ← Python deps (reportlab)
├── .env                   ← Notion API key
├── .venv/                 ← Python virtual environment
│
├── companies/             ← all company-specific content
│   └── {company}/
│       ├── {company}.json                    ← tailored CV + CL data
│       ├── {COMPANY}-CV.pdf                  ← generated CV
│       ├── {COMPANY}-CL.pdf                  ← generated cover letter
│       ├── {COMPANY}-APPLICATION-ANSWERS.md  ← application questions
│       ├── {COMPANY}-INTERVIEW-PREP.md       ← interview prep
│       └── (other company-specific docs)
│
├── notion_queue/          ← transient queue files (launchd watches this)
└── notion_queue_results/  ← processed queue audit trail
```

## Workflow Summary

Full details in WORKFLOW.md. The short version:

1. **Analyze** — Greg pastes a job posting. Claude Cowork updates the name of the conversation - "{COMPANY} - {ROLE}". Assess fit (score 0–100), green/red flags, gaps, salary read, company intel, Experience to Highlight bullets. Present the analysis and wait for Greg's go/skip decision.
2. **Notion entry** — Write a `create` JSON to `notion_queue/`. The launchd agent processes it automatically.
3. **Generate content** — Create `companies/{company}/{company}.json` using `companies/dash0/dash0.json` as the structural template. Tailor CV and CL per WORKFLOW.md rules.
4. **Generate PDFs** — Run `.venv/bin/python3 generate_pdfs.py {company}`.
5. **ATS check** — Extract text from the PDF, count keyword frequencies, verify clean parsing.
6. **Application answers** — If the application has extra questions, draft `companies/{company}/{COMPANY}-APPLICATION-ANSWERS.md`.
7. **Notion is the tracker** — all application status lives in the Notion database.

## Critical Rules

**Chronology is sacred.** Solo Recon and Modern Electric are CURRENT roles (2024–present). "Most recently" always means these. Never lead with Mobimeo as most recent. Check CONTEXT.md timeline before writing.

**People management started mid-2017.** That's 8+ years as of 2026. Never write "6+ years."

**No AI tells.** Never write summative self-congratulatory sentences like "my experience aligns perfectly with this role." Show, don't tell. Let specifics speak for themselves. See the "Writing Style" section in CONTEXT.md.

**No fake metrics.** Don't invent percentages, time savings, or impact numbers that aren't in CONTEXT.md.

**Experience to Highlight is a checkpoint.** Present the bullets to Greg explicitly and wait for feedback before generating documents. Don't rubber-stamp.

## Commands

### Notion writes — queue only

The queue is the only reliable write path. Write JSON to `notion_queue/` and the launchd agent on Greg's Mac processes it automatically. Do not attempt Notion MCP writes or direct CLI calls from Cowork.

```json
{"command": "create", "name": "Company", "position": "Role", "date": "2026-02-20", ...}
{"command": "update", "page_id": "PAGE_ID", "status": "Applied"}
{"command": "update", "page_id": "PAGE_ID", "status": "Done", "conclusion": "Outcome text"}
{"command": "highlights", "page_id": "PAGE_ID", "highlights": ["Bullet 1", "Bullet 2"]}
{"command": "research", "name": "Company", "research": ["Finding 1", "Finding 2"]}
{"command": "outreach", "name": "Company", "contacts": [{"name": "Jane Smith", "title": "VP Eng", "linkedin": "https://...", "note": "Leads Platform org, ex-Google SRE", "message": "Hi Jane — I applied for the Platform Lead role at Company. I built an IDP at 1KOMMA5° and led 23 eng at Mobimeo. Would love to connect."}]}
```

**Status updates are Greg's decision.** Do not auto-mark "Applied" or any other status. Greg will explicitly ask for status changes.

### PDF generation

```bash
.venv/bin/python3 generate_pdfs.py {company}
.venv/bin/python3 generate_pdfs.py {company} --cv-only
.venv/bin/python3 generate_pdfs.py {company} --cl-only
```

**Cowork note:** The `.venv/` symlink points to Greg's local Python and may not resolve in the Cowork VM. If it breaks, fall back to the queue for Notion and ask Greg to run PDF generation locally.

### Greg's local CLI (not for Cowork use)

These work on Greg's Mac but not from Cowork:

```bash
.venv/bin/python3 notion_update.py create --name "Company" --position "Role" --date "2026-02-20"
.venv/bin/python3 notion_update.py update --page-id "PAGE_ID" --status "Applied" --conclusion "Outcome"
.venv/bin/python3 notion_update.py research --name "Company" --research "Finding 1" "Finding 2"
.venv/bin/python3 notion_update.py outreach --name "Company" --contacts-json contacts.json
.venv/bin/python3 notion_update.py run-queue
```

## Notion Integration Notes

- **Notion is the single source of truth** for all application tracking, company research, and outreach contacts.
- **Writes**: Queue-based only. Write JSON to `notion_queue/`, launchd picks it up.
- **Reads**: Notion MCP tools (`notion-fetch`, `notion-search`) work for verification.
- **DON'T USE NOTION MCP FOR WRITES — IT IS BUGGY AS HELL.** Known Zod serialization bug on every write tool (`update-page`, `create-pages`). Both fail with "Expected object, received string" regardless of payload format. Do not attempt. Use the queue system for all writes.
- **File uploads**: Not supported by Notion API for internal integrations. Greg uploads PDFs manually.
- **Database ID**: `734d746c43b149298993464f5ccc23e7`
- **Page body sections**: "Experience to Highlight", "Company Research", and "Outreach Contacts" are managed as heading_3 + bullet blocks. Each command replaces the existing section — safe to re-run.

## Location Logic

- **European roles**: "Berlin, Germany • EU-based • Remote"
- **US roles**: "New York, NY • Berlin, Germany • Remote"
- **Global/ambiguous**: "Berlin, Germany • New York, NY • Remote"

## Do Not

- Modify `generate_pdfs.py` or `notion_update.py` unless Greg asks
- Create files outside `companies/{company}/` for company-specific content
- Skip the fit assessment and go straight to document generation
- Claim Greg has experience he doesn't have (check CONTEXT.md)
- Use marketing language in CVs or cover letters
- Leave TODO comments or placeholder content in JSON files
