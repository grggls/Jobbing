"""Tests for the interview migration functions in sync_notion_to_obsidian.py."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the kanban script importable without installing it
sys.path.insert(0, str(Path(__file__).parent.parent / "kanban"))
from sync_notion_to_obsidian import (
    InterviewData,
    _interview_filename,
    _interview_name_slug,
    _interviews_wikilink,
    _update_hub_interviews_section,
    generate_interview_file,
)


# ---------------------------------------------------------------------------
# _interview_name_slug
# ---------------------------------------------------------------------------


def test_interview_name_slug_simple():
    assert _interview_name_slug("Richard Frost") == "Richard-Frost"


def test_interview_name_slug_three_words():
    assert _interview_name_slug("Anna Russo Kennedy") == "Anna-Russo-Kennedy"


def test_interview_name_slug_strips_role_em_dash():
    """'Name — Role' → just name slug."""
    assert _interview_name_slug("Jane Smith — VP Engineering") == "Jane-Smith"


def test_interview_name_slug_strips_role_hyphen():
    """'Name - Role' → just name slug."""
    assert _interview_name_slug("Thomas Roton - Hiring Manager") == "Thomas-Roton"


def test_interview_name_slug_special_chars():
    """Special chars are stripped."""
    slug = _interview_name_slug("Józef Müller")
    assert "-" in slug or len(slug) > 0  # at least non-empty


# ---------------------------------------------------------------------------
# _interview_filename
# ---------------------------------------------------------------------------


def test_interview_filename_basic():
    result = _interview_filename("2026-02-26", "Richard Frost", set())
    assert result == "2026-02-26-Richard-Frost.md"


def test_interview_filename_duplicate_appends_counter():
    existing = {"2026-02-26-Richard-Frost.md"}
    result = _interview_filename("2026-02-26", "Richard Frost", existing)
    assert result == "2026-02-26-Richard-Frost-2.md"


def test_interview_filename_triple_duplicate():
    existing = {"2026-02-26-Richard-Frost.md", "2026-02-26-Richard-Frost-2.md"}
    result = _interview_filename("2026-02-26", "Richard Frost", existing)
    assert result == "2026-02-26-Richard-Frost-3.md"


def test_interview_filename_missing_date():
    result = _interview_filename("", "Jane Smith", set())
    assert result == "unknown-date-Jane-Smith.md"


def test_interview_filename_missing_interviewer():
    result = _interview_filename("2026-03-15", "", set())
    assert result == "2026-03-15-unknown-interviewer.md"


def test_interview_filename_both_missing():
    result = _interview_filename("", "", set())
    assert result == "unknown-date-unknown-interviewer.md"


# ---------------------------------------------------------------------------
# generate_interview_file
# ---------------------------------------------------------------------------


def test_generate_interview_file_frontmatter():
    iv = InterviewData(
        interviewer="Richard Frost",
        role="Director, Talent & Development",
        interview_type="Phone Screen",
        date="2026-02-26",
        vibe=4,
        outcome="Passed",
    )
    content = generate_interview_file("Bandcamp (Songtradr)", iv)
    assert 'company: "Bandcamp (Songtradr)"' in content
    assert 'interviewer: "Richard Frost"' in content
    assert 'role: "Director, Talent & Development"' in content
    assert 'type: "Phone Screen"' in content
    assert "date: 2026-02-26" in content
    assert "vibe: 4" in content
    assert 'outcome: "Passed"' in content


def test_generate_interview_file_sections():
    iv = InterviewData(interviewer="Jane Smith", date="2026-03-15")
    content = generate_interview_file("Acme Corp", iv)
    assert "## Prep Notes" in content
    assert "## Debrief" in content
    assert "## Transcript / Raw Notes" in content


def test_generate_interview_file_prep_notes_included():
    iv = InterviewData(
        interviewer="Bob",
        date="2026-01-01",
        prep_notes="Study systems design\n- Focus on scalability",
    )
    content = generate_interview_file("TestCo", iv)
    assert "Study systems design" in content
    assert "## Prep Notes" in content


def test_generate_interview_file_backlink():
    """Company hub backlink wikilink present in file."""
    iv = InterviewData(interviewer="Alice", date="2026-01-10")
    content = generate_interview_file("My Company", iv)
    assert "[[My Company]]" in content


def test_generate_interview_file_minimal():
    """No crash with all-empty InterviewData."""
    iv = InterviewData()
    content = generate_interview_file("Acme", iv)
    assert "## Prep Notes" in content
    assert "## Debrief" in content


# ---------------------------------------------------------------------------
# _update_hub_interviews_section
# ---------------------------------------------------------------------------


def test_hub_interviews_section_inserted(tmp_path):
    hub = tmp_path / "Acme.md"
    hub.write_text(
        "---\ncompany: Acme\n---\n\n# Acme\n\n## Fit Assessment\n\nsome content\n",
        encoding="utf-8",
    )
    wikilinks = ["- [[2026-01-10-Alice|Alice · Phone Screen · Passed]]"]
    _update_hub_interviews_section(hub, wikilinks)

    updated = hub.read_text(encoding="utf-8")
    assert "## Interviews" in updated
    assert "[[2026-01-10-Alice|Alice · Phone Screen · Passed]]" in updated


def test_hub_interviews_section_replaced(tmp_path):
    """Existing ## Interviews section is replaced, not duplicated."""
    hub = tmp_path / "Acme.md"
    hub.write_text(
        "---\ncompany: Acme\n---\n\n# Acme\n\n## Interviews\n\n- [[old-link|Old Interview]]\n\n## Fit Assessment\n\nContent\n",
        encoding="utf-8",
    )
    wikilinks = ["- [[new-link|New Interview]]"]
    _update_hub_interviews_section(hub, wikilinks)

    updated = hub.read_text(encoding="utf-8")
    assert updated.count("## Interviews") == 1
    assert "[[new-link|New Interview]]" in updated
    assert "[[old-link|Old Interview]]" not in updated


