# Job Application Workflow

**This is the authoritative workflow document.** If CONTEXT.md conflicts with anything here, WORKFLOW.md wins. Read this file first, then CONTEXT.md for profile/history context.

## Architecture

- **`jobbing` CLI** — unified command for PDF generation and tracker operations (`pip install -e .`)
- **Obsidian kanban** — source of truth for all application tracking (`kanban/`)
- **One data file per company:** `companies/{company}/{company}.json` — contains all tailored CV and CL content
- **Output:** `companies/{company}/{COMPANY}-CV.pdf` and `companies/{company}/{COMPANY}-CL.pdf`
- **All company files live in `companies/{company}/`** — JSON data, PDFs, application answers, etc.
- **Claude Code skills** — `/analyze`, `/apply`, `/outreach`, `/track` in `.claude/skills/`

## Step 1: Role Analysis & Discussion

Greg pastes a job posting. Claude analyzes:

- **Fit assessment:** Underqualified / right in the pocket / overqualified
- **Match score:** 0–100 (see Title Flexibility below)
- **Green flags:** Strong alignment with Greg's experience (cite specific roles and achievements)
- **Red flags:** Concerns about the role, company, or posting itself. Look for:
  - Vague titles masking lower-level work
  - Unrealistic scope for one person
  - "Startup" roles that are really contractor gigs
  - Companies with poor Glassdoor reviews or recent layoffs
  - Salary ranges below market for the level
- **Gaps:** Skills or experience the posting asks for that Greg lacks or is light on
- **Missing keywords:** Terms to weave into the CV if we proceed
- **Location:** Which location to use (Berlin or New York), or both
- **Salary read:** Benchmark against CONTEXT.md salary data. Research if needed via web search.
- **Company intel:** Quick web search for company size, funding stage, recent news, Glassdoor sentiment

### Title Flexibility

**Do not heavily penalize posted title/level in the fit score.** Job postings often advertise a level band (e.g., "Software Engineer, 4+ years") but the actual title and seniority are negotiable once the hiring team reviews the candidate.

When the tech stack, domain, and responsibilities are a strong match but the posted title seems junior relative to Greg's experience, treat this as a **mild yellow flag** (note it, don't tank the score). The score should primarily reflect: (1) technical and domain alignment, (2) company quality and trajectory, (3) actual responsibilities described in the posting, and (4) whether the role could plausibly be leveled up. Reserve heavy score penalties for cases where the role's *responsibilities* (not just title) are genuinely junior.

- **Experience to Highlight:** Draft the bullet points that would go into the hub's `## Experience to Highlight` section. Present these to Greg explicitly — this is a review checkpoint, not a rubber stamp. Pay special attention to:
  - Cleantech and sustainability experience (1KOMMA5°/Modern Electric, energy sector work)
  - Education background and how it maps to the role
  - Correct framing of domain-specific experience (e.g., energy, fintech, regulated industries)
  - Accuracy of technical claims and role characterizations

Greg and Claude discuss the analysis **and** the proposed Experience to Highlight bullets. Greg may correct, reframe, or add items. Greg decides: **proceed** or **skip**.

### Company Research (integrated into Step 1)

During the fit assessment, gather and present:

- **Funding stage and amount** (Crunchbase, press releases)
- **Headcount** (LinkedIn company page, Glassdoor)
- **Recent news** (last 6 months — layoffs, pivots, acquisitions, funding rounds)
- **Glassdoor sentiment** (overall rating, engineering reviews, leadership concerns)
- **Tech stack confirmation** (job postings, engineering blog, GitHub)

Research findings go into `## Company Research` in the hub file after Step 2 creates it.

### Outreach Research (after applying)

After Greg submits an application, research LinkedIn contacts for follow-up:

- **Hiring manager** (Director/VP Eng, Head of Platform, etc.)
- **Recruiter/TA** (Talent Acquisition, Technical Recruiter)
- **Peer connections** (engineers on the target team, mutual connections)

For each contact, capture four fields:

