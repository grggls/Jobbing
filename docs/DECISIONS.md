# Architecture Decision Records

## ADR-001: LangGraph for Agent Orchestration

**Status:** Accepted

**Context:** The autonomous scan workflow requires multi-step orchestration: scan boards, score postings with an LLM, filter results, create tracker entries, and notify. Options considered: plain Python functions, Celery task chains, custom state machine, LangGraph.

**Decision:** Use LangGraph `StateGraph` with typed state.

**Rationale:**
- Built-in state management with TypedDict
- Conditional edges for branching (e.g., filter threshold)
- Checkpointing for resumable runs
- Native LangSmith tracing integration
- Demonstrates LangChain ecosystem mastery (portfolio goal)

**Consequences:** Adds `langgraph` dependency. Graph definition is more declarative than imperative, which is a style trade-off.

---

## ADR-002: Keep Notion as Primary Tracker

**Status:** Accepted

**Context:** Evaluated GitHub Projects, plain JSON, and custom webapp alternatives. Already have 49 companies tracked in Notion with rich page bodies (research, outreach, interview notes).

**Decision:** Keep Notion, add JsonFileTracker for testing.

**Rationale:**
- Existing data and workflow already in Notion
- Rich text body (markdown, databases, relations) valuable for interview prep
- Notion API sufficient for programmatic CRUD
- JSON fallback demonstrates the Protocol pattern without requiring Notion access

**Consequences:** Requires Notion API key. Not fully portable, but the TrackerBackend Protocol makes adding new backends straightforward.

---

## ADR-003: APScheduler over launchd

**Status:** Accepted

**Context:** Previous system used macOS launchd plist for scheduling — hardcoded Python path, macOS-only, brittle.

**Decision:** Use APScheduler with cron triggers.

**Rationale:**
- Cross-platform (Linux, macOS, Windows)
- Pythonic API, runs in-process
- Cron + interval triggers cover both scheduled scans and queue polling
- Optional persistence via SQLite for crash recovery

**Consequences:** Scheduler runs as a long-lived Python process (`jobbing serve`). Needs process management (systemd, launchd, Docker) for production reliability.

---

## ADR-004: Scoring Transparency and Tunability

**Status:** Accepted

**Context:** Initial scoring was too aggressive — Claude scored 30-35 on roles that were actually good fits because it penalized implied seniority mismatch (e.g., "Senior DevOps Engineer" titles for roles with leadership scope).

**Decision:** Implement full scoring transparency with editable criteria.

**Rationale:**
- `scoring_criteria.md` is human-editable and version-tracked
- Every scoring decision preserved in `scan_results/` with full reasoning
- `ScoringResult` dataclass captures criteria_version, model, timestamp
- CLI provides `--review` (see filtered-out postings) and `--rescore` (re-evaluate with new criteria)
- Default threshold 60 (not 70) to avoid over-filtering

**Consequences:** More disk usage for scan logs. Adds complexity to the CLI. Worth it for trust and control.

---

## ADR-005: Autonomous Mode = Discovery Only

**Status:** Accepted

**Context:** Should the autonomous agent apply for jobs, or just find them?

**Decision:** Discovery only. The agent scans, scores, and creates "Researching" entries. It never applies.

**Rationale:**
- Applying requires human judgment (CV tailoring, cover letter tone, timing)
- Mistakes in automated applications are hard to reverse
- The value is in reducing the search funnel, not automating the application
- Interactive Skills handle the apply workflow with human-in-the-loop

**Consequences:** The user must review and act on discovered roles manually (via `/apply` Skill).

---

## ADR-006: src Layout Package Structure

**Status:** Accepted

**Context:** Python packages can use flat layout (`jobbing/`) or src layout (`src/jobbing/`).

**Decision:** Use src layout.

**Rationale:**
- Prevents accidental imports from the working directory
- Standard for modern Python packaging
- `pip install -e .` works correctly with src layout
- Consistent with professional Python projects

**Consequences:** Slightly deeper directory nesting. Minor inconvenience outweighed by correctness.

---

## ADR-007: TrackerBackend as Protocol (not ABC)

**Status:** Accepted

**Context:** Need a pluggable interface for tracker backends. Options: ABC, Protocol, duck typing.

**Decision:** Use `typing.Protocol` with `@runtime_checkable`.

**Rationale:**
- Structural subtyping — implementations don't need to inherit
- Runtime checking available via `isinstance()` if needed
- More Pythonic than ABC for this use case
- Demonstrates modern Python typing patterns

**Consequences:** Slightly less discoverable than ABC (no `raise NotImplementedError` on missing methods at class definition time). Trade-off is acceptable.

---

## ADR-008: ChatAnthropic as LLM Provider

**Status:** Deferred (requires separate Anthropic API key, not included in Max subscription)

**Context:** LangChain supports multiple LLM providers. Originally planned to use Claude Max plan with API access, but discovered Max subscription is separate from the API console.

**Decision:** Defer to Phase 5 (stretch goal). Use Claude Code skills for interactive workflows first.

**Rationale:**
- Max subscription does not include API access — separate billing on console.anthropic.com
- Interactive Claude Code sessions handle the primary workflow well
- LangGraph agent layer adds value mainly for unattended scanning
- Skills-first approach delivers immediate value without API costs

**Consequences:** Agent layer deferred. When API key is available, `ChatAnthropic` from `langchain-anthropic` is the planned provider.

---

## ADR-009: Claude Code Skills as Primary Workflow Interface

**Status:** Accepted

**Context:** The workflow has distinct phases (analyze, apply, outreach, track) that benefit from structured prompts. Options: free-form prompts with CLAUDE.md instructions, CLI-only workflow, Claude Code project skills.

**Decision:** Create project-level Claude Code skills in `.claude/skills/` for each workflow phase.

**Rationale:**
- Skills are discoverable as slash commands in Claude Code sessions
- Each skill encodes domain-specific instructions, reducing prompt engineering per session
- Skills reference shared context files (WORKFLOW.md, CONTEXT.md) without duplicating content
- Works in both Claude Code CLI and Cowork environments
- Skills + CLI provide two complementary interfaces: conversational and programmatic

**Consequences:** Skills are Claude Code-specific. Users of other AI coding tools would rely on CLAUDE.md and WORKFLOW.md directly. Skills need updating when workflow changes.
