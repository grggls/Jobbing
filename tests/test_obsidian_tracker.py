"""Tests for ObsidianTracker backend."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

from jobbing.models import Application, Contact, ScoringResult, Status
from jobbing.tracker.obsidian import (
    ObsidianTracker,
    _card_lines,
    _ensure_all_frontmatter,
    _ensure_all_sections,
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
        + "\n\n".join(
            f"## {lane}\n"
            for lane in ["Targeted", "Applied", "Followed-Up", "In Progress (Interviewing)", "Done"]
        )
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
    text = '---\ncompany: "Acme"\n---\n'
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
    assert "[[Acme Corp|Acme Corp]]" in lines[0]
    assert "Staff Engineer" in lines[0]
    assert "Score: 88" in lines[1]
    assert "2026-02-26" in lines[1]
    assert lines[1].startswith("\t")


def test_board_card_format_without_score():
    """Cards without a score still get a body line with Score: —."""
    app = _make_app()
    lines = _card_lines(app)
    assert len(lines) == 2
    assert "[[Acme Corp|Acme Corp]]" in lines[0]
    assert "Score: —" in lines[1]
    assert "no date" in lines[1]


def test_board_card_format_with_conclusion():
    """Conclusion text appears between Score and date on the body line."""
    app = _make_app(score=84, start_date=date(2026, 3, 5))
    app.conclusion = "Withdrew"
    lines = _card_lines(app)
    assert len(lines) == 2
    assert "Score: 84" in lines[1]
    assert "Withdrew" in lines[1]
    assert "2026-03-05" in lines[1]
    # Order: Score · Conclusion · Date
    body = lines[1]
    assert body.index("Score: 84") < body.index("Withdrew") < body.index("2026-03-05")


def test_board_card_format_empty_conclusion_excluded():
    """Empty or whitespace-only conclusion is not rendered on the card."""
    app = _make_app(score=80, start_date=date(2026, 3, 1))
    app.conclusion = "  "
    lines = _card_lines(app)
    # Body should be "Score: 80 · 2026-03-01" with no extra separator
    assert lines[1].strip() == "Score: 80 · 2026-03-01"


# ---------------------------------------------------------------------------
# ObsidianTracker.create
# ---------------------------------------------------------------------------


def test_create_writes_frontmatter(tmp_path):
    tracker = _make_tracker(tmp_path)
    app = _make_app(score=75, start_date=date(2026, 1, 10))
    tracker.create(app)

    path = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    assert path.is_file()
    fm = _parse_frontmatter(path.read_text(encoding="utf-8"))
    assert fm["company"] == "Acme Corp"
    assert fm["position"] == "Staff Engineer"
    assert fm["status"] == "Targeted"
    assert fm["score"] == 75


def test_create_scaffolds_sections(tmp_path):
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    for section in [
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
    ]:
        assert f"## {section}" in text


def test_create_adds_board_card(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())

    board_text = board.read_text(encoding="utf-8")
    assert "[[Acme Corp|Acme Corp]]" in board_text
    # Card should be in Targeted lane
    targeted_pos = board_text.index("## Targeted")
    card_pos = board_text.index("[[Acme Corp|Acme Corp]]")
    applied_pos = board_text.index("## Applied")
    assert targeted_pos < card_pos < applied_pos


def test_create_idempotent(tmp_path):
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    app = _make_app()
    tracker.create(app)
    # Add some content to a section
    path = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    _replace_section(path, "Fit Assessment", ["Great fit"])
    # Re-create should not wipe the section
    tracker.create(app)
    text = path.read_text(encoding="utf-8")
    assert "Great fit" in text
    # Board should not have duplicates
    board_text = board.read_text(encoding="utf-8")
    assert board_text.count("[[Acme Corp|Acme Corp]]") == 1


def test_create_no_board_file(tmp_path):
    """create() should not crash if board file doesn't exist."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    path = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    assert path.is_file()


# ---------------------------------------------------------------------------
# ObsidianTracker.update
# ---------------------------------------------------------------------------


