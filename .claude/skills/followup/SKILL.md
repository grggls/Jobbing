---
name: followup
description: Check all "In Progress (Interviewing)" entries for staleness. Surfaces stale conversations with last contact date, interviewer, and suggested follow-up actions. No auto-actions — information for Greg to act on.
---

# Follow-Up Cadence Monitor

Check all active interview processes for staleness. Surface companies where the last interview was more than N days ago with suggested next actions. No automatic actions — this is an information tool for Greg to decide what to do.

## Prerequisites

- At least one application with status "In Progress (Interviewing)" in the tracker
- Interviews DB entries with dates (created via `/prep` or `/debrief`)

## Instructions

### Step 1: Load Context

- Read WORKFLOW.md and CONTEXT.md if not already loaded this session
- This skill reads directly from the Notion tracker — no queue writes needed

### Step 2: Gather Active Interview Processes

Query the tracker for all applications with status "In Progress (Interviewing)":

1. Use `notion-search` or `notion-fetch` on the tracker database to find all pages with status "In Progress (Interviewing)"
2. For each page, read the Interviews inline database to find all interview entries
3. Extract the most recent interview date, interviewer name, and interview type from the Interviews DB
4. Also check the "Follow-Up Needed" field from the most recent debrief (if any) for pending action items

### Step 3: Calculate Staleness

For each active company:

- **Last activity date**: The most recent interview date from the Interviews DB. If no interviews exist in the DB, use the page's "Start Date" property as fallback.
- **Days since last activity**: Today's date minus the last activity date
- **Threshold**: Default 5 days, configurable via `FOLLOWUP_THRESHOLD_DAYS` in `.env`

Categorize each company:

- **Stale** (above threshold): Needs attention — suggest follow-up action
- **Active** (at or below threshold): Recently active, no action needed
- **No data**: Has "In Progress (Interviewing)" status but no interview dates — flag as needing review

### Step 4: Generate Follow-Up Suggestions

For each stale company, suggest a specific follow-up action based on context:

- **After a screening call**: "Send a brief check-in to [interviewer] — ask about timeline for next steps"
- **After a technical/system design round**: "Follow up with recruiter on [company] — technical round was [N] days ago"
- **After a hiring manager conversation**: "Check in with [interviewer] at [company] — last contact was [date]"
- **Pending action items**: If the most recent debrief has follow-up items, surface those specifically: "Outstanding action: [follow-up text]"
- **No interviews recorded**: "No interviews logged for [company] despite 'In Progress' status — verify timeline or update status"

### Step 5: Present the Summary

Format the output as a staleness report, sorted by days since last activity (most stale first):

```
## Follow-Up Check — [today's date]

### Needs Attention (N companies)

**CompanyName** — 8 days since last contact
  Last: Technical screen with Jane Smith (Feb 27)
  Suggested: Follow up with recruiter on timeline for next round
  Outstanding: Send architecture diagram (from debrief)

**CompanyName** — 6 days since last contact
  Last: Phone screen with Bob Jones (Mar 1)
  Suggested: Send a brief check-in — ask about timeline for next steps

### Recently Active (N companies)

**CompanyName** — 2 days since last contact
  Last: Hiring manager with Alice Chen (Mar 5)
  Next: System design round scheduled Mar 10

### No Interview Data (N companies)

**CompanyName** — Status is "In Progress" but no interviews logged
  Suggested: Log interviews or update status if process has ended
```

If no companies are stale, say so plainly: "All active interview processes have recent activity. Nothing needs follow-up right now."

### Step 6: Offer Actions

After presenting the summary, ask Greg if he wants to:

- Draft a follow-up email for any stale company
- Update the status of any company (e.g., move to "Done" if the process has ended)
- Add a debrief for a recent interview that wasn't captured

Do NOT take any of these actions automatically — wait for Greg's instruction.

## CLI Mode (Optional)

When invoked via `jobbing track followup`, output a plain-text summary to stdout (same format as Step 5) and optionally write to `notion_queue_results/followup-YYYY-MM-DD.md`.

## Threshold Configuration

Default: 5 days. Override via `.env`:

```
FOLLOWUP_THRESHOLD_DAYS=7
```

The threshold applies uniformly to all companies. If Greg finds certain companies need different cadences, he can adjust the threshold or simply note exceptions when reviewing the summary.

## Critical Rules

- Read-only — this skill does NOT write to Notion or the queue. It only reads and presents information.
- Today's date comes from the system, not from assumptions. Use the current date for all calculations.
- Do not fabricate interview dates or interviewer names — only surface what's actually in the Interviews DB
- Do not auto-update any status — status changes are Greg's decision
- If a company has "In Progress (Interviewing)" status but no Interviews DB entries, flag it as anomalous rather than assuming everything is fine
- Sort by staleness (most stale first) so the most urgent items are at the top

## Do Not

- Write to Notion or the queue — this is a read-only skill
- Auto-send follow-up emails or messages — only suggest actions
- Change any application status without Greg's explicit instruction
- Assume interview outcomes — if the debrief says "Pending", it's still pending
- Ignore companies with no interview data — they need attention too
- Use Notion MCP write tools — this skill doesn't write anything, but if Greg asks for a status update afterward, use the queue

## Related Skills

- `/prep` — Interview prep generation (run before interviews)
- `/debrief` — Post-interview debrief capture (provides the data this skill reads)
- `/track` — Status updates (use after reviewing follow-up summary)
- `/analyze` — Fit assessment (referenced for company context)
