# Jobbing v2: LangChain Portfolio Showcase

## Context

**Goal:** Transform the working Jobbing system into a GitHub portfolio piece demonstrating LangChain ecosystem mastery, targeting a Platform Engineering role at LangChain. NOT open-source — a personal portfolio project that shows deep, practical LangGraph/LangChain/LangSmith usage while remaining a working daily-driver job search tool.

**Current state works** — procedural scripts handle Notion tracking and PDF generation. But the code is architecturally weak (856 lines procedural, 3x duplicated property-building, `sys.exit(1)` from HTTP layer, macOS-only scheduling, no tests, no package structure). The refactor earns its keep by: (1) clean OO Python, (2) LangGraph for agent workflow, (3) LangSmith observability, (4) credible portfolio piece.

**What this demonstrates for the LangChain role:**

| JD Requirement | How Jobbing Shows It |
|---|---|
| "Build and Scale critical systems" | LangGraph agent pipeline ingesting from 50+ job boards |
| "Drive reliability" | LangSmith monitoring, structured error handling, retry logic |
| "SDK" | Clean Python package: `TrackerBackend` Protocol, typed models, CLI entry points |
| "Solve complex problems" | Structured output parsing, multi-step agent reasoning, human-in-the-loop |
| "Observability mastery" | LangSmith traces on every LLM call, tool invocation, and decision |
| "Operational mindset" | APScheduler daemon, queue processing, notification dispatch |

---

## Git strategy: public repo with private data

The project must be pushable to GitHub without leaking personal data. Everything personal stays local via `.gitignore`; the repo ships with examples and placeholders.

### What gets committed (public)

```
src/jobbing/          # All Python package code
.claude/skills/       # Claude Code Skills (project-level)
tests/                # Test suite
docs/                 # Architecture, decisions, design history
examples/             # Anonymized templates
  example_context.md  # Template CONTEXT.md with placeholder profile
  example_bookmarks.md # Template BOOKMARKS.md with example URLs
  example_company.json # Anonymized company JSON
pyproject.toml
README.md
WORKFLOW.md           # Workflow reference (no personal data)
.gitignore
.env.example          # Template with key names, no values
```

### What stays local only (.gitignore)

```
# Personal data
CONTEXT.md            # Real profile, career history, salary data
BOOKMARKS.md          # Real job board bookmarks
companies/            # All company-specific data, CVs, CLs, PDFs
.env                  # API keys (Notion, Anthropic, LangSmith)

# Runtime artifacts
notion_queue/
notion_queue_results/
scan_results/
*.pdf
.venv/

# Legacy (removed in Phase 6)
notion_update.py
generate_pdfs.py
notion_queue_runner.sh
```

### Placeholder directories

```
companies/.gitkeep              # Empty placeholder — real data stays local
notion_queue/.gitkeep           # Ditto
scan_results/.gitkeep           # Ditto
```

### Documentation committed to the repo

```
docs/
├── ARCHITECTURE.md             # System design, component relationships, diagrams
├── DECISIONS.md                # ADRs: why LangGraph, why Notion, why APScheduler, etc.
├── DESIGN_HISTORY.md           # Chronicle of design evolution (from procedural → OO → LangChain)
└── LANGCHAIN_INTEGRATION.md    # How LangGraph/LangSmith are used, what's demonstrated
```

This gives a GitHub visitor the full story: why it exists, how it was designed, what decisions were made, and what it demonstrates technically.

---

## Architecture

### Two execution modes, shared foundation

