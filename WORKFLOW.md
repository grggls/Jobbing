# Job Application Workflow

**This is the authoritative workflow document.** If CONTEXT.md conflicts with anything here, WORKFLOW.md wins. Read this file first, then CONTEXT.md for profile/history context.

## Architecture

- **`jobbing` CLI** — unified command for PDF generation, tracker operations, and queue processing (`pip install -e .`)
- **One data file per company:** `companies/{company}/{company}.json` — contains all tailored CV and CL content
- **Output:** `companies/{company}/{COMPANY}-CV.pdf` and `companies/{company}/{COMPANY}-CL.pdf`
- **All company files live in `companies/{company}/`** — JSON data, PDFs, application answers, interview prep, etc.
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

**Do not heavily penalize posted title/level in the fit score.** Job postings often advertise a level band (e.g., "Software Engineer, 4+ years") but the actual title and seniority are negotiable once the hiring team reviews the candidate. Real-world example: Acto posted a Senior Engineer role with leadership responsibilities; after reviewing Greg's experience, both sides agreed it was a Staff role.

When the tech stack, domain, and responsibilities are a strong match but the posted title seems junior relative to Greg's experience, treat this as a **mild yellow flag** (note it, don't tank the score). The score should primarily reflect: (1) technical and domain alignment, (2) company quality and trajectory, (3) actual responsibilities described in the posting, and (4) whether the role could plausibly be leveled up. Reserve heavy score penalties for cases where the role's *responsibilities* (not just title) are genuinely junior — e.g., pure execution work with no architecture ownership, no cross-team collaboration, no platform design.

- **Experience to Highlight:** Draft the bullet points that would go into the Notion tracker's "Experience to Highlight" section. Present these to Greg explicitly — this is a review checkpoint, not a rubber stamp. Pay special attention to:
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

Store research findings on the Notion page via a `research` queue file after Step 2 creates the page.

### Outreach Research (after applying)

After Greg submits an application, research LinkedIn contacts for follow-up:

- **Hiring manager** (Director/VP Eng, Head of Platform, etc.)
- **Recruiter/TA** (Talent Acquisition, Technical Recruiter)
- **Peer connections** (engineers on the target team, mutual connections)

For each contact, capture four fields:

1. **name** and **title** — who they are
2. **linkedin** — profile URL
3. **note** — why this person matters: their background, why they're the right contact, mutual connections, relevant context about their role or team. Think "intel for Greg before he sends the message."
4. **message** — a ready-to-paste LinkedIn connection request (<300 chars) tailored to this specific contact

Store on the Notion page via an `outreach` queue file. This sets "Follow on Linkedin" to "No" (contacts identified, outreach pending). Each contact renders in Notion as a bullet with nested sub-bullets for the note and message.

**Connection request message guidelines:**

- Draft a message for **every** contact — these go into the `"message"` field
- Always mention the company name ("at Kentik", "at Ashby") — never leave it implied
- Where possible, mention the contact's team or area ("your platform engineering team at Trade Republic")
- Keep under 300 characters (LinkedIn connection request limit)
- No AI tells — no "aligns perfectly" or summative self-congratulation
- Lead with the role applied for, then one or two concrete credentials
- **End with curiosity about them**, not a hard close. "Would love to learn more about {Company}" or "Would love to hear about what you're building at {Team}" — not "Happy to connect" or "Would welcome a conversation." Show interest in their work, not just your own credentials.
- **Tone: warm and human.** These are people, not ATS systems. Write like a peer reaching out, not a candidate pitching. Avoid stiff, transactional language.
- **Tailor to the contact's role:** engineering leaders get the Greg credentials most relevant to their domain (IDP work for platform leads, scale/SLO numbers for SRE leads, team-building for VPs). Recruiters get a concise experience summary. Peers get a shared-interest angle.
- **Map Greg's experience to what this person cares about.** Don't just list generic achievements — pick the 1-2 things from CONTEXT.md that would resonate with this specific person's responsibilities.
- **Reference example:** "I applied for the Lead Cloud Platform Engineer role at Think-it. I built AWS clouds at Mobimeo (Deutsche Bahn) and have years in cleantech/sustainability (1KOMMA5°, Modern Electric, Yara Digital Farming). I'm LFC131 certified (Linux Foundation Green Software). Would love to learn more about Think-it"

