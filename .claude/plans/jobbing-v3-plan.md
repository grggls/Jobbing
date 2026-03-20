# Migration Plan: Notion → Obsidian Kanban (Rich Interface)

## Context

The Notion kanban has been migrated to `~/Documents/Jobbing/kanban/` using the Obsidian kanban plugin. ~250 company hub files already exist. Obsidian is now the source of truth. The goal is:

1. Make the kanban board + company hub files a rich, navigable interface
2. Link CVs, cover letters, interviews, and research into company hub files
3. Update all skills, CLI, config, and documentation to write markdown directly — no queue, no Notion API, no launchd
4. Provide a clean install script so the full environment can be reproduced

**Vault root:** `~/Documents/Jobbing/` (entire project directory)
**Primary navigation:** Kanban board → click card → company hub file → links to everything

**Current architecture:**
- Writes: queue JSON → `notion_queue/` → launchd → Notion API
- Reads: `notion-fetch` / `notion-search` MCP tools

**Target architecture:**
- Writes: Read/Edit/Write tools directly on markdown files
- Reads: Read tool on `kanban/companies/{Company}.md` and interview files
- CLI: `track` kept as thin wrapper via ObsidianTracker; `queue` removed; `pdf` and `scan` unchanged

---

## File Structure (target)

```
~/Documents/Jobbing/                    ← Obsidian vault root
  .obsidian/                            ← Obsidian config (committed to repo)
    app.json                            ← appearance: Things theme, font settings
    community-plugins.json              ← enabled plugin list
    plugins/
      obsidian-kanban/                  ← Kanban plugin
      obsidian-style-settings/          ← Style Settings plugin
    themes/
      Things/
        theme.css                       ← Things theme CSS
        manifest.json
  kanban/
    Job Tracker.md                      ← kanban board (primary nav)
    companies/                          ← company hub files (one per application)
      Bandcamp (Songtradr).md
      Kevala.md
    interviews/                         ← NEW: one folder per company
      Bandcamp (Songtradr)/
        2026-02-26-Richard-Frost.md
        2026-03-15-Thomas-Roton.md
      Kevala/
        2026-03-10-Jane-Smith.md
  companies/                            ← CV/CL JSON data + generated PDFs (unchanged)
    bandcamp (songtradr)/
      bandcamp (songtradr).json
      BANDCAMP-SONGTRADR-CV.pdf
      BANDCAMP-SONGTRADR-CL.pdf
  src/jobbing/                          ← Python package
  scripts/
    install.sh                          ← NEW: full environment setup script
  tests/
    test_obsidian_tracker.py            ← NEW: ObsidianTracker unit tests
    test_sync_interviews.py             ← NEW: interview migration unit tests
```

---

## File Formats (canonical)

### Company hub: `kanban/companies/{Company}.md`

```markdown
---
company: "Bandcamp (Songtradr)"
position: "Lead Systems Engineer"
status: "In Progress (Interviewing)"
date: 2026-02-26
url: "https://songtradr.bamboohr.com/careers/150"
environment: [Remote, London]
salary: "€120K negotiating"
focus: [Music Tech, e-commerce, Creator Platform]
score: 88
conclusion: ""
notion_id: "3135de3c-..."   # legacy reference
---

# Bandcamp (Songtradr)
**Position:** Lead Systems Engineer · **Status:** In Progress (Interviewing) · **Score:** 88/100

[Job Posting](https://songtradr.bamboohr.com/careers/150)

## Documents
- [[BANDCAMP-SONGTRADR-CV|CV]] · [[BANDCAMP-SONGTRADR-CL|Cover Letter]]

## Interviews
- [[2026-02-26-Richard-Frost|Richard Frost — Phone Screen · Passed · Vibe 4/5]]
- [[2026-03-15-Thomas-Roton|Thomas Roton + Sami — Technical · Pending]]

## Fit Assessment

## Company Research

## Experience to Highlight

## Job Description

## Outreach Contacts

## Questions I Might Get Asked

## Questions to Ask

## Conclusion
```