```
┌─────────────────────────────────┐  ┌─────────────────────────────────┐
│  INTERACTIVE MODE               │  │  AUTONOMOUS MODE                │
│  (Greg in Claude Code / Cowork) │  │  (Scheduled, unattended)        │
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

**Cowork compatibility:** Claude Code CLI auto-discovers `.claude/skills/` and makes `/analyze`, `/apply`, etc. available as slash commands. Cowork does NOT auto-discover project-level skills — they must be uploaded manually via Settings > Capabilities. The underlying workflow (running `jobbing` CLI commands, reading files, accessing Notion) works in both environments. The README will document the Cowork upload step.

### Package structure

```
jobbing/
├── pyproject.toml
├── README.md
├── WORKFLOW.md
├── .gitignore
├── .env.example
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── DESIGN_HISTORY.md
│   └── LANGCHAIN_INTEGRATION.md
│
├── examples/
│   ├── example_context.md
│   ├── example_bookmarks.md
│   └── example_company.json
│
├── src/jobbing/
│   ├── __init__.py
│   ├── cli.py                      # Unified CLI entry point
│   ├── config.py                   # Config loading (env, .env, API keys, scoring criteria)
│   ├── models.py                   # Domain model (see Domain Model section below)
│   ├── pdf.py                      # PDFGenerator (from generate_pdfs.py)
│   ├── scanner.py                  # BookmarkScanner (parse + fetch boards)
│   ├── scheduler.py                # APScheduler wrapper (replaces launchd)
│   │
│   ├── tracker/
│   │   ├── __init__.py             # TrackerBackend Protocol + factory
│   │   ├── notion.py               # NotionTracker (clean rewrite of notion_update.py)
│   │   └── json_file.py            # JsonFileTracker (for testing + fallback)
│   │
│   └── agent/                      # LangChain ecosystem layer
│       ├── __init__.py
│       ├── graph.py                # LangGraph workflow definition
│       ├── nodes.py                # Graph node functions
│       ├── state.py                # TypedDict state schema
│       └── tools.py                # LangChain @tool definitions
│
├── .claude/skills/                 # Project-level Skills (committed to repo)
│   ├── analyze.md                  # /analyze — role fit assessment
│   ├── apply.md                    # /apply — full workflow
│   ├── outreach.md                 # /outreach — LinkedIn contacts
│   ├── scan.md                     # /scan — manual board scan trigger
│   └── track.md                    # /track — tracker operations
│
├── companies/.gitkeep              # Placeholder (real data in .gitignore)
├── scan_results/.gitkeep           # Placeholder
│
└── tests/
    ├── test_models.py
    ├── test_tracker.py
    ├── test_pdf.py
    └── test_agent.py
```

### Domain model (DDD-informed)

The domain has two aggregates: **Application** (the job tracking lifecycle) and **CompanyData** (the document generation data). Interviews are modeled as a value object list within Application.

```python
# src/jobbing/models.py

class Status(str, Enum):
    RESEARCHING = "Researching"     # Agent-discovered, pending human review
    TARGETED = "Targeted"           # Human-approved, preparing materials
    APPLIED = "Applied"
    FOLLOWED_UP = "Followed-Up"
    IN_PROGRESS = "In Progress (Interviewing)"
    DONE = "Done"

@dataclass
class Contact:
    name: str
    title: str
    linkedin: str
    note: str = ""
    message: str = ""

@dataclass
class Interview:
    """A single interview/meeting in an application process."""
    date: str                           # ISO date
    interview_type: str                 # "Phone Screen", "Technical", "System Design", "Behavioral", "Panel", "Final"
    interviewers: list[str] = field(default_factory=list)    # Names/titles
    prep_notes: str = ""                # Interview prep
    questions_to_ask: list[str] = field(default_factory=list)
    outcome: str = ""                   # "Passed", "Rejected", "Pending", notes

@dataclass
class ScoringResult:
    """Full transparency into how a posting was scored."""
    score: int                          # 0-100
    reasoning: str                      # Full LLM reasoning text
    green_flags: list[str]
    red_flags: list[str]
    gaps: list[str]
    keywords_missing: list[str]
    criteria_version: str               # Which scoring criteria were used
    timestamp: str                      # When scored
    model: str                          # Which LLM model scored it

@dataclass
class Application:
    """Aggregate root: a job application being tracked."""
    name: str
    position: str = ""
    status: Status = Status.TARGETED
    start_date: date | None = None
    url: str = ""
    environment: list[str] = field(default_factory=list)
    salary: str = ""
    focus: list[str] = field(default_factory=list)
    vision: str = ""
    mission: str = ""
    conclusion: str = ""
    highlights: list[str] = field(default_factory=list)
    research: list[str] = field(default_factory=list)
    contacts: list[Contact] = field(default_factory=list)
    interviews: list[Interview] = field(default_factory=list)
    scoring: ScoringResult | None = None  # How it was scored (if agent-discovered)
    page_id: str | None = None            # Notion page ID

