# Jobbing

AI-assisted job application workflow. Analyzes job postings against a candidate profile, generates tailored CVs and cover letters as PDFs, and tracks applications in a Notion database.

## How It Works

1. **`/analyze`** — Paste a job posting. Claude scores fit (0–100), identifies green/red flags, researches the company, and drafts Experience to Highlight bullets. You review and decide: proceed or skip.
2. **`/apply`** — Claude creates a Notion tracker entry, generates a tailored `{company}.json` with CV and cover letter content, renders PDFs, and runs an ATS keyword check.
3. **`/outreach`** — After applying, Claude researches LinkedIn contacts and drafts connection request messages.
4. **`/scan`** — Scan bookmarked job boards. Python fetches the pages, Claude extracts and scores postings in-conversation.
5. **`/track`** — Status updates, research, highlights — any tracker operation.

These are Claude Code skills (slash commands) defined in `.claude/skills/`. Full workflow details: [WORKFLOW.md](WORKFLOW.md)

## Setup

```bash
# Clone and install
git clone <repo-url> && cd Jobbing
python3 -m venv .venv
.venv/bin/pip install -e .

# Configure
cp .env.example .env
# Edit .env with your Notion API key

# Set up your profile
cp examples/example_context.md CONTEXT.md
cp examples/example_bookmarks.md BOOKMARKS.md
# Edit both with your real data
```

After `pip install -e .`, the `jobbing` CLI is available at `.venv/bin/jobbing`.

### Notion Queue Agent (launchd)

A launchd agent watches `notion_queue/` and auto-processes queue files written by Claude during sessions. To install:

```bash
# The plist runs: .venv/bin/python3 -m jobbing queue
cp com.grggls.notion-queue.plist ~/Library/LaunchAgents/
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.grggls.notion-queue.plist
```

The agent uses the project venv (`python3 -m jobbing queue`), so new queue commands are available immediately after `pip install -e .` — no agent restart needed.

To reload after plist changes:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.grggls.notion-queue.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.grggls.notion-queue.plist
```

**Troubleshooting:** If a queue command fails with "Unknown command", the installed package is likely stale. Run `pip install -e .` in the project venv. Check `notion_queue_results/launchd-stderr.log` for errors.

## Usage

### Generate PDFs

```bash
jobbing pdf <company>              # Both CV and cover letter
jobbing pdf <company> --cv-only    # Just the CV
jobbing pdf <company> --cl-only    # Just the cover letter
jobbing pdf <company> --output-dir /path
```

Reads `companies/{company}/{company}.json`, writes PDFs to the same directory.

### Tracker operations

```bash
jobbing track create --name "Company" --position "Role" --date 2026-02-22
jobbing track update --page-id "ID" --status "Applied"
jobbing track highlights --page-id "ID" --highlights "Bullet 1" "Bullet 2"
jobbing track research --name "Company" --research "Finding 1" "Finding 2"
jobbing track outreach --name "Company" --contacts-json contacts.json
```

All commands support `--dry-run` to preview without sending.

### Job board scanning

```bash
jobbing scan bookmarks                              # List all bookmarks by category
jobbing scan bookmarks --categories "Climate / Impact"  # List one category
jobbing scan existing                               # List companies already tracked
jobbing scan fetch                                  # Fetch all boards (~30s)
jobbing scan fetch --categories "Startup / Tech"    # Fetch one category
jobbing scan fetch --limit 5                        # Fetch first 5 boards
```

### Queue processing

Claude writes JSON files to `notion_queue/` during sessions. Process them:

```bash
jobbing queue
```

### Iterate on a PDF

1. Edit `companies/{company}/{company}.json`
2. Run `jobbing pdf {company}`

## Skills (Slash Commands)

| Skill | Purpose | When to use |
| ----- | ------- | ----------- |
| `/analyze` | Fit assessment, scoring, company research | First step — paste a job posting |
| `/apply` | Notion entry, JSON, PDFs, ATS check | After `/analyze` and go decision |
| `/outreach` | LinkedIn contact research + messages | After applying |
| `/scan` | Job board scanning and scoring | Periodic board sweeps |
| `/track` | Status updates, research, highlights | Any tracker operation |

Skills are defined in `.claude/skills/` and auto-discovered by Claude Code CLI as `/` slash commands. For Cowork, upload the `SKILL.md` files via Settings > Capabilities, then reference them naturally in conversation:

- "Analyze this job posting please" — triggers the analyze skill
- "Thanks, track this job posting and help me apply please" — triggers track + apply skills

## Project Structure

```text
Jobbing/
├── pyproject.toml              # Package metadata, deps, CLI entry point
├── WORKFLOW.md                 # Authoritative workflow instructions
├── CLAUDE.md                   # Project instructions for Claude Code
├── SCORING.md                  # Tunable scoring guidelines for job matching
│
├── .claude/skills/             # Claude Code slash commands
│   ├── analyze/SKILL.md        # /analyze — fit assessment
│   ├── apply/SKILL.md          # /apply — full application workflow
│   ├── outreach/SKILL.md       # /outreach — LinkedIn outreach
│   ├── scan/SKILL.md           # /scan — job board scanner
│   └── track/SKILL.md          # /track — tracker operations
│
├── src/jobbing/                # Python package
│   ├── cli.py                  # Unified CLI: jobbing track|queue|pdf|scan
│   ├── config.py               # Config loading (env, .env, paths)
│   ├── models.py               # Domain model (Application, Contact, CVData, etc.)
│   ├── pdf.py                  # PDF generator (CV + cover letter)
│   ├── scanner.py              # Bookmark parser + board fetcher
│   └── tracker/
│       ├── __init__.py         # TrackerBackend Protocol + factory
│       ├── notion.py           # Notion API tracker
│       └── json_file.py        # JSON file tracker (portable fallback)
│
├── docs/                       # Architecture, decisions, design history
├── examples/                   # Anonymized templates
├── tests/
│
├── CONTEXT.md                  # Your profile (gitignored, copy from examples/)
├── BOOKMARKS.md                # Your job board URLs (gitignored)
├── .env                        # API keys (gitignored)
├── companies/                  # Per-company data (gitignored)
└── scan_results/               # Scan logs (gitignored)
```

## Tracker Backends

The tracker uses a Protocol pattern — swap backends via `TRACKER_BACKEND` env var:

- **`notion`** (default): Full Notion API integration with rich page sections
- **`json`**: Local `tracker.json` file, zero dependencies, good for testing

## Configuration

All config is loaded from environment variables or `.env`:

| Variable | Required | Default | Purpose |
| -------- | -------- | ------- | ------- |
| `NOTION_API_KEY` | For Notion tracker | — | Notion integration token |
| `NOTION_DATABASE_ID` | No | built-in | Notion database ID |
| `TRACKER_BACKEND` | No | `notion` | `notion` or `json` |
| `SCORE_THRESHOLD` | No | `60` | Minimum score for scan matches |

## Cowork Compatibility

The `jobbing` CLI works in both Claude Code CLI and Cowork environments. Skills work differently in each:

- **Claude Code CLI**: Auto-discovers skills from `.claude/skills/` as `/analyze`, `/apply`, etc.
- **Cowork**: Upload each `SKILL.md` via Settings > Capabilities. Skills load as background context — use natural language ("analyze this job posting", "help me apply") instead of slash commands
