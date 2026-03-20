#!/usr/bin/env python3
"""Sync Notion Job Prospects database → Obsidian Kanban board + notes.

Usage:
    python kanban/sync_notion_to_obsidian.py          # full sync
    python kanban/sync_notion_to_obsidian.py --dry-run # preview without writing

Reads from Notion (read-only). Writes to kanban/ directory:
    kanban/
    ├── Job Tracker.md          ← Obsidian Kanban board file
    └── companies/
        └── {Company}.md        ← Per-company detail notes
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
KANBAN_DIR = Path(__file__).resolve().parent
COMPANIES_DIR = KANBAN_DIR / "companies"
BOARD_FILE = KANBAN_DIR / "Job Tracker.md"

NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
DATABASE_ID = "734d746c43b149298993464f5ccc23e7"

# Status lane ordering (matches Notion kanban)
STATUS_LANES = [
    "Targeted",
    "Applied",
    "Followed-Up",
    "In Progress (Interviewing)",
    "Done",
]


def _load_notion_key() -> str:
    """Load Notion API key from env or .env file."""
    key = os.environ.get("NOTION_API_KEY")
    if key:
        return key
    env_path = PROJECT_ROOT / ".env"
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("NOTION_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("NOTION_API_KEY not found in environment or .env")


# ---------------------------------------------------------------------------
# Notion API helpers
# ---------------------------------------------------------------------------


def _notion_request(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    """Make a Notion API request."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_API_VERSION,
        "Content-Type": "application/json",
    }
    data = json.dumps(payload).encode() if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"Notion API {e.code}: {body}") from e


# ---------------------------------------------------------------------------
# Data model (lighter than the full Application model)
# ---------------------------------------------------------------------------


@dataclass
class TrackedCompany:
    name: str
    position: str = ""
    status: str = "Targeted"
    score: int | None = None
    start_date: str = ""
    url: str = ""
    environment: list[str] = field(default_factory=list)
    salary: str = ""
    focus: list[str] = field(default_factory=list)
    conclusion: str = ""
    page_id: str = ""
    # Content sections (populated on full fetch)
    job_description: str = ""
    fit_assessment: str = ""
    company_research: str = ""
    highlights: list[str] = field(default_factory=list)
    outreach_contacts: str = ""
    questions_they_ask: str = ""
    questions_to_ask: str = ""


# ---------------------------------------------------------------------------
# Notion → TrackedCompany
# ---------------------------------------------------------------------------


def _extract_title(props: dict, name: str) -> str:
    prop = props.get(name, {})
    title_list = prop.get("title", [])
    return title_list[0].get("text", {}).get("content", "") if title_list else ""


def _extract_rich_text(props: dict, name: str) -> str:
    prop = props.get(name, {})
    rt = prop.get("rich_text", [])
    return rt[0].get("text", {}).get("content", "") if rt else ""


def _extract_select(props: dict, name: str) -> str:
    prop = props.get(name, {})
    sel = prop.get("select")
    return sel.get("name", "") if sel else ""


def _extract_multi_select(props: dict, name: str) -> list[str]:
    prop = props.get(name, {})
    return [ms.get("name", "") for ms in prop.get("multi_select", [])]


def _extract_date(props: dict, name: str) -> str:
    prop = props.get(name, {})
    d = prop.get("date")
    return d.get("start", "") if d else ""


def _extract_number(props: dict, name: str) -> int | None:
    prop = props.get(name, {})
    n = prop.get("number")
    return int(n) if n is not None else None


def page_to_company(page: dict) -> TrackedCompany:
    props = page.get("properties", {})
    return TrackedCompany(
        name=_extract_title(props, "Name"),
        position=_extract_rich_text(props, "Open Position"),
        status=_extract_select(props, "Status") or "Targeted",
        score=_extract_number(props, "Score"),
        start_date=_extract_date(props, "Start Date"),
        url=_extract_rich_text(props, "URL"),
        environment=_extract_multi_select(props, "Environment"),
        salary=_extract_rich_text(props, "Salary (Range)"),
        focus=_extract_multi_select(props, "Company Focus"),
        conclusion=_extract_rich_text(props, "Conclusion"),
        page_id=page.get("id", ""),
    )