@dataclass
class JobPosting:
    """A discovered posting from a board scan."""
    title: str
    company: str
    url: str
    source: str           # Which bookmark/board
    raw_text: str         # Full posting text

@dataclass
class CompanyData:
    """Document generation data. Reads/writes existing JSON schema."""
    company_upper: str
    cv: CVData
    cl: CLData

    @classmethod
    def from_json_file(cls, path: str) -> CompanyData: ...
    def to_json_file(self, path: str) -> None: ...
```

**Why Interview is here but lightweight:** Notion already has a nested database for interviews per application. The Python `Interview` type captures what's useful for the agent workflow (prep, questions to ask, outcomes) without trying to replace Notion's rich UI. Interview data lives primarily in Notion; the Python model is for when the agent needs to reason about interview state (e.g., generating prep materials, tracking outcomes for pattern analysis).

**Why ScoringResult is explicit:** This is the transparency mechanism for the filter step. Every scoring decision — including rejections — is preserved with full reasoning, criteria version, and model info. Greg can review, dispute, and adjust.

### Autonomous mode: discovery only

**The agent NEVER applies for jobs.** The autonomous workflow:

1. **Scan** — fetch boards, extract postings
2. **Score** — Claude evaluates each posting against CONTEXT.md + scoring criteria
3. **Filter** — keep matches above threshold (configurable, default 60)
4. **Log everything** — ALL postings + scores + reasoning saved to `scan_results/`
5. **Create Notion entries** — matches get status "Researching"
6. **Notify** — "Found 3 matches — review in Notion"
7. **STOP** — Greg reviews, decides, and runs `/apply` manually

The `apply`, `outreach`, and `generate_docs` nodes exist in the graph but are only invoked interactively via Skills, never by the scheduler.

### Scoring transparency and tunability

This addresses the over-filtering problem directly.

**Scoring criteria file:** `scoring_criteria.md` (committed to repo, editable)

```markdown
# Scoring Criteria

## Threshold
- Minimum score for Notion entry: 60 (configurable in .env: SCORE_THRESHOLD=60)
- Scores 40-59: logged but not tracked (review in scan_results/)
- Scores 0-39: logged only

## Scoring guidelines for the LLM
- Do NOT penalize for implied seniority mismatch if the role involves:
  - Leadership responsibilities
  - Defining a new function
  - "First hire" or "founding team" language
  - Cross-functional scope
- Leveling is negotiable during interviews — score based on scope, not title
- Weight domain match (cleantech, platform, SRE) heavily
- Weight location/remote compatibility heavily
- De-weight exact years-of-experience requirements (±3 years is fine)

## Score components
- Domain fit: 0-30 points
- Technical match: 0-25 points
- Seniority/scope alignment: 0-20 points
- Location/remote compatibility: 0-15 points
- Company quality signals: 0-10 points
```

**Scan results logging:** Every scan run saves a full log to `scan_results/`:

```
scan_results/
├── 2026-02-21_0100_scan.json     # All postings + scores + reasoning
├── 2026-02-21_1300_scan.json
└── ...
```

Each file contains:
```json
{
  "timestamp": "2026-02-21T01:00:00Z",
  "criteria_version": "v1.2",
  "threshold": 60,
  "boards_scanned": 12,
  "postings_found": 47,
  "matches": [
    {
      "company": "Kentik",
      "title": "Head of Platform Engineering",
      "url": "...",
      "score": 82,
      "reasoning": "Strong domain fit: network observability maps to SRE/platform experience...",
      "green_flags": ["Remote", "Series C", "Platform leadership"],
      "red_flags": ["No salary listed"],
      "action": "created_tracker_entry"
    }
  ],
  "filtered_out": [
    {
      "company": "Startup X",
      "title": "Senior DevOps Engineer",
      "score": 55,
      "reasoning": "Good technical match but title implies IC role. However, description mentions 'defining the DevOps function' which suggests...",
      "action": "logged_only"
    }
  ]
}
```

This is fully reviewable. Greg can look at `filtered_out`, see what was rejected and why, adjust `scoring_criteria.md`, and re-run. LangSmith traces also capture every scoring LLM call with full prompt/response.

### LangGraph agent workflow

```
                    ┌──────────┐
                    │  START   │
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │   scan   │  BookmarkScanner fetches boards (Python)
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │   score  │  Claude scores each vs CONTEXT.md (LLM)
                    │          │  Uses scoring_criteria.md for guidelines
                    │          │  Returns ScoringResult per posting
                    └────┬─────┘
                         │
                    ┌────▼──────┐
                    │  filter   │  Threshold filter (Python)
                    │           │  ALL results logged to scan_results/
                    └────┬──────┘
                         │
                    ┌────▼──────────┐
                    │ create_entries │  NotionTracker.create() for matches
                    │  (Python)     │  Status: "Researching"
                    └────┬──────────┘
                         │
                    ┌────▼─────┐
                    │  notify  │  macOS notification / stdout
                    └────┬─────┘
                         │
                    ┌────▼─────┐
                    │   END    │  Agent stops. Greg reviews in Notion.
                    └──────────┘
