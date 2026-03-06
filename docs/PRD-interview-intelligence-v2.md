# Jobbing v2 — Interview Intelligence & Pipeline Management

**Product Requirements Document**
**v1.0 — Draft | March 6, 2026**

---

## Table of Contents

1. Why This Update
2. Current State Assessment
3. What We Hope to Gain
4. Feature Specifications
   - 4.1 Interviews Database Schema
   - 4.2 Interview Prep on Scheduling
   - 4.3 Post-Interview Debrief Capture
   - 4.4 Follow-Up Cadence Monitor
   - 4.5 Living Fit Assessment
   - 4.6 Decision Comparison Framework
5. Implementation Plan
6. Changes to Existing System
7. Testing Strategy
8. Feedback Mechanisms
9. Risks and Mitigations
10. Success Metrics
11. Glossary

---

## 1. Why This Update

Jobbing v1 is strong on the front end of the application funnel. The /analyze skill produces honest, data-backed fit assessments. The /apply skill generates tailored CVs and cover letters that consistently pass ATS parsing. The Notion tracker captures company research, experience highlights, and outreach contacts in a structured, searchable format. The queue-based write system works reliably despite Notion API limitations.

But the system drops off right when the stakes are highest: the interview phase. An audit of all 10 "In Progress (Interviewing)" entries in the tracker revealed consistent gaps:

- 7 of 10 active interview processes are missing "Questions I Might Get Asked" — the highest-ROI section for interview prep.
- 5 of 10 are missing "Questions To Ask In An Interview."
- 2 of 10 are missing the Interviews inline database entirely.
- All 10 are missing the newly created "Fit Assessment" section and Score property.
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
| Interviews DB schema | Exists on 8/10 pages, no standard schema | Standardized schema with prep, debrief, and vibe fields |
| Interview prep | Manual, often skipped | Auto-generated when interview is scheduled via `/prep` |
| Post-interview debrief | Does not exist | Structured capture via `/debrief` |
| Follow-up cadence | No tracking | Scheduled task flags stale conversations |
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

The Interviews inline database exists on 8 of 10 active pages but has an inconsistent, minimal schema: just "Interviewer Name and Role" (title) and "Date". There's no structure for capturing interview type, preparation notes, debrief output, questions asked, or subjective assessment. This means every other feature in this PRD has nowhere to write its data.

#### Solution

Define a canonical Interviews database schema and migrate existing instances to match.

#### Schema

| Property | Type | Required | Description |
|---|---|---|---|
| Interviewer | Title | Yes | Name and title of interviewer (e.g., "Thomas Roton, Engineering Manager") |
| Date | Date | Yes | Interview date and time |
| Type | Select | Yes | Phone Screen, Technical, System Design, Behavioral, Panel, Hiring Manager, Executive, Take-Home |
| Prep Notes | Rich Text | No | Auto-generated prep material (talking points, interviewer research, questions to ask this person) |
| Debrief | Rich Text | No | Post-interview structured notes (what they asked, what landed, what you learned, updated read) |
| Questions They Asked | Rich Text | No | Actual questions asked during the interview, captured in debrief |
| Questions I Asked | Rich Text | No | Questions Greg asked, with notes on responses received |
| Follow-Up | Rich Text | No | Next steps, action items, who to contact |
| Vibe | Select | No | 1 (poor) through 5 (excellent) — gut-feel assessment of mutual fit |
| Outcome | Select | No | Pending, Passed, Rejected, Withdrawn |

#### Implementation Notes

- The Interviews database is created by the queue `create` command as an inline child database. The schema update needs to happen in the Python code (`src/jobbing/tracker/notion.py`) where the template body is built.
- Existing Interviews databases on the 10 active pages need migration — add new columns via Notion API (update-data-source or queue command). Existing data (interviewer names, dates) is preserved; new columns start empty.
- The `Interview` dataclass in `models.py` already has fields for `interview_type`, `interviewers`, `prep_notes`, `questions_to_ask`, and `outcome`. Extend it to match the full schema: add `debrief`, `questions_they_asked`, `questions_i_asked`, `follow_up`, and `vibe` fields.

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

- Prep material is written to the Prep Notes field of the corresponding Interviews database entry via a new queue command (`interview_prep`).
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

Greg says "debrief Bandcamp — talked to Thomas and Sami" and dumps his notes. Claude structures them into the seven categories above, writes to the Debrief and related fields on the Interviews database entry, and flags if a reassessment is warranted. The whole interaction should take under five minutes while the conversation is fresh.

#### Implementation

