# Design History

A chronicle of how Jobbing evolved from procedural scripts to a clean Python package with Claude Code skills.

## Phase 0: Procedural Scripts (v1.0)

**What existed:**
- `notion_update.py` (856 lines) — Monolithic script handling all Notion API operations: create, update, highlights, research, outreach, queue processing
- `generate_pdfs.py` (381 lines) — PDF generation for CVs and cover letters using ReportLab
- `notion_queue_runner.sh` — Shell script for queue processing (ultimately unused — launchd plist bypassed it)
- macOS launchd plist — Scheduled queue polling with hardcoded Python path

**What worked:**
- Functional Notion tracker with 49 companies
- PDF generation producing professional documents
- Queue-based workflow for batching operations

**What didn't:**
- Property-building code duplicated 3 times (lines 300-331, 386-425, 622-658)
- `sys.exit(1)` from HTTP layer prevented error recovery
- `_process_queue_file` had `except SystemExit` workaround
- No package structure, no tests, no type hints
- Module-level font registration side effects in PDF generator
- macOS-only scheduling with brittle hardcoded paths
- No domain model — everything passed as `argparse.Namespace`

## Phase 1: Architecture Analysis

**Key insight:** The system worked but was architecturally fragile. A refactor needed to preserve the working system while introducing proper structure.

**Analysis findings:**
- Identified the 3x property-building duplication as the highest-value refactor target
- `sys.exit(1)` from HTTP layer was a design smell preventing composition
- No separation between domain logic, API calls, and CLI handling
- Font registration at import time caused unnecessary side effects

## Phase 2: Portfolio Pivot (later abandoned)

**Catalyst:** A Platform Engineering role at LangChain appeared. The refactor was initially framed as a portfolio piece demonstrating LangChain ecosystem mastery (LangGraph, LangSmith, APScheduler). That framing was later abandoned — the tool proved more valuable as a clean, focused Python package with Claude Code skills as the interaction layer, without the LangChain dependency overhead.

**Design questions resolved:**

- **Notion vs alternatives:** Keep Notion (49 companies, rich content), add JSON fallback for pattern demo
- **Autonomy boundary:** Human-in-the-loop at every decision point — the tool never applies without approval

## Phase 3: Domain-Driven Redesign (v2.0)

**Key decisions:**

1. **Domain model** — Dataclasses replace implicit argparse Namespace. Two aggregates: Application (tracking lifecycle) and CompanyData (document generation). Value objects: Contact, Interview, ScoringResult.

2. **TrackerBackend Protocol** — Pluggable storage via structural subtyping. NotionTracker rewrites the 856-line monolith into ~400 lines with one `_to_properties()` method. JsonFileTracker for testing.

3. **Scoring transparency** — After discovering that Claude scored 30-35 on actually-good roles due to seniority title mismatch, we designed a full feedback loop: editable `SCORING.md`, score component weights, and criteria version tracking in every ScoringResult.

4. **Claude Code Skills** — Five project-level skills (`/analyze`, `/apply`, `/outreach`, `/scan`, `/track`) encode the workflow as structured prompts. Skills invoke the `jobbing` CLI and read local context files, providing a conversational interface over the Python package.

5. **Git safety** — Personal data (CONTEXT.md, BOOKMARKS.md, companies/, .env) gitignored. Repo ships with anonymized examples and placeholder directories.

## Design Principles

- **Working system first:** Every refactor step must preserve the ability to track jobs and generate documents
- **Transparency over automation:** The agent's scoring decisions are always reviewable and adjustable
- **Human-in-the-loop:** Autonomous mode discovers; humans decide and act
- **Clean boundaries:** Domain model, tracker backend, PDF generation, and agent orchestration are independent modules
- **Professional Python:** Type hints, dataclasses, Protocol pattern, proper packaging
