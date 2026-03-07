# Jobbing v2 — Interview Intelligence & Pipeline Management

**Product Requirements Document**
**v1.2 — Draft | March 7, 2026**

---

## Table of Contents

1. Why This Update
2. Current State Assessment
3. What We Hope to Gain
4. Feature Specifications
   - 4.1 Interviews Database Schema Standardization
   - 4.2 Interview Prep Generation (Trigger: Interview Scheduled)
   - 4.3 Post-Interview Debrief Capture
   - 4.4 Follow-Up Cadence Monitor
   - 4.5 Living Fit Assessment
   - 4.6 Decision Comparison Framework
5. Implementation Plan
   - Phase 1: Foundation (Interviews DB Schema + Read/Write Path)
   - Phase 2: Interview Prep Generation
   - Phase 3: Post-Interview Debrief
   - Phase 4: Follow-Up Cadence Monitor
   - Phase 5: Living Fit Assessment
   - Phase 6: Decision Comparison Framework
6. Changes to Existing System
7. Validation Strategy
8. Feedback Mechanisms
9. Risks and Mitigations
10. Success Metrics
11. Glossary

---

## 1. Why This Update

Jobbing v1 is strong on the front end of the application funnel. The /analyze skill produces honest, data-backed fit assessments. The /apply skill generates tailored CVs and cover letters that consistently pass ATS parsing. The Notion tracker captures company research, experience highlights, and outreach contacts in a structured, searchable format. The queue-based write system works reliably despite Notion API limitations.

But the system drops off right when the stakes are highest: the interview phase. An audit of all 10 "In Progress (Interviewing)" entries in the tracker revealed consistent gaps:

- 7 of 10 active interview processes are missing "Questions I Might Get Asked" — the highest-ROI section for interview prep.
- 5 of 10 are missing "Questions to Ask."
- All 10 are missing the newly created "Fit Assessment" section and Score property.

*Note: As of March 6, 2026, new pages created via the queue automatically get the Interviews inline database and all 7 managed toggle sections scaffolded as empty placeholders. The gaps above apply only to pages created before this change.*
- No mechanism exists for capturing what happens after an interview — debrief notes, updated reads on the company, revised scoring.
- No systematic follow-up cadence tracking — conversations go stale without anyone noticing.
- No framework for comparing multiple active opportunities when offers overlap.

The pattern is clear: v1 optimizes for getting into the pipeline but provides minimal support for moving through it. For someone managing 10 concurrent interview processes across different stages, time zones, and interview formats, this is the gap that costs the most. A missed follow-up, an under-prepared technical screen, or a poorly evaluated offer can each cost weeks of effort.

**This project addresses that gap by extending Jobbing's automation and structure into the interview lifecycle — from the moment an interview is scheduled through to offer comparison.**

---

## 2. Current State Assessment

### What Works Well

- Fit scoring (/analyze + /scoring) produces calibrated, explainable scores that Greg trusts for go/skip decisions.
- Document generation (/apply) creates tailored CVs and cover letters with ATS verification in a single automated flow.
- Queue-based Notion writes are reliable and idempotent — the launchd agent processes files atomically with audit trails.
- Company research, outreach contacts, and experience highlights are captured in a consistent, searchable Notion structure.
- The /scan and /disaggregate skills automate job discovery and aggregator spam parsing.

### What's Missing

| Capability | Current State | Proposed |
|---|---|---|
| Interviews DB schema | Exists on all new pages (2-column: title + date), missing on some older pages | Standardized schema with type, vibe, outcome properties + page-body content for prep and debrief |
| Interview prep | Manual, often skipped | Auto-generated when interview is scheduled via `/prep` |
| Post-interview debrief | Does not exist | Structured capture via `/debrief` |
| Follow-up cadence | No tracking | `/followup` skill surfaces stale conversations on-demand |
| Living Fit Assessment | Score is a cold-read snapshot | `/reassess` updates score with interview learnings |
| Offer comparison | Does not exist | `/compare` produces weighted side-by-side |

---

## 3. What We Hope to Gain

**The goal is not more automation for its own sake. It's about making sure Greg's time and energy during the interview phase — the most demanding part of the job search — is spent on preparation and performance rather than administration and memory.**

### Concrete Outcomes

- Never walk into an interview without role-specific, interviewer-aware prep material. The system generates it the moment an interview lands on the calendar, not as an afterthought.
- Capture every interview while it's fresh. Five minutes of structured debrief after each conversation compounds into pattern recognition across companies — what questions come up repeatedly, what answers land, which companies feel right.
- No stale conversations. When a promising lead goes quiet for five days, the system surfaces it so Greg can follow up intentionally rather than discovering the gap two weeks later.
- Make scoring a living signal, not a snapshot. The initial /analyze score is a cold read based on a job posting. After three rounds of interviews, Greg knows things the posting never said. The score should reflect that updated understanding.
- When multiple offers arrive in the same week, have the comparison framework already built. Compensation, team quality, mission alignment, remote flexibility, growth trajectory — weighted and side-by-side, informed by weeks of accumulated debrief data.

### What Success Looks Like

Greg opens a Notion tracker page before any interview and finds: structured prep tailored to that specific interviewer and interview type, a running log of prior conversations with debrief notes and vibe reads, an up-to-date fit score that reflects what he's actually learned, and a clear record of what follow-up is needed and when. When two companies make offers, he runs `/compare` and gets a substantive side-by-side that incorporates all of the above — not just salary numbers, but the full picture.

---

## 4. Feature Specifications

### 4.1 Interviews Database Schema Standardization

#### Problem

The Interviews inline database currently has a minimal 2-column schema: "Interviewer Name and Role" (title) and "Date". New pages get this database automatically via `_add_interviews_database()`, but there's no structure for capturing interview type, preparation notes, debrief output, questions asked, or subjective assessment. This means every other feature in this PRD has nowhere to write its data.

#### Solution

Define a canonical Interviews database schema and migrate existing instances to match. Long-form content (prep notes, debrief) goes in the **page body** of each Interviews DB row (every row in an inline Notion DB is itself a page with a body). Structured data (type, vibe, outcome) stays as DB properties.

This split avoids the **2000-character limit** on Notion Rich Text properties — prep notes and debriefs routinely exceed this.

#### Schema: DB Properties (structured data)