- New queue command: `debrief`. Takes company name (or page_id), interview identifier (interviewer name or date), and structured debrief fields.
- Update the `Interview` dataclass in `models.py` with debrief fields.
- Add debrief handling to `notion.py` — finds the matching Interviews DB entry and updates its properties.
- New `/debrief` section in the track SKILL.md.

### 4.4 Follow-Up Cadence Monitor

#### Problem

With 10 concurrent interview processes, conversations go stale without anyone noticing. A company that was responsive last week might have gone silent for six days, and Greg discovers the gap only when he manually reviews the tracker. By then, the window for a timely follow-up has passed.

#### Solution

A scheduled task that runs daily (or on-demand) and checks all "In Progress (Interviewing)" entries for staleness. For each entry, it looks at the most recent Interviews database entry's date and compares to today. If the gap exceeds a configurable threshold (default: 5 days), it surfaces a nudge with the company name, last contact, and a suggested follow-up action.

#### Output

- A summary of stale conversations, sorted by days since last activity.
- For each stale entry: company name, last interview date, interviewer, and a suggested follow-up (e.g., "Send a brief check-in to Richard Frost at Songtradr — last contact was the screening call on Feb 28").
- No automatic actions — the monitor surfaces information for Greg to act on.

#### Implementation

- New scheduled task via the `/schedule` skill. Cron expression: daily at 9:00 AM local time.
- The task reads all "In Progress (Interviewing)" pages from the Notion database, checks each page's Interviews DB for the most recent date, and calculates the gap.
- Threshold is configurable via `.env` (`FOLLOWUP_THRESHOLD_DAYS=5`).
- Output is a formatted summary in the chat — no Notion writes, no queue files. Greg decides what to do with the information.

### 4.5 Living Fit Assessment

#### Problem

The Fit Assessment score is set once during /analyze based on a job posting. By the third interview round, Greg has learned things the posting never mentioned: the team is smaller than expected, the tech stack is older than described, the engineering culture is stronger than Glassdoor suggested, the role scope expanded in conversation. None of this is reflected in the score or reasoning.

#### Solution

A `/reassess` command that takes a company name, reads the existing Fit Assessment and all debrief notes, and produces an updated score with revised reasoning. The original score is preserved for comparison (before/after), and the updated score replaces the Fit Assessment section and Score property on the Notion page.

#### Inputs for Reassessment

- Original Fit Assessment (score, reasoning, flags, gaps)
- All debrief notes from the Interviews database
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

### Phase 1: Foundation (Interviews DB Schema)

Target: 1 session. No dependencies.

- Define canonical Interviews DB schema in the Python code (`notion.py` template body builder).
- Update the `Interview` dataclass in `models.py` with all new fields (`debrief`, `questions_they_asked`, `questions_i_asked`, `follow_up`, `vibe`).
- Write a migration queue command (or script) to add new columns to existing Interviews DBs on all 10 active pages. Existing data is preserved; new columns start empty.
- Update WORKFLOW.md and CLAUDE.md to document the new schema.
- Update the track SKILL.md with new field descriptions.

### Phase 2: Interview Prep Generation

Target: 1 session. Depends on Phase 1 (needs Prep Notes field).

- Create `/prep` skill (or extend `/track`) with interview prep generation logic.
- Implement the `interview_prep` queue command in `notion.py` — writes prep material to the Prep Notes field of an Interviews DB entry.
- If the company is missing "Questions I Might Get Asked," auto-populate that section from the prep generation output.
- Update WORKFLOW.md to document the prep trigger and workflow.

### Phase 3: Post-Interview Debrief

Target: 1 session. Depends on Phase 1 (needs Debrief and related fields).

- Implement the `debrief` queue command in `notion.py` — finds the matching interview entry and writes structured debrief data.
- Create `/debrief` skill with its own SKILL.md.
- Include the "reassessment warranted" flag in debrief output when interview learnings significantly change the picture.

### Phase 4: Follow-Up Cadence Monitor

Target: 1 session. Depends on Phase 1 (reads Interviews DB dates).

- Create a scheduled task via the `/schedule` skill.
- The task queries Notion for all "In Progress (Interviewing)" entries, reads each page's Interviews DB, and computes days since last activity.
- Output: formatted summary of stale conversations with suggested actions.
- Add `FOLLOWUP_THRESHOLD_DAYS` to `.env` with a default of 5.

### Phase 5: Living Fit Assessment

Target: 1 session. Depends on Phase 3 (reads debrief data for reassessment).

- Create `/reassess` skill with its own SKILL.md.
- Reads existing Fit Assessment, all debriefs, and Greg's verbal input.
- Produces updated score and reasoning; writes via existing `fit_assessment` queue command.
- Preserves original score in the reasoning text for transparency.

### Phase 6: Decision Comparison Framework

