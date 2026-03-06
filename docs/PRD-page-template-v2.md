# PRD: Notion Page Template v2

**Author:** Greg Damiani + Claude
**Date:** 2026-02-23
**Status:** Draft
**Audience:** Greg, Claude (implementation reference)

## Problem

The queue processor's `_add_template_body()` in `src/jobbing/tracker/notion.py` creates page scaffolding that doesn't match the structure Greg gets when using the Notion "New Job Prospect" template manually. The gaps:

1. **Sections aren't collapsible.** The code creates plain `heading_3` blocks for Experience to Highlight, Company Research, Questions I Might Get Asked, and Questions To Ask. The Notion template uses toggle `heading_3` blocks (`is_toggleable: true`) so sections can be expanded/collapsed. Only Job Description is currently toggleable.
2. **No inline Interviews database.** The template creates an inline database for tracking interview rounds (interviewer name, date). The code doesn't create this at all.
3. **No Outreach Contacts section.** The code scaffolds the section only when the `outreach` queue command runs. It should be part of the initial template so the page structure is complete from creation.
4. **Section order doesn't match.** The template puts the Interviews database first (top of page), then a divider, then the content sections. The code puts Job Description first.

When Greg creates pages via the queue (which is the primary path for all new entries), he gets a structurally incomplete page. He then has to either apply the Notion template manually or live with the mismatch.

## Desired State

Every page created by `_add_template_body()` should produce the same structure as the Notion template, so that queue-created pages and template-created pages are interchangeable.

### Target page structure

```
┌─────────────────────────────────────────────┐
│  [Inline Database] Interviews               │
│  ┌─────────────────────────────────────────┐│
│  │ Interviewer Name and Role  │    Date    ││
│  │ (title)                    │   (date)   ││
│  └─────────────────────────────────────────┘│
│                                             │
│  ───────────── (divider) ──────────────     │
│                                             │
│  ▶ Job Description          [toggle h3]     │
│    └─ paragraph blocks (job posting text)   │
│                                             │
│  ▶ Company Research         [toggle h3]     │
│    └─ bulleted list items                   │
│                                             │
│  ▶ Experience to Highlight  [toggle h3]     │
│    └─ bulleted list items                   │
│                                             │
│  ▶ Questions to Ask During an Interview     │
│                              [toggle h3]    │
│    └─ bulleted list items                   │
│                                             │
│  ▶ Outreach Contacts        [toggle h3]     │
│    └─ bulleted list items (contact blocks)  │
└─────────────────────────────────────────────┘
```

### Section specifications

| # | Section | Block type | Default content | Populated by |
|---|---------|-----------|----------------|--------------|
| 1 | Interviews | Inline database | Empty (no rows) | Manual or future queue command |
| — | *(divider)* | `divider` | — | — |
| 2 | Job Description | `heading_3` with `is_toggleable: true` | Paragraphs from `app.job_description`, or empty paragraph | `create` command |
| 3 | Company Research | `heading_3` with `is_toggleable: true` | Bullets from `app.research`, or empty bullet | `create` or `research` command |
| 4 | Experience to Highlight | `heading_3` with `is_toggleable: true` | Bullets from `app.highlights`, or empty bullet | `create` or `highlights` command |
| 5 | Questions to Ask During an Interview | `heading_3` with `is_toggleable: true` | Empty bullet | `questions_to_ask` command |
| 6 | Outreach Contacts | `heading_3` with `is_toggleable: true` | Empty bullet | `outreach` command |

**Removed from template:** "Questions I Might Get Asked" (Q&A interview prep). This section exists in the current code but isn't part of the Notion template structure. It can still be added by the `interview_questions` queue command, which will append it to the page — it just won't be scaffolded at creation time. *(Greg: confirm this is correct or if you want it kept in the scaffold.)*

### Inline Interviews database schema

| Property | Type | Notes |
|----------|------|-------|
| Interviewer Name and Role | `title` | Required. The only title column. |
| Date | `date` | Interview date. |

Created via `POST /v1/databases` with:
```json
{
  "parent": { "type": "page_id", "page_id": "<new_page_id>" },
  "is_inline": true,
  "title": [{ "text": { "content": "Interviews" } }],
  "properties": {
    "Interviewer Name and Role": { "title": {} },
    "Date": { "date": {} }
  }
}
```

## Implementation Changes

### 1. New block builder: `_divider_block()`