Notes:
- Obsidian resolves wikilinks by shortest unique filename — `[[BANDCAMP-SONGTRADR-CV]]` resolves to the PDF in `companies/bandcamp (songtradr)/`
- Documents section only present after `/apply` runs (PDF files exist)
- Interviews section grows as prep and debrief files are created
- Section order matches application chronology

### Interview file: `kanban/interviews/{Company}/{date}-{slug}.md`

```markdown
---
company: "Bandcamp (Songtradr)"
interviewer: "Richard Frost"
role: "Director, Talent & Development"
type: "Phone Screen"
date: 2026-02-26
vibe: 4
outcome: "Passed"
---

# Richard Frost — Phone Screen · 2026-02-26
**Company:** [[Bandcamp (Songtradr)]] · **Outcome:** Passed · **Vibe:** 4/5

## Prep Notes

## Debrief

## Transcript / Raw Notes
```

Notes:
- `[[Bandcamp (Songtradr)]]` links back to the company hub — Obsidian backlinks panel shows all interviews for a company
- Prep Notes written by `/prep`, Debrief written by `/debrief`, Transcript can be pasted freely
- One file per interviewer (or per panel block); created by `/prep` if scheduled, or `/debrief` if unscheduled

### Board card format: `kanban/Job Tracker.md`

```
- [ ] [[companies/Bandcamp (Songtradr)|Bandcamp (Songtradr)]] — Lead Systems Engineer · Score: 88 · 2026-02-26
```

Card format: `- [ ] [[companies/{Company}|{Company}]] — {Position} · Score: {score} · {date}`
Score omitted if not set. Card updated whenever status changes.

---

## Work Breakdown

### Phase 0: Obsidian setup — install script + theme

**New file: `scripts/install.sh`**

A single idempotent shell script that sets up the full environment from scratch:

```bash
#!/usr/bin/env bash
# Usage: bash scripts/install.sh
# Idempotent — safe to re-run
```

Steps the script performs:

1. **Homebrew check** — warn if not installed, don't auto-install (too opinionated)
2. **Obsidian** — `brew install --cask obsidian` (skip if already installed)
3. **Python venv** — create `.venv/` if missing, install `pip install -e ".[dev]"`
4. **Things theme** — download `theme.css` + `manifest.json` from the obsidian-things GitHub release into `.obsidian/themes/Things/`
5. **Kanban plugin** — download `main.js` + `manifest.json` + `styles.css` from obsidian-kanban GitHub release into `.obsidian/plugins/obsidian-kanban/`
6. **Style Settings plugin** — download from obsidian-style-settings GitHub release into `.obsidian/plugins/obsidian-style-settings/`
7. **`.obsidian/app.json`** — write appearance config: theme = Things, font = Inter (or system sans-serif), readable line length = true, sensible content max width
8. **`.obsidian/community-plugins.json`** — write `["obsidian-kanban", "obsidian-style-settings"]` to enable plugins without needing the Obsidian UI
9. **`.env` check** — warn if `NOTION_API_KEY` is missing (needed only for the one-time migration step)
10. **Print next steps** — clear instructions for what to do after the script completes

**Commit `.obsidian/` config** (minus `workspace.json` which is machine-specific) so the vault is pre-configured for anyone who clones the repo.

**`.gitignore` additions:**

```
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache
```

---

### Phase 1: Interview data migration from Notion

⚠️ **Checkpoint before starting:** run `python kanban/sync_notion_to_obsidian.py --dry-run` to confirm existing company files are intact.