def test_update_frontmatter_fields(tmp_path):
    tracker = _make_tracker(tmp_path)
    app = _make_app()
    tracker.create(app)

    app.status = Status.APPLIED
    app.salary = "€120K"
    app.scoring = ScoringResult(score=90, reasoning="")
    tracker.update(app)

    path = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
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
    card_pos = board_text.index("[[Acme Corp|Acme Corp]]")
    followup_pos = board_text.index("## Followed-Up")
    assert applied_pos < card_pos < followup_pos


def test_update_missing_file(tmp_path):
    """update() on a non-existent file should not crash."""
    tracker = _make_tracker(tmp_path)
    tracker.update(_make_app())  # file doesn't exist — no crash


# ---------------------------------------------------------------------------
# ObsidianTracker.find_by_name
# ---------------------------------------------------------------------------


def test_find_by_name_returns_application(tmp_path):
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
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.set_highlights("Acme Corp", ["Old bullet"])
    tracker.set_highlights("Acme Corp", ["New bullet 1", "New bullet 2"])

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "- New bullet 1" in text
    assert "- New bullet 2" in text
    assert "Old bullet" not in text


def test_set_research_replaces_section(tmp_path):
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.set_research("Acme Corp", ["Finding A"])
    tracker.set_research("Acme Corp", ["Finding B"])

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "Finding B" in text
    assert "Finding A" not in text


def test_set_contacts_replaces_section(tmp_path):
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    contacts = [Contact(name="Jane Smith", title="VP Eng", linkedin="https://li.com/jane")]
    tracker.set_contacts("Acme Corp", contacts)

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "Jane Smith" in text
    assert "VP Eng" in text


# ---------------------------------------------------------------------------
# ObsidianTracker.add_interview_link
# ---------------------------------------------------------------------------


def test_add_interview_link_appends(tmp_path):
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_interview_link("Acme Corp", "2026-03-15-Jane-Smith.md", "Jane Smith · Technical")

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "[[2026-03-15-Jane-Smith|Jane Smith · Technical]]" in text


def test_add_interview_link_no_duplicate(tmp_path):
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_interview_link("Acme Corp", "2026-03-15-Jane-Smith.md", "Jane Smith")
    tracker.add_interview_link("Acme Corp", "2026-03-15-Jane-Smith.md", "Jane Smith")

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    assert text.count("[[2026-03-15-Jane-Smith|Jane Smith]]") == 1


def test_add_interview_link_multiple(tmp_path):
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_interview_link("Acme Corp", "2026-03-01-Alice.md", "Alice · Phone Screen")
    tracker.add_interview_link("Acme Corp", "2026-03-15-Bob.md", "Bob · Technical")

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "[[2026-03-01-Alice|Alice · Phone Screen]]" in text
    assert "[[2026-03-15-Bob|Bob · Technical]]" in text


# ---------------------------------------------------------------------------
# ObsidianTracker.add_documents_section
# ---------------------------------------------------------------------------


def test_add_documents_section_writes_links(tmp_path):
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    tracker.add_documents_section("Acme Corp", "ACME-CORP-CV", "ACME-CORP-CL")

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    assert "[[ACME-CORP-CV|CV]]" in text
    assert "[[ACME-CORP-CL|Cover Letter]]" in text


# ---------------------------------------------------------------------------
# Hub frontmatter completeness (_scaffold_hub always emits all required fields)
# ---------------------------------------------------------------------------


REQUIRED_FIELDS = [
    "company",
    "position",
    "status",
    "date",
    "url",
    "environment",
    "salary",
    "focus",
    "vision",
    "mission",
    "score",
    "conclusion",
]


def test_scaffold_hub_emits_all_required_fields(tmp_path):
    """New hub files must contain all required frontmatter fields."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())

    text = (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)
    for field in REQUIRED_FIELDS:
        assert field in fm, f"Missing required frontmatter field: {field!r}"


def test_scaffold_hub_emits_vision_and_mission(tmp_path):
    """Specifically check that vision and mission are always present."""
    tracker = _make_tracker(tmp_path)
    app = Application(
        name="Acme Corp",
        position="Staff Engineer",
        vision="Build the future",
        mission="Help developers",
    )
    tracker.create(app)

    fm = _parse_frontmatter(
        (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    )
    assert fm["vision"] == "Build the future"
    assert fm["mission"] == "Help developers"


def test_scaffold_hub_emits_vision_and_mission_when_empty(tmp_path):
    """vision and mission appear even when not set."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())

    fm = _parse_frontmatter(
        (tmp_path / "companies" / "Acme Corp" / "Acme Corp.md").read_text(encoding="utf-8")
    )
    assert "vision" in fm
    assert "mission" in fm


