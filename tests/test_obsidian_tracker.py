"""Tests for ObsidianTracker backend."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from jobbing.models import Application, Contact, ScoringResult, Status
from jobbing.tracker.obsidian import (
    ObsidianTracker,
    _card_lines,
    _find_card_in_board,
    _parse_frontmatter,
    _replace_section,
    _write_frontmatter,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_board(tmp_path: Path) -> Path:
    """Create a minimal kanban board file."""
    board = tmp_path / "Job Tracker.md"
    board.write_text(
        "---\nkanban-plugin: basic\n---\n\n"
        + "\n\n".join(f"## {lane}\n" for lane in [
            "Targeted", "Applied", "Followed-Up", "In Progress (Interviewing)", "Done"
        ])
        + "\n\n%% kanban:settings\n```\n{}\n```\n%%\n",
        encoding="utf-8",
    )
    return board


def _make_tracker(tmp_path: Path) -> ObsidianTracker:
    config = MagicMock()
    config.kanban_dir = tmp_path
    config.kanban_companies_dir = tmp_path / "companies"
    config.kanban_board_path = tmp_path / "Job Tracker.md"
    return ObsidianTracker(config)


def _make_app(
    name: str = "Acme Corp",
    position: str = "Staff Engineer",
    status: Status = Status.TARGETED,
    score: int | None = None,
    start_date: date | None = None,
) -> Application:
    app = Application(name=name, position=position, status=status, start_date=start_date)
    if score is not None:
        app.scoring = ScoringResult(score=score, reasoning="")
    return app


# ---------------------------------------------------------------------------
# _parse_frontmatter
# ---------------------------------------------------------------------------


def test_parse_frontmatter_basic():
    text = '---\ncompany: "Acme"\nposition: "Engineer"\n---\n\nBody'
    fm = _parse_frontmatter(text)
    assert fm["company"] == "Acme"
    assert fm["position"] == "Engineer"


def test_parse_frontmatter_handles_lists():
    text = "---\nenvironment: [Remote, Berlin]\nfocus: [SaaS]\n---\n"
    fm = _parse_frontmatter(text)
    assert fm["environment"] == ["Remote", "Berlin"]
    assert fm["focus"] == ["SaaS"]


def test_parse_frontmatter_handles_integers():
    text = "---\nscore: 88\n---\n"
    fm = _parse_frontmatter(text)
    assert fm["score"] == 88


def test_parse_frontmatter_empty():
    fm = _parse_frontmatter("No frontmatter here")
    assert fm == {}


def test_parse_frontmatter_no_body():
    text = "---\ncompany: \"Acme\"\n---\n"
    fm = _parse_frontmatter(text)
    assert fm["company"] == "Acme"


# ---------------------------------------------------------------------------
# _replace_section
# ---------------------------------------------------------------------------


def test_replace_section_inserts(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("---\n---\n\n# Title\n\n## Other\n\nOther content\n", encoding="utf-8")
    _replace_section(f, "Company Research", ["- Finding 1", "- Finding 2"])
    text = f.read_text(encoding="utf-8")
    assert "## Company Research" in text
    assert "- Finding 1" in text


def test_replace_section_replaces(tmp_path):
    f = tmp_path / "test.md"
    f.write_text(
        "---\n---\n\n## Company Research\n\n- Old finding\n\n## Job Description\n\nJD text\n",
        encoding="utf-8",
    )
    _replace_section(f, "Company Research", ["- New finding"])
    text = f.read_text(encoding="utf-8")
    assert "- New finding" in text
    assert "- Old finding" not in text
    assert "## Job Description" in text  # preserved


def test_replace_section_idempotent(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("---\n---\n\n## Notes\n\n- Item\n", encoding="utf-8")
    _replace_section(f, "Notes", ["- Item"])
    _replace_section(f, "Notes", ["- Item"])
    text = f.read_text(encoding="utf-8")
    assert text.count("## Notes") == 1
    assert text.count("- Item") == 1


# ---------------------------------------------------------------------------
# _card_lines
# ---------------------------------------------------------------------------


def test_board_card_format_with_score():
    app = _make_app(score=88, start_date=date(2026, 2, 26))
    lines = _card_lines(app)
    assert len(lines) == 2
    assert "[[companies/Acme Corp|Acme Corp]]" in lines[0]
    assert "Staff Engineer" in lines[0]
    assert "Score: 88" in lines[1]
    assert "2026-02-26" in lines[1]
    assert lines[1].startswith("  ")


def test_board_card_format_without_score():
    app = _make_app()
    lines = _card_lines(app)
    assert len(lines) == 1
    assert "Score:" not in lines[0]
    assert "[[companies/Acme Corp|Acme Corp]]" in lines[0]


# ---------------------------------------------------------------------------
# ObsidianTracker.create
# ---------------------------------------------------------------------------


def test_create_writes_frontmatter(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    app = _make_app(score=75, start_date=date(2026, 1, 10))
    tracker.create(app)

    path = tmp_path / "companies" / "Acme Corp.md"
    assert path.is_file()
    fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["company"] == "Acme Corp"
    assert fm["position"] == "Staff Engineer"
    assert fm["status"] == "Targeted"
    assert fm["score"] == 75


def test_create_scaffolds_sections(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    for section in ["Documents", "Interviews", "Fit Assessment", "Company Research",
                    "Experience to Highlight", "Job Description", "Outreach Contacts",
                    "Questions I Might Get Asked", "Questions to Ask", "Conclusion"]:
        assert f"## {section}" in text


def test_create_adds_board_card(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())

    board_text = board.read_text(encoding="utf-8")
    assert "[[companies/Acme Corp|Acme Corp]]" in board_text
    # Card should be in Targeted lane
    targeted_pos = board_text.index("## Targeted")
    card_pos = board_text.index("[[companies/Acme Corp|Acme Corp]]")
    applied_pos = board_text.index("## Applied")
    assert targeted_pos < card_pos < applied_pos


def test_create_idempotent(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    app = _make_app()
    tracker.create(app)
    # Add some content to a section
    path = tmp_path / "companies" / "Acme Corp.md"
    _replace_section(path, "Fit Assessment", ["Great fit"])
    # Re-create should not wipe the section
    tracker.create(app)
    text = path.read_text(encoding="utf-8")
    assert "Great fit" in text
    # Board should not have duplicates
    board_text = board.read_text(encoding="utf-8")
    assert board_text.count("[[companies/Acme Corp|Acme Corp]]") == 1


def test_create_no_board_file(tmp_path):
    """create() should not crash if board file doesn't exist."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    path = tmp_path / "companies" / "Acme Corp.md"
    assert path.is_file()