def fetch_all_entries(token: str) -> list[TrackedCompany]:
    """Query the Notion database for all entries."""
    url = f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query"
    results: list[TrackedCompany] = []
    payload: dict[str, Any] = {"page_size": 100}

    while True:
        response = _notion_request("POST", url, token, payload)
        for page in response.get("results", []):
            if not page.get("archived"):
                company = page_to_company(page)
                if company.name:  # skip blank rows
                    results.append(company)
        if not response.get("has_more"):
            break
        payload["start_cursor"] = response["next_cursor"]

    return results


# ---------------------------------------------------------------------------
# Fetch page content (block children → section text)
# ---------------------------------------------------------------------------


def _rich_text_to_str(rt_list: list[dict]) -> str:
    """Convert Notion rich_text array to plain string."""
    parts = []
    for rt in rt_list:
        text = rt.get("text", {}).get("content", "") or rt.get("plain_text", "")
        annotations = rt.get("annotations", {})
        if annotations.get("bold"):
            text = f"**{text}**"
        if annotations.get("italic"):
            text = f"*{text}*"
        parts.append(text)
    return "".join(parts)


def _blocks_to_text(blocks: list[dict], indent: int = 0) -> str:
    """Convert Notion blocks to markdown-ish text."""
    lines: list[str] = []
    prefix = "  " * indent

    for block in blocks:
        btype = block.get("type", "")

        if btype == "paragraph":
            text = _rich_text_to_str(block.get("paragraph", {}).get("rich_text", []))
            if text:
                lines.append(f"{prefix}{text}")
            else:
                lines.append("")

        elif btype == "bulleted_list_item":
            text = _rich_text_to_str(block.get("bulleted_list_item", {}).get("rich_text", []))
            lines.append(f"{prefix}- {text}")

        elif btype == "numbered_list_item":
            text = _rich_text_to_str(block.get("numbered_list_item", {}).get("rich_text", []))
            lines.append(f"{prefix}1. {text}")

        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = int(btype[-1])
            text = _rich_text_to_str(block.get(btype, {}).get("rich_text", []))
            lines.append(f"{'#' * level} {text}")

        elif btype == "toggle":
            text = _rich_text_to_str(block.get("toggle", {}).get("rich_text", []))
            lines.append(f"{prefix}> **{text}**")

        elif btype == "divider":
            lines.append("---")

        elif btype == "child_database":
            title = block.get("child_database", {}).get("title", "")
            lines.append(f"*[Database: {title}]*")

        # Handle nested children
        if block.get("has_children") and "children" not in block:
            # Children not inline — would need separate fetch
            pass
        elif "children" in block:
            child_text = _blocks_to_text(block["children"], indent + 1)
            if child_text:
                lines.append(child_text)

    return "\n".join(lines)


def _fetch_block_children(token: str, block_id: str) -> list[dict]:
    """Fetch all children of a block, handling pagination."""
    url = f"{NOTION_BASE_URL}/blocks/{block_id}/children?page_size=100"
    all_blocks: list[dict] = []

    while url:
        response = _notion_request("GET", url, token)
        all_blocks.extend(response.get("results", []))
        if response.get("has_more") and response.get("next_cursor"):
            base = f"{NOTION_BASE_URL}/blocks/{block_id}/children"
            url = f"{base}?page_size=100&start_cursor={response['next_cursor']}"
        else:
            url = ""

    return all_blocks


def _fetch_toggle_children(token: str, block_id: str) -> list[dict]:
    """Fetch children inside a toggle block."""
    return _fetch_block_children(token, block_id)


SECTION_NAMES = {
    "job description": "job_description",
    "fit assessment": "fit_assessment",
    "company research": "company_research",
    "experience to highlight": "highlights",
    "outreach contacts": "outreach_contacts",
    "questions i might get asked": "questions_they_ask",
    "questions to ask": "questions_to_ask",
}