# ---------------------------------------------------------------------------
# find_by_name restores score from frontmatter
# ---------------------------------------------------------------------------


def test_find_by_name_restores_score(tmp_path):
    """find_by_name should hydrate scoring from the score: frontmatter field."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app(score=83))

    app = tracker.find_by_name("Acme Corp")
    assert app is not None
    assert app.scoring is not None
    assert app.scoring.score == 83


def test_find_by_name_no_score_returns_none_scoring(tmp_path):
    """find_by_name with score=0 should not set scoring (score=0 means unscored)."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app(score=None))  # no score set

    app = tracker.find_by_name("Acme Corp")
    assert app is not None
    assert app.scoring is None


# ---------------------------------------------------------------------------
# validate_hubs
# ---------------------------------------------------------------------------


def _make_tracker_with_companies(tmp_path: Path) -> ObsidianTracker:
    """Tracker — same as _make_tracker, kept for backward compat in validate/sync tests."""
    return _make_tracker(tmp_path)


def test_validate_hubs_clean(tmp_path):
    """A freshly created hub with all fields set should produce no issues."""
    _make_board(tmp_path)
    tracker = _make_tracker_with_companies(tmp_path)
    app = Application(
        name="Acme Corp",
        position="Staff Engineer",
        vision="v",
        mission="m",
        url="https://example.com",
        salary="€100K",
        environment=["Remote"],
        focus=["SaaS"],
    )
    app.scoring = ScoringResult(score=80, reasoning="")
    tracker.create(app)

    issues = tracker.validate_hubs()
    # The only issues allowed are CL date staleness (no JSON file exists here)
    non_date_issues = [
        i
        for i in issues
        if "missing frontmatter" in i or "mismatch" in i or "not found on board" in i
    ]
    assert non_date_issues == [], non_date_issues


def test_validate_hubs_flags_missing_fields(tmp_path):
    """Hub file missing vision/mission should be flagged."""
    _make_board(tmp_path)
    tracker = _make_tracker_with_companies(tmp_path)

    # Write a hub manually with missing fields in per-company subdir
    hub_dir = tmp_path / "companies" / "Bad Corp"
    hub_dir.mkdir(parents=True, exist_ok=True)
    hub = hub_dir / "Bad Corp.md"
    hub.write_text(
        '---\ncompany: "Bad Corp"\nstatus: "Targeted"\n---\n\n# Bad Corp\n',
        encoding="utf-8",
    )
    # Add to board
    board = tmp_path / "Job Tracker.md"
    board_text = board.read_text(encoding="utf-8")
    board.write_text(
        board_text.replace(
            "## Targeted\n",
            "## Targeted\n\n- [ ] [[Bad Corp|Bad Corp]]\n",
        ),
        encoding="utf-8",
    )

    issues = tracker.validate_hubs()
    missing = [i for i in issues if "Bad Corp" in i and "missing" in i]
    assert any("vision" in i for i in missing)
    assert any("mission" in i for i in missing)


def test_validate_hubs_flags_status_mismatch(tmp_path):
    """Hub with status=Applied but card in Targeted lane should be flagged."""
    _make_board(tmp_path)
    tracker = _make_tracker_with_companies(tmp_path)
    app = Application(
        name="Mismatch Co",
        position="SRE",
        vision="v",
        mission="m",
        url="https://x.com",
        salary="€90K",
    )
    app.scoring = ScoringResult(score=70, reasoning="")
    tracker.create(app)

    # Change hub status to Applied but leave card in Targeted
    hub = tmp_path / "companies" / "Mismatch Co" / "Mismatch Co.md"
    _write_frontmatter(hub, {"status": "Applied"})

    issues = tracker.validate_hubs()
    mismatch = [i for i in issues if "Mismatch Co" in i and "mismatch" in i]
    assert len(mismatch) == 1
    assert "Applied" in mismatch[0]
    assert "Targeted" in mismatch[0]


