#!/usr/bin/env python3
"""Sync Notion Job Prospects database → Obsidian Kanban board + notes.

Usage:
    python kanban/sync_notion_to_obsidian.py          # full sync
    python kanban/sync_notion_to_obsidian.py --dry-run # preview without writing

Reads from Notion (read-only). Writes to kanban/ directory:
    kanban/
    ├── Job Tracker.md                  ← Obsidian Kanban board file
    └── companies/
        ├── Parloa/
        │   ├── Parloa.md               ← Company hub note
        │   └── interviews/
        │       └── 2026-03-10 — Jane Smith.md
        └── GitLab/
            └── GitLab.md
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
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
# Data models
# ---------------------------------------------------------------------------


@dataclass
class SyncedInterview:
    """An interview row from a Notion Interviews inline database."""

    interviewer: str = ""  # "Jane Smith — VP Engineering"
    date: str = ""  # ISO date
    interview_type: str = ""  # Phone Screen, Technical, etc.
    outcome: str = ""  # Passed, Rejected, Pending, Withdrawn
    vibe: int = 0  # 1-5, 0 = not set
    prep_notes: str = ""
    debrief: str = ""
    questions_they_asked: list[str] = field(default_factory=list)
    questions_i_asked: list[str] = field(default_factory=list)
    follow_up: str = ""


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
    # Interviews (populated from child_database)
    interviews: list[SyncedInterview] = field(default_factory=list)


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
            pass  # Children not inline — need separate fetch
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


# ---------------------------------------------------------------------------
# Fetch interviews from child_database
# ---------------------------------------------------------------------------


def _find_interviews_db(token: str, page_id: str, blocks: list[dict] | None = None) -> str | None:
    """Find the Interviews inline database on a page. Returns DB ID or None."""
    if blocks is None:
        blocks = _fetch_block_children(token, page_id)
    for block in blocks:
        if block.get("type") == "child_database":
            title = block.get("child_database", {}).get("title", "")
            if title == "Interviews":
                return str(block["id"])
    return None


def _parse_debrief_body(children: list[dict]) -> tuple[str, list[str], list[str], str]:
    """Parse Debrief toggle children into (debrief, q_they_asked, q_i_asked, follow_up)."""
    current_section: str | None = None
    debrief_parts: list[str] = []
    questions_they_asked: list[str] = []
    questions_i_asked: list[str] = []
    follow_up_parts: list[str] = []

    for child in children:
        child_type = child.get("type", "")

        if child_type == "heading_3":
            rt = child.get("heading_3", {}).get("rich_text", [])
            text = "".join(seg.get("text", {}).get("content", "") for seg in rt)
            current_section = text
            continue

        rt_data = child.get(child_type, {}).get("rich_text", [])
        text = "".join(seg.get("text", {}).get("content", "") for seg in rt_data)
        if not text:
            continue

        if current_section == "Questions They Asked":
            questions_they_asked.append(text)
        elif current_section == "Questions I Asked":
            questions_i_asked.append(text)
        elif current_section == "Follow-Up":
            follow_up_parts.append(text)
        else:
            debrief_parts.append(text)

    return (
        "\n\n".join(debrief_parts),
        questions_they_asked,
        questions_i_asked,
        "\n\n".join(follow_up_parts),
    )


def fetch_interviews(
    token: str, page_id: str, blocks: list[dict] | None = None
) -> list[SyncedInterview]:
    """Fetch all interview rows from a page's Interviews child_database."""
    db_id = _find_interviews_db(token, page_id, blocks)
    if not db_id:
        return []

    # Query the interviews database
    url = f"{NOTION_BASE_URL}/databases/{db_id}/query"
    payload: dict[str, Any] = {"page_size": 100}
    rows: list[dict] = []

    while True:
        result = _notion_request("POST", url, token, payload)
        rows.extend(result.get("results", []))
        if not result.get("has_more"):
            break
        payload["start_cursor"] = result["next_cursor"]

    interviews: list[SyncedInterview] = []
    for row in rows:
        props = row.get("properties", {})

        # Title (interviewer name and role)
        title_list = props.get("Interviewer Name and Role", {}).get("title", [])
        interviewer = title_list[0].get("text", {}).get("content", "") if title_list else ""

        # Date
        date_val = props.get("Date", {}).get("date")
        interview_date = date_val.get("start", "") if date_val else ""

        # Selects
        type_sel = props.get("Type", {}).get("select")
        interview_type = type_sel.get("name", "") if type_sel else ""

        vibe_sel = props.get("Vibe", {}).get("select")
        vibe = int(vibe_sel.get("name", "0")) if vibe_sel else 0

        outcome_sel = props.get("Outcome", {}).get("select")
        outcome = outcome_sel.get("name", "") if outcome_sel else ""

        # Read page body for prep notes and debrief
        prep_notes = ""
        debrief_text = ""
        questions_they_asked: list[str] = []
        questions_i_asked: list[str] = []
        follow_up = ""

        try:
            row_children = _fetch_block_children(token, row["id"])
            for block in row_children:
                if block.get("type") != "heading_3":
                    continue
                rt = block.get("heading_3", {}).get("rich_text", [])
                heading = rt[0].get("text", {}).get("content", "") if rt else ""
                if not block.get("has_children"):
                    continue

                toggle_children = _fetch_toggle_children(token, block["id"])

                if heading == "Prep Notes":
                    prep_notes = _blocks_to_text(toggle_children)
                elif heading == "Debrief":
                    debrief_text, questions_they_asked, questions_i_asked, follow_up = (
                        _parse_debrief_body(toggle_children)
                    )
        except RuntimeError:
            pass  # Row may have no body content

        interviews.append(
            SyncedInterview(
                interviewer=interviewer,
                date=interview_date,
                interview_type=interview_type,
                outcome=outcome,
                vibe=vibe,
                prep_notes=prep_notes,
                debrief=debrief_text,
                questions_they_asked=questions_they_asked,
                questions_i_asked=questions_i_asked,
                follow_up=follow_up,
            )
        )

    return interviews