```

**Key LangGraph features demonstrated:**
- `StateGraph` with typed state (`TypedDict`)
- Conditional edges (filter threshold branching)
- Node functions mixing pure Python and LLM calls
- Checkpointing (resumable runs)
- Full LangSmith tracing on every node transition

The `apply` and `outreach` nodes are defined in the graph code (showing the full design) but only invoked via the interactive `/apply` and `/outreach` Skills, not by the scheduler.

### LangSmith: how to see/visualize traces

**LangSmith is a web dashboard** at [smith.langchain.com](https://smith.langchain.com/).

**Free tier:** 5,000 traces/month, 14-day retention. More than sufficient for this project (two scans/day × ~50 LLM calls per scan ≈ 3,000 traces/month).

**What you see in the dashboard:**
- **Trace waterfall:** Every LLM call, tool invocation, and node transition as a hierarchical timeline
- **Full prompts and responses:** Click any trace to see exactly what Claude was asked and what it returned
- **Latency breakdown:** Per-node timing (scan: 12s, score: 45s, filter: 0.1s)
- **Token usage:** Cost per scan run, per node, per LLM call
- **Error tracking:** Failed tool calls, API errors, retry attempts
- **Custom dashboards:** Charts for score distributions, scan frequency, match rates over time

**Setup is 3 env vars:**
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_...
LANGCHAIN_PROJECT=jobbing
```

Every LangChain/LangGraph call is then automatically traced. No code changes needed beyond the env vars.

**Open-source alternative:** Langfuse (MIT, self-hosted, 19K GitHub stars) has a new LangGraph graph view. Could swap in later if LangSmith limits become an issue.

### Core Python classes

**`config.py`** — `Config` dataclass. Loads API keys (Notion, Anthropic, LangSmith) from env → `.env` → `~/.zshrc-secrets`. Paths, scan schedule, score threshold, notification method, scoring criteria path.

**`tracker/notion.py`** — `NotionTracker`. Clean rewrite of `notion_update.py`:
- ONE `_to_properties(app)` method (replaces 3 copies at lines 300-331, 386-425, 622-658)
- `_request()` raises `NotionAPIError` instead of `sys.exit(1)`
- Methods take `Application` objects, not `argparse.Namespace`
- Queue processing reads JSON → `Application` → same methods

**`tracker/json_file.py`** — `JsonFileTracker`. For tests and demonstrating the Protocol pattern.

**`pdf.py`** — `PDFGenerator` + `PDFStyles`. Font registration in `__init__()`, not at import time. Styles defined once, shared.

**`scanner.py`** — `BookmarkScanner`. Parses BOOKMARKS.md, fetches boards. Start with 10 highest-yield boards (HN, YC, ClimateTechList, Berlin Startup Jobs, Wellfound, etc.).

**`scheduler.py`** — `Scheduler` wrapping APScheduler. Cron at 1am/1pm invokes the LangGraph scan subgraph. Interval poll checks queue dir every 5s (replaces launchd).

### CLI

```
jobbing pdf <company> [--cv-only] [--cl-only]
jobbing track create|update|highlights|research|outreach ...
jobbing queue                         # Process queue files
jobbing scan [--threshold N]          # Run one scan cycle
jobbing scan --review                 # Review latest scan_results/, show filtered-out postings
jobbing serve                         # Start scheduler daemon (1am + 1pm + queue polling)
```