def populate_page_content(token: str, company: TrackedCompany) -> None:
    """Fetch block children and populate content sections."""
    page_id = company.page_id.replace("-", "")
    blocks = _fetch_block_children(token, page_id)

    for block in blocks:
        btype = block.get("type", "")

        # Toggle heading_3 blocks contain the sections
        if btype == "heading_3":
            heading_text = _rich_text_to_str(
                block.get("heading_3", {}).get("rich_text", [])
            ).strip().lower()

            field_name = SECTION_NAMES.get(heading_text)
            if not field_name or not block.get("has_children"):
                continue

            # Fetch toggle children
            children = _fetch_toggle_children(token, block["id"])
            content = _blocks_to_text(children)

            if field_name == "highlights":
                # Parse bullet items into a list
                company.highlights = [
                    line.lstrip("- ").strip()
                    for line in content.splitlines()
                    if line.strip().startswith("- ") or line.strip().startswith("* ")
                ]
                if not company.highlights and content.strip():
                    company.highlights = [content.strip()]
            else:
                setattr(company, field_name, content.strip())


# ---------------------------------------------------------------------------
# Obsidian file generation
# ---------------------------------------------------------------------------


def _sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    return name.replace("/", "-").replace("\\", "-").replace(":", " -").strip()


def generate_company_note(company: TrackedCompany) -> str:
    """Generate an Obsidian markdown note for a company."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f"company: \"{company.name}\"")
    lines.append(f"position: \"{company.position}\"")
    lines.append(f"status: \"{company.status}\"")
    if company.score is not None:
        lines.append(f"score: {company.score}")
    if company.start_date:
        lines.append(f"date: {company.start_date}")
    if company.url:
        lines.append(f"url: \"{company.url}\"")
    if company.environment:
        lines.append(f"environment: [{', '.join(company.environment)}]")
    if company.salary:
        lines.append(f"salary: \"{company.salary}\"")
    if company.focus:
        lines.append(f"focus: [{', '.join(company.focus)}]")
    if company.conclusion:
        lines.append(f"conclusion: \"{company.conclusion}\"")
    lines.append(f"notion_id: \"{company.page_id}\"")
    lines.append(f"synced: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    lines.append("---")
    lines.append("")

    # Title
    lines.append(f"# {company.name}")
    if company.position:
        lines.append(f"**Position:** {company.position}")
    lines.append("")

    # Properties summary
    props = []
    if company.score is not None:
        props.append(f"**Score:** {company.score}/100")
    if company.status:
        props.append(f"**Status:** {company.status}")
    if company.start_date:
        props.append(f"**Date:** {company.start_date}")
    if company.salary:
        props.append(f"**Salary:** {company.salary}")
    if company.environment:
        props.append(f"**Environment:** {', '.join(company.environment)}")
    if company.focus:
        props.append(f"**Focus:** {', '.join(company.focus)}")
    if props:
        lines.append(" · ".join(props))
        lines.append("")

    if company.url:
        lines.append(f"[Job Posting]({company.url})")
        lines.append("")

    # Content sections
    if company.fit_assessment:
        lines.append("## Fit Assessment")
        lines.append(company.fit_assessment)
        lines.append("")

    if company.highlights:
        lines.append("## Experience to Highlight")
        for h in company.highlights:
            lines.append(f"- {h}")
        lines.append("")

    if company.company_research:
        lines.append("## Company Research")
        lines.append(company.company_research)
        lines.append("")

    if company.job_description:
        lines.append("## Job Description")
        lines.append(company.job_description)
        lines.append("")

    if company.outreach_contacts:
        lines.append("## Outreach Contacts")
        lines.append(company.outreach_contacts)
        lines.append("")

    if company.questions_they_ask:
        lines.append("## Questions I Might Get Asked")
        lines.append(company.questions_they_ask)
        lines.append("")

    if company.questions_to_ask:
        lines.append("## Questions to Ask")
        lines.append(company.questions_to_ask)
        lines.append("")

    if company.conclusion:
        lines.append("## Conclusion")
        lines.append(company.conclusion)
        lines.append("")

    return "\n".join(lines)


def generate_kanban_board(companies: list[TrackedCompany]) -> str:
    """Generate an Obsidian Kanban board markdown file."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append("kanban-plugin: basic")
    lines.append("---")
    lines.append("")

    # Group companies by status
    by_status: dict[str, list[TrackedCompany]] = {s: [] for s in STATUS_LANES}
    for c in companies:
        lane = c.status if c.status in by_status else "Targeted"
        by_status[lane].append(c)

    # Sort each lane: by score descending (None last), then name
    for lane in by_status.values():
        lane.sort(key=lambda c: (-(c.score or 0), c.name))

    # Generate lanes
    for status in STATUS_LANES:
        entries = by_status[status]
        lines.append(f"## {status}")
        lines.append("")

        for c in entries:
            safe_name = _sanitize_filename(c.name)
            # Card text: link to company note + metadata
            card_parts = [f"[[companies/{safe_name}|{c.name}]]"]
            meta = []
            if c.position:
                meta.append(c.position)
            if c.score is not None:
                meta.append(f"Score: {c.score}")
            if c.start_date:
                meta.append(c.start_date)
            if meta:
                card_parts.append(f" — {' · '.join(meta)}")

            card_text = "".join(card_parts)
            lines.append(f"- [ ] {card_text}")

        lines.append("")

    # Kanban settings
    lines.append("")
    lines.append("%% kanban:settings")
    lines.append("```")
    settings = {
        "kanban-plugin": "basic",
        "lane-width": 280,
        "show-checkboxes": False,
        "show-relative-date": True,
    }
    lines.append(json.dumps(settings, indent=2))
    lines.append("```")
    lines.append("%%")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Interview migration (--include-interviews)