1. **name** and **title** — who they are
2. **linkedin** — profile URL
3. **note** — why this person matters: their background, why they're the right contact, mutual connections, relevant context about their role or team.
4. **message** — a ready-to-paste LinkedIn connection request (<300 chars) tailored to this specific contact

Contacts go into `## Outreach Contacts` in the hub file.

**Connection request message guidelines:**

- Draft a message for **every** contact
- Always mention the company name — never leave it implied
- Where possible, mention the contact's team or area
- Keep under 300 characters (LinkedIn connection request limit)
- No AI tells — no "aligns perfectly" or summative self-congratulation
- Lead with the role applied for, then one or two concrete credentials
- **End with curiosity about them**, not a hard close — show interest in their work, not just your credentials
- **Tone: warm and human.** Write like a peer reaching out, not a candidate pitching.
- **Tailor to the contact's role:** engineering leaders get Greg's credentials relevant to their domain. Recruiters get a concise experience summary. Peers get a shared-interest angle.

## Step 2: Obsidian Hub Entry

If proceeding, create a company hub file at `kanban/companies/{Company}.md`.

### What to populate

1. **Filename:** company name exactly (e.g., `Bandcamp (Songtradr).md`)
2. **YAML frontmatter:** all structured properties
3. **Body sections:** scaffold all sections; populate Job Description and Fit Assessment immediately

### Hub file format

```markdown
---
company: "Company Name"
position: "Role Title"
status: "Targeted"
date: 2026-03-15
url: "https://jobs.example.com/posting"
environment: [Remote, Berlin]
salary: "€130K–€170K"
focus: [FinTech, Payments]
vision: "Company vision statement"
mission: "Company mission statement"
score: 82
conclusion: ""
---

# Company Name
**Position:** Role Title · **Status:** Targeted · **Score:** 82/100

[Job Posting](https://jobs.example.com/posting)

## Documents

## Interviews

## Fit Assessment

## Company Research

## Experience to Highlight

## Job Description

## Outreach Contacts

## Questions I Might Get Asked

## Questions to Ask

## Conclusion
```

### How to write tracker data

All writes are direct file edits using Read/Edit/Write tools on the markdown files. No queue, no API.

**Create a new hub (Step 2):** Write `kanban/companies/{Company}.md` with the format above.

**Add the hub to the board:** Add a card to the correct lane in `kanban/Job Tracker.md`:

```text
- [ ] [[companies/Company Name|Company Name]] — Role Title · Score: 82 · 2026-03-15
```

**Update status (e.g., after applying):** Edit the `status:` field in the hub's YAML frontmatter and move the card to the correct lane in `Job Tracker.md`.

**Close out with a conclusion:** Edit `status: "Done"` and `conclusion: "Rejected after final round — internal candidate."` in the frontmatter.

**Write company research:** Edit the `## Company Research` section with bullet findings:

```markdown
## Company Research

- Founded 2020, Series B ($50M) — Feb 2025
- 120 employees, Berlin HQ
- Glassdoor 4.2/5 (engineering: strong reviews, fast-moving)
- Stack: Go, Kubernetes, PostgreSQL, Kafka
```

**Write Experience to Highlight:** Edit the `## Experience to Highlight` section with bullets approved by Greg in Step 1.

**Write Job Description:** Paste full posting text into `## Job Description`.

**Write Fit Assessment:** Edit `## Fit Assessment` with score, reasoning, flags, gaps:

```markdown
## Fit Assessment

**Score: 82/100**

**Green flags:**
- Strong match on platform engineering scope
- Cleantech domain alignment

**Red flags:**
- Series B — some execution risk

**Gaps:**
- Limited Kafka experience (have Pub/Sub)
```

Also update `score: 82` in the YAML frontmatter.

**Write outreach contacts:** Edit `## Outreach Contacts`:

```markdown
## Outreach Contacts

- **Jane Smith** — VP Engineering · [LinkedIn](https://linkedin.com/in/janesmith)
  - Leads Platform org. Ex-Google SRE. 2nd connection via Alex.
  - Message: "Hi Jane — I applied for the Platform Lead role at CompanyName. I built an IDP at 1KOMMA5° (+350% deploys) and led 23 engineers at Mobimeo. Would love to connect."
```