### Claude Code Skills (project-level, committed to repo)

Skills live in `.claude/skills/` **within the project** so they're part of the GitHub repo.

| Skill | What it does | Auto-applies? |
|-------|-------------|------|
| `/analyze` | Fit assessment, scoring, company intel | Never — Greg initiates |
| `/apply` | Tracker create → JSON → PDFs → ATS scan | Never — requires Greg's "proceed" |
| `/outreach` | LinkedIn contact research + messages | Never — Greg decides when |
| `/scan` | Manual trigger of scan cycle | Yes in autonomous mode (scan+score+filter+log+notify only) |
| `/track` | Natural-language tracker operations | Never |

---

## Dependencies

```toml
[project]
dependencies = [
    "reportlab>=4.0",
    "langchain-core>=0.3",
    "langchain-anthropic>=0.3",
    "langgraph>=0.2",
    "langsmith>=0.2",
    "apscheduler>=3.10",
]

[project.scripts]
jobbing = "jobbing.cli:main"
```

---

## Migration phases

### Phase 1: Package foundation + Models + Git structure
- Create `src/jobbing/` package structure
- Write `models.py` — Application, Contact, Interview, ScoringResult, CVData, CLData, CompanyData, Status
- Write `config.py` — consolidate API key loading, paths, scoring config
- Update `pyproject.toml` — src layout, entry points, all deps
- Create `examples/` — anonymized templates (example_context.md, example_bookmarks.md, example_company.json)
- Create `.env.example` — template with key names, no values
- Update `.gitignore` — CONTEXT.md, BOOKMARKS.md, companies/, .env, scan_results/, notion_queue/
- Create placeholder `.gitkeep` files
- Create `scoring_criteria.md` — tunable scoring guidelines
- Create `docs/` — ARCHITECTURE.md, DECISIONS.md, DESIGN_HISTORY.md
- `pip install -e .` — verify imports work
- **Files:** `src/jobbing/__init__.py`, `models.py`, `config.py`, `pyproject.toml`, `examples/`, `docs/`, `.gitignore`, `.env.example`, `scoring_criteria.md`

### Phase 2: Tracker + PDF refactor
- Write `tracker/__init__.py` — `TrackerBackend` Protocol + `get_tracker()` factory
- Write `tracker/notion.py` — `NotionTracker` (rewrite from `notion_update.py`)
- Write `tracker/json_file.py` — `JsonFileTracker`
- Write `pdf.py` — `PDFGenerator` + `PDFStyles` (rewrite from `generate_pdfs.py`)
- Write `cli.py` — `jobbing track`, `jobbing queue`, `jobbing pdf` subcommands
- **Verify:** `jobbing track create --dry-run` matches old script; `jobbing pdf dash0` produces identical PDFs
- **Files:** `tracker/`, `pdf.py`, `cli.py`

### Phase 3: Skills + Documentation ← YOU ARE HERE
- Create `.claude/skills/analyze.md` — from WORKFLOW.md Step 1 (fit assessment, scoring, company research, Experience to Highlight checkpoint)
- Create `.claude/skills/apply.md` — from Steps 2-3 (Notion entry, JSON generation, PDF generation, ATS check)
- Create `.claude/skills/outreach.md` — LinkedIn contact research and outreach message drafting
- Create `.claude/skills/track.md` — tracker operations (status updates, highlights, research)
- Update `CLAUDE.md` — reference skills, new `jobbing` CLI commands, remove old script references
- Update `WORKFLOW.md` — reference `jobbing` CLI instead of old scripts
- Finalize `docs/DECISIONS.md` with all ADRs
- **Verify:** Skills appear as slash commands in Claude Code; `/analyze` works with a real posting
- **Files:** `.claude/skills/`, `CLAUDE.md`, `WORKFLOW.md`, `docs/DECISIONS.md`

### Phase 4: /scan skill for manual bookmark scanning
- Create `.claude/skills/scan.md` — manual scan trigger for Claude-driven bookmark scanning
- Write `scanner.py` — `BookmarkScanner` (parse BOOKMARKS.md, fetch job boards)
- Implement scan results logging to `scan_results/`
- **Verify:** `/scan` in Claude Code session reads BOOKMARKS.md, fetches boards, scores postings, logs results
- **Files:** `.claude/skills/scan.md`, `scanner.py`, `scan_results/`