# ---------------------------------------------------------------------------


INTERVIEWS_DIR = KANBAN_DIR / "interviews"


@dataclass
class InterviewData:
    """Minimal interview record extracted from the Notion Interviews DB."""

    interviewer: str = ""
    role: str = ""
    interview_type: str = ""
    date: str = ""
    vibe: int = 0
    outcome: str = ""
    prep_notes: str = ""
    debrief: str = ""


def _interview_name_slug(interviewer: str) -> str:
    """Convert an interviewer name to a filename-safe slug.

    'Richard Frost' → 'Richard-Frost'
    'Anna Russo Kennedy' → 'Anna-Russo-Kennedy'
    Strips anything after a dash/em-dash separator (role suffix).
    """
    import re

    # Split on em dash, en dash, or ' - ' to strip role suffix
    name_only = re.split(r"\s*[—–]\s*|\s+-\s+", interviewer, maxsplit=1)[0].strip()
    # Replace non-alphanumeric characters (except spaces) with nothing
    safe = re.sub(r"[^\w\s-]", "", name_only)
    # Replace spaces with dashes
    return re.sub(r"\s+", "-", safe.strip())


def _interview_filename(
    date_str: str,
    interviewer: str,
    existing: set[str],
) -> str:
    """Generate a unique interview filename.

    Format: {date}-{Slug}.md  e.g. 2026-02-26-Richard-Frost.md
    Falls back to 'unknown-date' or 'unknown-interviewer' if empty.
    Appends '-2', '-3' etc. for duplicates within the same company.
    """
    date_part = date_str or "unknown-date"
    name_part = _interview_name_slug(interviewer) if interviewer else "unknown-interviewer"
    base = f"{date_part}-{name_part}"
    filename = f"{base}.md"
    if filename not in existing:
        return filename
    # Deduplicate
    counter = 2
    while f"{base}-{counter}.md" in existing:
        counter += 1
    return f"{base}-{counter}.md"


def _rich_text_to_plain(rt_list: list[dict]) -> str:
    """Extract plain text from a Notion rich_text array."""
    return "".join(
        seg.get("text", {}).get("content", "") or seg.get("plain_text", "")
        for seg in rt_list
    )