```python
def _divider_block() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}
```

### 2. New method: `_create_inline_interviews_db(page_id)`

Creates the inline Interviews database on a page. Uses the existing `_request()` method to `POST /v1/databases`. Returns the database ID (not currently needed, but useful for future automation — e.g., a queue command that adds interview rows).

### 3. Modify `_add_template_body()`

Replace the current implementation with the new section order and block types:

```
1. Create inline Interviews database (separate API call)
2. Append all content blocks in one PATCH:
   a. divider
   b. Job Description — toggle heading_3 (already works this way)
   c. Company Research — toggle heading_3 (currently plain heading_3)
   d. Experience to Highlight — toggle heading_3 (currently plain heading_3)
   e. Questions to Ask During an Interview — toggle heading_3 (currently "Questions To Ask In An Interview", plain heading_3)
   f. Outreach Contacts — toggle heading_3 (new, currently not scaffolded)
```

### 4. Modify `_append_section()` to use toggle headings

Currently `_append_section()` creates plain `heading_3` blocks when replacing sections. It needs to create toggle `heading_3` blocks instead, so that sections remain collapsible after being replaced by queue commands (`research`, `highlights`, `outreach`, etc.).

Two options:

**Option A (simpler):** Change `_append_section()` to always use `_toggle_heading3_block()` for heading_3 sections. Since all heading_3 sections on these pages are toggleable, this is safe.

**Option B (explicit):** Add a `toggleable: bool = True` parameter to `_append_section()`. Default to `True` for heading_3.

Recommend **Option A** — there's no use case for non-toggleable heading_3 sections on tracker pages.

**Important:** `_toggle_heading3_block()` nests children *inside* the heading block. But `_append_section()` currently appends the heading and bullets as *sibling* blocks. For toggle headings, the bullets need to be children of the heading, not siblings. This is a structural change to how `_append_section()` builds its block list.

Current behavior:
```
[heading_3 block]     ← appended as child of page
[bullet block]        ← appended as child of page (sibling of heading)
[bullet block]        ← appended as child of page (sibling of heading)
```

Required behavior:
```
[heading_3 block (is_toggleable: true)]   ← appended as child of page
  └─ [bullet block]                       ← child of heading block
  └─ [bullet block]                       ← child of heading block
```

### 5. Modify `_remove_section()` for toggle headings

Currently `_remove_section()` finds a heading block, then walks forward deleting sibling `bulleted_list_item` blocks until it hits the next heading. With toggle headings, the bullets are *children* of the heading block, not siblings. Deleting the heading block automatically deletes its children.

This actually simplifies `_remove_section()` — for toggle headings, just find and delete the heading block. No need to walk siblings.

However, the method must remain backward-compatible with existing pages that have the old sibling-bullet structure (plain heading_3 + sibling bullets). Detection: check `is_toggleable` on the matched heading block. If toggleable, delete just the heading. If not, use the current walk-and-delete logic.

### 6. Rename section heading text

| Current code | New text |
|-------------|----------|
| `"Questions To Ask In An Interview"` | `"Questions to Ask During an Interview"` |

The case-insensitive matching in `_remove_section()` handles backward compatibility with existing pages that have either casing.

### 7. Update `set_questions_to_ask()` heading text

Change the heading text passed to `_append_section()` from `"Questions To Ask In An Interview"` to `"Questions to Ask During an Interview"`.

## Migration / Backward Compatibility

- **Existing pages are unaffected.** The `_remove_section()` changes ensure old pages (sibling-bullet structure) and new pages (toggle-heading structure) both work.
- **No data migration needed.** Queue commands that replace sections (`research`, `highlights`, `outreach`, `questions_to_ask`, `interview_questions`) will produce toggle headings on their next run, regardless of the page's original structure.
- **Existing pages won't get the Interviews database retroactively.** That's fine — Greg can apply the template manually to add it to older entries, or we could add a separate `add_interviews_db` queue command later if needed.

## Out of Scope

- **Adding rows to the Interviews database via queue.** Future enhancement. Would require a new queue command (e.g., `interview`) that creates a page in the inline database.
- **"Questions I Might Get Asked" in scaffold.** Currently scaffolded by the code but not part of the Notion template. The `interview_questions` queue command can still add this section on demand — it just won't appear in the initial page structure.
- **Sub-document pages.** The old template structure used sub-pages for interview prep. The toggle heading approach replaces this. No sub-pages needed.