def test_validate_hubs_flags_score_mismatch(tmp_path):
    """Hub score differing from board card score should be flagged."""
    _make_board(tmp_path)
    tracker = _make_tracker_with_companies(tmp_path)
    app = Application(
        name="Score Co", position="SRE", vision="v", mission="m", url="https://x.com", salary="€90K"
    )
    app.scoring = ScoringResult(score=75, reasoning="")
    tracker.create(app)

    # Change hub score to something different
    hub = tmp_path / "companies" / "Score Co" / "Score Co.md"
    _write_frontmatter(hub, {"score": 99})

    issues = tracker.validate_hubs()
    score_issues = [i for i in issues if "Score Co" in i and "score mismatch" in i]
    assert len(score_issues) == 1


def test_validate_hubs_flags_stale_cl_date(tmp_path):
    """CL date older than 7 days should be flagged."""
    import json

    _make_board(tmp_path)
    tracker = _make_tracker_with_companies(tmp_path)
    app = Application(
        name="Old Date Co",
        position="SRE",
        vision="v",
        mission="m",
        url="https://x.com",
        salary="€90K",
    )
    app.scoring = ScoringResult(score=70, reasoning="")
    tracker.create(app)

    # Create a JSON file with an old CL date in the per-company dir (new structure)
    co_dir = tmp_path / "companies" / "Old Date Co"
    (co_dir / "old date co.json").write_text(
        json.dumps({"cl": {"date": "January 1, 2026"}}), encoding="utf-8"
    )

    issues = tracker.validate_hubs()
    stale = [i for i in issues if "Old Date Co" in i and "CL date" in i]
    assert len(stale) == 1
    assert "days old" in stale[0]


# ---------------------------------------------------------------------------
# sync_board
# ---------------------------------------------------------------------------


def test_sync_board_moves_misplaced_cards(tmp_path):
    """sync_board should move a card to the correct lane based on hub status."""
    board = _make_board(tmp_path)
    tracker = _make_tracker_with_companies(tmp_path)
    app = _make_app(score=80)
    tracker.create(app)

    # Manually update hub status without touching the board
    hub = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    _write_frontmatter(hub, {"status": "Applied"})

    # Board still shows Targeted
    board_text = board.read_text(encoding="utf-8")
    targeted_pos = board_text.index("## Targeted")
    card_pos = board_text.index("[[Acme Corp|Acme Corp]]")
    applied_pos = board_text.index("## Applied")
    assert targeted_pos < card_pos < applied_pos  # still in Targeted

    # After sync, card should be in Applied
    tracker.sync_board()
    board_text = board.read_text(encoding="utf-8")
    applied_pos = board_text.index("## Applied")
    card_pos = board_text.index("[[Acme Corp|Acme Corp]]")
    followup_pos = board_text.index("## Followed-Up")
    assert applied_pos < card_pos < followup_pos


def test_sync_board_updates_score_on_card(tmp_path):
    """sync_board should update the score shown on the board card."""
    board = _make_board(tmp_path)
    tracker = _make_tracker_with_companies(tmp_path)
    tracker.create(_make_app(score=70))

    # Update hub score directly
    hub = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    _write_frontmatter(hub, {"score": 90})

    tracker.sync_board()

    board_text = board.read_text(encoding="utf-8")
    assert "Score: 90" in board_text
    assert "Score: 70" not in board_text


# ---------------------------------------------------------------------------
# _normalize_company_name (fuzzy hub lookup)
# ---------------------------------------------------------------------------


def test_normalize_company_name():
    from jobbing.cli import _normalize_company_name

    assert _normalize_company_name("Talentedge (Anonymous IoT Client)") == "talentedge"
    assert _normalize_company_name("Bandcamp (Songtradr)") == "bandcamp"
    assert _normalize_company_name("Acme Corp") == "acme corp"
    assert _normalize_company_name("UPPER CASE") == "upper case"
    assert (
        _normalize_company_name("Multi (Paren) Corp") == "multi (paren) corp"
    )  # only strips trailing