# ---------------------------------------------------------------------------
# Populate page content (sections + interviews)
# ---------------------------------------------------------------------------


def populate_page_content(token: str, company: TrackedCompany) -> None:
    """Fetch block children and populate content sections + interviews."""
    page_id = company.page_id.replace("-", "")
    blocks = _fetch_block_children(token, page_id)

    for block in blocks:
        btype = block.get("type", "")

        # Toggle heading_3 blocks contain the sections
        if btype == "heading_3":
            heading_text = (
                _rich_text_to_str(block.get("heading_3", {}).get("rich_text", [])).strip().lower()
            )

            field_name = SECTION_NAMES.get(heading_text)
            if not field_name or not block.get("has_children"):
                continue

            # Fetch toggle children
            children = _fetch_toggle_children(token, block["id"])
            content = _blocks_to_text(children)

            if field_name == "highlights":
                company.highlights = [
                    line.lstrip("- ").strip()
                    for line in content.splitlines()
                    if line.strip().startswith("- ") or line.strip().startswith("* ")
                ]
                if not company.highlights and content.strip():
                    company.highlights = [content.strip()]
            else:
                setattr(company, field_name, content.strip())

    # Fetch interviews from inline database
    company.interviews = fetch_interviews(token, page_id, blocks)


# ---------------------------------------------------------------------------
# Filename helpers
# ---------------------------------------------------------------------------


def _sanitize_filename(name: str) -> str:
    """Make a string safe for use as a filename."""
    return name.replace("/", "-").replace("\\", "-").replace(":", " -").strip()


def _extract_name(interviewer: str) -> str:
    """Extract person's name from 'Name — Role' or 'Name - Role'."""
    parts = re.split(r"\s*[—–]\s*|\s+-\s+", interviewer, maxsplit=1)
    return parts[0].strip()


def _synced_interview_filename(interview: SyncedInterview) -> str:
    """Generate filename for a Notion-synced interview note."""
    name = _extract_name(interview.interviewer) if interview.interviewer else "Unknown"
    safe_name = _sanitize_filename(name)
    date_str = interview.date or "undated"
    return f"{date_str} — {safe_name}.md"


# ---------------------------------------------------------------------------
# Obsidian-first interview helpers (used by /prep, /debrief, CLI)
# ---------------------------------------------------------------------------


@dataclass
class InterviewData:
    """Structured interview data for obsidian-first file generation."""

    interviewer: str = ""
    role: str = ""
    interview_type: str = ""
    date: str = ""
    vibe: int = 0
    outcome: str = ""
    prep_notes: str = ""
    debrief: str = ""