# ---------------------------------------------------------------------------
# ObsidianTracker.update
# ---------------------------------------------------------------------------


def test_update_frontmatter_fields(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    app = _make_app()
    tracker.create(app)

    app.status = Status.APPLIED
    app.salary = "€120K"
    app.scoring = ScoringResult(score=90, reasoning="")
    tracker.update(app)

    path = tmp_path / "companies" / "Acme Corp.md"
    fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["status"] == "Applied"
    assert fm["salary"] == "€120K"
    assert fm["score"] == 90


def test_update_status_moves_board_card(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    app = _make_app()
    tracker.create(app)

    app.status = Status.APPLIED
    tracker.update(app)

    board_text = board.read_text(encoding="utf-8")
    applied_pos = board_text.index("## Applied")
    card_pos = board_text.index("[[companies/Acme Corp|Acme Corp]]")
    followup_pos = board_text.index("## Followed-Up")
    assert applied_pos < card_pos < followup_pos


def test_update_missing_file(tmp_path):
    """update() on a non-existent file should not crash."""
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.update(_make_app())  # file doesn't exist — no crash


# ---------------------------------------------------------------------------
# ObsidianTracker.find_by_name
# ---------------------------------------------------------------------------


def test_find_by_name_returns_application(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app(score=77, start_date=date(2026, 3, 1)))

    app = tracker.find_by_name("Acme Corp")
    assert app is not None
    assert app.name == "Acme Corp"
    assert app.position == "Staff Engineer"
    assert app.status == Status.TARGETED


def test_find_by_name_missing(tmp_path):
    tracker = _make_tracker(tmp_path)
    assert tracker.find_by_name("Nonexistent Co") is None


# ---------------------------------------------------------------------------
# ObsidianTracker.list_all
# ---------------------------------------------------------------------------


def test_list_all_counts(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    for name in ["Alpha Corp", "Beta Inc", "Gamma Ltd"]:
        tracker.create(_make_app(name=name))

    apps = tracker.list_all()
    assert len(apps) == 3
    names = {a.name for a in apps}
    assert "Alpha Corp" in names
    assert "Beta Inc" in names
    assert "Gamma Ltd" in names


def test_list_all_empty(tmp_path):
    tracker = _make_tracker(tmp_path)
    assert tracker.list_all() == []


# ---------------------------------------------------------------------------
# ObsidianTracker.set_highlights / set_research / set_contacts
# ---------------------------------------------------------------------------


def test_set_highlights_replaces_section(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.set_highlights("Acme Corp", ["Old bullet"])
    tracker.set_highlights("Acme Corp", ["New bullet 1", "New bullet 2"])

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "- New bullet 1" in text
    assert "- New bullet 2" in text
    assert "Old bullet" not in text


def test_set_research_replaces_section(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.set_research("Acme Corp", ["Finding A"])
    tracker.set_research("Acme Corp", ["Finding B"])

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "Finding B" in text
    assert "Finding A" not in text


def test_set_contacts_replaces_section(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    contacts = [Contact(name="Jane Smith", title="VP Eng", linkedin="https://li.com/jane")]
    tracker.set_contacts("Acme Corp", contacts)

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "Jane Smith" in text
    assert "VP Eng" in text


# ---------------------------------------------------------------------------
# ObsidianTracker.add_interview_link
# ---------------------------------------------------------------------------


def test_add_interview_link_appends(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_interview_link("Acme Corp", "2026-03-15-Jane-Smith.md", "Jane Smith · Technical")

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "[[2026-03-15-Jane-Smith|Jane Smith · Technical]]" in text


def test_add_interview_link_no_duplicate(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_interview_link("Acme Corp", "2026-03-15-Jane-Smith.md", "Jane Smith")
    tracker.add_interview_link("Acme Corp", "2026-03-15-Jane-Smith.md", "Jane Smith")

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    assert text.count("[[2026-03-15-Jane-Smith|Jane Smith]]") == 1


def test_add_interview_link_multiple(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_interview_link("Acme Corp", "2026-03-01-Alice.md", "Alice · Phone Screen")
    tracker.add_interview_link("Acme Corp", "2026-03-15-Bob.md", "Bob · Technical")

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "[[2026-03-01-Alice|Alice · Phone Screen]]" in text
    assert "[[2026-03-15-Bob|Bob · Technical]]" in text


# ---------------------------------------------------------------------------
# ObsidianTracker.add_documents_section
# ---------------------------------------------------------------------------


def test_add_documents_section_writes_links(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_documents_section("Acme Corp", "ACME-CORP-CV", "ACME-CORP-CL")

    text = (tmp_path / "companies" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "[[ACME-CORP-CV|CV]]" in text
    assert "[[ACME-CORP-CL|Cover Letter]]" in text
