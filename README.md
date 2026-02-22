# Jobbing

AI-assisted job application workflow. Tailors CVs and cover letters per company, generates PDFs, and tracks applications in a Notion database.

## How It Works

1. **Paste a job posting** into a Claude Code session (instructions auto-load from `CLAUDE.md`)
2. **Claude analyzes fit** against `CONTEXT.md` (profile, career history, skills)
3. **Claude generates `{company}.json`** with tailored CV and cover letter content
4. **`generate_pdfs.py`** renders the JSON into professional PDFs
5. **Notion tracker** is updated via a queue-based system (`notion_update.py`)

Full workflow details: [WORKFLOW.md](WORKFLOW.md)

## Project Structure

```
Jobbing/
├── README.md                  # This file
├── CONTEXT.md                 # Profile, career history, skills (read first)
├── WORKFLOW.md                # Authoritative workflow instructions (read second)
├── CLAUDE.md                  # Project instructions for Claude Code (auto-loaded)
├── CV-GREGORY-DAMIANI.pdf     # Master CV (generic)
│
├── generate_pdfs.py           # PDF generator (reads JSON, outputs PDFs)
├── notion_update.py           # Notion API client (create/update tracker pages)
├── notion_queue_runner.sh     # launchd queue processor
├── pyproject.toml             # Python project metadata and dependencies
├── .env                       # Notion API key (not committed)
├── .venv/                     # Python virtual environment
│
├── companies/                 # All company-specific content
│   ├── acto/                  # Interview prep docs
│   ├── ashby/                 # JSON + PDFs + application answers
│   ├── dash0/                 # JSON + PDFs + application answers
│   ├── perplexity/            # JSON + PDFs + application answers
│   └── ...                    # One directory per company
│
├── notion_queue/              # Transient: queue files for Notion updates
└── notion_queue_results/      # Audit trail: processed queue operations
```

### Company Directories

Each company gets its own directory under `companies/`:

```
companies/dash0/
├── dash0.json                 # Tailored CV + CL content (source of truth)
├── DASH0-CV.pdf               # Generated CV
├── DASH0-CL.pdf               # Generated cover letter
└── DASH0-APPLICATION-ANSWERS.md  # Application questions (when needed)
```

Some companies also have interview prep, email drafts, or architecture docs.

## Setup

```bash
# Create virtual environment and install dependencies
python3 -m venv .venv
.venv/bin/pip install reportlab

# Set up Notion API key
echo 'NOTION_API_KEY=your_key_here' > .env
```

## Usage

### Generate PDFs for a company

```bash
.venv/bin/python3 generate_pdfs.py {company}              # Both CV and CL
.venv/bin/python3 generate_pdfs.py {company} --cv-only    # Just the CV
.venv/bin/python3 generate_pdfs.py {company} --cl-only    # Just the cover letter
.venv/bin/python3 generate_pdfs.py {company} --output-dir /path  # Custom output dir
```

### Iterate on a PDF

1. Edit `companies/{company}/{company}.json`
2. Re-run `generate_pdfs.py`

### Notion tracker

The Notion integration uses a queue-based system. Claude writes JSON files to `notion_queue/`, and a launchd agent processes them automatically via `notion_queue_runner.sh`.

```bash
# Manual queue processing (if needed)
.venv/bin/python3 notion_update.py run-queue

# Direct CLI usage
.venv/bin/python3 notion_update.py create --name "Company" --position "Role" --date "2026-02-20"
.venv/bin/python3 notion_update.py update --page-id "PAGE_ID" --status "Applied"
```

## Key Files

| File | Purpose |
|------|---------|
| `CONTEXT.md` | Greg's profile, career timeline, skills, salary benchmarks |
| `WORKFLOW.md` | Step-by-step workflow instructions for Claude |
| `CLAUDE.md` | Project instructions for Claude Code (auto-loaded every session) |
| `generate_pdfs.py` | Reads `companies/{company}/{company}.json`, outputs PDFs |
| `notion_update.py` | Creates/updates Notion database pages via REST API |
