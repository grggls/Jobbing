---
name: debrief
description: Capture a structured post-interview debrief. Greg dumps raw thoughts, Claude structures them into the interview file with questions asked, what landed, what stumbled, new learnings, vibe rating, and follow-up items.
---

# Post-Interview Debrief Capture

Capture what happened in an interview while the conversation is fresh. Greg talks through his impressions; Claude structures them into the interview file. The whole interaction should take under five minutes.

## Prerequisites

- Company is tracked in Obsidian (`kanban/companies/{Company}.md`)
- Greg has just finished an interview and wants to capture notes

## Instructions

### Step 1: Load Context

- Read WORKFLOW.md and CONTEXT.md if not already loaded this session
- Read `kanban/companies/{Company}.md` to confirm the company exists and pull current status, score, and any existing interview wikilinks in `## Interviews`
- If the company hub file does not exist, STOP and tell Greg to run `/analyze` and `/apply` first

### Step 2: Parse the Trigger

Extract from Greg's natural language input:

- **Company name** (required) — match to existing hub file
- **Interviewer name** (required if multiple interviews exist) — to find the correct interview file
- **Interview date** (optional) — defaults to today if not specified
- **Raw debrief notes** — Greg's unstructured thoughts about how it went

Examples:
- "Debrief FICO — just talked to Jess Wilson. Went well, she seemed engaged..."
- "Debrief Bandcamp — talked to Thomas and Sami today. Thomas asked about..."
- "Quick debrief on the Cozero technical screen"

If the company has multiple interview files and Greg doesn't specify which interviewer, ask.

### Step 3: Load Existing Interview File (If It Exists)

Derive the expected file path from the date and interviewer name:
- `kanban/interviews/{Company}/{date}-{FirstName-LastName}.md`
- Example: `kanban/interviews/FICO/2026-03-09-Jess-Wilson.md`

Use the Read tool to check if the file exists. If `/prep` was already run, the file will exist with Prep Notes populated and an empty `## Debrief` section. Read it now to understand the context.

### Step 4: Structure the Debrief

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

### Step 5: Present for Review — CHECKPOINT

Present the structured debrief to Greg for review. This is a mandatory checkpoint — wait for feedback before writing any files. Greg may:

- Correct details about what was discussed
- Add things he forgot to mention
- Adjust the vibe rating
- Clarify follow-up items
- Flag whether the fit score needs reassessment

### Step 6: Write to Interview File

After Greg approves:

**If the interview file already exists** (created by `/prep`):
- Use the Edit tool to populate the `## Debrief` section with the structured content
- Update `vibe:` and `outcome:` in the YAML frontmatter

**If no interview file exists yet** (unscheduled interview, no prior `/prep`):
- Derive the slug from the interviewer name: `{date}-{FirstName-LastName}.md`
- Create `kanban/interviews/{Company}/{date}-{FirstName-LastName}.md` with full frontmatter and all sections:

```markdown
---
company: "Company Name"
interviewer: "Jess Wilson"
role: "Recruiter / Talent Acquisition"
type: "Phone Screen"
date: 2026-03-09
vibe: 4
outcome: "Pending"
---

# Jess Wilson — Phone Screen · 2026-03-09
**Company:** [[Company Name]] · **Outcome:** Pending · **Vibe:** 4/5

## Prep Notes

## Debrief

## Transcript / Raw Notes
```

Then populate `## Debrief` with the structured content.

**Outcome values:** Pending, Passed, Rejected, Withdrawn. Use "Pending" if the result isn't known yet (which is typical immediately after an interview). Greg will update the outcome later when he hears back.

### Step 7: Update Hub Interviews Section

In `kanban/companies/{Company}.md`, update the `## Interviews` section:

- **If a wikilink for this interview already exists** (added by `/prep`): update the display text to reflect the outcome, e.g.:
  - `- [[2026-03-09-Jess-Wilson|Jess Wilson — Phone Screen · Pending · Vibe 4/5]]`
- **If no wikilink exists yet**: append a new line to `## Interviews`:
  - `- [[2026-03-09-Jess-Wilson|Jess Wilson — Phone Screen · Pending · Vibe 4/5]]`

Use the Edit tool to make this change.

### Panel Interviews

When Greg met multiple interviewers in a single session:

- **Back-to-back 1:1s** (e.g., "talked to Thomas, then Sami"): Create one interview file per interviewer, each with the same date and interview type but separate debrief content. Add a wikilink per file in the hub.
- **True panel** (one conversation with multiple interviewers): Use a combined interviewer field: "Thomas Roton + Sami Chen, Panel". Create a single interview file.
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

- Skip the review checkpoint — present the structured debrief to Greg and wait for feedback before writing any files
- Fabricate debrief content — only structure what Greg actually tells you. If a section is empty, write "Nothing noted" rather than inventing content
- Auto-set Outcome to anything other than "Pending" unless Greg explicitly states the result
- Overwrite an existing debrief section without confirming — ask if content already exists
- Create a debrief for a company not tracked in Obsidian — tell Greg to run `/analyze` + `/apply` first
- Infer interviewer reactions that Greg didn't describe — "What Landed" comes from Greg's perception, not Claude's speculation
- Change the vibe rating Greg provides — it's his gut feel, not yours to adjust

## Related Skills

- `/prep` — Interview prep generation (run before the interview)
- `/analyze` — Fit assessment (run before everything)
- `/apply` — Full application workflow (creates the hub file)
- `/track` — Status updates, including updating Outcome after hearing back