def _interview_name_slug(name: str) -> str:
    """Convert 'Name — Role' or 'Name - Role' to 'First-Last' slug."""
    # Strip role suffix
    parts = re.split(r"\s*[—–]\s*|\s+-\s+", name, maxsplit=1)
    clean = parts[0].strip()
    # Replace spaces with hyphens, strip non-alphanum except hyphens
    words = re.sub(r"[^\w\s-]", "", clean).split()
    return "-".join(words) if words else clean


def _interview_filename(date: str, interviewer: str, existing: set[str]) -> str:
    """Generate a unique filename: '{date}-{Name-Slug}.md'."""
    date_part = date.strip() if date.strip() else "unknown-date"
    name_part = _interview_name_slug(interviewer) if interviewer.strip() else "unknown-interviewer"
    base = f"{date_part}-{name_part}.md"
    if base not in existing:
        return base
    counter = 2
    while True:
        candidate = f"{date_part}-{name_part}-{counter}.md"
        if candidate not in existing:
            return candidate
        counter += 1


def _interviews_wikilink(filename: str, iv: InterviewData) -> str:
    """Generate a hub wikilink for an interview file."""
    stem = filename.removesuffix(".md")
    parts = [iv.interviewer] if iv.interviewer else [stem]
    if iv.interview_type:
        parts.append(iv.interview_type)
    if iv.outcome:
        parts.append(iv.outcome)
    if iv.vibe:
        parts.append(f"Vibe {iv.vibe}/5")
    display = " · ".join(parts)
    return f"- [[{stem}|{display}]]"


def _update_hub_interviews_section(hub: Path, wikilinks: list[str]) -> None:
    """Replace or insert ## Interviews section in a hub file."""
    if not hub.exists():
        return
    text = hub.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    section_lines = ["## Interviews\n", "\n"] + [f"{w}\n" for w in wikilinks] + ["\n"]

    # Find existing ## Interviews section and replace it
    start = next((i for i, ln in enumerate(lines) if ln.strip() == "## Interviews"), None)
    if start is not None:
        end = start + 1
        while end < len(lines) and not lines[end].startswith("## "):
            end += 1
        lines[start:end] = section_lines
    else:
        # Insert after ## Documents if present, else before ## Fit Assessment
        anchor = next(
            (i for i, ln in enumerate(lines) if ln.strip() == "## Documents"),
            None,
        )
        if anchor is None:
            anchor = next(
                (i for i, ln in enumerate(lines) if ln.strip().startswith("## ")),
                len(lines),
            )
        else:
            # Move past ## Documents section content
            anchor += 1
            while anchor < len(lines) and not lines[anchor].startswith("## "):
                anchor += 1
        lines[anchor:anchor] = section_lines

    hub.write_text("".join(lines), encoding="utf-8")


