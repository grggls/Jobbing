"""ObsidianTracker — markdown-file-based tracker backend.

Writes directly to kanban/companies/{Company}.md and updates
kanban/Job Tracker.md. No API, no queue, no network required.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jobbing.config import Config
    from jobbing.models import Application, Contact

# Status lane labels (canonical order)
STATUS_LANES = [
    "Targeted",
    "Applied",
    "Followed-Up",
    "In Progress (Interviewing)",
    "Done",
]


# ---------------------------------------------------------------------------
# Frontmatter helpers (stdlib only — no PyYAML dependency)
# ---------------------------------------------------------------------------


def _parse_frontmatter(text: str) -> dict[str, object]:
    """Parse YAML frontmatter from a markdown string.

    Handles string values (quoted or unquoted), integer/float values,
    and inline lists: ``environment: [Remote, Berlin]``.

    Returns an empty dict if no frontmatter block is present.
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    yaml_block = text[3:end].strip()
    result: dict[str, object] = {}
    for line in yaml_block.splitlines():
        if ":" not in line:
            continue
        key, _, raw_value = line.partition(":")
        key = key.strip()
        val = raw_value.strip()

        # Inline list: [A, B, C]
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip() for v in val[1:-1].split(",")]
            result[key] = [v for v in items if v]
            continue

        # Strip surrounding quotes
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            result[key] = val[1:-1]
            continue

        # Numeric
        try:
            if "." in val:
                result[key] = float(val)
            else:
                result[key] = int(val)
            continue
        except ValueError:
            pass

        result[key] = val
    return result


def _frontmatter_value(v: object) -> str:
    """Render a value for YAML frontmatter."""
    if isinstance(v, list):
        return "[" + ", ".join(str(i) for i in v) + "]"
    if isinstance(v, str):
        # Quote strings that contain special YAML chars
        if any(c in v for c in ('"', "'", ":", "#", "[", "]", "{", "}", ",")):
            escaped = v.replace('"', '\\"')
            return f'"{escaped}"'
        return f'"{v}"'
    if v is None:
        return '""'
    return str(v)


def _write_frontmatter(path: Path, updates: dict[str, object]) -> None:
    """Update YAML frontmatter fields in-place, preserving unknown fields."""
    text = path.read_text(encoding="utf-8")
    existing = _parse_frontmatter(text)
    merged = {**existing, **updates}

    # Rebuild frontmatter block
    fm_lines = ["---"]
    for k, v in merged.items():
        fm_lines.append(f"{k}: {_frontmatter_value(v)}")
    fm_lines.append("---")
    new_fm = "\n".join(fm_lines) + "\n"

    # Replace the old frontmatter block
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            body = text[end + 4:]  # skip '\n---'
            path.write_text(new_fm + body, encoding="utf-8")
            return

    # No existing frontmatter — prepend
    path.write_text(new_fm + "\n" + text, encoding="utf-8")