| Property | Type | Required | Description |
|---|---|---|---|
| Interviewer Name and Role | Title | Yes | Name and title of interviewer (e.g., "Thomas Roton, Engineering Manager") |
| Date | Date | Yes | Interview date and time |
| Type | Select | No | Phone Screen, Technical, System Design, Behavioral, Panel, Hiring Manager, Executive, Take-Home |
| Vibe | Select | No | 1 (poor) through 5 (excellent) — gut-feel assessment of mutual fit |
| Outcome | Select | No | Pending, Passed, Rejected, Withdrawn |

#### Schema: Page Body (long-form content)

Each Interviews DB row is a Notion page. The following sections are written as toggle heading_3 blocks inside the row's page body:

| Section | Block Type | Written By | Content |
|---|---|---|---|
| Prep Notes | toggle heading_3 | `/prep` skill → `interview_prep` queue command | Interviewer research, likely questions, talking points, questions to ask this person |
| Debrief | toggle heading_3 | `/debrief` skill → `debrief` queue command | Structured post-interview notes (what they asked, what landed, what stumbled, what you learned, updated read) |
| Questions They Asked | bulleted list inside Debrief toggle | `/debrief` | Actual questions asked during the interview |
| Questions I Asked | bulleted list inside Debrief toggle | `/debrief` | Questions Greg asked, with notes on responses received |
| Follow-Up | paragraph inside Debrief toggle | `/debrief` | Next steps, action items, who to contact |

#### Helper Methods Required

The current code creates the Interviews DB via `_add_interviews_database()` but **discards the database ID**. To write rows or update the schema on existing pages, we need:

- **`_find_interviews_db(page_id) -> str | None`** — Walk the page's children blocks, find the `child_database` block with title "Interviews", return its database ID. This is the gating function for every subsequent phase.
- **`_find_interview_entry(db_id, interviewer=None, date=None) -> str | None`** — Query the Interviews DB for a row matching interviewer name and/or date. Returns the row's page ID.
- **`add_interview_entry(page_id, interview: Interview) -> str`** — Find the Interviews DB on the page, create a new row with properties (Interviewer, Date, Type, Vibe, Outcome) and page-body content. Only write toggle sections that have content — an `interview_prep` call writes Prep Notes only (no empty Debrief placeholder); a `debrief` create-if-missing writes Debrief only. Returns the new row's page ID.
- **`update_interview_entry(entry_id, interview: Interview) -> None`** — Update an existing row's properties via `PATCH /v1/pages/{entry_id}` and page body content using the **remove-then-append** pattern (same as `_remove_section()` + `_append_section()` on tracker pages). `PATCH /v1/blocks/{id}/children` **appends** — it does not replace — so updating a "Debrief" toggle requires: (1) find the existing toggle block in the row's children, (2) delete it, (3) append the new toggle. Without this, running debrief twice would create duplicate sections.
- **`get_interviews(page_id) -> list[Interview]`** — Find the Interviews DB, read all rows, return them as `Interview` objects. This read path is needed by Phases 4 (follow-up monitor), 5 (reassess), and 6 (compare).

#### Implementation Notes

- `_add_interviews_database()` already exists in `notion.py` and creates the inline DB with title + date columns. Update it to also create the Type, Vibe, and Outcome select properties. Update it to **return the database ID**.
- Existing Interviews databases on active pages need migration — `PATCH /v1/databases/{db_id}` to add new property columns. Existing data (interviewer names, dates) is preserved; new columns start empty. See **Migration Steps** below.
- The `Interview` dataclass in `models.py` already has fields for `interview_type`, `interviewers`, `prep_notes`, `questions_to_ask`, and `outcome`. Extend it to match the full schema: add `debrief`, `questions_they_asked`, `questions_i_asked`, `follow_up`, and `vibe` fields.
- **TrackerBackend protocol** (`tracker/__init__.py`): The new interview methods (`add_interview_entry`, `update_interview_entry`, `get_interviews`) are **Notion-specific** — they depend on inline databases and page body content that the JSON fallback tracker doesn't support. Do not add them to the `TrackerBackend` protocol. They live on `NotionTracker` directly. Callers (queue handlers, skills) already work with the concrete `NotionTracker` instance, not the protocol. Also note: the protocol's `create() -> str` signature already drifts from the implementation's `create() -> tuple[str, list[str]]` — fix that when touching the protocol file.

#### Migration Steps

Concrete procedure for extending the schema on existing pages:

1. Query the tracker database for all non-archived pages: `POST /v1/databases/{tracker_db_id}/query`
2. For each page, call `_find_interviews_db(page_id)` to locate the inline Interviews DB
3. If no Interviews DB found: call `_add_interviews_database(page_id)` (with updated schema) — creates the DB from scratch
4. If Interviews DB found: call `PATCH /v1/databases/{db_id}` with the new properties to add columns:

   ```json
   {
     "properties": {
       "Type": { "select": { "options": [
         {"name": "Phone Screen"}, {"name": "Technical"},
         {"name": "System Design"}, {"name": "Behavioral"},
         {"name": "Panel"}, {"name": "Hiring Manager"},
         {"name": "Executive"}, {"name": "Take-Home"}
       ]}},
       "Vibe": { "select": { "options": [
         {"name": "1"}, {"name": "2"}, {"name": "3"},
         {"name": "4"}, {"name": "5"}
       ]}},
       "Outcome": { "select": { "options": [
         {"name": "Pending"}, {"name": "Passed"},
         {"name": "Rejected"}, {"name": "Withdrawn"}
       ]}}
     }
   }
   ```

5. Log results: page name, DB ID, action taken (created / migrated / already current)

Implement as a new queue command `migrate_interviews_schema` or a standalone method `migrate_all_interviews_dbs()` callable from a one-off script. This is a one-time operation but should be idempotent — running it twice is safe (Notion silently ignores adding properties that already exist).

### 4.2 Interview Prep Generation (Trigger: Interview Scheduled)

#### Problem

7 of 10 active interview processes have no prep material for likely questions. When it does exist (Bandcamp, Trade Republic), it was created manually and ad hoc during the /analyze phase — long before a specific interview was scheduled, with a specific interviewer, for a specific interview type.

#### Solution

When Greg adds an interview to the Interviews database (or tells Claude an interview is scheduled), generate targeted prep material based on three inputs: the interviewer's role and seniority, the interview type (screen vs. technical vs. behavioral vs. executive), and the existing Experience to Highlight bullets and company research on the tracker page.