def _blocks_to_markdown(blocks: list[dict], indent: int = 0) -> str:
    """Convert Notion blocks to simple markdown text for migration output."""
    lines: list[str] = []
    prefix = "  " * indent

    for block in blocks:
        btype = block.get("type", "")
        if btype == "paragraph":
            text = _rich_text_to_plain(block.get("paragraph", {}).get("rich_text", []))
            lines.append(f"{prefix}{text}" if text else "")
        elif btype == "bulleted_list_item":
            text = _rich_text_to_plain(block.get("bulleted_list_item", {}).get("rich_text", []))
            lines.append(f"{prefix}- {text}")
        elif btype == "numbered_list_item":
            text = _rich_text_to_plain(block.get("numbered_list_item", {}).get("rich_text", []))
            lines.append(f"{prefix}1. {text}")
        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = int(btype[-1])
            text = _rich_text_to_plain(block.get(btype, {}).get("rich_text", []))
            lines.append(f"{'#' * level} {text}")
        elif btype == "toggle":
            text = _rich_text_to_plain(block.get("toggle", {}).get("rich_text", []))
            lines.append(f"{prefix}**{text}**")
        elif btype == "divider":
            lines.append("---")

        if "children" in block:
            child_text = _blocks_to_markdown(block["children"], indent + 1)
            if child_text:
                lines.append(child_text)

    return "\n".join(lines)


def _fetch_interview_row_content(token: str, row_id: str) -> tuple[str, str]:
    """Fetch Prep Notes and Debrief from an interview row's page body.

    Returns (prep_notes_md, debrief_md).
    """
    url = f"{NOTION_BASE_URL}/blocks/{row_id}/children?page_size=100"
    try:
        result = _notion_request("GET", url, token)
    except RuntimeError:
        return "", ""

    prep_notes = ""
    debrief = ""

    for block in result.get("results", []):
        if block.get("type") != "heading_3":
            continue
        rt = block.get("heading_3", {}).get("rich_text", [])
        heading = _rich_text_to_plain(rt).strip()
        if not block.get("has_children"):
            continue

        children_url = f"{NOTION_BASE_URL}/blocks/{block['id']}/children?page_size=100"
        try:
            children = _notion_request("GET", children_url, token).get("results", [])
        except RuntimeError:
            children = []

        text = _blocks_to_markdown(children).strip()
        if heading == "Prep Notes":
            prep_notes = text
        elif heading == "Debrief":
            debrief = text

    return prep_notes, debrief


def fetch_interviews_for_page(
    token: str,
    page_id: str,
) -> list[InterviewData]:
    """Fetch all interview rows from a page's inline Interviews database.

    Returns an empty list if no Interviews DB exists.
    """
    # Find the Interviews child_database block
    page_id = page_id.replace("-", "")
    url = f"{NOTION_BASE_URL}/blocks/{page_id}/children?page_size=100"
    try:
        result = _notion_request("GET", url, token)
    except RuntimeError:
        return []

    db_id: str | None = None
    for block in result.get("results", []):
        if block.get("type") == "child_database":
            title = block.get("child_database", {}).get("title", "")
            if title == "Interviews":
                db_id = block["id"]
                break

    if not db_id:
        return []

    # Query all rows in the Interviews DB
    query_url = f"{NOTION_BASE_URL}/databases/{db_id}/query"
    rows: list[dict] = []
    payload: dict = {"page_size": 100}
    while True:
        try:
            r = _notion_request("POST", query_url, token, payload)
        except RuntimeError:
            break
        rows.extend(r.get("results", []))
        if not r.get("has_more"):
            break
        payload["start_cursor"] = r["next_cursor"]

    interviews: list[InterviewData] = []
    for row in rows:
        props = row.get("properties", {})

        title_list = props.get("Interviewer Name and Role", {}).get("title", [])
        interviewer_full = _rich_text_to_plain(title_list)

        # Split 'Name — Role' or 'Name - Role'
        import re
        parts = re.split(r"\s*[—–]\s*|\s+-\s+", interviewer_full, maxsplit=1)
        interviewer_name = parts[0].strip()
        interviewer_role = parts[1].strip() if len(parts) > 1 else ""

        date_val = props.get("Date", {}).get("date")
        interview_date = date_val.get("start", "") if date_val else ""

        type_sel = props.get("Type", {}).get("select")
        interview_type = type_sel.get("name", "") if type_sel else ""

        vibe_sel = props.get("Vibe", {}).get("select")
        vibe = int(vibe_sel.get("name", "0")) if vibe_sel else 0

        outcome_sel = props.get("Outcome", {}).get("select")
        outcome = outcome_sel.get("name", "") if outcome_sel else ""

        prep_notes, debrief = _fetch_interview_row_content(token, row["id"])

        interviews.append(InterviewData(
            interviewer=interviewer_name,
            role=interviewer_role,
            interview_type=interview_type,
            date=interview_date,
            vibe=vibe,
            outcome=outcome,
            prep_notes=prep_notes,
            debrief=debrief,
        ))

    return interviews