Target: 1 session. Depends on Phases 1–5 (reads all accumulated data).

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
| `src/jobbing/tracker/notion.py` | Extend | New queue commands (`interview_prep`, `debrief`); extended Interviews DB template schema |
| `src/jobbing/cli.py` | Extend | New CLI subcommands: `debrief`, `reassess`, `compare`, `prep` |
| `.claude/skills/track/SKILL.md` | Extend | Cross-reference new skills (`/prep`, `/debrief`, `/reassess`, `/compare`) |
| `WORKFLOW.md` | Extend | Document interview lifecycle: prep trigger, debrief workflow, reassessment, comparison |
| `CLAUDE.md` | Extend | Update queue commands list, Interviews DB schema description, project structure |
| `.env` | Extend | Add `FOLLOWUP_THRESHOLD_DAYS=5` |

### New Files

| File | Purpose |
|---|---|
| `.claude/skills/prep/SKILL.md` | Interview prep generation skill |
| `.claude/skills/debrief/SKILL.md` | Post-interview debrief capture skill |
| `.claude/skills/reassess/SKILL.md` | Living Fit Assessment update skill |
| `.claude/skills/compare/SKILL.md` | Decision comparison framework skill |
| Scheduled task: `follow-up-monitor` | Daily scheduled task for follow-up cadence checking |

### Backward Compatibility

- All existing queue commands (`create`, `update`, `highlights`, `research`, `outreach`, `interview_questions`, `questions_to_ask`, `fit_assessment`, `job_description`) continue to work unchanged.
- The Interviews DB schema extension is additive — new columns are added alongside existing ones. No data loss.
- Existing tracker pages are not rebuilt or reformatted. New features write to new fields only.
- The `pip install -e .` editable install picks up source changes immediately.

---

## 7. Testing Strategy

**Testing follows the same pragmatic approach as v1: the system's primary interface is a conversation, so testing must validate both the code paths and the conversational workflows.**

### Unit Tests (Python)

- Extend existing test suite with tests for new queue command handlers (`interview_prep`, `debrief`).
- Test `Interview` dataclass serialization/deserialization with all new fields.
- Test the follow-up cadence calculator (days-since-last-activity logic).
- Test Interviews DB schema builder produces correct Notion API payloads.

### Integration Tests (Queue + Notion)

- Dry-run mode for all new queue commands — verify payload structure without making Notion API calls.
- Round-trip test: write a debrief via queue, then read it back via `notion-fetch` and verify content.
- Migration test: run schema migration on a test page's Interviews DB, verify existing data is preserved and new columns are added.

### Conversational Acceptance Tests

Each feature should be validated end-to-end in a real Claude session with the actual Notion database. Test scenarios:

1. **Prep generation:** "I have a technical screen with Thomas Roton at Bandcamp on Thursday" → verify prep material appears in the Interviews DB entry's Prep Notes field.
2. **Debrief capture:** "debrief Bandcamp — talked to Thomas, he asked about GCP migration, I told the 1KOMMA5° story, it landed well" → verify structured debrief in the Interviews DB entry.
3. **Follow-up monitor:** run the scheduled task, verify it correctly identifies entries with no recent interview activity.
4. **Reassessment:** "reassess Cozero — turns out the team is 3 people and the CTO handles all architecture" → verify updated score and reasoning on the Notion page.
5. **Comparison:** "compare Bandcamp and Cozero" → verify a formatted comparison document is produced with data from both tracker pages.

### Regression Guard

- After each phase, run the existing test suite to verify no regressions in v1 features.
- Verify all existing queue commands still process correctly by running `jobbing queue` with test payloads.
- Spot-check 2–3 existing tracker pages to confirm no formatting changes from the schema update.

---

## 8. Feedback Mechanisms

**The system should surface problems early and make quality visible. These mechanisms help Greg and Claude identify what's working and what needs adjustment.**

### Built-In Feedback Loops

- **Debrief-to-prep feedback:** When debrief notes reveal that certain questions keep coming up across companies (e.g., "why leave Solo Recon?" appeared in 4 of 6 screens), the prep generation should prioritize those questions and draw from the best previous answers. This is pattern recognition that improves prep quality over time.
- **Reassessment delta tracking:** When a score changes significantly after reassessment (e.g., 72 → 58), flag this as a learning opportunity. What did the original /analyze miss? This feedback can improve the scoring criteria in /scoring over time.
- **Follow-up effectiveness:** Track whether follow-ups that were prompted by the cadence monitor actually restarted stale conversations. Over time, this data can tune the threshold (5 days might be too aggressive or too lenient depending on the market).

### Manual Feedback Points