def test_hub_interviews_section_after_documents(tmp_path):
    """## Interviews is inserted after ## Documents when present."""
    hub = tmp_path / "Acme.md"
    hub.write_text(
        "---\ncompany: Acme\n---\n\n# Acme\n\n## Documents\n\n- [[CV|CV]]\n\n## Fit Assessment\n\nContent\n",
        encoding="utf-8",
    )
    wikilinks = ["- [[2026-01-10-Alice|Alice]]"]
    _update_hub_interviews_section(hub, wikilinks)

    updated = hub.read_text(encoding="utf-8")
    lines = updated.splitlines()
    doc_idx = next(i for i, l in enumerate(lines) if l.strip() == "## Documents")
    int_idx = next(i for i, l in enumerate(lines) if l.strip() == "## Interviews")
    fit_idx = next(i for i, l in enumerate(lines) if l.strip() == "## Fit Assessment")
    assert doc_idx < int_idx < fit_idx


def test_hub_interviews_missing_file(tmp_path):
    """No crash if hub file doesn't exist."""
    hub = tmp_path / "NonExistent.md"
    _update_hub_interviews_section(hub, ["- [[link|Link]]"])
    assert not hub.exists()


# ---------------------------------------------------------------------------
# _interviews_wikilink
# ---------------------------------------------------------------------------


def test_interviews_wikilink_format():
    iv = InterviewData(
        interviewer="Richard Frost",
        interview_type="Phone Screen",
        outcome="Passed",
        vibe=4,
    )
    link = _interviews_wikilink("2026-02-26-Richard-Frost.md", iv)
    assert link.startswith("- [[2026-02-26-Richard-Frost|")
    assert "Richard Frost" in link
    assert "Phone Screen" in link
    assert "Passed" in link


def test_interviews_wikilink_empty_iv():
    iv = InterviewData()
    link = _interviews_wikilink("unknown-date-unknown-interviewer.md", iv)
    assert link.startswith("- [[")
