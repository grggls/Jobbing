# Architecture

## Overview

Jobbing is a Python package that orchestrates an AI-assisted job application workflow using LangGraph for agent orchestration, LangSmith for observability, and Notion for tracking.

## System Diagram

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│  INTERACTIVE MODE               │  │  AUTONOMOUS MODE                │
│  (Claude Code / Cowork session) │  │  (Scheduled, unattended)        │
│                                 │  │                                 │
│  /analyze  /apply  /outreach    │  │  jobbing serve                  │
│  Claude Code Skills             │  │  APScheduler → LangGraph agent  │
│  (prompts with judgment logic)  │  │  (discovery only — never applies│
│                                 │  │   without human approval)       │
└────────────┬────────────────────┘  └────────────┬────────────────────┘
             │                                    │
             └──────────────┬─────────────────────┘
                            │ both use
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│  PYTHON PACKAGE: src/jobbing/                                       │
│                                                                     │
│  models.py    config.py    pdf.py    scanner.py    scheduler.py     │
│  tracker/notion.py    tracker/json_file.py                          │
│  agent/graph.py    agent/nodes.py    agent/state.py    agent/tools.py│
│                                                                     │
│  ALL calls traced via LangSmith                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Two Execution Modes

### Interactive Mode

The user works in a Claude Code (or Cowork) session. Skills (`.claude/skills/`) provide structured prompts for:

- `/analyze` — Role fit assessment and company intelligence
- `/apply` — Full application workflow (tracker create → JSON → PDFs → ATS scan)
- `/outreach` — LinkedIn contact research and message generation
- `/scan` — Manual trigger of a board scan cycle
- `/track` — Natural-language tracker operations

Skills invoke `jobbing` CLI commands and read local files (CONTEXT.md, companies/, etc.).

### Autonomous Mode

`jobbing serve` starts an APScheduler daemon that runs the LangGraph scan subgraph at 1am and 1pm daily. The autonomous workflow:

1. **Scan** — BookmarkScanner fetches configured job boards
2. **Score** — Claude evaluates each posting against CONTEXT.md + scoring_criteria.md
3. **Filter** — Keep matches above threshold (default: 60)
4. **Log** — ALL postings + scores + reasoning saved to `scan_results/`
5. **Create entries** — Matches get Notion entries with status "Researching"
6. **Notify** — macOS notification or stdout summary
7. **Stop** — The agent never applies. The user reviews and decides.

## Package Structure

```
src/jobbing/
├── __init__.py
├── cli.py                  # Unified CLI entry point
├── config.py               # Config loading (env, .env, secrets)
├── models.py               # Domain model (dataclasses)
├── pdf.py                  # PDF generation (CV + cover letter)
├── scanner.py              # Job board scanning
├── scheduler.py            # APScheduler wrapper
├── tracker/
│   ├── __init__.py         # TrackerBackend Protocol + factory
│   ├── notion.py           # Notion API tracker
│   └── json_file.py        # JSON file tracker (testing/fallback)
└── agent/
    ├── __init__.py
    ├── graph.py            # LangGraph StateGraph definition
    ├── nodes.py            # Graph node functions
    ├── state.py            # TypedDict state schema
    └── tools.py            # LangChain @tool definitions
```

## Domain Model

Two aggregates:

- **Application** — Job tracking lifecycle (status, scoring, interviews, contacts)
- **CompanyData** — Document generation data (CV content, cover letter, reads/writes existing JSON schema)

Key value objects: `Contact`, `Interview`, `ScoringResult`, `ScoredPosting`.

See `src/jobbing/models.py` for full definitions.

## Tracker Backend

The `TrackerBackend` Protocol allows pluggable storage:

- **NotionTracker** — Primary backend. Reads/writes Notion database via API.
- **JsonFileTracker** — For testing and environments without Notion access.

Factory function `get_tracker()` dispatches based on `TRACKER_BACKEND` env var.

## LangGraph Agent Workflow

```
START → scan → score → filter → create_entries → notify → END
```

- `scan`: Pure Python. BookmarkScanner fetches boards.
- `score`: LLM node. Claude scores each posting against CONTEXT.md.
- `filter`: Pure Python. Threshold filter, logs all results.
- `create_entries`: Pure Python. NotionTracker.create() for matches.
- `notify`: Pure Python. macOS notification or stdout.

Additional nodes (`apply`, `outreach`, `generate_docs`) exist in the graph definition but are only invoked via interactive Skills, not by the scheduler.

## Observability

Every LangChain/LangGraph call is automatically traced to LangSmith via three env vars:

```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_...
LANGCHAIN_PROJECT=jobbing
```

The LangSmith dashboard shows trace waterfalls, full prompts/responses, latency breakdown, token usage, and error tracking.