def generate_interview_file(company_name: str, iv: InterviewData) -> str:
    """Generate an Obsidian interview markdown file."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f"company: \"{company_name}\"")
    if iv.interviewer:
        lines.append(f"interviewer: \"{iv.interviewer}\"")
    if iv.role:
        lines.append(f"role: \"{iv.role}\"")
    if iv.interview_type:
        lines.append(f"type: \"{iv.interview_type}\"")
    if iv.date:
        lines.append(f"date: {iv.date}")
    if iv.vibe:
        lines.append(f"vibe: {iv.vibe}")
    if iv.outcome:
        lines.append(f"outcome: \"{iv.outcome}\"")
    lines.append("---")
    lines.append("")

    # Title
    title_parts = []
    if iv.interviewer:
        title_parts.append(iv.interviewer)
    if iv.interview_type:
        title_parts.append(iv.interview_type)
    if iv.date:
        title_parts.append(iv.date)
    lines.append(f"# {' — '.join(title_parts)}")

    # Subtitle line
    meta_parts = [f"**Company:** [[{company_name}]]"]
    if iv.outcome:
        meta_parts.append(f"**Outcome:** {iv.outcome}")
    if iv.vibe:
        meta_parts.append(f"**Vibe:** {iv.vibe}/5")
    lines.append(" · ".join(meta_parts))
    lines.append("")

    # Sections
    lines.append("## Prep Notes")
    lines.append("")
    if iv.prep_notes:
        lines.append(iv.prep_notes)
        lines.append("")

    lines.append("## Debrief")
    lines.append("")
    if iv.debrief:
        lines.append(iv.debrief)
        lines.append("")

    lines.append("## Transcript / Raw Notes")
    lines.append("")

    return "\n".join(lines)


def _interviews_wikilink(filename: str, iv: InterviewData) -> str:
    """Format a wikilink line for the hub's ## Interviews section."""
    stem = filename.replace(".md", "")
    display_parts = []
    if iv.interviewer:
        display_parts.append(iv.interviewer)
    if iv.interview_type:
        display_parts.append(iv.interview_type)
    if iv.outcome:
        display_parts.append(iv.outcome)
    if iv.vibe:
        display_parts.append(f"Vibe {iv.vibe}/5")
    display = " · ".join(display_parts) if display_parts else stem
    return f"- [[{stem}|{display}]]"