**Status values** (in order): `Targeted` → `Applied` → `Followed-Up` → `In Progress (Interviewing)` → `Done`. Do NOT invent new status values.

**Status updates are Greg's decision.** Do not auto-mark Applied or any other status change.

### CLI (for programmatic updates)

```bash
jobbing track create --name "Company" --position "Role" --date "2026-03-15"
jobbing track update --name "Company" --status "Applied"
jobbing track highlights --name "Company" --highlights "Bullet 1" "Bullet 2"
jobbing track research --name "Company" --research "Finding 1" "Finding 2"
jobbing track outreach --name "Company" --contacts-json contacts.json
```

All track commands support `--dry-run`.

## Step 3: Tailored CV + Cover Letter

If proceeding:

1. **Create `companies/{company}/{company}.json`** with two top-level keys: `"cv"` and `"cl"`. Use `examples/example_company.json` as the structural template.
2. **Tailor the CV data:**
   - Rewrite summary to lead with the role's core requirements
   - Reorder/rewrite core skills to front-load what matters
   - Rewrite key achievements using X-Y-Z formula ("Accomplished X as measured by Y, by doing Z")
   - Add role-specific bullets to relevant jobs (especially older roles — draw from CONTEXT.md)
   - Work in missing keywords naturally
   - Set location (Berlin, New York, or both)
   - Include `earlierExperience` section when roles like TradingScreen/JP Morgan add value
3. **Tailor the CL data:**
   - Opening: 20+ years + role-specific framing
   - Para 1: Current work (Solo Recon + Modern Electric) — chronology is sacred
   - Para 2: Most relevant leadership role for this posting
   - Para 3: Largest-scale infrastructure leadership (usually Mobimeo)
   - Para 4: Cross-functional / people leadership highlights
   - Closing: Available for conversation
   - **CRITICAL:** "Most recently" = Solo Recon/Modern Electric. Never lead with Mobimeo as "most recent."
   - Single page, professional, keyword-rich
4. **Generate PDFs:**

   ```bash
   jobbing pdf {company}
   ```

   This automatically updates `## Documents` in the hub file with CV/CL wikilinks.

5. **ATS scan:** Extract text from PDF, count keyword frequencies, verify clean parsing
6. **When Greg says to mark as Applied:** Edit `status: "Applied"` in the hub's YAML frontmatter and move the board card to the Applied lane. **Do not auto-mark Applied** — Greg decides when to update status.

## Step 4: Application Questions (if needed)

If the application has additional questions, draft answers in `companies/{company}/{COMPANY}-APPLICATION-ANSWERS.md`.

## Step 5: Interview Prep

When Greg has an upcoming interview, use `/prep` to generate targeted preparation material.

**Trigger:** "I have an interview with Thomas Roton at Bandcamp on Thursday, it's a technical screen" or "Prep me for Cozero — meeting the CTO next Tuesday."

**What it generates:**

