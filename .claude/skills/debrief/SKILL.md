---
name: debrief
description: Capture a structured post-interview debrief. Greg dumps raw thoughts, Claude structures them into the Interviews DB row with questions asked, what landed, what stumbled, new learnings, vibe rating, and follow-up items.
---

# Post-Interview Debrief Capture

Capture what happened in an interview while the conversation is fresh. Greg talks through his impressions; Claude structures them into the Interviews DB entry. The whole interaction should take under five minutes.

## Prerequisites

- Company is tracked in Notion (created via `/analyze` + `/apply`)
- An Interviews DB row exists for this interview (created via `/prep` or `/track`)
- Greg has just finished an interview and wants to capture notes

## Instructions

### Step 1: Load Context

- Read WORKFLOW.md and CONTEXT.md if not already loaded this session
- Look up the company page in Notion via `notion-search` (by company name)
- Read the company page via `notion-fetch` to confirm it exists and pull existing context
- If the company does not exist in the tracker, STOP and tell Greg to run `/analyze` and `/apply` first

### Step 2: Parse the Trigger

Extract from Greg's natural language input:

- **Company name** (required) — match to existing tracker entry
- **Interviewer name** (required if multiple interviews exist) — to find the correct DB row
- **Interview date** (optional) — defaults to today if not specified
- **Raw debrief notes** — Greg's unstructured thoughts about how it went

Examples:
- "Debrief FICO — just talked to Jess Wilson. Went well, she seemed engaged..."
- "Debrief Bandcamp — talked to Thomas and Sami today. Thomas asked about..."
- "Quick debrief on the Cozero technical screen"

If the company has multiple interview rows and Greg doesn't specify which interviewer, ask.

### Step 3: Structure the Debrief

Organize Greg's raw thoughts into seven sections:

**1. Questions They Asked**
- What the interviewer actually asked, in Greg's words
- Note which questions felt like softballs vs. probing deep-dives

**2. What Landed**
- Which of Greg's answers or stories got visible positive reactions
- Moments of genuine connection or engagement
- Topics where the interviewer leaned in or asked follow-up questions

**3. What Stumbled**
- Anything that didn't go well, or where Greg felt under-prepared
- Questions that caught him off guard
- Areas where the answer was vague or unconvincing
- Use this to inform prep for the next round

**4. What You Learned**
- New information about the role, team, company, or culture that wasn't in the job posting or company research
- Corrections to earlier assumptions (team size different than expected, tech stack different, etc.)
- Organizational dynamics, management style, team health signals

**5. Updated Read**
- Has this interview changed Greg's overall assessment of the opportunity?
- Flag if the fit score should be reassessed (e.g., "learned the team is 3 people, not 8 — reassessment warranted")
- If nothing changed, say so: "Assessment unchanged"

**6. Follow-Up Needed**
- Action items: send additional materials, email a contact, prepare for a specific next-round topic
- Timeline: when is the next step expected?
- Anyone Greg should reach out to

**7. Vibe** (1–5)
- Gut-feel rating of mutual fit:
  - 1 = Bad signs, probably withdrawing
  - 2 = Lukewarm, concerns remain
  - 3 = Neutral, need more data
  - 4 = Good conversation, optimistic
  - 5 = Strong mutual fit, excited about this one

### Step 4: Present for Review — CHECKPOINT

Present the structured debrief to Greg for review. This is a mandatory checkpoint — wait for feedback before writing to Notion. Greg may:

- Correct details about what was discussed
- Add things he forgot to mention
- Adjust the vibe rating
- Clarify follow-up items
- Flag whether the fit score needs reassessment

### Step 5: Write to Notion

After Greg approves, write to `notion_queue/`:

```json
{
  "command": "debrief",
  "name": "CompanyName",
  "date": "2026-03-09",
  "interviewer": "Jess Wilson — Recruiter / Talent Acquisition",
  "outcome": "Pending",
  "vibe": 4,
  "debrief": "## Questions They Asked\n- ...\n\n## What Landed\n- ...\n\n## What Stumbled\n- ...\n\n## What You Learned\n- ...\n\n## Updated Read\n- ...\n\n## Follow-Up Needed\n- ...",
  "questions_they_asked": ["Tell me about yourself", "Why FICO?", "Salary expectations?"],
  "questions_i_asked": ["Team size and structure?", "Interview timeline?"],
  "follow_up": "Next round expected within a week. Prepare system design examples."
}
```

Queue file naming: `YYYYMMDD_companyname_debrief.json`

**Outcome values:** Pending, Passed, Rejected, Withdrawn. Use "Pending" if the result isn't known yet (which is typical immediately after an interview). Greg will update the outcome later via `/track` when he hears back.

### Panel Interviews

When Greg met multiple interviewers in a single session:

- **Back-to-back 1:1s** (e.g., "talked to Thomas, then Sami"): Create one debrief queue file per interviewer, each with the same date and interview type but separate debrief content.
- **True panel** (one conversation with multiple interviewers): Use a combined interviewer field: "Thomas Roton + Sami Chen, Panel". Create a single debrief entry.
- Make this judgment from context — if Greg describes distinct conversations, they're separate. If it was one discussion, it's a panel.

## Critical Rules

- Check CONTEXT.md before every assertion about Greg's experience — dates, team sizes, achievements must be accurate
- Structure Greg's raw notes faithfully — don't add information he didn't provide
- Vibe rating is Greg's gut feel — don't override or "correct" it
- Outcome is almost always "Pending" right after an interview — don't assume Passed or Rejected unless Greg explicitly says so
- Flag reassessment honestly — if Greg learned something that materially changes the fit picture, say so
- No AI tells — no "aligns perfectly", "uniquely positioned", "proven track record"
- Debrief notes are for Greg's eyes only — be direct and strategic, not polished

## Do Not

- Skip the review checkpoint — present the structured debrief to Greg and wait for feedback before writing to Notion
- Fabricate debrief content — only structure what Greg actually tells you. If a section is empty, write "Nothing noted" rather than inventing content
- Auto-set Outcome to anything other than "Pending" unless Greg explicitly states the result
- Overwrite an existing debrief without confirming — the debrief command replaces the Debrief toggle section
- Create a debrief for a company not tracked in Notion — tell Greg to run `/analyze` + `/apply` first
- Infer interviewer reactions that Greg didn't describe — "What Landed" comes from Greg's perception, not Claude's speculation
- Use Notion MCP write tools — queue system only for all writes
- Change the vibe rating Greg provides — it's his gut feel, not yours to adjust

## Related Skills

- `/prep` — Interview prep generation (run before the interview)
- `/analyze` — Fit assessment (run before everything)
- `/apply` — Full application workflow (creates the tracker entry)
- `/track` — Status updates, including updating Outcome after hearing back