def _update_hub_interviews_section(hub_path: Path, wikilinks: list[str]) -> None:
    """Insert or replace the ## Interviews section in a company hub file.

    The section is inserted after the Documents section (if present),
    or after the first blank line after the title block.
    """
    if not hub_path.is_file():
        return

    text = hub_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    section_heading = "## Interviews"
    new_section = [section_heading, ""] + wikilinks + [""]

    # Check if section already exists
    for i, line in enumerate(lines):
        if line.strip() == section_heading:
            # Find end of existing section (next ## heading or EOF)
            end = i + 1
            while end < len(lines) and not (
                lines[end].startswith("## ") and lines[end].strip() != section_heading
            ):
                end += 1
            # Replace existing section
            updated = lines[:i] + new_section + lines[end:]
            hub_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
            return

    # Section doesn't exist — insert after ## Documents or after first heading
    insert_after = None
    for i, line in enumerate(lines):
        if line.strip() == "## Documents":
            # Find end of Documents section
            j = i + 1
            while j < len(lines) and not lines[j].startswith("## "):
                j += 1
            insert_after = j
            break

    if insert_after is None:
        # Insert after first ## heading block (the title section)
        for i, line in enumerate(lines):
            if line.startswith("## "):
                insert_after = i
                break

    if insert_after is None:
        insert_after = len(lines)

    updated = lines[:insert_after] + new_section + lines[insert_after:]
    hub_path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def migrate_interviews(
    token: str,
    companies: list[TrackedCompany],
    dry_run: bool = False,
) -> None:
    """Migrate all Notion Interviews DB rows to Obsidian interview files.

    For each company with interviews:
    - Writes kanban/interviews/{Company}/{date}-{Name}.md
    - Updates kanban/companies/{Company}.md ## Interviews section
    """
    total_written = 0
    total_skipped = 0

    for company in companies:
        if not company.page_id:
            continue

        print(f"  [{company.name}] fetching interviews...", end="", flush=True)
        try:
            interviews = fetch_interviews_for_page(token, company.page_id)
        except Exception as e:
            print(f" ERROR: {e}")
            continue

        if not interviews:
            print(" (none)")
            continue

        print(f" {len(interviews)} found")

        company_dir = INTERVIEWS_DIR / _sanitize_filename(company.name)
        hub_path = COMPANIES_DIR / (_sanitize_filename(company.name) + ".md")
        seen_filenames: set[str] = set()
        wikilinks: list[str] = []

        for iv in interviews:
            filename = _interview_filename(iv.date, iv.interviewer, seen_filenames)
            seen_filenames.add(filename)
            wikilink = _interviews_wikilink(filename, iv)
            wikilinks.append(wikilink)

            interview_path = company_dir / filename

            if dry_run:
                print(f"    [DRY RUN] Would write: {interview_path}")
                print(f"    [DRY RUN] Hub wikilink: {wikilink}")
                total_written += 1
                continue

            company_dir.mkdir(parents=True, exist_ok=True)
            content = generate_interview_file(company.name, iv)
            interview_path.write_text(content, encoding="utf-8")
            print(f"    → {interview_path.name}")
            total_written += 1

        if not dry_run and wikilinks:
            _update_hub_interviews_section(hub_path, wikilinks)
            print(f"    Updated hub: {hub_path.name}")

    action = "Would write" if dry_run else "Wrote"
    print(f"\n{action} {total_written} interview files ({total_skipped} skipped)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _save_snapshot(companies: list[TrackedCompany], path: Path) -> None:
    """Save companies to a JSON snapshot for offline generation."""
    data = {
        "synced_at": datetime.now().isoformat(),
        "companies": [
            {
                "name": c.name, "position": c.position, "status": c.status,
                "score": c.score, "start_date": c.start_date, "url": c.url,
                "environment": c.environment, "salary": c.salary, "focus": c.focus,
                "conclusion": c.conclusion, "page_id": c.page_id,
                "job_description": c.job_description, "fit_assessment": c.fit_assessment,
                "company_research": c.company_research, "highlights": c.highlights,
                "outreach_contacts": c.outreach_contacts,
                "questions_they_ask": c.questions_they_ask,
                "questions_to_ask": c.questions_to_ask,
            }
            for c in companies
        ],
    }
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"Saved snapshot: {path}")


