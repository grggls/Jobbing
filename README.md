# Jobbing

AI-assisted job application workflow. Analyzes job postings against a candidate profile, generates tailored CVs and cover letters as PDFs, and tracks applications in a Notion database. Built with LangGraph for autonomous job board scanning and LangSmith for observability.

## How It Works

1. **Paste a job posting** into a Claude Code session (instructions auto-load from `CLAUDE.md`)
2. **Claude analyzes fit** against `CONTEXT.md` (profile, career history, skills)
3. **Claude generates `{company}.json`** with tailored CV and cover letter content
4. **`jobbing pdf`** renders the JSON into professional PDFs
5. **`jobbing track`** updates the Notion tracker (or JSON fallback)

Full workflow details: [WORKFLOW.md](WORKFLOW.md)

## Setup

```bash
# Clone and install
git clone <repo-url> && cd Jobbing
python3 -m venv .venv
.venv/bin/pip install -e .

# Configure API keys
cp .env.example .env
# Edit .env with your Notion, Anthropic, and LangSmith keys

# Set up your profile
cp CONTEXT.example.md CONTEXT.md
cp BOOKMARKS.example.md BOOKMARKS.md
# Edit both with your real data
```

After `pip install -e .`, the `jobbing` CLI is available at `.venv/bin/jobbing`.

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

### Queue processing

Claude writes JSON files to `notion_queue/` during sessions. Process them:

```bash
jobbing queue
```

### Iterate on a PDF

1. Edit `companies/{company}/{company}.json`
2. Run `jobbing pdf {company}`

## Project Structure

```
Jobbing/
├── pyproject.toml              # Package metadata, deps, CLI entry point
├── WORKFLOW.md                 # Authoritative workflow instructions
├── CLAUDE.md                   # Project instructions for Claude Code
├── scoring_criteria.md         # Tunable scoring guidelines for job matching
│
├── src/jobbing/                # Python package
│   ├── cli.py                  # Unified CLI: jobbing track|queue|pdf
│   ├── config.py               # Config loading (env, .env, API keys)
│   ├── models.py               # Domain model (Application, Contact, CVData, etc.)
│   ├── pdf.py                  # PDF generator (CV + cover letter)
│   ├── tracker/
│   │   ├── __init__.py         # TrackerBackend Protocol + factory
│   │   ├── notion.py           # Notion API tracker
│   │   └── json_file.py        # JSON file tracker (portable fallback)
│   └── agent/                  # LangGraph agent (Phase 3)
│
├── docs/                       # Architecture, decisions, design history
├── examples/                   # Anonymized templates
├── tests/
│
├── CONTEXT.md                  # Your profile (gitignored, copy from .example)
├── BOOKMARKS.md                # Your job board URLs (gitignored)
├── .env                        # API keys (gitignored)
├── companies/                  # Per-company data (gitignored)
└── scan_results/               # Autonomous scan logs (gitignored)
```

## Tracker Backends

The tracker uses a Protocol pattern — swap backends via `TRACKER_BACKEND` env var:

- **`notion`** (default): Full Notion API integration with rich page sections
- **`json`**: Local `tracker.json` file, zero dependencies, good for testing

## Configuration

All config is loaded from environment variables or `.env`:

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `NOTION_API_KEY` | For Notion tracker | — | Notion integration token |
| `NOTION_DATABASE_ID` | No | built-in | Notion database ID |
| `ANTHROPIC_API_KEY` | For agent | — | Claude API key |
| `LANGCHAIN_API_KEY` | No | — | LangSmith tracing |
| `LANGCHAIN_PROJECT` | No | `jobbing` | LangSmith project name |
| `TRACKER_BACKEND` | No | `notion` | `notion` or `json` |
| `SCORE_THRESHOLD` | No | `60` | Minimum score for Notion entry |

## Cowork Compatibility

The `jobbing` CLI works in both Claude Code CLI and Cowork environments. Claude Code CLI auto-discovers project-level Skills from `.claude/skills/`; Cowork requires manual upload via Settings > Capabilities.