def generate_interview_file(company_name: str, iv: InterviewData) -> str:
    """Generate an Obsidian markdown interview file from InterviewData."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f'company: "{company_name}"')
    if iv.interviewer:
        lines.append(f'interviewer: "{iv.interviewer}"')
    if iv.role:
        lines.append(f'role: "{iv.role}"')
    if iv.interview_type:
        lines.append(f'type: "{iv.interview_type}"')
    if iv.date:
        lines.append(f"date: {iv.date}")
    if iv.vibe:
        lines.append(f"vibe: {iv.vibe}")
    if iv.outcome:
        lines.append(f'outcome: "{iv.outcome}"')
    lines.append("---")
    lines.append("")

    # Title
    name = iv.interviewer or "Unknown"
    type_str = f" — {iv.interview_type}" if iv.interview_type else ""
    date_str = f" · {iv.date}" if iv.date else ""
    lines.append(f"# {name}{type_str}{date_str}")
    meta = [f"**Company:** [[{company_name}]]"]
    if iv.outcome:
        meta.append(f"**Outcome:** {iv.outcome}")
    if iv.vibe:
        meta.append(f"**Vibe:** {iv.vibe}/5")
    lines.append(" · ".join(meta))
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


# ---------------------------------------------------------------------------
# Obsidian file generation
# ---------------------------------------------------------------------------


def generate_interview_note(interview: SyncedInterview, company_name: str) -> str:
    """Generate an Obsidian markdown note for a single interview."""
    lines: list[str] = []

    # Extract name and role from "Name — Role"
    name = _extract_name(interview.interviewer) if interview.interviewer else "Unknown"
    role_match = re.split(r"\s*[—–]\s*|\s+-\s+", interview.interviewer or "", maxsplit=1)
    role = role_match[1].strip() if len(role_match) > 1 else ""

    # Frontmatter
    lines.append("---")
    lines.append(f'company: "{company_name}"')
    lines.append(f'interviewer: "{name}"')
    if role:
        lines.append(f'role: "{role}"')
    if interview.interview_type:
        lines.append(f'type: "{interview.interview_type}"')
    if interview.date:
        lines.append(f"date: {interview.date}")
    if interview.vibe:
        lines.append(f"vibe: {interview.vibe}")
    if interview.outcome:
        lines.append(f'outcome: "{interview.outcome}"')
    lines.append("---")
    lines.append("")

    # Title
    type_str = f" — {interview.interview_type}" if interview.interview_type else ""
    date_str = f" · {interview.date}" if interview.date else ""
    lines.append(f"# {name}{type_str}{date_str}")
    meta_parts = [f"**Company:** [[{company_name}]]"]
    if interview.outcome:
        meta_parts.append(f"**Outcome:** {interview.outcome}")
    if interview.vibe:
        meta_parts.append(f"**Vibe:** {interview.vibe}/5")
    lines.append(" · ".join(meta_parts))
    lines.append("")

    # Prep Notes
    if interview.prep_notes:
        lines.append("## Prep Notes")
        lines.append("")
        lines.append(interview.prep_notes)
        lines.append("")

    # Debrief
    if interview.debrief:
        lines.append("## Debrief")
        lines.append("")
        lines.append(interview.debrief)
        lines.append("")

    if interview.questions_they_asked:
        lines.append("## Questions They Asked")
        lines.append("")
        for q in interview.questions_they_asked:
            lines.append(f"- {q}")
        lines.append("")

    if interview.questions_i_asked:
        lines.append("## Questions I Asked")
        lines.append("")
        for q in interview.questions_i_asked:
            lines.append(f"- {q}")
        lines.append("")

    if interview.follow_up:
        lines.append("## Follow-Up")
        lines.append("")
        lines.append(interview.follow_up)
        lines.append("")

    return "\n".join(lines)


def generate_company_note(company: TrackedCompany) -> str:
    """Generate an Obsidian markdown note for a company."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f'company: "{company.name}"')
    lines.append(f'position: "{company.position}"')
    lines.append(f'status: "{company.status}"')
    if company.score is not None:
        lines.append(f"score: {company.score}")
    if company.start_date:
        lines.append(f"date: {company.start_date}")
    if company.url:
        lines.append(f'url: "{company.url}"')
    if company.environment:
        lines.append(f"environment: [{', '.join(company.environment)}]")
    if company.salary:
        lines.append(f'salary: "{company.salary}"')
    if company.focus:
        lines.append(f"focus: [{', '.join(company.focus)}]")
    if company.conclusion:
        lines.append(f'conclusion: "{company.conclusion}"')
    lines.append(f'notion_id: "{company.page_id}"')
    lines.append(f"synced: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}")
    lines.append("---")
    lines.append("")

    # Title and summary
    lines.append(f"# {company.name}")
    score_str = f" · **Score:** {company.score}/100" if company.score is not None else ""
    lines.append(f"**Position:** {company.position} · **Status:** {company.status}{score_str}")
    lines.append("")

    # Properties summary
    props = []
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

    # Documents (placeholder — filled by jobbing pdf)
    lines.append("## Documents")
    lines.append("")

    # Interviews section
    lines.append("## Interviews")
    lines.append("")
    if company.interviews:
        for iv in sorted(company.interviews, key=lambda x: x.date or ""):
            name = _extract_name(iv.interviewer) if iv.interviewer else "Unknown"
            iv_filename = _synced_interview_filename(iv)
            iv_link_path = f"interviews/{iv_filename.removesuffix('.md')}"
            parts = [f"[[{iv_link_path}|{name}]]"]
            meta = []
            if iv.interview_type:
                meta.append(iv.interview_type)
            if iv.outcome:
                meta.append(iv.outcome)
            if iv.vibe:
                meta.append(f"Vibe {iv.vibe}/5")
            if meta:
                parts.append(f" — {' · '.join(meta)}")
            lines.append(f"- {iv.date or 'undated'}: {''.join(parts)}")
        lines.append("")
    else:
        lines.append("*No interviews synced.*")
        lines.append("")

    if company.url:
        lines.append(f"[Job Posting]({company.url})")
        lines.append("")

    # Content sections
    if company.fit_assessment:
        lines.append("## Fit Assessment")
        lines.append("")
        lines.append(company.fit_assessment)
        lines.append("")

    if company.highlights:
        lines.append("## Experience to Highlight")
        lines.append("")
        for h in company.highlights:
            lines.append(f"- {h}")
        lines.append("")

    if company.company_research:
        lines.append("## Company Research")
        lines.append("")
        lines.append(company.company_research)
        lines.append("")

    if company.job_description:
        lines.append("## Job Description")
        lines.append("")
        lines.append(company.job_description)
        lines.append("")

    if company.outreach_contacts:
        lines.append("## Outreach Contacts")
        lines.append("")
        lines.append(company.outreach_contacts)
        lines.append("")

    if company.questions_they_ask:
        lines.append("## Questions I Might Get Asked")
        lines.append("")
        lines.append(company.questions_they_ask)
        lines.append("")

    if company.questions_to_ask:
        lines.append("## Questions to Ask")
        lines.append("")
        lines.append(company.questions_to_ask)
        lines.append("")

    if company.conclusion:
        lines.append("## Conclusion")
        lines.append("")
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
            # Link into the company subfolder: companies/Company/Company
            card_parts = [f"[[companies/{safe_name}/{safe_name}|{c.name}]]"]
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
# Snapshot save/load
# ---------------------------------------------------------------------------