def _load_snapshot(path: Path) -> list[TrackedCompany]:
    """Load companies from a JSON snapshot."""
    data = json.loads(path.read_text(encoding="utf-8"))
    companies = []
    for d in data["companies"]:
        companies.append(TrackedCompany(
            name=d["name"], position=d.get("position", ""),
            status=d.get("status", "Targeted"), score=d.get("score"),
            start_date=d.get("start_date", ""), url=d.get("url", ""),
            environment=d.get("environment", []), salary=d.get("salary", ""),
            focus=d.get("focus", []), conclusion=d.get("conclusion", ""),
            page_id=d.get("page_id", ""),
            job_description=d.get("job_description", ""),
            fit_assessment=d.get("fit_assessment", ""),
            company_research=d.get("company_research", ""),
            highlights=d.get("highlights", []),
            outreach_contacts=d.get("outreach_contacts", ""),
            questions_they_ask=d.get("questions_they_ask", ""),
            questions_to_ask=d.get("questions_to_ask", ""),
        ))
    print(f"Loaded {len(companies)} entries from snapshot ({data.get('synced_at', '?')})")
    return companies


def main():
    parser = argparse.ArgumentParser(description="Sync Notion → Obsidian Kanban")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument("--board-only", action="store_true", help="Only generate board, skip page content fetch")
    parser.add_argument("--from-json", type=str, metavar="FILE", help="Load from JSON snapshot instead of Notion API")
    parser.add_argument("--save-snapshot", action="store_true", help="Save fetched data to snapshot.json")
    parser.add_argument(
        "--include-interviews",
        action="store_true",
        help="Migrate Notion Interviews DB rows → kanban/interviews/{Company}/ files (one-time migration)",
    )
    args = parser.parse_args()

    if args.from_json:
        companies = _load_snapshot(Path(args.from_json))
    else:
        token = _load_notion_key()
        print("Fetching entries from Notion...")
        companies = fetch_all_entries(token)
        print(f"  Found {len(companies)} entries")

    # Sort summary
    for status in STATUS_LANES:
        count = sum(1 for c in companies if c.status == status)
        if count:
            print(f"    {status}: {count}")

    if not args.from_json and not args.board_only:
        print("Fetching page content for each entry...")
        for i, company in enumerate(companies, 1):
            print(f"  [{i}/{len(companies)}] {company.name}...", end="", flush=True)
            try:
                populate_page_content(token, company)
                sections = sum(1 for f in [
                    company.job_description, company.fit_assessment,
                    company.company_research, company.outreach_contacts,
                    company.questions_they_ask, company.questions_to_ask,
                ] if f) + (1 if company.highlights else 0)
                print(f" {sections} sections")
            except Exception as e:
                print(f" ERROR: {e}")

    if not args.from_json and args.save_snapshot:
        _save_snapshot(companies, KANBAN_DIR / "snapshot.json")

    if args.dry_run and not args.include_interviews:
        print("\n[DRY RUN] Would write:")
        print(f"  {BOARD_FILE}")
        for c in companies:
            print(f"  {COMPANIES_DIR / (_sanitize_filename(c.name) + '.md')}")
        # Show board preview
        board = generate_kanban_board(companies)
        print(f"\n--- Board preview (first 60 lines) ---")
        for line in board.splitlines()[:60]:
            print(line)
        return

    # Interview migration (--include-interviews, runs independently of company sync)
    if args.include_interviews:
        if args.from_json:
            print("Warning: --include-interviews requires live Notion API; --from-json companies used but interviews fetched live.")
        print("\nMigrating interview notes from Notion...")
        # Need token for interview migration even if companies loaded from snapshot
        if args.from_json:
            iv_token = _load_notion_key()
        else:
            iv_token = token  # already loaded above
        migrate_interviews(iv_token, companies, dry_run=args.dry_run)
        if args.dry_run:
            return

    if args.dry_run:
        return

    # Write files
    COMPANIES_DIR.mkdir(parents=True, exist_ok=True)

    # Board
    board = generate_kanban_board(companies)
    BOARD_FILE.write_text(board, encoding="utf-8")
    print(f"\nWrote board: {BOARD_FILE}")

    # Company notes
    for company in companies:
        note = generate_company_note(company)
        filename = _sanitize_filename(company.name) + ".md"
        filepath = COMPANIES_DIR / filename
        filepath.write_text(note, encoding="utf-8")

    print(f"Wrote {len(companies)} company notes to {COMPANIES_DIR}/")
    print("Done.")


if __name__ == "__main__":
    main()