### Phase 5: LangGraph agent layer (stretch goal — requires Anthropic API key)
- Write `agent/state.py` — `AgentState` TypedDict
- Write `agent/tools.py` — LangChain `@tool` wrappers for tracker, PDF, scanner
- Write `agent/nodes.py` — scan, score, filter, create_entries, notify nodes
- Write `agent/graph.py` — `StateGraph` with edges, conditional routing, checkpointing
- Write `scheduler.py` — `Scheduler` (APScheduler: cron at 1am/1pm + queue polling)
- Configure LangSmith tracing (env vars)
- Add `jobbing scan` and `jobbing serve` subcommands to CLI
- Write `docs/LANGCHAIN_INTEGRATION.md` — detailed LangGraph/LangSmith documentation
- **Verify:** `jobbing scan` completes; LangSmith shows traces; `jobbing serve` fires on schedule
- **Files:** `agent/`, `scanner.py`, `scheduler.py`, updated `cli.py`, `docs/LANGCHAIN_INTEGRATION.md`

### Phase 6: Cleanup + Tests
- Write `tests/test_models.py`, `test_tracker.py`, `test_pdf.py`
- Delete `notion_update.py`, `generate_pdfs.py`, `notion_queue_runner.sh`
- Remove or update launchd plist
- Final git cleanup: verify `.gitignore` works, no personal data in staged files
- **Verify:** `git status` shows only public files; tests pass; full end-to-end works

---

## Key files

| File | Action | Source |
|------|--------|--------|
| `src/jobbing/models.py` | Create | New (Application, Contact, Interview, ScoringResult, CompanyData) |
| `src/jobbing/config.py` | Create | Extract from `notion_update.py:51-86` + new config fields |
| `src/jobbing/tracker/notion.py` | Create | Rewrite of `notion_update.py` (856→~400 lines) |
| `src/jobbing/tracker/json_file.py` | Create | New |
| `src/jobbing/pdf.py` | Create | Rewrite of `generate_pdfs.py` (381→~300 lines) |
| `src/jobbing/scanner.py` | Create | New |
| `src/jobbing/scheduler.py` | Create | New |
| `src/jobbing/cli.py` | Create | New |
| `src/jobbing/agent/*.py` | Create (5) | New (LangGraph + LangChain) |
| `.claude/skills/*.md` | Create (5) | Extract from WORKFLOW.md |
| `scoring_criteria.md` | Create | New — tunable scoring rules |
| `docs/*.md` | Create (4) | New — architecture, decisions, history, LangChain docs |
| `examples/*` | Create (3) | Anonymized templates |
| `.env.example` | Create | Template with key names |
| `pyproject.toml` | Modify | Add deps, src layout, entry points |
| `.gitignore` | Modify | Add personal data exclusions |
| `CLAUDE.md` | Modify | Reference skills, new CLI |
| `README.md` | Rewrite | Portfolio-quality project description |
| `notion_update.py` | Delete (Phase 6) | Replaced by tracker/notion.py |
| `generate_pdfs.py` | Delete (Phase 6) | Replaced by pdf.py |
| `notion_queue_runner.sh` | Delete (Phase 6) | Replaced by scheduler.py |

---

## Verification

- **Phase 1:** `pip install -e .` succeeds; `from jobbing.models import Application, Interview, ScoringResult` works; `git status` shows no personal data
- **Phase 2:** `jobbing track create --name "Test" --dry-run` matches old script; `jobbing pdf dash0` produces identical PDFs
- **Phase 3:** Skills appear as slash commands in Claude Code; `/analyze` works with a real posting
- **Phase 4:** `/scan` in Claude Code reads BOOKMARKS.md, fetches boards, scores postings, logs to `scan_results/`
- **Phase 5:** `jobbing scan` completes; LangSmith dashboard shows traces; `jobbing serve` fires on schedule
- **Phase 6:** Tests pass; `git diff --cached` shows only public files; no PDFs, no CONTEXT.md, no companies/
- **End-to-end:** `/scan` finds matches → `/analyze` assesses fit → `/apply` generates docs → `/track` updates status
