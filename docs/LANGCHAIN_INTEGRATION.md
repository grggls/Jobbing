# LangChain Integration

How Jobbing uses the LangChain ecosystem: LangGraph for orchestration, LangChain for tools, and LangSmith for observability.

## LangGraph: Agent Workflow

### StateGraph

The autonomous scan workflow is a LangGraph `StateGraph` with typed state:

```python
# agent/state.py
class AgentState(TypedDict):
    bookmarks: list[str]           # Board URLs to scan
    postings: list[JobPosting]     # Discovered postings
    scored: list[ScoredPosting]    # Postings with scores
    matches: list[ScoredPosting]   # Above-threshold matches
    created_ids: list[str]         # Notion page IDs created
    context: str                   # User profile (CONTEXT.md)
    criteria: str                  # Scoring criteria text
    threshold: int                 # Score threshold
    messages: list[BaseMessage]    # LLM conversation history
```

### Graph Definition

```python
# agent/graph.py
graph = StateGraph(AgentState)

graph.add_node("scan", scan_node)
graph.add_node("score", score_node)
graph.add_node("filter", filter_node)
graph.add_node("create_entries", create_entries_node)
graph.add_node("notify", notify_node)

graph.add_edge(START, "scan")
graph.add_edge("scan", "score")
graph.add_edge("score", "filter")
graph.add_conditional_edges("filter", has_matches,
    {True: "create_entries", False: "notify"})
graph.add_edge("create_entries", "notify")
graph.add_edge("notify", END)
```

### Node Types

| Node | Type | What it does |
|------|------|-------------|
| `scan` | Python | BookmarkScanner fetches job boards, extracts postings |
| `score` | LLM | Claude evaluates each posting against profile + criteria |
| `filter` | Python | Threshold filter, logs all results to scan_results/ |
| `create_entries` | Python | NotionTracker.create() for matches (status: Researching) |
| `notify` | Python | macOS notification or stdout summary |

### Key Features Demonstrated

- **Typed state** — `TypedDict` ensures state shape is documented and type-checked
- **Conditional edges** — `has_matches` routes to create_entries or directly to notify
- **Mixed node types** — Pure Python nodes alongside LLM-calling nodes
- **Checkpointing** — Resumable runs via LangGraph's built-in checkpointer

## LangChain: Tools

Python backend functions are wrapped as LangChain tools:

```python
# agent/tools.py
from langchain_core.tools import tool

@tool
def score_posting(posting_text: str, context: str, criteria: str) -> ScoringResult:
    """Score a job posting against the user profile and criteria."""
    ...

@tool
def create_tracker_entry(name: str, position: str, url: str, score: int) -> str:
    """Create a new tracker entry in Notion with status Researching."""
    ...

@tool
def fetch_board(url: str) -> list[dict]:
    """Fetch job postings from a board URL."""
    ...
```

### LLM Provider

```python
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-5-20250929")
```

## LangSmith: Observability

### Setup

Three environment variables enable automatic tracing:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls_...
LANGCHAIN_PROJECT=jobbing
```

No code changes needed — every LangChain/LangGraph call is traced automatically.

### What LangSmith Shows

| View | What you see |
|------|-------------|
| **Trace waterfall** | Every LLM call, tool invocation, and node transition as a hierarchical timeline |
| **Prompts & responses** | Click any trace to see the full prompt sent to Claude and its response |
| **Latency breakdown** | Per-node timing (e.g., scan: 12s, score: 45s, filter: 0.1s) |
| **Token usage** | Cost per scan run, per node, per individual LLM call |
| **Error tracking** | Failed tool calls, API errors, retry attempts with full context |
| **Custom dashboards** | Charts for score distributions, scan frequency, match rates over time |

### Free Tier

- 5,000 traces/month, 14-day retention
- Two scans/day x ~50 LLM calls per scan = ~3,000 traces/month (well within limits)

### Tracing in Practice

A single scan run produces traces like:

```
jobbing_scan (run)
├── scan_node (chain)
│   ├── fetch_board: hnhiring.com (tool)
│   ├── fetch_board: climatetechlist.com (tool)
│   └── ... (parallel board fetches)
├── score_node (chain)
│   ├── score_posting: "Head of Platform, Kentik" (llm)
│   ├── score_posting: "Senior SRE, Stripe" (llm)
│   └── ... (one LLM call per posting)
├── filter_node (chain)
│   └── (threshold filter, no LLM calls)
├── create_entries_node (chain)
│   ├── notion_create: "Kentik" (tool)
│   └── ... (one per match)
└── notify_node (chain)
```

Each trace includes the full ScoringResult (score, reasoning, green/red flags, gaps, keywords) — providing complete transparency into every scoring decision.

### Alternative: Langfuse

Langfuse (MIT license, 19K GitHub stars) is a self-hosted open-source alternative with a LangGraph graph view. Could swap in later if LangSmith limits become an issue.