def test_update_hub_documents_fuzzy_lookup(tmp_path, monkeypatch):
    """jobbing pdf talentedge should find hub 'Talentedge (Anonymous IoT Client)'."""
    from jobbing.cli import _update_hub_documents

    # Set up kanban companies dir with a compound-name per-company subdir
    companies_dir = tmp_path / "kanban" / "companies"
    company_name = "Talentedge (Anonymous IoT Client)"
    company_dir = companies_dir / company_name
    company_dir.mkdir(parents=True)
    hub = company_dir / f"{company_name}.md"
    hub.write_text(
        f'---\ncompany: "{company_name}"\nstatus: "Targeted"\n---\n\n## Documents\n',
        encoding="utf-8",
    )

    config = MagicMock()
    config.kanban_companies_dir = companies_dir
    config.project_dir = tmp_path
    config.tracker_backend = "obsidian"
    config.kanban_dir = tmp_path / "kanban"
    config.kanban_board_path = tmp_path / "kanban" / "Job Tracker.md"

    cv = tmp_path / "TALENTEDGE-CV.pdf"
    cl = tmp_path / "TALENTEDGE-CL.pdf"
    cv.write_bytes(b"%PDF-1.4 fake")
    cl.write_bytes(b"%PDF-1.4 fake")

    _update_hub_documents("talentedge", [cv, cl], config)

    text = hub.read_text(encoding="utf-8")
    assert "[[TALENTEDGE-CV|CV]]" in text
    assert "[[TALENTEDGE-CL|Cover Letter]]" in text


def test_update_hub_documents_removes_obsidian_stubs(tmp_path):
    """jobbing pdf should delete 0-byte stub .md files left by Obsidian."""
    from jobbing.cli import _update_hub_documents

    companies_dir = tmp_path / "kanban" / "companies"
    company_dir = companies_dir / "Acme Corp"
    company_dir.mkdir(parents=True)
    hub = company_dir / "Acme Corp.md"
    hub.write_text(
        '---\ncompany: "Acme Corp"\nstatus: "Targeted"\n---\n\n## Documents\n',
        encoding="utf-8",
    )

    config = MagicMock()
    config.kanban_companies_dir = companies_dir
    config.project_dir = tmp_path
    config.tracker_backend = "obsidian"
    config.kanban_dir = tmp_path / "kanban"
    config.kanban_board_path = tmp_path / "kanban" / "Job Tracker.md"

    cv = tmp_path / "ACME-CORP-CV.pdf"
    cl = tmp_path / "ACME-CORP-CL.pdf"
    cv.write_bytes(b"%PDF-1.4 fake")
    cl.write_bytes(b"%PDF-1.4 fake")

    # Simulate Obsidian stubs (0-byte .md files at vault root)
    cv_stub = tmp_path / "ACME-CORP-CV.md"
    cl_stub = tmp_path / "ACME-CORP-CL.md"
    cv_stub.write_text("")
    cl_stub.write_text("")

    _update_hub_documents("Acme Corp", [cv, cl], config)

    assert not cv_stub.exists(), "CV stub should have been removed"
    assert not cl_stub.exists(), "CL stub should have been removed"


# ---------------------------------------------------------------------------
# _ensure_all_sections / _ensure_all_frontmatter
# ---------------------------------------------------------------------------


def test_ensure_all_sections_adds_missing(tmp_path):
    """Missing sections are appended to an existing hub file."""
    f = tmp_path / "test.md"
    f.write_text(
        '---\ncompany: "X"\n---\n\n# X\n\n## Documents\n\n## Fit Assessment\n',
        encoding="utf-8",
    )
    added = _ensure_all_sections(f)
    text = f.read_text(encoding="utf-8")
    # Documents and Fit Assessment already existed
    assert "Documents" not in added
    assert "Fit Assessment" not in added
    # Conclusion and others should have been added
    assert "Conclusion" in added
    assert "## Conclusion" in text
    assert "## Interviews" in text
    # Existing content preserved
    assert "## Documents" in text