The existing `kanban/sync_notion_to_obsidian.py` fetches company pages but not the inline Interviews DB (child databases). The `NotionTracker.get_interviews()` method in `src/jobbing/tracker/notion.py` already knows how to fetch them (calls `_find_interviews_db()` + queries all rows + fetches each row's child page blocks).

**Extend `sync_notion_to_obsidian.py`:**

- Add `--include-interviews` flag (default off to not break existing runs)
- For each company with a Notion Interviews DB, fetch all interview rows + child content (Prep Notes toggle, Debrief toggle) via existing API logic
- Write each interview row → `kanban/interviews/{Company}/{date}-{slug}.md` with YAML frontmatter + sections
- Update the company hub file to add/populate the `## Interviews` section with wikilinks to each created file
- Handle edge cases: missing date → `unknown-date` slug; missing interviewer → `unknown-interviewer`; duplicate interviewers on same date → append `-2`
- Add `--include-interviews --dry-run` support: print what would be written without writing

**New tests: `tests/test_sync_interviews.py`**

- `test_interview_filename_slug` — "Richard Frost" → `2026-02-26-Richard-Frost.md`; special chars handled
- `test_interview_filename_duplicate` — same company + date + name → appends `-2`
- `test_generate_interview_file` — correct YAML frontmatter, correct section headings
- `test_hub_interviews_section_updated` — wikilink appended correctly to company file
- `test_missing_date_fallback` — interview with no date uses `unknown-date` slug
- `test_missing_interviewer_fallback` — no name uses `unknown-interviewer` slug

**✅ Checkpoint:** Run migration with `--dry-run`, review output for 5 representative companies. Then run for real. Open Obsidian. Manually click through 3 company hub files; verify interview links resolve and interview files look correct.

This is a one-time migration run. After it completes, Notion is no longer consulted.

---

### Phase 2: Python — New ObsidianTracker backend

**New file: `src/jobbing/tracker/obsidian.py`**

`ObsidianTracker` implementing `TrackerBackend` protocol:

- `create(app)` — Create `kanban/companies/{Company}.md` with YAML frontmatter + scaffolded sections. Add card to correct lane in `kanban/Job Tracker.md`. Idempotent: if file exists, update frontmatter and preserve existing section content.
- `update(app)` — Update YAML frontmatter in company file; move board card if status changed.
- `find_by_name(name)` — Read and parse company file; return `Application` or `None`.
- `set_highlights(app_id, highlights)` — Replace `## Experience to Highlight` section.
- `set_research(app_id, research)` — Replace `## Company Research` section.
- `set_contacts(app_id, contacts)` — Replace `## Outreach Contacts` section.
- `list_all()` — Glob `kanban/companies/*.md`, parse all, return `list[Application]`.
- `add_documents_section(company_name, cv_path, cl_path)` — Write or update `## Documents` section with CV/CL wikilinks.
- `add_interview_link(company_name, filename, display_text)` — Append wikilink to `## Interviews` section.

Helper utilities:

- `_parse_frontmatter(text) → dict` — parse YAML block (stdlib only, no PyYAML needed for this subset)
- `_write_frontmatter(path, updates)` — replace YAML block in-place, preserve unmodified fields
- `_replace_section(path, heading, content)` — idempotent section upsert: remove existing heading+content block, insert new one
- `_company_file(name) → Path` — `kanban/companies/{name}.md`
- `_board_add_or_move_card(app)` — scan all board lanes for existing card, remove from old lane, insert in correct lane
- `_card_line(app) → str` — format board card string

**New tests: `tests/test_obsidian_tracker.py`**

Uses `tmp_path` fixture to create a scratch kanban directory — no real files touched.

- `test_create_writes_frontmatter` — correct YAML fields in new file
- `test_create_scaffolds_sections` — all 9 section headings present
- `test_create_adds_board_card` — card appears in correct lane in board file
- `test_create_idempotent` — running twice doesn't duplicate card or wipe sections
- `test_update_frontmatter_fields` — status, score, salary update correctly
- `test_update_status_moves_board_card` — card moves from Targeted → Applied lane
- `test_find_by_name_returns_application` — parses frontmatter into Application correctly
- `test_find_by_name_missing` — returns None if file doesn't exist
- `test_list_all_counts` — correct number of Application objects returned
- `test_set_highlights_replaces_section` — old content gone, new bullets present
- `test_set_research_replaces_section`
- `test_set_contacts_replaces_section`
- `test_add_interview_link_appends` — link added to Interviews section
- `test_add_interview_link_no_duplicate` — same link not added twice
- `test_add_documents_section_writes_links` — CV and CL wikilinks present
- `test_parse_frontmatter_handles_lists` — `environment: [Remote, Berlin]` parses correctly
- `test_replace_section_idempotent` — calling twice with same content produces same result
- `test_board_card_format_with_score` — correct card string with score
- `test_board_card_format_without_score` — score omitted when None

**✅ Checkpoint:** `pytest tests/test_obsidian_tracker.py -v` — all pass. Then manually run `jobbing scan existing` to confirm it reads from the new backend.

**Update `src/jobbing/tracker/__init__.py`:**

- Add `"obsidian"` branch in `get_tracker()`
- Default backend: `"obsidian"`

**Update `src/jobbing/config.py`:**

- Add `kanban_dir` → `project_dir / "kanban"`
- Add `kanban_companies_dir` → `kanban_dir / "companies"`
- Add `kanban_interviews_dir` → `kanban_dir / "interviews"`
- Add `kanban_board_path` → `kanban_dir / "Job Tracker.md"`
- Change `TRACKER_BACKEND` default to `"obsidian"`
- Keep legacy `queue_dir` / `queue_results_dir` (don't break historical result files)

---

### Phase 3: CLI update

**Update `src/jobbing/cli.py`:**

- **Remove** `queue` subcommand entirely (Notion-specific, gone)
- **Keep** `track` subcommand — it already routes through `TrackerBackend`. Switching the default backend to `"obsidian"` means `jobbing track create`, `update`, `highlights`, `research`, `outreach`, and `followup` all automatically route to `ObsidianTracker`. No individual command rewrites needed — the protocol handles it.
- **Remove** `--page-id` / `page_id` arguments from track subcommands — replaced by `--name` (company name = identifier in Obsidian)
- **Keep** `pdf` subcommand — after generating PDFs, call `obsidian_tracker.add_documents_section(company_name)` to update the hub's `## Documents` section
- **Keep** `scan` subcommand — unchanged

**✅ Checkpoint:** `jobbing pdf {some-existing-company}` runs without error and `## Documents` section appears in the company hub file with working wikilinks. `jobbing track followup` reads from kanban files correctly.

---

### Phase 4: CLAUDE.md

Replace Notion-centric sections with Obsidian-centric equivalents:

**"Commands" section** — remove entirely, replace with:

- **Obsidian writes** — direct file edits to `kanban/companies/{Company}.md` and `kanban/interviews/` using Read/Edit/Write tools. No queue, no CLI needed.
- **PDF generation** — `jobbing pdf {company}` (unchanged); automatically updates `## Documents` section
- **Scan** — `jobbing scan` commands (unchanged)
- Document company hub format (all frontmatter fields + section structure)
- Document interview file format (frontmatter fields + sections)
- Document board card format and lane progression

**"Notion Integration Notes"** → **"Obsidian Integration Notes"**

- Source of truth: `kanban/companies/{Company}.md` (company hub) + `kanban/interviews/{Company}/` (interview files)
- Board: `kanban/Job Tracker.md` — updated when status changes
- Reads: use Read tool on markdown files directly
- Writes: use Edit/Write tools on markdown files directly
- No queue, no launchd, no Notion API, no MCP write tools
- Status values unchanged (same 5, same progression rules)
- Company identifier = company name = filename (no page_id concept)

Remove: Database ID, Data Source ID, template page IDs, queue file naming, launchd plist references.

---

### Phase 5: WORKFLOW.md

Rewrite all Notion/queue references:

| Old | New |
|-----|-----|
| "Write create JSON to `notion_queue/`" | "Create `kanban/companies/{Company}.md` with frontmatter + sections" |
| "launchd agent processes it" | (removed) |
| "save the page_id from queue results" | "company name is the identifier" |
| "use notion-fetch/notion-search" | "Read `kanban/companies/{Company}.md`" |
| Queue JSON `{"command": "..."}` examples | Markdown file edit descriptions |
| "Queue for all Notion writes" rule | "Edit markdown files directly" |
| All page_id references | Company name / filename |

Update Step 2 (Tracker Entry) and all subsequent steps that touch Notion.

---

### Phase 6: Skills — 12 SKILL.md files

**No changes needed:**
- `/scoring` — reference skill, no tracker interaction
- `/disaggregate` — aggregator parser, no tracker interaction

**Minor updates:**
- `/analyze` — remove mention of "pass scoring data to Notion create queue"
- `/scan` — `jobbing scan existing` works unchanged; remove any queue refs

**Significant rewrites:**

#### `/apply`
- Step 1: Create `kanban/companies/{Company}.md` with frontmatter + scaffolded sections
- Step 1: Add card to `kanban/Job Tracker.md` in Targeted lane
- Step 1: Write Fit Assessment section + update `score:` in frontmatter
- Step 1: Write Job Description section
- After PDF generation: `## Documents` section updated automatically by `jobbing pdf`
- Remove all queue JSON; replace with hub file template

#### `/track`
- Replace queue commands → direct frontmatter/section edits
- Replace notion-search → "file is at `kanban/companies/{Company}.md`"
- Remove page_id concept throughout

#### `/outreach`
- Replace queue `outreach` JSON → edit `## Outreach Contacts` section directly

#### `/debrief`
- Step 1: Read `kanban/companies/{Company}.md` for context
- Step 5: Create or update `kanban/interviews/{Company}/{date}-{slug}.md`
- Step 5: If new, append wikilink to `## Interviews` in hub
- Remove queue `debrief` block

#### `/prep`
- Step 1: Read `kanban/companies/{Company}.md` for context
- Step 6: Create `kanban/interviews/{Company}/{date}-{slug}.md` with prep notes
- Step 6: Append wikilink to `## Interviews` in hub
- Remove notion-search/notion-fetch; remove queue block

#### `/followup`
- Step 2: Read `kanban/Job Tracker.md` → find In Progress cards
- Step 3: For each, read company hub + list interview files to find last contact date
- Remove notion-search/notion-fetch

#### `/reassess`
- Step 2: Read company hub → parse Fit Assessment + Interviews links → read each interview file
- Step 7: Update `## Fit Assessment` + `score:` in frontmatter
- Remove notion-fetch/notion-search; remove queue block

#### `/compare`
- Step 3: Read company hub + interview files for each company being compared
- Remove notion-fetch/notion-search

**✅ Checkpoint:** Grep for stragglers:

```bash
grep -r "notion_queue\|notion-fetch\|notion-search\|launchd\|page_id\|queue" \
  .claude/skills/ CLAUDE.md WORKFLOW.md
```

Zero hits expected (except `notion_id` in frontmatter docs, which is intentional legacy).

---

### Phase 7: Cleanup

- `kanban/sync_notion_to_obsidian.py` — move to `docs/archive/sync_notion_to_obsidian.py` after migration
- `notion_queue/` and `notion_queue_results/` — retain on disk as historical archive, remove from all active docs
- launchd plist — no filesystem changes needed; remove all doc references

---

## Files Modified

| File | Change |
|------|--------|
| `scripts/install.sh` | **NEW** — full environment setup |
| `.obsidian/app.json` | **NEW** — Things theme + appearance config |
| `.obsidian/community-plugins.json` | **NEW** — enable kanban + style settings |
| `.obsidian/plugins/obsidian-kanban/` | **NEW** — downloaded by install script |
| `.obsidian/plugins/obsidian-style-settings/` | **NEW** — downloaded by install script |
| `.obsidian/themes/Things/` | **NEW** — downloaded by install script |
| `.gitignore` | Add `.obsidian/workspace*.json`, `.obsidian/cache` |
| `kanban/sync_notion_to_obsidian.py` | Extend with `--include-interviews` |
| `tests/test_sync_interviews.py` | **NEW** — interview migration tests |
| `src/jobbing/tracker/obsidian.py` | **NEW** — ObsidianTracker implementation |
| `tests/test_obsidian_tracker.py` | **NEW** — ObsidianTracker unit tests |
| `src/jobbing/tracker/__init__.py` | Add obsidian branch, change default |
| `src/jobbing/config.py` | Add kanban paths, change default backend |
| `src/jobbing/cli.py` | Remove queue; remove page_id args from track; add documents hook to pdf |
| `CLAUDE.md` | Rewrite Commands + Integration sections |
| `WORKFLOW.md` | Replace all Notion/queue refs |
| `.claude/skills/apply/SKILL.md` | Major rewrite |
| `.claude/skills/track/SKILL.md` | Major rewrite |
| `.claude/skills/outreach/SKILL.md` | Replace queue with markdown edit |
| `.claude/skills/debrief/SKILL.md` | Replace reads + writes; interview files |
| `.claude/skills/prep/SKILL.md` | Replace reads + writes; interview files |
| `.claude/skills/followup/SKILL.md` | Replace reads; board + interview dirs |
| `.claude/skills/reassess/SKILL.md` | Replace reads + writes |
| `.claude/skills/compare/SKILL.md` | Replace reads |
| `.claude/skills/analyze/SKILL.md` | Minor |
| `.claude/skills/scan/SKILL.md` | Minor |

**Not changed:** `scoring/SKILL.md`, `disaggregate/SKILL.md`, `src/jobbing/pdf.py`, `src/jobbing/models.py`, `src/jobbing/scanner.py`, `pyproject.toml`

---

## Execution Order (with checkpoints)

| Step | Action | Checkpoint |
|------|--------|------------|
| 0a | Write `scripts/install.sh` | Run it on a clean shell; Obsidian opens with Things theme |
| 0b | Commit `.obsidian/` config files | `git status` shows only workspace.json excluded |
| 1a | Extend sync script + write tests | `pytest tests/test_sync_interviews.py` passes |
| 1b | Run `--include-interviews --dry-run` | Review output for 5 companies |
| 1c | Run migration for real | Open Obsidian; click 3 interview links |
| 2a | Write ObsidianTracker + tests | `pytest tests/test_obsidian_tracker.py -v` all pass |
| 2b | Update config + tracker factory | `jobbing scan existing` lists companies correctly |
| 3 | Update CLI (remove queue, rewire track via ObsidianTracker) | `jobbing track followup` + `jobbing pdf {co}` both work |
| 4 | Rewrite CLAUDE.md + WORKFLOW.md | Grep for Notion references → 0 unintentional hits |
| 5 | Update 12 SKILL.md files | Grep for queue/notion refs → 0 unintentional hits |
| 6 | Final verification | Full Obsidian walkthrough (see below) |

---

## Verification (final)

1. `bash scripts/install.sh` — runs clean on a fresh shell
2. Open Obsidian → vault loads → Things theme applied → Kanban board renders
3. Click a card in "In Progress (Interviewing)" → company hub opens → Documents and Interviews sections have working links
4. Click a PDF link → Obsidian built-in PDF viewer opens (no plugin needed)
5. Click an interview link → interview file opens with correct frontmatter and sections
6. `jobbing pdf {company}` → Documents section updated in hub file
7. `jobbing scan existing` → lists all companies from kanban files
8. `pytest` → full test suite passes (including new ObsidianTracker + migration tests)
9. Grep audit: `grep -r "notion_queue\|launchd\|page_id\|notion-fetch\|notion-search" .claude/skills/ CLAUDE.md WORKFLOW.md` → 0 unintentional hits
10. Graph View in Obsidian → no unresolved (red) wikilinks
