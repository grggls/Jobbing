# Architecture

## Overview

Jobbing is a Python package that orchestrates an AI-assisted job application workflow. Claude Code skills provide the conversational interface; a CLI and Notion API handle tracking and document generation.

## System Diagram

```
┌─────────────────────────────────────────────────────────┐
│  INTERACTIVE MODE                                        │
│  (Claude Code / Cowork session)                          │
│                                                          │
│  /analyze  /apply  /outreach  /scan  /track              │
│  Claude Code Skills (.claude/skills/)                    │
│  (structured prompts with judgment logic)                │
└────────────────────────┬─────────────────────────────────┘
                         │ invokes
                         ▼
┌─────────────────────────────────────────────────────────┐
│  PYTHON PACKAGE: src/jobbing/                            │
│                                                          │
│  cli.py     config.py     models.py     pdf.py           │
│  scanner.py                                              │
│  tracker/notion.py    tracker/json_file.py               │
└─────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│  EXTERNAL SERVICES                                       │
│                                                          │
│  Notion API (tracker)    Job boards (scanner)            │
└─────────────────────────────────────────────────────────┘
```

## Package Structure

```
src/jobbing/
├── __init__.py
├── __main__.py             # python -m jobbing entry point
├── cli.py                  # Unified CLI: jobbing track|queue|pdf|scan
├── config.py               # Config loading (env, .env, paths)
├── models.py               # Domain model (dataclasses)
├── pdf.py                  # PDF generation (CV + cover letter)
├── scanner.py              # Job board bookmark parsing + fetching
└── tracker/
    ├── __init__.py         # TrackerBackend Protocol + factory
    ├── notion.py           # Notion API tracker
    └── json_file.py        # JSON file tracker (testing/fallback)
```

## Domain Model

Two aggregates:

- **Application** — Job tracking lifecycle (status, scoring, contacts, highlights)
- **CompanyData** — Document generation data (CV content, cover letter, reads/writes JSON)

Key value objects: `Contact`, `ScoringResult`, `ScoredPosting`.

See `src/jobbing/models.py` for full definitions.

## Tracker Backend

The `TrackerBackend` Protocol allows pluggable storage:

- **NotionTracker** — Primary backend. Reads/writes Notion database via API. Queue-based writes (JSON files in `notion_queue/`, processed by launchd agent).
- **JsonFileTracker** — For testing and environments without Notion access.

Factory function `get_tracker()` dispatches based on `TRACKER_BACKEND` env var.

## Skills

Skills in `.claude/skills/` provide structured prompts for each workflow phase:

| Skill | What it does |
|-------|-------------|
| `/analyze` | Fit assessment, scoring, company research |
| `/apply` | Tracker create → JSON → PDFs → ATS check |
| `/outreach` | LinkedIn contact research + messages |
| `/scan` | Manual job board scanning and scoring |
| `/track` | Status updates, research, highlights |

Skills invoke `jobbing` CLI commands and read local files (CONTEXT.md, SCORING.md, companies/).

## Scoring

Job posting scoring uses `SCORING.md` for tunable criteria. The `/analyze` and `/scan` skills apply these criteria during in-conversation evaluation. Score results are logged to `scan_results/` for review.