def test_ensure_all_sections_noop_when_complete(tmp_path):
    """No changes when all sections already exist."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    path = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    added = _ensure_all_sections(path)
    assert added == []


def test_ensure_all_frontmatter_adds_missing(tmp_path):
    """Missing frontmatter fields are backfilled with defaults."""
    f = tmp_path / "test.md"
    f.write_text('---\ncompany: "X"\nstatus: "Targeted"\n---\n\n# X\n', encoding="utf-8")
    added = _ensure_all_frontmatter(f)
    fm = _parse_frontmatter(f.read_text(encoding="utf-8"))
    assert "conclusion" in added
    assert "vision" in added
    assert "conclusion" in fm
    assert "vision" in fm
    # Existing fields preserved
    assert fm["company"] == "X"
    assert fm["status"] == "Targeted"


def test_ensure_all_frontmatter_noop_when_complete(tmp_path):
    """No changes when all frontmatter fields already exist."""
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app())
    path = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    added = _ensure_all_frontmatter(path)
    assert added == []


def test_create_backfills_existing_hub(tmp_path):
    """create() on an existing hub with missing sections/fields backfills them."""
    _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)

    # Write a minimal hub manually (missing most sections and fields)
    hub_dir = tmp_path / "companies" / "Sparse Co"
    hub_dir.mkdir(parents=True)
    hub = hub_dir / "Sparse Co.md"
    hub.write_text(
        '---\ncompany: "Sparse Co"\nstatus: "Targeted"\n---\n\n# Sparse Co\n\n## Documents\n',
        encoding="utf-8",
    )

    # create() should backfill
    app = _make_app(name="Sparse Co")
    _, sections = tracker.create(app)

    text = hub.read_text(encoding="utf-8")
    fm = _parse_frontmatter(text)

    # Frontmatter backfilled
    assert "conclusion" in fm
    assert "vision" in fm
    assert "score" in fm

    # Sections backfilled
    assert "## Conclusion" in text
    assert "## Interviews" in text
    assert "## Fit Assessment" in text

    # Sections report includes backfill info
    assert any("backfilled" in s for s in sections)


# ---------------------------------------------------------------------------
# sync_from_board (Board → Hub reverse sync)
# ---------------------------------------------------------------------------


def test_sync_from_board_updates_hub_status(tmp_path):
    """Dragging a card to a new lane on the board should update hub frontmatter."""
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    app = _make_app(score=84, start_date=date(2026, 3, 5))
    tracker.create(app)

    # Verify card is in Targeted
    hub = tmp_path / "companies" / "Acme Corp" / "Acme Corp.md"
    fm = _parse_frontmatter(hub.read_text(encoding="utf-8"))
    assert fm["status"] == "Targeted"

    # Simulate dragging card to Done: manually move the card in the board file
    board_text = board.read_text(encoding="utf-8")
    # Remove from Targeted
    card_lines = _card_lines(app)
    for cl in card_lines:
        board_text = board_text.replace(cl + "\n", "")
    # Add to Done
    board_text = board_text.replace(
        "## Done\n",
        "## Done\n\n" + "\n".join(card_lines) + "\n",
    )
    board.write_text(board_text, encoding="utf-8")

    # Run reverse sync
    changes = tracker.sync_from_board()
    assert len(changes) == 1
    assert "Acme Corp" in changes[0]
    assert "Done" in changes[0]

    # Hub frontmatter should now say Done
    fm = _parse_frontmatter(hub.read_text(encoding="utf-8"))
    assert fm["status"] == "Done"


def test_sync_from_board_noop_when_matched(tmp_path):
    """No changes when board and hub already agree."""
    _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)
    tracker.create(_make_app(score=80))

    changes = tracker.sync_from_board()
    assert changes == []


def test_sync_from_board_skips_missing_hubs(tmp_path):
    """Cards on the board without a hub file are silently skipped."""
    board = _make_board(tmp_path)
    tracker = _make_tracker(tmp_path)

    # Add a card to the board manually with no hub file
    board_text = board.read_text(encoding="utf-8")
    board_text = board_text.replace(
        "## Targeted\n",
        "## Targeted\n\n- [ ] [[Ghost Co|Ghost Co]] — Engineer\n\t  Score: — · no date\n",
    )
    board.write_text(board_text, encoding="utf-8")

    changes = tracker.sync_from_board()
    assert changes == []