#### Trigger

Greg says something like "I have an interview with Thomas Roton at Bandcamp on Thursday, it's a technical screen" or "Prep me for Cozero — meeting the CTO next Tuesday." This is a natural language trigger, not a form submission. Claude parses the company, interviewer, date, and interview type from the request.

#### Prep Material Generated

- **Interviewer research** — Claude researches the interviewer before generating any other prep material. This means finding and reading their LinkedIn profile, checking for blog posts, conference talks, podcast appearances, open-source contributions, published articles, or anything else publicly available. The goal is twofold: give Greg context on who he's talking to (background, tenure, what they care about, what they've built), and surface connection points (shared interests, mutual contacts, overlapping experience). This research has consistently been one of the highest-value prep activities in v1 when done manually — automating it ensures it happens for every interview, not just the ones where Greg has time.
- **Likely questions** based on interview type and interviewer seniority. A phone screen with a recruiter gets different prep than a system design session with a VP Engineering. The interviewer's background informs question prediction — a former SRE turned engineering manager will ask different technical questions than a product-focused CTO.
- **Talking points** drawn from Experience to Highlight, reframed for the specific interview type. Technical screens get architecture stories; behavioral rounds get leadership examples. Where interviewer research reveals specific interests or expertise, talking points are tuned to resonate — e.g., if the interviewer has a background in observability, lead with the Prometheus/Grafana work at 1KOMMA5° and Mobimeo.
- **Questions to ask** this specific interviewer, tailored to their role and background. An engineering manager gets questions about team structure and on-call; a CTO gets questions about technical vision and architecture decisions. Where the interviewer's LinkedIn reveals something specific (e.g., they joined 3 months ago, or they previously worked at a competitor), the questions reference that context.

#### Output

- Prep material is written to the **page body** of the corresponding Interviews DB row as a "Prep Notes" toggle heading_3 section, via a new queue command (`interview_prep`). This avoids the 2000-char Rich Text property limit.
- If the interview is also the first for a company that's missing the "Questions I Might Get Asked" page-level section, populate that section as well — it serves as the canonical question bank across all interviews for that company.

#### Skill Changes