def _replace_section(path: Path, heading: str, content_lines: list[str]) -> None:
    """Idempotent section upsert.

    Finds the ``## {heading}`` line, removes all content until the next
    ``## `` heading or EOF, inserts ``content_lines`` in its place.
    If the section doesn't exist, appends it at the end.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    heading_line = f"## {heading}"

    start: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == heading_line:
            start = i
            break

    new_section = [heading_line, ""] + content_lines + [""]

    if start is not None:
        # Find end of section
        end = start + 1
        while end < len(lines) and not (
            lines[end].startswith("## ") and lines[end].strip() != heading_line
        ):
            end += 1
        updated = lines[:start] + new_section + lines[end:]
    else:
        # Append at end (skip trailing blank lines first)
        while lines and not lines[-1].strip():
            lines.pop()
        updated = lines + [""] + new_section

    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------


def _card_lines(app: "Application") -> list[str]:
    """Format a kanban board card as one or two lines.

    Title line: [[link|Name]] — Position
    Body line (if any metadata):  Score: N · YYYY-MM-DD
    """
    safe_name = app.name.replace("/", "-").replace("\\", "-").replace(":", " -").strip()
    title = f"[[companies/{safe_name}|{app.name}]]"
    if app.position:
        title += f" — {app.position}"
    meta: list[str] = []
    if app.scoring and app.scoring.score is not None:
        meta.append(f"Score: {app.scoring.score}")
    if app.start_date:
        meta.append(str(app.start_date))
    result = [f"- [ ] {title}"]
    if meta:
        result.append(f"  {' · '.join(meta)}")
    return result


def _find_card_in_board(lines: list[str], company_name: str) -> int | None:
    """Find the line index of a card title line for company_name in the board."""
    safe_name = company_name.replace("/", "-").replace("\\", "-").replace(":", " -").strip()
    needle = f"[[companies/{safe_name}|"
    for i, line in enumerate(lines):
        if needle in line:
            return i
    return None


def _is_card_body(line: str) -> bool:
    """Return True if line is a card body line (indented, not a list item)."""
    return line.startswith("  ") and not line.strip().startswith("- [")


def _board_add_or_move_card(board_path: Path, app: "Application") -> None:
    """Add a new card to the board, or move it if the status changed.

    Cards are inserted into the correct lane. Within a lane, cards are
    sorted by score descending (no score = 0), then by name.
    """
    text = board_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Remove existing card (title + optional body line)
    existing_idx = _find_card_in_board(lines, app.name)
    if existing_idx is not None:
        lines.pop(existing_idx)
        if existing_idx < len(lines) and _is_card_body(lines[existing_idx]):
            lines.pop(existing_idx)

    # Find target lane heading
    status_label = app.status.value if hasattr(app.status, "value") else str(app.status)
    target_heading = f"## {status_label}"
    lane_start: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == target_heading:
            lane_start = i
            break

    new_card = _card_lines(app)

    if lane_start is None:
        # Lane not found — append at end before settings block
        lines.extend(new_card)
    else:
        # Find lane end (next ## heading or settings block)
        lane_end = lane_start + 1
        while lane_end < len(lines):
            l = lines[lane_end]
            if l.startswith("## ") or l.strip().startswith("%% kanban"):
                break
            lane_end += 1

        # Collect existing cards as (title, body) pairs
        section = lines[lane_start + 1 : lane_end]
        cards: list[tuple[str, str]] = []
        i = 0
        while i < len(section):
            line = section[i]
            if line.strip().startswith("- ["):
                body = ""
                if i + 1 < len(section) and _is_card_body(section[i + 1]):
                    body = section[i + 1]
                    i += 1
                cards.append((line, body))
            i += 1

        # Add new card
        new_title = new_card[0]
        new_body = new_card[1] if len(new_card) > 1 else ""
        cards.append((new_title, new_body))

        def _card_sort_key(card: tuple[str, str]) -> tuple[int, str]:
            combined = card[0] + card[1]
            m = re.search(r"Score:\s*(\d+)", combined)
            score = int(m.group(1)) if m else 0
            name_m = re.search(r"\[\[companies/[^\|]+\|([^\]]+)\]\]", card[0])
            name = name_m.group(1) if name_m else card[0]
            return (-score, name)

        cards.sort(key=_card_sort_key)

        lane_content: list[str] = []
        for title, body in cards:
            lane_content.append(title)
            if body:
                lane_content.append(body)

        lines = lines[: lane_start + 1] + [""] + lane_content + [""] + lines[lane_end:]

    board_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Hub file generation
# ---------------------------------------------------------------------------


_SECTION_ORDER = [
    "Documents",
    "Interviews",
    "Fit Assessment",
    "Company Research",
    "Experience to Highlight",
    "Job Description",
    "Outreach Contacts",
    "Questions I Might Get Asked",
    "Questions to Ask",
    "Conclusion",
]


def _scaffold_hub(app: "Application") -> str:
    """Generate a new company hub markdown file."""
    lines: list[str] = []

    # Frontmatter
    lines.append("---")
    lines.append(f"company: {_frontmatter_value(app.name)}")
    lines.append(f"position: {_frontmatter_value(app.position)}")
    status_val = app.status.value if hasattr(app.status, "value") else str(app.status)
    lines.append(f"status: {_frontmatter_value(status_val)}")
    if app.start_date:
        lines.append(f"date: {app.start_date}")
    if app.url:
        lines.append(f"url: {_frontmatter_value(app.url)}")
    if app.environment:
        lines.append(f"environment: [{', '.join(app.environment)}]")
    if app.salary:
        lines.append(f"salary: {_frontmatter_value(app.salary)}")
    if app.focus:
        lines.append(f"focus: [{', '.join(app.focus)}]")
    if app.scoring:
        lines.append(f"score: {app.scoring.score}")
    lines.append('conclusion: ""')
    lines.append("---")
    lines.append("")

    # Title block
    lines.append(f"# {app.name}")
    meta_parts: list[str] = []
    if app.position:
        meta_parts.append(f"**Position:** {app.position}")
    status_str = app.status.value if hasattr(app.status, "value") else str(app.status)
    meta_parts.append(f"**Status:** {status_str}")
    if app.scoring:
        meta_parts.append(f"**Score:** {app.scoring.score}/100")
    if meta_parts:
        lines.append(" · ".join(meta_parts))
    lines.append("")

    if app.url:
        lines.append(f"[Job Posting]({app.url})")
        lines.append("")

    # Scaffold all sections
    for section in _SECTION_ORDER:
        lines.append(f"## {section}")
        lines.append("")
        # Pre-populate sections that have content in app
        if section == "Experience to Highlight" and app.highlights:
            for h in app.highlights:
                lines.append(f"- {h}")
            lines.append("")
        elif section == "Company Research" and app.research:
            for r in app.research:
                lines.append(f"- {r}")
            lines.append("")
        elif section == "Job Description" and app.job_description:
            lines.append(app.job_description)
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ObsidianTracker
# ---------------------------------------------------------------------------


class ObsidianTracker:
    """TrackerBackend implementation that writes to Obsidian kanban files.

    Reads/writes kanban/companies/{Company}.md and kanban/Job Tracker.md.
    No external dependencies, no network required.
    """

    def __init__(self, config: "Config") -> None:
        self._kanban_dir = config.kanban_dir
        self._companies_dir = config.kanban_companies_dir
        self._board_path = config.kanban_board_path

    # -- Internal helpers --

    def _company_file(self, name: str) -> Path:
        safe = name.replace("/", "-").replace("\\", "-").replace(":", " -").strip()
        return self._companies_dir / f"{safe}.md"

    # -- TrackerBackend protocol --

    def create(self, app: "Application") -> tuple[str, list[str]]:
        """Create or update a company hub file and board card.

        Returns (company_name, sections_written).
        If file already exists, updates frontmatter but preserves all
        section content (idempotent).
        """
        self._companies_dir.mkdir(parents=True, exist_ok=True)
        path = self._company_file(app.name)
        sections: list[str] = []

        if not path.is_file():
            content = _scaffold_hub(app)
            path.write_text(content, encoding="utf-8")
            sections = ["hub_created"] + [s for s in _SECTION_ORDER]
        else:
            # Update frontmatter only; preserve existing section content
            status_val = app.status.value if hasattr(app.status, "value") else str(app.status)
            updates: dict[str, object] = {"status": status_val}
            if app.position:
                updates["position"] = app.position
            if app.start_date:
                updates["date"] = str(app.start_date)
            if app.url:
                updates["url"] = app.url
            if app.salary:
                updates["salary"] = app.salary
            if app.scoring:
                updates["score"] = app.scoring.score
            _write_frontmatter(path, updates)
            sections = ["frontmatter_updated"]

        # Populate content sections if data present (only on new or explicit call)
        if app.highlights:
            _replace_section(path, "Experience to Highlight", [f"- {h}" for h in app.highlights])
            sections.append("highlights")
        if app.research:
            _replace_section(path, "Company Research", [f"- {r}" for r in app.research])
            sections.append("research")

        # Board card
        if self._board_path.is_file():
            _board_add_or_move_card(self._board_path, app)
            sections.append("board_card")

        return app.name, sections

    def update(self, app: "Application") -> None:
        """Update frontmatter and move board card if status changed."""
        path = self._company_file(app.name)
        if not path.is_file():
            return

        status_val = app.status.value if hasattr(app.status, "value") else str(app.status)
        updates: dict[str, object] = {"status": status_val}
        if app.position:
            updates["position"] = app.position
        if app.salary:
            updates["salary"] = app.salary
        if app.scoring:
            updates["score"] = app.scoring.score
        if app.conclusion:
            updates["conclusion"] = app.conclusion
        _write_frontmatter(path, updates)

        if self._board_path.is_file():
            _board_add_or_move_card(self._board_path, app)

    def find_by_name(self, name: str) -> "Application | None":
        """Read and parse a company hub file into an Application."""
        from jobbing.models import Application, Status

        path = self._company_file(name)
        if not path.is_file():
            return None

        text = path.read_text(encoding="utf-8")
        fm = _parse_frontmatter(text)

        status_str = str(fm.get("status", "Targeted"))
        try:
            status = Status(status_str)
        except ValueError:
            status = Status.TARGETED

        start_date_raw = fm.get("date")
        start_date = None
        if start_date_raw:
            from datetime import date as date_type

            try:
                parts = str(start_date_raw).split("-")
                start_date = date_type(int(parts[0]), int(parts[1]), int(parts[2]))
            except (ValueError, IndexError):
                pass

        env = fm.get("environment", [])
        if isinstance(env, str):
            env = [env] if env else []

        focus = fm.get("focus", [])
        if isinstance(focus, str):
            focus = [focus] if focus else []

        return Application(
            name=str(fm.get("company", name)),
            position=str(fm.get("position", "")),
            status=status,
            start_date=start_date,
            url=str(fm.get("url", "")),
            environment=list(env),
            salary=str(fm.get("salary", "")),
            focus=list(focus),
            conclusion=str(fm.get("conclusion", "")),
            page_id=str(fm.get("notion_id", name)),
        )

    def set_highlights(self, app_id: str, highlights: list[str]) -> None:
        """Replace ## Experience to Highlight section."""
        path = self._company_file(app_id)
        if path.is_file():
            _replace_section(path, "Experience to Highlight", [f"- {h}" for h in highlights])

    def set_research(self, app_id: str, research: list[str]) -> None:
        """Replace ## Company Research section."""
        path = self._company_file(app_id)
        if path.is_file():
            _replace_section(path, "Company Research", [f"- {r}" for r in research])

    def set_contacts(self, app_id: str, contacts: list["Contact"]) -> None:
        """Replace ## Outreach Contacts section."""
        path = self._company_file(app_id)
        if not path.is_file():
            return
        lines: list[str] = []
        for c in contacts:
            line = f"- **{c.name}**"
            if c.title:
                line += f" — {c.title}"
            if c.linkedin:
                line += f" — {c.linkedin}"
            if c.note:
                line += f"\n  {c.note}"
            if c.message:
                line += f"\n  *Message:* {c.message}"
            lines.append(line)
        _replace_section(path, "Outreach Contacts", lines)

    def list_all(self) -> list["Application"]:
        """List all tracked applications from kanban/companies/*.md."""
        if not self._companies_dir.is_dir():
            return []
        apps: list[Application] = []
        for path in sorted(self._companies_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            fm = _parse_frontmatter(text)
            if not fm.get("company"):
                continue
            app = self.find_by_name(str(fm["company"]))
            if app:
                apps.append(app)
        return apps

    # -- Extra helpers (not on protocol, used by skills and CLI) --

    def add_documents_section(
        self,
        company_name: str,
        cv_stem: str,
        cl_stem: str,
    ) -> None:
        """Write or update ## Documents section with CV/CL wikilinks."""
        path = self._company_file(company_name)
        if not path.is_file():
            return
        lines = [
            f"- [[{cv_stem}|CV]] · [[{cl_stem}|Cover Letter]]",
        ]
        _replace_section(path, "Documents", lines)

    def add_interview_link(self, company_name: str, filename: str, display_text: str) -> None:
        """Append a wikilink to ## Interviews section (no duplicates)."""
        path = self._company_file(company_name)
        if not path.is_file():
            return

        text = path.read_text(encoding="utf-8")
        stem = filename.replace(".md", "")
        link = f"[[{stem}|{display_text}]]"

        # Already present?
        if link in text:
            return

        # Read existing Interviews section lines
        lines = text.splitlines()
        heading = "## Interviews"
        start: int | None = None
        for i, line in enumerate(lines):
            if line.strip() == heading:
                start = i
                break

        if start is None:
            # Section doesn't exist — create it
            _replace_section(path, "Interviews", [f"- {link}"])
            return

        # Find end of section
        end = start + 1
        while end < len(lines) and not (
            lines[end].startswith("## ") and lines[end].strip() != heading
        ):
            end += 1

        # Collect existing links, append new one
        section_lines = lines[start + 1 : end]
        # Remove trailing blank lines
        while section_lines and not section_lines[-1].strip():
            section_lines.pop()
        section_lines.append(f"- {link}")
        updated = lines[:start] + [heading, ""] + section_lines + [""] + lines[end:]
        path.write_text("\n".join(updated) + "\n", encoding="utf-8")
