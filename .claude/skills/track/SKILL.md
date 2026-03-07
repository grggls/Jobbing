---
name: track
description: Manage the Notion job application tracker. Status updates, research, highlights, conclusions, and other tracker operations outside the main /analyze and /apply flow.
---

# Tracker Operations

Manage the Notion job application tracker. Use this for status updates, adding research, updating highlights, or any tracker operations outside the main `/analyze` → `/apply` flow.

## Common Operations

### Update Status

When Greg asks to change an application's status:

```json
{"command": "update", "page_id": "PAGE_ID", "status": "Applied"}
```

Valid statuses: Targeted, Applied, Followed-Up, In Progress (Interviewing), Done

Write to `notion_queue/` or use: `jobbing track update --page-id "PAGE_ID" --status "Applied"`

### Close Out an Application

```json
{"command": "update", "page_id": "PAGE_ID", "status": "Done", "conclusion": "Outcome text"}
```

### Update Research

Add or replace company research on a tracker entry:

```json
{
  "command": "research",
  "name": "CompanyName",
  "research": ["Founded 2020, Series B ($50M)", "120 employees, Berlin HQ", "Glassdoor 4.2/5"]
}
```

Or: `jobbing track research --name "CompanyName" --research "Finding 1" "Finding 2"`

### Update Highlights

Replace the Experience to Highlight bullets:

```json
{
  "command": "highlights",
  "page_id": "PAGE_ID",
  "highlights": ["New bullet 1", "New bullet 2"]
}
```

Or: `jobbing track highlights --page-id "PAGE_ID" --highlights "Bullet 1" "Bullet 2"`

### Update Interview Questions

Replace the "Questions I Might Get Asked" section (Q as bullet, A as nested sub-bullet):

```json
{
  "command": "interview_questions",
  "name": "CompanyName",
  "questions": [
    {"question": "Tell me about scaling a DevOps team?", "answer": "At Mobimeo, scaled from 8 to 23..."},
    {"question": "How do you handle incident response?", "answer": "Blameless postmortems, standardized on-call..."}
  ]
}
```

### Update Questions To Ask

Replace the "Questions to Ask" section:

```json
{
  "command": "questions_to_ask",
  "name": "CompanyName",
  "questions": ["What does the on-call rotation look like?", "How is the platform team structured?"]
}
```

## How to Find a Page ID

- Use Notion MCP read tools: `notion-search` to find by company name
- The page ID is returned when creating entries via `/apply`
- Greg may provide it directly

## Rules

- **Status updates are Greg's decision.** Never auto-mark "Applied" or any other status.
- **Queue for all Notion writes.** Write JSON to `notion_queue/`, the launchd agent processes it. Do not use any Notion MCP write tools (Zod serialization bugs).
- **Notion MCP reads work fine.** Use `notion-fetch` and `notion-search` for verification and lookups.
- All `--dry-run` flags are available on CLI commands for previewing.

## Do Not
- Change any Notion status without Greg's explicit instruction — never auto-mark "Applied", "Done", or any other status
- Use any Notion MCP write tools (`update-page`, `create-pages`) — they have Zod serialization bugs. Use the queue for all writes.
- Guess at a page ID — look it up via `notion-search` or ask Greg
- Write a conclusion without Greg's input — conclusions capture Greg's assessment, not Claude's
- Overwrite existing highlights or research without confirming — these operations replace the entire section
- Create duplicate tracker entries — check if one already exists before creating
- Modify status to "Done" without a conclusion — always include the outcome text

### Interview Prep

Write prep notes to an Interviews DB row (finds or creates the row):

```json
{
  "command": "interview_prep",
  "name": "CompanyName",
  "date": "2026-03-15",
  "interviewer": "Jane Smith — VP Engineering",
  "interview_type": "Hiring Manager",
  "prep_notes": "## Key Topics\n- Platform strategy\n- Team scaling",
  "questions_to_ask": ["What's the team's biggest challenge right now?"]
}
```

### Debrief

Write debrief + outcome after an interview:

```json
{
  "command": "debrief",
  "name": "CompanyName",
  "date": "2026-03-15",
  "interviewer": "Jane Smith — VP Engineering",
  "outcome": "Passed",
  "vibe": 4,
  "debrief": "Strong conversation about platform strategy.",
  "questions_they_asked": ["How did you handle the Terraform migration?"],
  "questions_i_asked": ["What's the on-call rotation?"],
  "follow_up": "Send architecture diagram. Next round: system design."
}
```

## CLI Reference

```bash
jobbing track create --name "Company" --position "Role" --date 2026-02-22 [--dry-run]
jobbing track update --page-id "ID" --status "Applied" [--dry-run]
jobbing track highlights --page-id "ID" --highlights "Bullet 1" "Bullet 2" [--dry-run]
jobbing track research --name "Company" --research "Finding 1" "Finding 2" [--dry-run]
jobbing track outreach --name "Company" --contacts-json contacts.json [--dry-run]
jobbing queue  # process all pending queue files
```

## Related Skills

- `/analyze` — Fit assessment (always the first step)
- `/apply` — Full application workflow (Notion entry + JSON + PDFs)
- `/outreach` — LinkedIn contact research and messages