- New skill: `/prep`. Standalone skill — not a `/track` subcommand, because interview prep is its own workflow with distinct inputs and outputs. Reads the tracker page (Experience to Highlight, Company Research, Fit Assessment), researches the interviewer via web search, generates prep, writes to the Interviews DB entry.
- Update `/track` SKILL.md to cross-reference `/prep` (but the workflow lives in `/prep`'s own SKILL.md).

### 4.3 Post-Interview Debrief Capture

#### Problem

After an interview, there is no structured mechanism to capture what happened. Insights about the team, red flags that surfaced, questions that were asked, what answers landed — all of this lives in Greg's head until he either writes it up manually or forgets it. Over 10 concurrent processes, this creates information loss that directly impacts preparation for subsequent rounds and offer evaluation.

#### Solution

A `/debrief` command that takes a company name, identifies the most recent interview, and captures structured notes. Greg dumps raw thoughts; Claude structures them into the Interviews database entry.

#### Debrief Structure

1. **Questions they asked** — what the interviewer actually asked, in Greg's words.
2. **What landed** — which of Greg's answers or stories got visible positive reactions.
3. **What stumbled** — anything that didn't go well, or where Greg felt under-prepared.
4. **What you learned** — new information about the role, team, company, or culture that wasn't in the job posting or company research.
5. **Updated read** — has this interview changed Greg's overall assessment of the opportunity? Flag if the fit score should be reassessed.
6. **Follow-up needed** — any action items: send additional materials, email a contact, prepare for a specific next-round topic.
7. **Vibe** — 1 to 5 gut-feel rating of mutual fit.

#### Workflow

Greg says "debrief Bandcamp — talked to Thomas" and dumps his notes. Claude structures them into the seven categories above, writes the structured debrief to the **page body** of the matching Interviews DB row (as a "Debrief" toggle heading_3 section with sub-sections for questions asked, questions Greg asked, and follow-up), sets the Vibe DB property (if provided) and Outcome DB property (if known — often "Pending" immediately after an interview), and flags if a reassessment is warranted. The whole interaction should take under five minutes while the conversation is fresh.

**Panel interviews:** When Greg meets multiple interviewers in a single session (e.g., "talked to Thomas and Sami"), the `/debrief` skill creates one Interviews DB row per interviewer, each with the same date and interview type but separate debrief content. The title property uses the primary interviewer's name; secondary interviewers are noted in the debrief text. Alternatively, for a true panel (one conversation, not back-to-back), use a combined title: "Thomas Roton + Sami Chen, Panel". The skill makes this judgment from context.

#### Implementation

- New queue command: `debrief`. Takes company name (or page_id), interview identifier (interviewer name or date), and structured debrief fields. Uses `_find_interviews_db()` → `_find_interview_entry()` → `update_interview_entry()` to write to the correct row.
- Update the `Interview` dataclass in `models.py` with debrief fields (done in Phase 1).
- Add debrief handling to `notion.py` — finds the matching Interviews DB row and writes debrief content to its page body + updates Vibe/Outcome properties.
- New `/debrief` skill with its own SKILL.md (standalone, not a `/track` subcommand).

### 4.4 Follow-Up Cadence Monitor

#### Problem

With 10 concurrent interview processes, conversations go stale without anyone noticing. A company that was responsive last week might have gone silent for six days, and Greg discovers the gap only when he manually reviews the tracker. By then, the window for a timely follow-up has passed.

#### Solution

A `/followup` skill (invoked conversationally or via CLI) that checks all "In Progress (Interviewing)" entries for staleness. For each entry, it looks at the most recent Interviews database entry's date and compares to today. If the gap exceeds a configurable threshold (default: 5 days), it surfaces a nudge with the company name, last contact, and a suggested follow-up action. Optionally, a launchd plist can run this daily and write a summary file.

#### Output

- A summary of stale conversations, sorted by days since last activity.
- For each stale entry: company name, last interview date, interviewer, and a suggested follow-up (e.g., "Send a brief check-in to Richard Frost at Songtradr — last contact was the screening call on Feb 28").
- No automatic actions — the monitor surfaces information for Greg to act on.

#### Implementation

- **Primary interface:** New `/followup` skill, invoked conversationally ("any stale conversations?", "check my follow-ups"). This is the main interaction mode — Greg asks in a Cowork session, Claude reads the data and presents the summary.
- **Optional automation:** A launchd plist that runs `jobbing track followup` daily at 9:00 AM, writing a summary to `notion_queue_results/followup-YYYY-MM-DD.md` for Greg to review. This is a convenience, not a requirement — the skill works on-demand.
- The task reads all "In Progress (Interviewing)" pages from the Notion database via `list_all()`, calls `get_interviews(page_id)` for each, finds the most recent interview date, and calculates the gap.
- Threshold is configurable via `.env` (`FOLLOWUP_THRESHOLD_DAYS=5`).
- **API cost:** For N active companies, this makes N+1 API calls per company (1 DB query + N page body reads per company's `get_interviews()`). At current volume (~10 companies, ~3–6 interviews each), this is 40–70 calls — well within Notion's rate limits (3 req/sec for internal integrations). If volume grows, optimize by reading DB properties only (dates are DB properties, not page body).

### 4.5 Living Fit Assessment

#### Problem

The Fit Assessment score is set once during /analyze based on a job posting. By the third interview round, Greg has learned things the posting never mentioned: the team is smaller than expected, the tech stack is older than described, the engineering culture is stronger than Glassdoor suggested, the role scope expanded in conversation. None of this is reflected in the score or reasoning.

#### Solution

A `/reassess` command that takes a company name, reads the existing Fit Assessment and all debrief notes, and produces an updated score with revised reasoning. The original score is preserved for comparison (before/after), and the updated score replaces the Fit Assessment section and Score property on the Notion page.

#### Inputs for Reassessment

- Original Fit Assessment (score, reasoning, flags, gaps)
- All debrief notes from the Interviews database (read via `get_interviews(page_id)` which returns `Interview` objects with populated `debrief` fields)
- Updated company research (if any has been added since the original analysis)
- Greg's verbal input on what's changed ("they said the team is actually 3 people, not 8" or "the CTO was impressive, much stronger than I expected")

#### Output

- Updated score (0–100) with revised reasoning that explicitly references what changed and why.
- Updated green/red flags and gaps, incorporating interview learnings.
- Written to the Fit Assessment section and Score property via the existing `fit_assessment` queue command.
- The original score is noted in the reasoning for transparency (e.g., "Original score: 72. Updated to 81 after...").

### 4.6 Decision Comparison Framework

#### Problem

When multiple companies reach the offer stage in the same week, there is no structured way to compare them. Compensation, team quality, mission alignment, remote flexibility, visa/entity situation, and growth trajectory all matter — but comparing them from memory across 10 Notion pages is error-prone and stressful during a time-pressured decision.

#### Solution

A `/compare` command that takes two or more company names, reads their tracker pages (including Fit Assessment, debrief notes, company research, salary data), and produces a weighted side-by-side comparison.

#### Comparison Dimensions

| Dimension | Weight | Data Sources |
|---|---|---|
| Compensation | High | Salary property, negotiation notes from debriefs |
| Technical Fit | High | Fit Assessment score, tech stack match, debrief impressions |
| Team & Culture | Medium | Debrief vibe scores, interviewer quality, company research |
| Mission Alignment | Medium | Company Focus tags, Vision/Mission properties, domain match |
| Growth Trajectory | Medium | Role scope from debriefs, company funding/headcount trajectory |
| Remote & Location | Low | Environment property, entity/visa situation from research |
| Risk Factors | Low | Red flags from Fit Assessment, Glassdoor data, debrief concerns |

#### Output

- A formatted comparison document (Markdown or .docx) with each dimension scored and annotated with supporting evidence from the tracker.
- A clear recommendation with caveats — not a single "winner" but a structured presentation of tradeoffs.
- This is a read-only analysis — no Notion writes. Greg makes the final decision.

---

## 5. Implementation Plan

**The features are ordered by dependency and immediate value. Each phase builds on the previous one, and each delivers standalone value even if subsequent phases are delayed.**

### Phase 1: Foundation (Interviews DB Schema + Read/Write Path)

Target: 1–2 sessions. No dependencies.

Phase 1 builds the complete foundation that Phases 2–6 depend on: the extended Interviews DB schema, the helper methods to find/read/write interview rows, and the two new queue command handlers. Without this phase, no subsequent phase can write to or read from the Interviews DB.

#### 1a. Extend `Interview` dataclass (`models.py`)

Add fields to match the full schema:

```python
@dataclass
class Interview:
    date: str  # ISO date
    interview_type: str = ""  # Phone Screen, Technical, System Design, etc.
    interviewers: list[str] = field(default_factory=list)
    prep_notes: str = ""
    questions_to_ask: list[str] = field(default_factory=list)
    outcome: str = ""  # Passed, Rejected, Pending, Withdrawn
    debrief: str = ""  # Structured debrief text
    questions_they_asked: list[str] = field(default_factory=list)
    questions_i_asked: list[str] = field(default_factory=list)
    follow_up: str = ""  # Next steps, action items
    vibe: int = 0  # 1-5 gut-feel rating, 0 = not set
```

#### 1b. Update `_add_interviews_database()` (`notion.py`)

- Add Type (select), Vibe (select), Outcome (select) properties to the schema
- **Return the database ID** from the API response (currently discarded)

#### 1c. Add helper methods (`notion.py`)

- **`_find_interviews_db(page_id) -> str | None`** — Walk page children via `GET /v1/blocks/{page_id}/children`, find the block where `type == "child_database"` and title is "Interviews", return its ID
- **`_find_interview_entry(db_id, interviewer=None, date=None) -> str | None`** — Query the Interviews DB via `POST /v1/databases/{db_id}/query` with a filter on title (interviewer) and/or date. Returns the matching row's page ID
- **`add_interview_entry(page_id, interview: Interview) -> str`** — Call `_find_interviews_db()`, then `POST /v1/pages` to create a row with DB properties (Interviewer, Date, Type, Vibe, Outcome). Only write page-body toggle sections that have content (e.g., `interview_prep` creates Prep Notes only; `debrief` create-if-missing creates Debrief only). Returns the new row's page ID
- **`update_interview_entry(entry_id, interview: Interview) -> None`** — Update properties via `PATCH /v1/pages/{entry_id}`. For page body content, use the **remove-then-append** pattern: find the target toggle block (e.g., "Debrief") in the row's children, delete it via `DELETE /v1/blocks/{block_id}`, then append the new toggle via `PATCH /v1/blocks/{entry_id}/children`. This prevents duplicate sections on re-run. (Same pattern as `_remove_section()` + `_append_section()` on tracker pages.)
- **`get_interviews(page_id) -> list[Interview]`** — Call `_find_interviews_db()`, query all rows via `POST /v1/databases/{db_id}/query`, read each row's properties + page body (via `GET /v1/blocks/{row_id}/children` per row), return as `Interview` objects. **Note:** This makes N+1 API calls (1 query + N page body reads). For the current volume (~6 interviews per company), this is fine. If volume grows, consider reading properties only and fetching page body on demand. This read path is needed by Phases 4, 5, and 6

Additionally, fix `_parse_section_children()` to handle the "Fit Assessment" section correctly. Currently it falls through to the default parser (bullets only), which drops paragraphs containing the score and reasoning text. Add a Fit Assessment-specific case that captures both paragraph blocks (score line, reasoning) and bullet blocks (green/red flags, gaps, keywords). This fix is needed now because `_read_existing_sections()` is called on every create-update cycle, and the lost data causes silent degradation when rebuilding pages.

#### 1d. Add queue command handlers (`notion.py`)

Register two new commands in `process_queue_file()`:

- **`interview_prep`** — Finds (or creates) the interview row, writes prep content to its page body as a "Prep Notes" toggle section, and optionally populates the page-level "Questions I Might Get Asked" section. If no Interviews DB exists on the page, fail with a clear error message: "No Interviews database found on page — run migration first."
- **`debrief`** — Finds the matching interview row, writes debrief content to its page body as a "Debrief" toggle section, updates Vibe and Outcome DB properties. **If no matching row exists, create one** — Greg may debrief without having run `/prep` first. The debrief command should never silently fail because the row is missing.

Both handlers use the helper methods from 1c. The actual prep/debrief *generation* logic lives in the `/prep` and `/debrief` skills (Phases 2 and 3) — Phase 1 only builds the write path.

**Queue JSON field mapping:**

- **`interviewer`** (string) → Notion title property "Interviewer Name and Role" + dataclass field: `interviewers=[task["interviewer"]]`.
- **`vibe`** (integer 1–5) → Notion Select property expects a string: `_select(str(interview.vibe))`. The value `0` (not set) should skip writing the Vibe property.
- **`outcome`** (string, optional) → Notion Select property "Outcome". If empty or absent, skip writing the property (Greg may not know the outcome at debrief time). Valid values: "Pending", "Passed", "Rejected", "Withdrawn".
- **`prep_notes`** and **`debrief`** (markdown strings) → The queue handler must convert these from markdown to Notion blocks inside the toggle section. Minimal parser: split on `\n\n` for paragraphs, lines starting with `## ` become `heading_3` blocks, lines starting with `- ` become `bulleted_list_item` blocks, everything else becomes `paragraph` blocks. This is the same markdown-to-blocks challenge that already exists for `job_description` (which currently just splits on `\n\n` for paragraphs) but prep/debrief content is richer. A shared `_markdown_to_blocks(text) -> list[dict]` helper avoids duplicating this logic.

#### 1e. Run migration on existing pages

Execute the migration procedure from Section 4.1 (Migration Steps):

1. Query all non-archived tracker pages
2. For each: find or create the Interviews DB with the extended schema
3. Verify on ZZ-Test-Dummy first, then run across all active pages
4. Spot-check 2–3 existing pages to confirm no data loss

#### 1f. Update documentation

- **WORKFLOW.md**: Add queue JSON schemas for `interview_prep` and `debrief` commands (see Section 6 below). Document the Interviews DB extended schema.
- **CLAUDE.md**: Update queue commands list and Interviews DB description to include new properties and page-body content model.
- **`/track` SKILL.md**: Cross-reference `/prep`, `/debrief`, `/followup`, `/reassess`, `/compare` skills. Also fix pre-existing stale data: (1) status values on line 20 say "Targeted, Researching, Applied, Interviewing, Offered, Done" — correct to "Targeted, Applied, Followed-Up, In Progress (Interviewing), Done"; (2) section name on line 75 says "Questions To Ask In An Interview" — correct to "Questions to Ask".

#### 1g. Validation

Validate each code path on the ZZ-Test-Dummy page in a live Claude session:

1. Create fresh ZZ-Test-Dummy → verify Interviews DB has 5 properties (Interviewer, Date, Type, Vibe, Outcome)
2. Run `interview_prep` queue command → verify row created in Interviews DB with Prep Notes in page body
3. Run `debrief` queue command → verify Debrief section added to same row's page body, Vibe and Outcome properties set
4. Call `get_interviews(page_id)` → verify it returns the Interview object with all fields populated
5. Run migration on one real "In Progress" page → verify existing interviewer/date data preserved, new columns added
6. Run all existing queue commands (`create`, `update`, `highlights`, etc.) → verify no regressions

### Phase 2: Interview Prep Generation

Target: 1 session. Depends on Phase 1 (needs `add_interview_entry()` and `interview_prep` queue handler).

- Create `/prep` skill with its own SKILL.md — standalone skill, not a `/track` subcommand.
- Skill reads the tracker page (Experience to Highlight, Company Research, Fit Assessment), researches the interviewer via web search, generates prep material, and writes it via the `interview_prep` queue command (write path built in Phase 1).
- If the company is missing "Questions I Might Get Asked," auto-populate that page-level section from the prep generation output.
- Update WORKFLOW.md to document the prep trigger and workflow.

### Phase 3: Post-Interview Debrief

Target: 1 session. Depends on Phase 1 (needs `update_interview_entry()` and `debrief` queue handler).

- Create `/debrief` skill with its own SKILL.md — standalone skill.
- Skill takes company name and raw notes from Greg, structures them into the debrief categories (questions asked, what landed, what stumbled, what learned, updated read, follow-up, vibe), and writes via the `debrief` queue command (write path built in Phase 1).
- Include the "reassessment warranted" flag in debrief output when interview learnings significantly change the picture.

### Phase 4: Follow-Up Cadence Monitor

Target: 1 session. Depends on Phase 1 (needs `get_interviews()` to read dates).

- Create `/followup` skill with its own SKILL.md — invoked conversationally or via CLI (`jobbing track followup`).
- The skill calls `list_all()` to find "In Progress (Interviewing)" pages, calls `get_interviews(page_id)` for each, and computes days since last activity.
- Output: formatted summary of stale conversations with suggested actions.
- Add `FOLLOWUP_THRESHOLD_DAYS` to `.env` with a default of 5.
- Optional: add a launchd plist for daily automated summaries to `notion_queue_results/`.

### Phase 5: Living Fit Assessment

Target: 1 session. Depends on Phase 1 (`get_interviews()` for reading debriefs) and Phase 3 (debrief data must exist to reassess against).

- Create `/reassess` skill with its own SKILL.md.
- Reads existing Fit Assessment, calls `get_interviews()` to collect all debrief data, incorporates Greg's verbal input.
- **Prerequisite:** Depends on the Fit Assessment parser fix in Phase 1c. Without that fix, `_read_existing_sections()` drops the score and reasoning paragraphs when reading the Fit Assessment section, so `/reassess` would have incomplete input. If Phase 1c is complete, this prerequisite is already satisfied.
- Produces updated score and reasoning; writes via existing `fit_assessment` queue command.
- Preserves original score in the reasoning text for transparency.

### Phase 6: Decision Comparison Framework

Target: 1 session. Depends on Phase 1 (`get_interviews()` for reading interview data). Produces richer output when Phase 3 (debrief data) and Phase 5 (reassessed scores) exist, but can function with Phase 1 alone — tracker properties (salary, environment, focus), Fit Assessment, and company research are all v1 data.

- Create `/compare` skill with its own SKILL.md.
- Reads tracker pages for specified companies, including Fit Assessment, debriefs, research, salary data.
- Produces a formatted comparison document with weighted dimensions and evidence.
- Output is a Markdown file or .docx in `companies/` — no Notion writes.

---

## 6. Changes to Existing System

**Each change is scoped to minimize disruption to the working v1 system. No existing queue commands are modified — all changes are additive.**

### Files Modified

| File | Change Type | Description |
|---|---|---|
| `src/jobbing/models.py` | Extend | Add `debrief`, `questions_they_asked`, `questions_i_asked`, `follow_up`, `vibe` fields to `Interview` dataclass |
| `src/jobbing/tracker/notion.py` | Extend | Helper methods (`_find_interviews_db`, `_find_interview_entry`, `add_interview_entry`, `update_interview_entry`, `get_interviews`); new queue commands (`interview_prep`, `debrief`); extended Interviews DB template schema; return DB ID from `_add_interviews_database()`; Fit Assessment-specific parser in `_parse_section_children()` |
| `src/jobbing/tracker/__init__.py` | Fix | Correct `create() -> str` signature to match implementation's `create() -> tuple[str, list[str]]`. Interview methods stay on `NotionTracker` only (not added to protocol). |
| `src/jobbing/cli.py` | Extend | New CLI subcommands: `prep`, `debrief`, `followup`, `reassess`, `compare` |
| `.claude/skills/track/SKILL.md` | Fix + Extend | Fix stale status values and section name; cross-reference new skills (`/prep`, `/debrief`, `/followup`, `/reassess`, `/compare`) |
| `WORKFLOW.md` | Extend | Document interview lifecycle, new queue command schemas (see below), Interviews DB extended schema |
| `CLAUDE.md` | Extend | Update queue commands list, Interviews DB schema description, project structure |
| `.env` | Extend | Add `FOLLOWUP_THRESHOLD_DAYS=5` |

### New Queue Command Schemas

These schemas should be added to WORKFLOW.md and CLAUDE.md when Phase 1 is implemented.

**`interview_prep`** — Add an interview row with prep material:

```json
{
  "command": "interview_prep",
  "name": "Company",
  "interviewer": "Thomas Roton, Engineering Manager",
  "date": "2026-03-10",
  "interview_type": "Technical",
  "prep_notes": "## Interviewer Research\n\nThomas Roton has been...\n\n## Likely Questions\n\n- ...\n\n## Talking Points\n\n- ...\n\n## Questions to Ask Thomas\n\n- ...",
  "questions_to_ask": ["How is the on-call rotation structured?", "What does the platform roadmap look like for Q3?"]
}
```

**`debrief`** — Write post-interview debrief to an existing interview row:

```json
{
  "command": "debrief",
  "name": "Company",
  "interviewer": "Thomas Roton",
  "date": "2026-03-10",
  "debrief": "## What They Asked\n\n- ...\n\n## What Landed\n\n- ...\n\n## What Stumbled\n\n- ...\n\n## What I Learned\n\n- ...\n\n## Updated Read\n\n...",
  "questions_they_asked": ["Tell me about a time you migrated a monolith", "How do you approach on-call?"],
  "questions_i_asked": ["How does the team handle incident response?", "What's the deploy cadence?"],
  "follow_up": "Send portfolio link to Thomas. Prepare system design example for Round 2.",
  "vibe": 4,
  "outcome": "Passed"
}
```

Both commands resolve the page via company name (using `_find_page()`), then locate the Interviews DB via `_find_interviews_db()`. The `interview_prep` command creates a new row if one doesn't exist for that interviewer/date. The `debrief` command looks for an existing row via `_find_interview_entry()` — **if no row exists, it creates one** (Greg may debrief without having run `/prep` first).

### New Files

| File | Purpose |
|---|---|
| `.claude/skills/prep/SKILL.md` | Interview prep generation skill |
| `.claude/skills/debrief/SKILL.md` | Post-interview debrief capture skill |
| `.claude/skills/followup/SKILL.md` | Follow-up cadence monitor skill |
| `.claude/skills/reassess/SKILL.md` | Living Fit Assessment update skill |
| `.claude/skills/compare/SKILL.md` | Decision comparison framework skill |

### Backward Compatibility

- All existing queue commands (`create`, `update`, `highlights`, `research`, `outreach`, `interview_questions`, `questions_to_ask`, `fit_assessment`, `job_description`) continue to work unchanged.
- The Interviews DB schema extension is additive — new property columns are added alongside existing ones. No data loss. Existing interviewer names and dates are preserved.
- `_find_interviews_db()` returns `None` for pages that don't have an Interviews DB — callers must handle this gracefully.
- Existing tracker pages are not rebuilt or reformatted. New features write to new fields only.
- The `pip install -e .` editable install symlinks the source directory — all Python code changes are picked up immediately with no re-run needed. Only re-run if `pyproject.toml` changes (new dependencies or entry points).

---

## 7. Validation Strategy

**This is a single-user application running on Greg's laptop, exercised through conversations in Claude Code / Cowork. Validation means running real code paths against the real Notion database and verifying the results — not a formal test suite.**

### Per-Phase Validation (ZZ-Test-Dummy)

Each phase is validated on the ZZ-Test-Dummy page before touching real data. The validation script for each phase is specified in that phase's section above (e.g., Phase 1 section 1g). The pattern is:

1. Archive any existing ZZ-Test-Dummy page
2. Create a fresh page via the queue
3. Exercise the new code paths (queue commands, helper methods)
4. Verify results by reading back from Notion (block children, DB queries)
5. Run all existing queue commands to check for regressions
6. Archive the test page

### Conversational Acceptance (Real Data)

After ZZ-Test-Dummy validation, exercise each feature in a real Cowork session:

1. **Phase 1:** Run migration on one real "In Progress" page. Verify Interviews DB has new columns. Verify existing interviewer/date data preserved.
2. **Phase 2:** "I have a technical screen with Thomas Roton at Bandcamp on Thursday" → verify prep material appears in the Interviews DB row's page body.
3. **Phase 3:** "debrief Bandcamp — talked to Thomas, he asked about GCP migration, I told the 1KOMMA5° story, it landed well" → verify structured debrief in the row's page body, Vibe and Outcome set.
4. **Phase 4:** Run the follow-up monitor, verify it correctly identifies stale entries.
5. **Phase 5:** "reassess Cozero — turns out the team is 3 people" → verify updated score and reasoning.
6. **Phase 6:** "compare Bandcamp and Cozero" → verify formatted comparison document.

### Regression Guard

After each phase:

- Run all 9 existing queue commands (`create`, `update`, `highlights`, `research`, `outreach`, `interview_questions`, `questions_to_ask`, `fit_assessment`, `job_description`) with test payloads on ZZ-Test-Dummy
- Spot-check 2–3 existing tracker pages to confirm no formatting changes
- Verify `jobbing queue` still processes files correctly
- Verify `pip install -e .` was run at least once in the venv (editable install picks up source changes automatically)

---

## 8. Feedback Mechanisms

**The system should surface problems early and make quality visible. These mechanisms help Greg and Claude identify what's working and what needs adjustment.**

### Built-In Feedback Loops

These are prompt-level instructions in the skill SKILL.md files, not automated data pipelines. Claude executes them when it has the relevant data in context.

- **Debrief-to-prep feedback:** The `/prep` skill instruction should include: "Before generating prep, call `get_interviews()` across all active companies to check for recurring questions in debriefs. If a question appears in 3+ debriefs (e.g., 'why leave Solo Recon?'), prioritize it and draw from the best previous answers." This is a prompt instruction, not a stored index — Claude reads the debriefs in-context at prep time and does the pattern recognition live.
- **Reassessment delta tracking:** The `/reassess` skill instruction should include: "When the updated score differs from the original by ≥15 points, explicitly note what the original /analyze missed and whether this suggests a tuning opportunity for `scoring_criteria.md`." Greg reviews these notes and manually adjusts the scoring criteria when a pattern emerges. No automated feedback pipeline.
- **Follow-up effectiveness:** Not tracked automatically. Greg can periodically ask Claude: "Review my follow-up history — which nudges led to resumed conversations?" Claude reads the tracker data and answers conversationally. If the 5-day threshold feels wrong, Greg adjusts `FOLLOWUP_THRESHOLD_DAYS` manually.

### Manual Feedback Points

- After each prep generation, Greg reviews the material before the interview. If he finds the prep unhelpful or off-target, that's a signal to adjust the `/prep` SKILL.md prompt instructions or input weighting.
- After each debrief, Greg can flag if the structured output missed something important from his raw notes. This improves the `/debrief` SKILL.md parsing prompts.
- The comparison framework is explicitly presented as "recommendation with caveats" — Greg's final decision may differ from the weighted output. When it does, that's worth noting: which dimension did the framework underweight?

### Metrics (Queryable from Notion Data)

These aren't tracked separately — they're computed on-demand by asking Claude to query the Notion data. Example: "How's my debrief completion rate?"

- **Prep coverage:** Count Interviews DB rows with non-empty "Prep Notes" page body vs total rows. Query: `get_interviews()` across all active pages.
- **Debrief completion rate:** Count rows with non-empty "Debrief" page body vs total rows with dates in the past. Same query source.
- **Score delta magnitude:** Compare Score property with reassessed scores noted in Fit Assessment reasoning text. Requires reading Fit Assessment sections.
- **Staleness patterns:** Average days between interviews per company, computed from Interviews DB dates via `get_interviews()`.

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Notion API rate limits | Medium | The follow-up monitor reads multiple pages in quick succession. Batch reads with delays; cache responses where possible. Current volume (10–20 pages) is well within limits. |
| Interviews DB schema migration breaks existing data | High | Migration is additive only — new columns alongside existing ones. Test on one page before running across all 10. Dry-run mode for all queue commands. |
| Debrief capture adds friction to post-interview flow | Medium | Keep the interaction under 5 minutes. Greg dumps raw notes; Claude does the structuring. If it feels burdensome, it won't get used. Optimize for speed over completeness. |
| Prep material is generic or unhelpful | Medium | Prep quality depends on having good inputs: Experience to Highlight, company research, and interviewer context. If any of these are thin, prep will be thin. The manual feedback point (Greg reviews before the interview) catches this early. |
| `pip install -e .` not yet run in venv | Low | The editable install must be run once (`pip install -e .`); after that, all source changes are picked up automatically. Only re-run if `pyproject.toml` changes (new dependencies or entry points). |
| Follow-up monitor automation (optional) | Low | If the optional launchd plist is added, uses the same scheduling mechanism as the queue watcher. If the machine is asleep at 9 AM, launchd runs the task on wake. The primary interface is conversational (`/followup` skill), so the scheduled plist is a convenience, not a dependency. |

---

## 10. Success Metrics

**These are not KPIs to optimize against — they're signals that the system is delivering value. If the numbers look wrong, it's a prompt to investigate, not a target to hit.**

### Leading Indicators (Adoption)

- Prep generated for 80%+ of scheduled interviews within the first two weeks of Phase 2 launch.
- Debrief captured for 70%+ of conducted interviews within the first two weeks of Phase 3 launch.
- Follow-up monitor reviewed daily when active interview processes exist.

### Lagging Indicators (Outcomes)

- Reduction in "walked in under-prepared" moments (self-assessed by Greg).
- Faster follow-up: average time between last interview and next contact decreases.
- Reassessment usage: at least one score update per company that reaches Round 3+.
- When offers arrive: comparison framework is used (not bypassed) for final decision.

### Anti-Metrics (Things That Should Not Happen)

- Debrief capture taking more than 5 minutes — if it does, the process is too heavy.
- Prep material being ignored consistently — if it's not useful, fix or remove it.
- Follow-up monitor producing false urgency — if every company is "stale," the threshold is wrong.
- Reassessment scores drifting wildly from original — either /analyze is bad or reassessment is over-indexing on interview impressions.

---

## 11. Glossary

This project has accumulated terminology organically. These definitions are the canonical meanings — use them consistently across skills, documentation, and conversation.

### System Components

| Term | Definition |
|---|---|
| **Tracker** | The Notion database that tracks all job applications. Database ID: `734d746c43b149298993464f5ccc23e7`. Each row is a company/role pair. Sometimes called "the tracker" or "tracker page" (for an individual entry). |
| **Tracker page** | A single Notion page within the tracker database, representing one application to one company. Contains properties (status, salary, etc.) and body content (toggle sections, Interviews DB). |
| **Queue** | The `notion_queue/` directory on Greg's Mac. JSON files dropped here are processed by a launchd agent and sent to the Notion API. The only reliable write path to Notion. |
| **Queue command** | A JSON object with a `command` field that tells the queue processor what to do. Commands: `create`, `update`, `highlights`, `research`, `outreach`, `interview_questions`, `questions_to_ask`, `fit_assessment`, `job_description`, `debrief` (new), `interview_prep` (new). |
| **Interviews DB** | An inline Notion database nested inside each tracker page. DB properties: Interviewer Name and Role (title), Date, Type (select), Vibe (select), Outcome (select). Long-form content (Prep Notes, Debrief) lives in each row's page body as toggle heading_3 sections. One DB per tracker page. |
| **Skill** | A Claude Code slash command (e.g., `/analyze`, `/apply`, `/track`). Defined in `.claude/skills/{name}/SKILL.md`. In Cowork, skills load as background context and are invoked via natural language. |
| **Data source** | Notion's internal term for a "collection" — the underlying data behind a database view. Referenced by `collection://` URLs in Notion MCP tools. The tracker's data source ID is `7d7b1f6a-4af7-40e1-913f-95b65a89ae41`. |

### Workflow Stages

| Term | Definition |
|---|---|
| **Analyze** | The first step for any job posting. Produces a fit score (0–100), green/red flags, gaps, salary read, company intel, and Experience to Highlight bullets. Skill: `/analyze`. |
| **Apply** | The full application workflow: Notion entry → tailored JSON → PDFs → ATS check. Only runs after `/analyze` and Greg's go decision. Skill: `/apply`. |
| **Prep** | Interview preparation material generated when an interview is scheduled. Includes interviewer research, likely questions, talking points, and questions to ask. Triggered by Greg, not automatic. Skill: `/prep`. |
| **Debrief** | Post-interview structured capture: what they asked, what landed, what you learned, vibe rating, follow-up needed. Written to the Interviews DB entry. Skill: `/debrief`. |
| **Follow-up** | Check all active interview processes for staleness. Surfaces companies where the last interview was more than N days ago with suggested next actions. Conversational or CLI. Skill: `/followup`. |
| **Reassess** | Update a Fit Assessment score based on interview learnings. Reads debriefs and Greg's input, produces revised score with reasoning. Skill: `/reassess`. |
| **Compare** | Side-by-side evaluation of two or more active opportunities across weighted dimensions. Read-only analysis, no Notion writes. Skill: `/compare`. |

### Data Objects

| Term | Definition |
|---|---|
| **Fit Assessment** | The scoring output from `/analyze`: score (0–100), reasoning, green flags, red flags, gaps, missing keywords. Stored as both a toggle section in the tracker page body and a Score number property on the database row. |
| **Experience to Highlight** | Bullet points identifying which of Greg's roles, achievements, and skills are most relevant for a specific application. Presented as a checkpoint during `/analyze` for Greg's review before document generation. |
| **Company Research** | Structured intel about a company: funding stage, headcount, Glassdoor sentiment, tech stack, recent news. Gathered via web search during `/analyze` and stored as a toggle section. |
| **Outreach Contacts** | LinkedIn contacts researched after applying. Includes name, title, LinkedIn URL, context note, and a drafted connection request message (under 300 characters). Skill: `/outreach`. |
| **Tailored JSON** | The `companies/{company}/{company}.json` file containing all CV and cover letter data, tailored to a specific role. Consumed by the PDF generator (`jobbing pdf`). |

### Notion-Specific Terms

| Term | Definition |
|---|---|
| **Toggle section** | A `heading_3` block with `is_toggleable: True` in Notion. The standard container for tracker page content. Seven managed sections in canonical order: Job Description, Fit Assessment, Company Research, Experience to Highlight, Outreach Contacts, Questions I Might Get Asked, Questions to Ask. |
| **Status** | A select property on the tracker database. Valid values in order: `Targeted` → `Applied` → `Followed-Up` → `In Progress (Interviewing)` → `Done`. Only Greg changes status. |
| **Conclusion** | A text property set when status moves to `Done`. Captures the outcome in Greg's words. |
| **Score** | A number property (0–100) on the tracker database. Set by the `fit_assessment` queue command or the `create` command when `score` is included. |

### Infrastructure Terms

| Term | Definition |
|---|---|
| **launchd agent** | A macOS background process on Greg's Mac that watches `notion_queue/` for new JSON files and processes them. Also runs scheduled tasks. |
| **Notion MCP** | The Model Context Protocol connector for Notion. Read tools (`notion-fetch`, `notion-search`) work reliably. Write tools (`update-page`, `create-pages`) have a Zod serialization bug and must not be used — use the queue instead. |
| **Editable install** | `pip install -e .` in the Jobbing venv. Creates a symlink so the `jobbing` CLI runs directly from the source tree — all Python code changes are picked up immediately with no re-run needed. Only re-run if `pyproject.toml` changes (new entry points or dependencies). |