def _interview_to_dict(iv: SyncedInterview) -> dict:
    return {
        "interviewer": iv.interviewer,
        "date": iv.date,
        "interview_type": iv.interview_type,
        "outcome": iv.outcome,
        "vibe": iv.vibe,
        "prep_notes": iv.prep_notes,
        "debrief": iv.debrief,
        "questions_they_asked": iv.questions_they_asked,
        "questions_i_asked": iv.questions_i_asked,
        "follow_up": iv.follow_up,
    }


def _interview_from_dict(d: dict) -> SyncedInterview:
    return SyncedInterview(
        interviewer=d.get("interviewer", ""),
        date=d.get("date", ""),
        interview_type=d.get("interview_type", ""),
        outcome=d.get("outcome", ""),
        vibe=d.get("vibe", 0),
        prep_notes=d.get("prep_notes", ""),
        debrief=d.get("debrief", ""),
        questions_they_asked=d.get("questions_they_asked", []),
        questions_i_asked=d.get("questions_i_asked", []),
        follow_up=d.get("follow_up", ""),
    )


def _save_snapshot(companies: list[TrackedCompany], path: Path) -> None:
    """Save companies to a JSON snapshot for offline generation."""
    data = {
        "synced_at": datetime.now().isoformat(),
        "companies": [
            {
                "name": c.name,
                "position": c.position,
                "status": c.status,
                "score": c.score,
                "start_date": c.start_date,
                "url": c.url,
                "environment": c.environment,
                "salary": c.salary,
                "focus": c.focus,
                "conclusion": c.conclusion,
                "page_id": c.page_id,
                "job_description": c.job_description,
                "fit_assessment": c.fit_assessment,
                "company_research": c.company_research,
                "highlights": c.highlights,
                "outreach_contacts": c.outreach_contacts,
                "questions_they_ask": c.questions_they_ask,
                "questions_to_ask": c.questions_to_ask,
                "interviews": [_interview_to_dict(iv) for iv in c.interviews],
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
        companies.append(
            TrackedCompany(
                name=d["name"],
                position=d.get("position", ""),
                status=d.get("status", "Targeted"),
                score=d.get("score"),
                start_date=d.get("start_date", ""),
                url=d.get("url", ""),
                environment=d.get("environment", []),
                salary=d.get("salary", ""),
                focus=d.get("focus", []),
                conclusion=d.get("conclusion", ""),
                page_id=d.get("page_id", ""),
                job_description=d.get("job_description", ""),
                fit_assessment=d.get("fit_assessment", ""),
                company_research=d.get("company_research", ""),
                highlights=d.get("highlights", []),
                outreach_contacts=d.get("outreach_contacts", ""),
                questions_they_ask=d.get("questions_they_ask", ""),
                questions_to_ask=d.get("questions_to_ask", ""),
                interviews=[_interview_from_dict(iv) for iv in d.get("interviews", [])],
            )
        )
    print(f"Loaded {len(companies)} entries from snapshot ({data.get('synced_at', '?')})")
    return companies


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Sync Notion → Obsidian Kanban")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    parser.add_argument(
        "--board-only", action="store_true", help="Only generate board, skip page content fetch"
    )
    parser.add_argument(
        "--from-json",
        type=str,
        metavar="FILE",
        help="Load from JSON snapshot instead of Notion API",
    )
    parser.add_argument(
        "--save-snapshot", action="store_true", help="Save fetched data to snapshot.json"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove old flat company .md files before writing new folder structure",
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
        print("Fetching page content + interviews for each entry...")
        for i, company in enumerate(companies, 1):
            print(f"  [{i}/{len(companies)}] {company.name}...", end="", flush=True)
            try:
                populate_page_content(token, company)
                sections = sum(
                    1
                    for f in [
                        company.job_description,
                        company.fit_assessment,
                        company.company_research,
                        company.outreach_contacts,
                        company.questions_they_ask,
                        company.questions_to_ask,
                    ]
                    if f
                ) + (1 if company.highlights else 0)
                iv_count = len(company.interviews)
                print(f" {sections} sections, {iv_count} interviews")
            except Exception as e:
                print(f" ERROR: {e}")

    if not args.from_json and args.save_snapshot:
        _save_snapshot(companies, KANBAN_DIR / "snapshot.json")

    # Count total interviews
    total_interviews = sum(len(c.interviews) for c in companies)
    companies_with_interviews = sum(1 for c in companies if c.interviews)

    if args.dry_run:
        print("\n[DRY RUN] Would write:")
        print(f"  {BOARD_FILE}")
        for c in companies:
            safe = _sanitize_filename(c.name)
            company_dir = COMPANIES_DIR / safe
            print(f"  {company_dir / (safe + '.md')}")
            for iv in c.interviews:
                print(f"    {company_dir / 'interviews' / _synced_interview_filename(iv)}")
        print(
            f"\n  Total: {len(companies)} companies, {total_interviews} interviews "
            f"({companies_with_interviews} companies with interviews)"
        )
        # Board preview
        board = generate_kanban_board(companies)
        print("\n--- Board preview (first 40 lines) ---")
        for line in board.splitlines()[:40]:
            print(line)
        return

    # Clean old flat files if requested
    if args.clean:
        old_flat = list(COMPANIES_DIR.glob("*.md"))
        if old_flat:
            for f in old_flat:
                f.unlink()
            print(f"Cleaned {len(old_flat)} old flat company files")

    # Write files
    # Board
    board = generate_kanban_board(companies)
    BOARD_FILE.write_text(board, encoding="utf-8")
    print(f"\nWrote board: {BOARD_FILE}")

    # Company notes + interview notes
    interview_count = 0
    for company in companies:
        safe = _sanitize_filename(company.name)
        company_dir = COMPANIES_DIR / safe
        company_dir.mkdir(parents=True, exist_ok=True)

        # Company hub note
        note = generate_company_note(company)
        (company_dir / f"{safe}.md").write_text(note, encoding="utf-8")

        # Interview notes (only create interviews/ folder if there are interviews)
        if company.interviews:
            iv_dir = company_dir / "interviews"
            iv_dir.mkdir(exist_ok=True)
            for iv in company.interviews:
                iv_note = generate_interview_note(iv, company.name)
                iv_path = iv_dir / _synced_interview_filename(iv)
                iv_path.write_text(iv_note, encoding="utf-8")
                interview_count += 1

    print(
        f"Wrote {len(companies)} company notes + {interview_count} interview notes"
        f" to {COMPANIES_DIR}/"
    )
    print("Done.")


if __name__ == "__main__":
    main()