## Step 2: Notion Tracker Entry

If proceeding, create a tracking entry in the [Job Applications database](https://www.notion.so/grggls/734d746c43b149298993464f5ccc23e7?v=a02dac09c0354f7496b7d4f0733a1233).

### What to populate

1. **Page title:** company name (e.g., "Perplexity")
2. **Status:** defaults to "Targeted" from the template — no change needed initially
3. **Properties from the job posting and Step 1 analysis:**
   - **Start Date:** today's date
   - **URL:** link to the job description/application page (if available)
   - **Open Position:** the role title from the posting
   - **Environment:** remote / hybrid / on-site and location (multi-select)
   - **Salary (Range):** from the posting or Step 1 salary benchmark
   - **Company Focus:** what the company does (multi-select tags)
   - **Vision:** the company's stated vision (from posting or company intel)
   - **Mission:** the company's stated mission (from posting or company intel)
4. **Populate "Experience to Highlight"** in the page body with Greg's most relevant skills and experience for this role, drawn from the Step 1 analysis (green flags, matching skills, relevant achievements)
5. **After Step 3 generates PDFs**, upload `{COMPANY}-CV.pdf` and `{COMPANY}-CL.pdf` as attachments to the Notion page

### How to populate

Use the **queue-based system**: write a JSON file to `notion_queue/`, and a launchd agent on Greg's Mac picks it up and runs `jobbing queue` automatically.

**Create the entry (after Step 1 discussion):**

Write a JSON file to `notion_queue/` with a descriptive name (e.g., `notion_queue/20260219_companyname_create.json`):

```json
{
  "command": "create",
  "name": "CompanyName",
  "position": "Role Title",
  "date": "2026-02-19",
  "url": "https://jobs.example.com/posting",
  "environment": ["Remote", "Berlin office"],
  "salary": "€130K–€170K",
  "focus": ["FinTech", "Payments"],
  "vision": "Company vision statement",
  "mission": "Company mission statement",
  "highlights": ["Relevant skill 1", "Relevant skill 2", "Relevant skill 3"]
}
```

**Update properties later (e.g., after applying):**

```json
{
  "command": "update",
  "page_id": "PAGE_ID",
  "status": "Applied"
}
```

**Close out an application with a conclusion:**

```json
{
  "command": "update",
  "page_id": "PAGE_ID",
  "status": "Done",
  "conclusion": "Rejected after final round — they went with an internal candidate."
}
```

**Replace highlights on an existing page:**

```json
{
  "command": "highlights",
  "page_id": "PAGE_ID",
  "highlights": ["New bullet 1", "New bullet 2"]
}
```

**Add company research to a page (by name or page_id):**

```json
{
  "command": "research",
  "name": "CompanyName",
  "research": ["Founded 2020, Series B ($50M)", "120 employees, Berlin HQ", "Glassdoor 4.2/5"]
}
```

**Add outreach contacts to a page (sets Follow on Linkedin to "No"):**

```json
{
  "command": "outreach",
  "name": "CompanyName",
  "contacts": [
    {
      "name": "Jane Smith",
      "title": "VP Engineering",
      "linkedin": "https://www.linkedin.com/in/janesmith",
      "note": "Leads the Platform org. Ex-Google SRE. 2nd connection via Alex.",
      "message": "Hi Jane — I applied for the Platform Lead role at CompanyName. I built an IDP at 1KOMMA5° (+350% deploys) and led 23 engineers at Mobimeo. Would love to connect."
    },
    {
      "name": "Bob Jones",
      "title": "Senior Technical Recruiter",
      "linkedin": "https://www.linkedin.com/in/bobjones",
      "note": "Posts actively about CompanyName eng roles. Joined 6 months ago from Stripe.",
      "message": "Hi Bob — I applied for the Platform Lead role at CompanyName. 20+ yrs in platform eng and SRE, most recently Director-level at Mobimeo (Deutsche Bahn). Happy to connect."
    }
  ]
}
```

**Interview prep** (write prep notes to an Interviews DB row):

```json
{
  "command": "interview_prep",
  "name": "CompanyName",
  "date": "2026-03-15",
  "interviewer": "Jane Smith — VP Engineering",
  "interview_type": "Hiring Manager",
  "prep_notes": "## Key Topics\n- Platform strategy\n- Team scaling\n\n## Their Background\n- Ex-Google SRE, 12 years",
  "questions_to_ask": ["What's the team's biggest challenge right now?", "How do you measure platform success?"]
}
```

**Debrief** (write debrief + outcome to an Interviews DB row):

```json
{
  "command": "debrief",
  "name": "CompanyName",
  "date": "2026-03-15",
  "interviewer": "Jane Smith — VP Engineering",
  "interview_type": "Hiring Manager",
  "outcome": "Passed",
  "vibe": 4,
  "debrief": "Strong conversation about platform strategy. She was engaged on the IDP work at 1KOMMA5°.",
  "questions_they_asked": ["How did you handle the Terraform migration?", "Tell me about incident response at Mobimeo"],
  "questions_i_asked": ["What's the on-call rotation?", "How is the platform team structured?"],
  "follow_up": "Send architecture diagram of the IDP. Next round: system design with lead architect."
}
```

Both `interview_prep` and `debrief` find or create the interview row by matching interviewer name and date. If no Interviews DB exists on the page, one is created automatically.

Both `research` and `outreach` commands accept either `"name"` (looks up the page) or `"page_id"`. They replace existing sections — safe to re-run with updated data.

The launchd agent (`com.grggls.notion-queue`) watches the `notion_queue/` directory. When a file appears, it runs `jobbing queue` via the project venv (`.venv/bin/python3 -m jobbing queue`). Processed files are moved to `notion_queue_results/` with timestamped result files. The plist lives at `~/Library/LaunchAgents/com.grggls.notion-queue.plist`. After adding new queue commands, run `pip install -e .` in the venv — the editable install picks up source changes immediately.

The `create` command is idempotent — if a page with the same company name exists, it updates properties and rebuilds all managed body sections. Queue files are claimed atomically (renamed to `.processing` before Notion API calls) to prevent race conditions with the launchd agent.

**Page layout** (canonical order, enforced by code — matches application chronology):

1. **Interviews** — inline child database with 5 properties: Title (interviewer name/role), Date, Type (select: Phone Screen, Technical, System Design, Behavioral, Panel, Hiring Manager, Executive, Take-Home), Vibe (select: 1–5), Outcome (select: Passed, Rejected, Pending, Withdrawn). Each row's page body holds Prep Notes and Debrief toggles. Created once on new pages; preserved on updates.
2. *(divider)* — visual separator between database and content sections
3. **Job Description** — toggle heading_3 with posting text (discovery: what's the role?)
4. **Fit Assessment** — toggle heading_3 with score, reasoning, green/red flags, gaps, keywords (analysis: how well do we match?)
5. **Company Research** — toggle heading_3 with bulleted list (research: what's the company like?)
6. **Experience to Highlight** — toggle heading_3 with bulleted list (preparation: CV/CL talking points)
7. **Outreach Contacts** — toggle heading_3 with contact bullets (post-apply: who to reach out to)
8. **Questions I Might Get Asked** — toggle heading_3 with Q&A bullets (interview prep: anticipated questions)
9. **Questions to Ask** — toggle heading_3 with bulleted list (during interview: our questions)

The `create` command always rebuilds the 7 toggle sections in this order. On existing pages, it reads current section content before removal and preserves data for any section the new JSON doesn't include — a `create` with only `highlights` won't wipe previously-written `research` or `job_description`. Individual section commands (`highlights`, `research`, `job_description`, `outreach`, etc.) replace their target section in place.

**Direct CLI usage** (after `pip install -e .`):

```bash
jobbing track create --name "Company" --position "Role" --date "2026-02-19"
jobbing track update --page-id "PAGE_ID" --status "Applied"
jobbing track highlights --page-id "PAGE_ID" --highlights "Bullet 1" "Bullet 2"
jobbing track research --name "Company" --research "Finding 1" "Finding 2"
jobbing track outreach --name "Company" --contacts-json contacts.json
jobbing queue  # process all files in notion_queue/
```

All track commands support `--dry-run`. Config loads `NOTION_API_KEY` from (in order): environment variable, `.env` file in the Jobbing directory, or `~/.zshrc-secrets`.

**Why not Notion MCP or browser automation?**

- MCP write tools have a [known parameter serialization bug](https://github.com/makenotion/notion-mcp-server/issues/176) (Zod object/string mismatch)
- MCP read tools (`notion-fetch`, `notion-search`) work and can verify data
- Browser automation via Chrome MCP is unreliable (timeouts, login confusion)
- The Cowork VM's network blocks direct access to `api.notion.com`

**File uploads** are not supported by the Notion API for internal integrations — Greg uploads CV/CL PDFs manually.

### Reference pages

- Default template: `30c5de3c370f80af9034ef052813029e`
- Example (Perplexity): `30c5de3c370f8095abd6ea4bb52a03dd`
- Database ID: `734d746c43b149298993464f5ccc23e7`
- Data source ID: `7d7b1f6a-4af7-40e1-913f-95b65a89ae41`

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

5. **ATS scan:** Extract text from PDF, count keyword frequencies, verify clean parsing
6. **When Greg says to mark as Applied:** Write a queue file to update the status:

   ```json
   {"command": "update", "page_id": "PAGE_ID", "status": "Applied"}
   ```

   Save to `notion_queue/` — the launchd agent will process it automatically. **Do not auto-mark Applied** — Greg decides when to update status. Greg uploads CV/CL PDFs manually.

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

**Output:** Prep Notes toggle in the Interviews DB row page body, via `interview_prep` queue command. If "Questions I Might Get Asked" is empty, auto-populates that section too.

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
companies/{company}/{COMPANY}-INTERVIEW-PREP.md      — interview prep (when needed)
```

## Running the PDF Generator

```bash
jobbing pdf {company}              # both CV and CL
jobbing pdf {company} --cv-only    # just the CV
jobbing pdf {company} --cl-only    # just the cover letter
jobbing pdf {company} --output-dir /path  # custom output directory
```

Reads from `companies/{company}/{company}.json` and outputs PDFs to the same directory (unless `--output-dir` is specified). Uses DejaVu Sans fonts (full Unicode: bullets, em-dashes, euro signs) where available, with Helvetica fallback.

## Location Logic

- **European roles:** Use "Berlin, Germany • EU-based • Remote"
- **US roles:** Use "New York, NY • Berlin, Germany • Remote"
- **Global/ambiguous:** Use "Berlin, Germany • New York, NY • Remote"

## Cleanup

After generating PDFs, there are no intermediate files to clean up. The only artifacts are:

- `companies/{company}/{company}.json` — keep (this is the source of truth for what was sent)
- `companies/{company}/*.pdf` — keep (the deliverables)
- `companies/{company}/*-APPLICATION-ANSWERS.md` — keep (when applicable)
- `notion_queue/` — transient (files are moved to results after processing)
- `notion_queue_results/` — audit trail (log of all processed queue operations)