1. Interviewer research (LinkedIn, background, connection points)
2. Likely questions (tailored to interview type + interviewer seniority)
3. Talking points (Experience to Highlight reframed for interview type)
4. Questions to ask (tailored to this interviewer's role)

**Output:** Create `kanban/interviews/{Company}/{date}-{Interviewer-Slug}.md` with prep notes, then append a wikilink to `## Interviews` in the hub file:

```markdown
## Interviews

- [[2026-03-15-Jane-Smith|Jane Smith — Phone Screen · Pending · Vibe —]]
```

If `## Questions I Might Get Asked` is empty in the hub, auto-populate it.

### Staff/Principal Interview Performance Standards

All interview prep at Greg's level must address the **Four Pillars** — the specific areas where Staff/Principal candidates most commonly fail.

1. **Quantified Impact** — The #1 rejection reason. Every story must connect technical work to hard business metrics (revenue, latency, efficiency, cost). "I don't know the numbers" is a red flag at this level.
2. **Architectural Decision Making** — Walk through real ADRs with trade-offs, buy-in process, and long-term risk mitigation. No hypotheticals — concrete decisions seen through to completion.
3. **Analytical Depth & Root Cause** — Incidents need a systematic elimination chain + architectural prevention. If the root cause was simple, it's not a Principal-level story.
4. **Executive Communication** — STAR format, under 4 minutes per answer. Systems-wide framing, not niche. Self-awareness when pushed on weak areas, not defensiveness.

**Quick prep checklist (apply to every interview):**

- Every story has a hard number
- At least one ADR walk-through ready
- Every incident story has methodology + systemic prevention
- Each answer deliverable in under 4 minutes

## Step 6: Post-Interview Debrief

After an interview, use `/debrief` to capture what happened while the conversation is fresh. Greg dumps raw thoughts; Claude structures them into the interview file.

**Trigger:** "Debrief FICO — just talked to Jess Wilson" or "Quick debrief on the Cozero technical screen."

**What it captures:**

1. Questions they asked
2. What landed (positive reactions, engagement)
3. What stumbled (under-prepared areas, caught off guard)
4. What you learned (new info about role, team, company)
5. Updated read (fit score reassessment warranted?)
6. Follow-up needed (action items, next steps, timeline)
7. Vibe (1–5 gut-feel rating)

**Output:** Write debrief to `## Debrief` in the interview file (`kanban/interviews/{Company}/{date}-{slug}.md`). Update `vibe:` and `outcome:` in the interview file's YAML frontmatter. Update the wikilink in the hub's `## Interviews` section with the outcome.

If no interview file exists yet (unscheduled debrief), create it first then write.

## Step 7: Follow-Up Cadence Monitor

Periodically check all active interview processes for staleness. Use `/followup` conversationally or `jobbing track followup` from CLI.

**Trigger:** "Any stale conversations?", "Check my follow-ups", or run `jobbing track followup`.

**What it checks:**

1. All applications with status "In Progress (Interviewing)" — read from kanban company hub files
2. For each, reads the hub's `## Interviews` section and any linked interview files for last activity date
3. Calculates days since last activity
4. Flags companies exceeding the threshold (default: 5 days, configurable via `FOLLOWUP_THRESHOLD_DAYS` in `.env`)

**Output:** A summary sorted by staleness — stale companies first with suggested follow-up actions, then recently active companies.

**No auto-actions.** This is a read-only check. Greg decides what to do based on the summary.

**CLI:**

```bash
jobbing track followup                    # default threshold (5 days)
jobbing track followup --threshold 7      # custom threshold
jobbing track followup --save             # save report to disk
```

## Step 8: Living Fit Assessment

After one or more interview rounds, the original `/analyze` score may no longer reflect reality. Use `/reassess` to update the score based on what Greg has learned.

**Trigger:** "Reassess Cozero — turns out the team is 3 people" or "Update the score for Bandcamp after the technical round."

**Inputs:**

1. Existing Fit Assessment from `## Fit Assessment` in the hub file
2. All debrief notes from linked interview files
3. Greg's verbal input on what's changed (team size, stack, scope, culture, comp)

**Output:** Updated score (0–100) with revised reasoning that explicitly states the original score, what changed, and which scoring components moved. Written directly to `## Fit Assessment` in the hub file; `score:` frontmatter field updated.

**Greg approves before writing.** The updated assessment is presented with a before/after comparison. Greg confirms before editing the file.

## Step 9: Decision Comparison

When multiple companies reach the offer stage or Greg needs a structured decision framework, use `/compare` to produce a weighted side-by-side analysis.

**Trigger:** "Compare Bandcamp and Cozero" or "Compare my top three."

**Inputs:** Hub files for specified companies — Fit Assessment, interview files, company research, salary data, vibe ratings, interview outcomes.

**Dimensions** (weighted):

| Dimension | Weight |
| --- | --- |
| Compensation | High |
| Technical Fit | High |
| Team & Culture | Medium |
| Mission Alignment | Medium |
| Growth Trajectory | Medium |
| Remote & Location | Low |
| Risk Factors | Low |

**Output:** A Markdown comparison document saved to `companies/comparison-{date}.md` with a summary table, dimension deep-dives with evidence, and a synthesis with tradeoffs. Not a single "winner" — structured tradeoffs for Greg to weigh.

**Read-only.** No file writes beyond the comparison document. Greg makes the final decision.

## Iteration

When Greg reads a PDF and wants changes:

1. Edit `companies/{company}/{company}.json` (just the data fields that need changing)
2. Re-run `jobbing pdf {company}` (or `--cv-only` / `--cl-only`)
3. Done

## JSON Data Schema

```json
{
  "companyUpper": "COMPANY",
  "cv": {
    "name": "GREGORY DAMIANI",
    "location": "Berlin, Germany • EU-based • Remote",
    "email": "gregory.damiani@gmail.com",
    "github": "https://github.com/grggls/",
    "linkedin": "https://www.linkedin.com/in/gregorydamiani/",
    "summary": ["paragraph 1", "paragraph 2", "paragraph 3"],
    "coreSkills": ["skill 1", "skill 2"],
    "keyAchievements": ["achievement 1", "achievement 2"],
    "jobs": [
      {
        "title": "Job Title",
        "company": "Company Name, Location",
        "dates": "Month Year – Month Year",
        "bullets": ["bullet 1", "bullet 2"]
      }
    ],
    "earlierExperience": [
      {
        "title": "Job Title",
        "company": "Company Name",
        "dates": "optional",
        "bullets": ["bullet 1"]
      }
    ],
    "education": [
      {
        "degree": "Degree Name",
        "school": "School Name, Location",
        "detail": "Optional detail"
      }
    ],
    "skills": {
      "Category": "item1, item2, item3"
    }
  },
  "cl": {
    "date": "Month Day, Year",
    "recipient": "Hiring Manager",
    "company": "Company Name",
    "greeting": "Dear Hiring Team,",
    "paragraphs": ["opening", "para 1", "para 2", "para 3", "para 4", "closing"],
    "closing": "Best regards,",
    "name": "Gregory Damiani",
    "email": "gregory.damiani@gmail.com",
    "linkedin": "linkedin.com/in/gregorydamiani"
  }
}
```

## Naming Convention

All company files live in `companies/{company}/`:

```text
companies/{company}/{company}.json                   — tailored data (lowercase)
companies/{company}/{COMPANY}-CV.pdf                 — CV output
companies/{company}/{COMPANY}-CL.pdf                 — cover letter output
companies/{company}/{COMPANY}-APPLICATION-ANSWERS.md — application questions (when needed)
```

All tracker files live in `kanban/`:

```text
kanban/Job Tracker.md                                — kanban board
kanban/companies/{Company}.md                        — company hub (exact case)
kanban/interviews/{Company}/{date}-{Slug}.md         — interview files
```

## Running the PDF Generator

```bash
jobbing pdf {company}              # both CV and CL
jobbing pdf {company} --cv-only    # just the CV
jobbing pdf {company} --cl-only    # just the cover letter
jobbing pdf {company} --output-dir /path  # custom output directory
```

Reads from `companies/{company}/{company}.json` and outputs PDFs to the same directory (unless `--output-dir` is specified). Uses DejaVu Sans fonts (full Unicode: bullets, em-dashes, euro signs) where available, with Helvetica fallback.

After generating PDFs, automatically updates `## Documents` in the hub file with wikilinks:

```markdown
## Documents

- [[COMPANY-CV|CV]] · [[COMPANY-CL|Cover Letter]]
```

## Location Logic

- **European roles:** Use "Berlin, Germany • EU-based • Remote"
- **US roles:** Use "New York, NY • Berlin, Germany • Remote"
- **Global/ambiguous:** Use "Berlin, Germany • New York, NY • Remote"

## Cleanup

After generating PDFs, the only artifacts are:

- `companies/{company}/{company}.json` — keep (source of truth for what was sent)
- `companies/{company}/*.pdf` — keep (the deliverables)
- `companies/{company}/*-APPLICATION-ANSWERS.md` — keep (when applicable)
- `kanban/companies/{Company}.md` — keep (live tracker hub)
- `kanban/interviews/{Company}/` — keep (interview history)