- After each prep generation, Greg reviews the material before the interview. If he finds the prep unhelpful or off-target, that's a signal to adjust the prep templates or input weighting.
- After each debrief, Greg can flag if the structured output missed something important from his raw notes. This improves the debrief parsing prompts.
- The comparison framework is explicitly presented as "recommendation with caveats" — Greg's final decision may differ from the weighted output. When it does, that's worth noting: which dimension did the framework underweight?

### Metrics to Track (Informally)

- **Prep usage rate:** Of interviews where prep was generated, how often did Greg actually reference it?
- **Debrief completion rate:** Of all interviews conducted, what percentage have a debrief captured within 24 hours?
- **Stale conversation recovery:** Of follow-ups prompted by the cadence monitor, how many led to resumed activity?
- **Score delta accuracy:** When reassessments happen, how often does the new score better predict eventual outcomes (offer vs. rejection)?

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Notion API rate limits | Medium | The follow-up monitor reads multiple pages in quick succession. Batch reads with delays; cache responses where possible. Current volume (10–20 pages) is well within limits. |
| Interviews DB schema migration breaks existing data | High | Migration is additive only — new columns alongside existing ones. Test on one page before running across all 10. Dry-run mode for all queue commands. |
| Debrief capture adds friction to post-interview flow | Medium | Keep the interaction under 5 minutes. Greg dumps raw notes; Claude does the structuring. If it feels burdensome, it won't get used. Optimize for speed over completeness. |
| Prep material is generic or unhelpful | Medium | Prep quality depends on having good inputs: Experience to Highlight, company research, and interviewer context. If any of these are thin, prep will be thin. The manual feedback point (Greg reviews before the interview) catches this early. |
| `pip install -e .` dependency for new queue commands | Low | Greg must run `pip install -e .` in his venv after each phase to pick up new queue command handlers. Document this clearly in each phase's delivery notes. |
| Scheduled task (follow-up monitor) reliability | Low | Uses the existing launchd-based scheduling on Greg's Mac. Same mechanism as the queue watcher. If the machine is asleep at 9 AM, launchd runs the task on wake. |

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
| **Interviews DB** | An inline Notion database nested inside each tracker page. Tracks individual interviews: who, when, what type, prep, debrief, outcome. One per tracker page. |
| **Skill** | A Claude Code slash command (e.g., `/analyze`, `/apply`, `/track`). Defined in `.claude/skills/{name}/SKILL.md`. In Cowork, skills load as background context and are invoked via natural language. |
| **Data source** | Notion's internal term for a "collection" — the underlying data behind a database view. Referenced by `collection://` URLs in Notion MCP tools. The tracker's data source ID is `7d7b1f6a-4af7-40e1-913f-95b65a89ae41`. |

### Workflow Stages

| Term | Definition |
|---|---|
| **Analyze** | The first step for any job posting. Produces a fit score (0–100), green/red flags, gaps, salary read, company intel, and Experience to Highlight bullets. Skill: `/analyze`. |
| **Apply** | The full application workflow: Notion entry → tailored JSON → PDFs → ATS check. Only runs after `/analyze` and Greg's go decision. Skill: `/apply`. |
| **Prep** | Interview preparation material generated when an interview is scheduled. Includes interviewer research, likely questions, talking points, and questions to ask. Triggered by Greg, not automatic. Skill: `/prep`. |
| **Debrief** | Post-interview structured capture: what they asked, what landed, what you learned, vibe rating, follow-up needed. Written to the Interviews DB entry. Skill: `/debrief`. |
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
| **Toggle section** | A `heading_3` block with `is_toggleable: True` in Notion. The standard container for tracker page content: Job Description, Fit Assessment, Company Research, Experience to Highlight, Questions I Might Get Asked, Questions To Ask In An Interview. |
| **Status** | A select property on the tracker database. Valid values in order: `Targeted` → `Applied` → `Followed-Up` → `In Progress (Interviewing)` → `Done`. Only Greg changes status. |
| **Conclusion** | A text property set when status moves to `Done`. Captures the outcome in Greg's words. |
| **Score** | A number property (0–100) on the tracker database. Set by the `fit_assessment` queue command or the `create` command when `score` is included. |

### Infrastructure Terms

| Term | Definition |
|---|---|
| **launchd agent** | A macOS background process on Greg's Mac that watches `notion_queue/` for new JSON files and processes them. Also runs scheduled tasks. |
| **Notion MCP** | The Model Context Protocol connector for Notion. Read tools (`notion-fetch`, `notion-search`) work reliably. Write tools (`update-page`, `create-pages`) have a Zod serialization bug and must not be used — use the queue instead. |
| **Editable install** | `pip install -e .` in the Jobbing venv. Makes the `jobbing` CLI available and picks up source code changes without reinstalling. Must be re-run after Python code changes. |
