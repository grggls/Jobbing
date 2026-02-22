# /track — Tracker Operations

Manage the Notion job application tracker. Use this for status updates, adding research, updating highlights, or any tracker operations outside the main `/analyze` → `/apply` flow.

## Common Operations

### Update Status

When Greg asks to change an application's status:

```json
{"command": "update", "page_id": "PAGE_ID", "status": "Applied"}
```

Valid statuses: Targeted, Researching, Applied, Interviewing, Offered, Done

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

## How to Find a Page ID

- Use Notion MCP read tools: `notion-search` to find by company name
- The page ID is returned when creating entries via `/apply`
- Greg may provide it directly

## Rules

- **Status updates are Greg's decision.** Never auto-mark "Applied" or any other status.
- **Queue-only for writes.** Write JSON to `notion_queue/` — the launchd agent processes it. Do not use Notion MCP write tools.
- **Notion MCP reads work fine.** Use `notion-fetch` and `notion-search` for verification and lookups.
- All `--dry-run` flags are available on CLI commands for previewing.

## CLI Reference

```bash
jobbing track create --name "Company" --position "Role" --date 2026-02-22 [--dry-run]
jobbing track update --page-id "ID" --status "Applied" [--dry-run]
jobbing track highlights --page-id "ID" --highlights "Bullet 1" "Bullet 2" [--dry-run]
jobbing track research --name "Company" --research "Finding 1" "Finding 2" [--dry-run]
jobbing track outreach --name "Company" --contacts-json contacts.json [--dry-run]
jobbing queue  # process all pending queue files
```
