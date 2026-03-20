---
name: scan
description: Scan bookmarked job boards for relevant postings. Python fetches the pages, Claude extracts and scores postings in-conversation. No API key needed.
---

# /scan — Job Board Scanner

Scan bookmarked job boards for relevant postings. Python handles HTTP fetching, you handle extraction and scoring.

## Instructions

### Step 1: Load context

Read these if not already loaded this session:
- `CONTEXT.md` — Greg's profile (scoring reference)
- `.claude/skills/scoring/SKILL.md` — scoring rubric (the `/scoring` skill)

### Step 2: Get existing applications

Run this first to know what's already being tracked:

```bash
jobbing scan existing
```

Keep this list in mind — **do not present postings for companies already in the tracker**.

### Step 3: Fetch boards

Ask Greg which categories to scan, or scan all. Use the CLI to fetch:

```bash
# List available categories
jobbing scan bookmarks

# Fetch specific categories
jobbing scan fetch --categories "Climate / Impact" "Startup / Tech"

# Fetch all boards (93 bookmarks — takes ~30s)
jobbing scan fetch

# Fetch a subset for quick check
jobbing scan fetch --categories "Climate / Impact" --limit 5
```

The fetch saves results to `scan_results/YYYYMMDD_HHMMSS_fetch.json`.

### Step 4: Extract and score

Read the fetch results file. For each board with content:

1. **Extract** — Scan the page content for individual job postings. Look for:
   - Job titles containing: devops, platform, SRE, infrastructure, cloud, engineering manager, head of engineering, VP engineering, director engineering
   - Seniority signals: senior, lead, staff, principal, head, director, VP

2. **Filter out**:
   - Companies already in the tracker (from Step 2)
   - Pure frontend/mobile/data science roles with no infrastructure component
   - Entry-level or junior roles
   - Defense contractors, military tech, weapons companies

3. **Do NOT filter out based on title alone.** Per the `/scoring` skill:
   - A "Senior DevOps Engineer" that involves defining a function and hiring a team should score like a "Head of DevOps"
   - Roles described as "first hire", "founding team", or "building from scratch" are leadership-track regardless of title
   - Score based on **scope**, not **title** — leveling is negotiable

4. **Score** — For each relevant posting, score 0-100 using the `/scoring` skill:
   - Domain fit (0-30)
   - Technical match (0-25)
   - Seniority/scope (0-20)
   - Location/remote (0-15)
   - Company signals (0-10)

5. **Present results** — Show Greg a summary:
   - Total boards scanned, postings found
   - Matches (>= 60): title, company, score, reasoning, URL
   - Near-misses (40-59): title, company, score, one-line reason
   - Skip count (< 40)

### Step 5: Act on matches

For any posting Greg wants to pursue:
- Run `/analyze` with the posting URL or text
- The normal workflow takes over from there

## Key behaviors

- **Filter existing.** Always run `jobbing scan existing` first. Never present a role that's already tracked.
- **Be selective.** Most boards will have 0-2 relevant postings. That's normal. Don't pad results.
- **Be scope-aware.** A "Senior DevOps Engineer" at a 20-person startup building from scratch is a different role than a "Senior DevOps Engineer" on a 50-person infra team. Read the posting text, not just the title.
- **Be fast.** Skim page content for relevant titles first, only score those that look plausible.
- **Be honest.** A board full of junior roles or frontend jobs is a "no matches" — say so.
- **Skip JS-rendered boards.** If page content is mostly boilerplate with no job listings, note it and move on.
- **Check for duplicates.** Same company+role across multiple boards = one result.
- **Use Chrome MCP.** Use my browser when you run into robots.txt that prevents your scraping.

## Do Not

- Call the Anthropic API directly — you ARE the LLM, just read the content and score it
- Present roles for companies already in the tracker
- Filter out roles solely because the title says "Senior" — read the scope first
- Create Notion entries automatically — matches go through `/analyze` first
