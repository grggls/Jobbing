"""Tests for jobbing.cli — argument parsing, command dispatch, and handler functions."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from jobbing.cli import (
    VALID_LINKEDIN,
    VALID_STATUSES,
    _args_to_application,
    _build_parser,
    _cmd_pdf,
    _cmd_scan,
    _preview_application,
    _scan_bookmarks,
    _scan_existing,
    _scan_fetch,
    _track_create,
    _track_followup,
    _track_highlights,
    _track_outreach,
    _track_research,
    _track_update,
    main,
)
from jobbing.config import Config
from jobbing.models import Application, LinkedInStatus, Status

# ---------------------------------------------------------------------------
# Patch targets
# ---------------------------------------------------------------------------

_PATCH_GET_TRACKER = "jobbing.tracker.get_tracker"
_PATCH_PDF_GENERATOR = "jobbing.pdf.PDFGenerator"
_PATCH_COMPANY_DATA = "jobbing.models.CompanyData.from_json_file"
_PATCH_PARSE_BOOKMARKS = "jobbing.scanner.parse_bookmarks"
_PATCH_FETCH_BOARDS = "jobbing.scanner.fetch_boards"
_PATCH_SAVE_FETCH = "jobbing.scanner.save_fetch_results"

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def config(tmp_path: Path) -> Config:
    """Minimal config pointing at a temp directory."""
    (tmp_path / ".env").write_text('NOTION_API_KEY="test-key"\n')
    (tmp_path / "kanban" / "companies").mkdir(parents=True)
    (tmp_path / "notion_queue").mkdir()
    (tmp_path / "notion_queue_results").mkdir()
    (tmp_path / "scan_results").mkdir()
    return Config.load(project_dir=tmp_path)


@pytest.fixture()
def parser() -> Any:
    return _build_parser()


@pytest.fixture()
def mock_tracker() -> MagicMock:
    tracker = MagicMock()
    tracker.create.return_value = ("Acme", ["Job Description", "Fit Assessment"])
    tracker.list_all.return_value = [
        Application(name="Acme", position="Senior Eng", status=Status.APPLIED),
        Application(name="Globex", position="Staff Eng", status=Status.TARGETED),
    ]
    return tracker


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_valid_statuses_contains_all_enum_values(self) -> None:
        assert set(VALID_STATUSES) == {s.value for s in Status}

    def test_valid_linkedin_contains_all_enum_values(self) -> None:
        assert set(VALID_LINKEDIN) == {ls.value for ls in LinkedInStatus}


# ---------------------------------------------------------------------------
# Argument parser construction
# ---------------------------------------------------------------------------


class TestBuildParser:
    """Verify _build_parser produces a parser with correct subcommands."""

    def test_track_subcommand_exists(self, parser: Any) -> None:
        args = parser.parse_args(["track", "create", "--name", "Acme"])
        assert args.command == "track"
        assert args.track_command == "create"

    def test_track_create_required_name(self, parser: Any) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["track", "create"])

    def test_track_create_all_options(self, parser: Any) -> None:
        args = parser.parse_args(
            [
                "track",
                "create",
                "--name",
                "Acme",
                "--position",
                "Senior Eng",
                "--date",
                "2026-03-08",
                "--url",
                "https://acme.com/job",
                "--status",
                "Applied",
                "--environment",
                "Remote",
                "Hybrid",
                "--salary",
                "120k-150k",
                "--focus",
                "Climate",
                "AI",
                "--vision",
                "Save the world",
                "--mission",
                "Build tools",
                "--linkedin",
                "Yes",
                "--conclusion",
                "Strong fit",
                "--highlights",
                "Led migration",
                "Built platform",
                "--job-description",
                "We are looking for...",
                "--dry-run",
            ]
        )
        assert args.name == "Acme"
        assert args.position == "Senior Eng"
        assert args.date == "2026-03-08"
        assert args.url == "https://acme.com/job"
        assert args.status == "Applied"
        assert args.environment == ["Remote", "Hybrid"]
        assert args.salary == "120k-150k"
        assert args.focus == ["Climate", "AI"]
        assert args.vision == "Save the world"
        assert args.mission == "Build tools"
        assert args.linkedin == "Yes"
        assert args.conclusion == "Strong fit"
        assert args.highlights == ["Led migration", "Built platform"]
        assert args.job_description == "We are looking for..."
        assert args.dry_run is True

    def test_track_update_requires_name(self, parser: Any) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["track", "update"])

    def test_track_update_with_status(self, parser: Any) -> None:
        args = parser.parse_args(["track", "update", "--name", "Acme", "--status", "Applied"])
        assert args.name == "Acme"
        assert args.status == "Applied"

    def test_track_update_invalid_status_rejected(self, parser: Any) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["track", "update", "--name", "Acme", "--status", "InvalidStatus"])

    def test_track_highlights_requires_name_and_highlights(self, parser: Any) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["track", "highlights"])

    def test_track_highlights_valid(self, parser: Any) -> None:
        args = parser.parse_args(
            [
                "track",
                "highlights",
                "--name",
                "Acme",
                "--highlights",
                "Bullet 1",
                "Bullet 2",
            ]
        )
        assert args.name == "Acme"
        assert args.highlights == ["Bullet 1", "Bullet 2"]

    def test_track_research_requires_name(self, parser: Any) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["track", "research", "--research", "Finding"])

    def test_track_research_by_name(self, parser: Any) -> None:
        args = parser.parse_args(["track", "research", "--name", "Acme", "--research", "Finding 1"])
        assert args.name == "Acme"

    def test_track_followup(self, parser: Any) -> None:
        args = parser.parse_args(["track", "followup"])
        assert args.track_command == "followup"
        assert args.threshold is None
        assert args.save is False

    def test_track_followup_with_options(self, parser: Any) -> None:
        args = parser.parse_args(["track", "followup", "--threshold", "7", "--save"])
        assert args.threshold == 7
        assert args.save is True

    def test_track_outreach_requires_name(self, parser: Any) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args(["track", "outreach", "--contacts-json", "contacts.json"])

    def test_track_outreach_valid(self, parser: Any) -> None:
        args = parser.parse_args(
            [
                "track",
                "outreach",
                "--name",
                "Acme",
                "--contacts-json",
                "contacts.json",
            ]
        )
        assert args.name == "Acme"
        assert args.contacts_json == "contacts.json"

    def test_pdf_subcommand(self, parser: Any) -> None:
        args = parser.parse_args(["pdf", "acme"])
        assert args.command == "pdf"
        assert args.company == "acme"
        assert args.cv_only is False
        assert args.cl_only is False

    def test_pdf_cv_only(self, parser: Any) -> None:
        args = parser.parse_args(["pdf", "acme", "--cv-only"])
        assert args.cv_only is True

    def test_pdf_cl_only(self, parser: Any) -> None:
        args = parser.parse_args(["pdf", "acme", "--cl-only"])
        assert args.cl_only is True

    def test_scan_bookmarks(self, parser: Any) -> None:
        args = parser.parse_args(["scan", "bookmarks"])
        assert args.command == "scan"
        assert args.scan_command == "bookmarks"

    def test_scan_bookmarks_with_categories(self, parser: Any) -> None:
        args = parser.parse_args(
            ["scan", "bookmarks", "--categories", "Climate / Impact", "Startup / Tech"]
        )
        assert args.categories == ["Climate / Impact", "Startup / Tech"]

    def test_scan_fetch(self, parser: Any) -> None:
        args = parser.parse_args(["scan", "fetch"])
        assert args.scan_command == "fetch"

    def test_scan_fetch_with_limit(self, parser: Any) -> None:
        args = parser.parse_args(["scan", "fetch", "--limit", "5"])
        assert args.limit == 5

    def test_scan_existing(self, parser: Any) -> None:
        args = parser.parse_args(["scan", "existing"])
        assert args.scan_command == "existing"

    def test_no_subcommand_exits(self, parser: Any) -> None:
        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_queue_subcommand_removed(self, parser: Any) -> None:
        """queue subcommand has been removed."""
        with pytest.raises(SystemExit):
            parser.parse_args(["queue"])


# ---------------------------------------------------------------------------
# _args_to_application
# ---------------------------------------------------------------------------


class TestArgsToApplication:
    def test_minimal_args(self) -> None:
        ns = argparse.Namespace(
            name="Acme",
            position=None,
            date=None,
            url=None,
            status=None,
            environment=None,
            salary=None,
            focus=None,
            vision=None,
            mission=None,
            linkedin=None,
            conclusion=None,
            highlights=None,
            job_description=None,
        )
        app = _args_to_application(ns)
        assert app.name == "Acme"
        assert app.status == Status.TARGETED
        assert app.start_date is None
        assert app.linkedin == LinkedInStatus.NA
        assert app.environment == []
        assert app.focus == []
        assert app.highlights == []

    def test_full_args(self) -> None:
        ns = argparse.Namespace(
            name="Globex",
            position="Staff Eng",
            date="2026-03-01",
            url="https://globex.com/job",
            status="Applied",
            environment=["Remote"],
            salary="150k-180k",
            focus=["AI"],
            vision="Transform logistics",
            mission="Ship fast",
            linkedin="Yes",
            conclusion="Great fit",
            highlights=["Led team of 10"],
            job_description="Looking for a staff engineer...",
        )
        app = _args_to_application(ns)
        assert app.name == "Globex"
        assert app.position == "Staff Eng"
        assert app.start_date == date(2026, 3, 1)
        assert app.status == Status.APPLIED
        assert app.url == "https://globex.com/job"
        assert app.environment == ["Remote"]
        assert app.salary == "150k-180k"
        assert app.focus == ["AI"]
        assert app.vision == "Transform logistics"
        assert app.mission == "Ship fast"
        assert app.linkedin == LinkedInStatus.YES
        assert app.conclusion == "Great fit"
        assert app.highlights == ["Led team of 10"]
        assert app.job_description == "Looking for a staff engineer..."

    def test_missing_attrs_default_gracefully(self) -> None:
        """_args_to_application uses getattr with defaults, so missing attrs are safe."""
        ns = argparse.Namespace(name="Bare")
        app = _args_to_application(ns)
        assert app.name == "Bare"
        assert app.position == ""
        assert app.status == Status.TARGETED


# ---------------------------------------------------------------------------
# _preview_application
# ---------------------------------------------------------------------------


class TestPreviewApplication:
    def test_minimal(self) -> None:
        app = Application(name="Acme")
        preview = _preview_application(app)
        assert preview == {"name": "Acme", "status": "Targeted"}

    def test_includes_all_set_fields(self) -> None:
        app = Application(
            name="Acme",
            position="Senior Eng",
            status=Status.APPLIED,
            start_date=date(2026, 3, 1),
            url="https://acme.com",
            environment=["Remote"],
            salary="120k",
            focus=["Climate"],
            vision="Save planet",
            mission="Build tools",
            highlights=["Led migration"],
            job_description="Short desc",
        )
        preview = _preview_application(app)
        assert preview["name"] == "Acme"
        assert preview["position"] == "Senior Eng"
        assert preview["status"] == "Applied"
        assert preview["start_date"] == "2026-03-01"
        assert preview["url"] == "https://acme.com"
        assert preview["environment"] == ["Remote"]
        assert preview["salary"] == "120k"
        assert preview["focus"] == ["Climate"]
        assert preview["vision"] == "Save planet"
        assert preview["mission"] == "Build tools"
        assert preview["highlights"] == ["Led migration"]
        assert preview["job_description"] == "Short desc"

    def test_long_job_description_truncated(self) -> None:
        long_desc = "x" * 200
        app = Application(name="Acme", job_description=long_desc)
        preview = _preview_application(app)
        assert preview["job_description"] == "x" * 100 + "..."

    def test_exactly_100_char_description_not_truncated(self) -> None:
        desc = "y" * 100
        app = Application(name="Acme", job_description=desc)
        preview = _preview_application(app)
        assert preview["job_description"] == desc

    def test_omits_empty_optional_fields(self) -> None:
        app = Application(name="Acme")
        preview = _preview_application(app)
        assert "position" not in preview
        assert "url" not in preview
        assert "environment" not in preview
        assert "salary" not in preview
        assert "focus" not in preview
        assert "vision" not in preview
        assert "mission" not in preview
        assert "highlights" not in preview
        assert "job_description" not in preview


# ---------------------------------------------------------------------------
# Track command handlers
# ---------------------------------------------------------------------------


class TestTrackCreate:
    def test_creates_entry(
        self,
        config: Config,
        mock_tracker: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ns = argparse.Namespace(
            name="Acme",
            position="Eng",
            date=None,
            url=None,
            status=None,
            environment=None,
            salary=None,
            focus=None,
            vision=None,
            mission=None,
            linkedin=None,
            conclusion=None,
            highlights=None,
            job_description=None,
            dry_run=False,
        )
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_create(ns, config)

        mock_tracker.create.assert_called_once()
        app_arg = mock_tracker.create.call_args[0][0]
        assert app_arg.name == "Acme"
        assert "Acme" in capsys.readouterr().out

    def test_dry_run_prints_preview(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ns = argparse.Namespace(
            name="Acme",
            position="Eng",
            date=None,
            url=None,
            status=None,
            environment=None,
            salary=None,
            focus=None,
            vision=None,
            mission=None,
            linkedin=None,
            conclusion=None,
            highlights=None,
            job_description=None,
            dry_run=True,
        )
        _track_create(ns, config)

        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert parsed["name"] == "Acme"


class TestTrackUpdate:
    def test_updates_entry(
        self,
        config: Config,
        mock_tracker: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ns = argparse.Namespace(
            name="Acme",
            position=None,
            date=None,
            url=None,
            status="Applied",
            environment=None,
            salary=None,
            focus=None,
            vision=None,
            mission=None,
            linkedin=None,
            conclusion=None,
            dry_run=False,
        )
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_update(ns, config)

        mock_tracker.update.assert_called_once()
        app_arg = mock_tracker.update.call_args[0][0]
        assert app_arg.name == "Acme"
        assert app_arg.status == Status.APPLIED
        assert "Updated entry: Acme" in capsys.readouterr().out

    def test_dry_run(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        ns = argparse.Namespace(
            name="Acme",
            position=None,
            date=None,
            url=None,
            status="Done",
            environment=None,
            salary=None,
            focus=None,
            vision=None,
            mission=None,
            linkedin=None,
            conclusion="Rejected",
            dry_run=True,
        )
        _track_update(ns, config)

        parsed = json.loads(capsys.readouterr().out)
        assert parsed["status"] == "Done"


class TestTrackHighlights:
    def test_sets_highlights(
        self,
        config: Config,
        mock_tracker: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ns = argparse.Namespace(
            name="Acme",
            highlights=["Bullet 1", "Bullet 2"],
            dry_run=False,
        )
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_highlights(ns, config)

        mock_tracker.set_highlights.assert_called_once_with("Acme", ["Bullet 1", "Bullet 2"])
        assert "Highlights updated on: Acme" in capsys.readouterr().out

    def test_dry_run(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        ns = argparse.Namespace(
            name="Acme",
            highlights=["Bullet 1"],
            dry_run=True,
        )
        _track_highlights(ns, config)
        parsed = json.loads(capsys.readouterr().out)
        assert parsed["name"] == "Acme"
        assert parsed["highlights"] == ["Bullet 1"]


class TestTrackResearch:
    def test_sets_research_by_name(
        self,
        config: Config,
        mock_tracker: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ns = argparse.Namespace(
            name="Acme",
            research=["Finding 1"],
            dry_run=False,
        )
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_research(ns, config)

        mock_tracker.set_research.assert_called_once_with("Acme", ["Finding 1"])
        assert "Research updated on: Acme" in capsys.readouterr().out

    def test_dry_run(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        ns = argparse.Namespace(
            name="Acme",
            research=["Finding 1"],
            dry_run=True,
        )
        with patch(_PATCH_GET_TRACKER, return_value=MagicMock()):
            _track_research(ns, config)

        parsed = json.loads(capsys.readouterr().out)
        assert parsed["name"] == "Acme"
        assert parsed["research"] == ["Finding 1"]


class TestTrackFollowup:
    def test_no_in_progress_prints_message(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_tracker = MagicMock()
        mock_tracker.list_all.return_value = [
            Application(name="Acme", status=Status.APPLIED),
        ]

        ns = argparse.Namespace(threshold=None, save=False)
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_followup(ns, config)

        assert "No applications currently in progress." in capsys.readouterr().out

    def test_shows_stale_applications(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_tracker = MagicMock()
        mock_tracker.list_all.return_value = [
            Application(
                name="Acme",
                position="Eng",
                status=Status.IN_PROGRESS,
                start_date=date(2025, 1, 1),  # very stale
            ),
        ]

        ns = argparse.Namespace(threshold=5, save=False)
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_followup(ns, config)

        output = capsys.readouterr().out
        assert "Stale" in output
        assert "Acme" in output

    def test_custom_threshold(self, config: Config) -> None:
        mock_tracker = MagicMock()
        mock_tracker.list_all.return_value = []

        ns = argparse.Namespace(threshold=10, save=False)
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_followup(ns, config)

    def test_save_writes_file(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        mock_tracker = MagicMock()
        mock_tracker.list_all.return_value = [
            Application(
                name="Acme",
                position="Eng",
                status=Status.IN_PROGRESS,
                start_date=date(2025, 1, 1),
            ),
        ]

        ns = argparse.Namespace(threshold=5, save=True)
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_followup(ns, config)

        output = capsys.readouterr().out
        assert "Saved to:" in output

        results_dir = config.scan_results_dir
        saved_files = list(results_dir.glob("followup-*.md"))
        assert len(saved_files) == 1


class TestTrackOutreach:
    def test_loads_contacts_and_sets(
        self,
        config: Config,
        mock_tracker: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        contacts_file = tmp_path / "contacts.json"
        contacts_data = [
            {
                "name": "Jane Smith",
                "title": "VP Eng",
                "linkedin": "https://linkedin.com/in/jane",
                "note": "Ex-Google",
                "message": "Hi Jane",
            }
        ]
        contacts_file.write_text(json.dumps(contacts_data))

        ns = argparse.Namespace(
            name="Acme",
            contacts_json=str(contacts_file),
            dry_run=False,
        )
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_outreach(ns, config)

        mock_tracker.set_contacts.assert_called_once()
        app_id_arg, contacts_arg = mock_tracker.set_contacts.call_args[0]
        assert app_id_arg == "Acme"
        assert len(contacts_arg) == 1
        assert contacts_arg[0].name == "Jane Smith"
        assert contacts_arg[0].title == "VP Eng"
        assert "Outreach contacts updated on: Acme" in capsys.readouterr().out

    def test_missing_contacts_json_exits(self, config: Config) -> None:
        ns = argparse.Namespace(
            name="Acme",
            contacts_json=None,
            dry_run=False,
        )
        with pytest.raises(SystemExit, match="1"):
            _track_outreach(ns, config)

    def test_dry_run(
        self,
        config: Config,
        mock_tracker: MagicMock,
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        contacts_file = tmp_path / "contacts.json"
        contacts_data = [{"name": "Jane", "title": "Eng", "linkedin": "url"}]
        contacts_file.write_text(json.dumps(contacts_data))

        ns = argparse.Namespace(
            name="Acme",
            contacts_json=str(contacts_file),
            dry_run=True,
        )
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _track_outreach(ns, config)

        parsed = json.loads(capsys.readouterr().out)
        assert parsed["name"] == "Acme"
        assert parsed["contacts"] == contacts_data


# ---------------------------------------------------------------------------
# PDF command
# ---------------------------------------------------------------------------


class TestCmdPdf:
    def test_generates_pdfs(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        company_dir = config.kanban_companies_dir / "Acme"
        company_dir.mkdir()
        json_file = company_dir / "Acme.json"
        json_file.write_text("{}")

        mock_company_data = MagicMock()
        mock_path1 = MagicMock()
        mock_path1.name = "ACME-CV.pdf"
        mock_path1.stem = "ACME-CV"
        mock_path1.stat.return_value.st_size = 12345
        mock_path2 = MagicMock()
        mock_path2.name = "ACME-CL.pdf"
        mock_path2.stem = "ACME-CL"
        mock_path2.stat.return_value.st_size = 6789

        mock_generator = MagicMock()
        mock_generator.generate.return_value = [mock_path1, mock_path2]

        ns = argparse.Namespace(company="Acme", output_dir=None, cv_only=False, cl_only=False)
        with (
            patch(_PATCH_COMPANY_DATA, return_value=mock_company_data),
            patch(_PATCH_PDF_GENERATOR, return_value=mock_generator),
            patch("jobbing.cli._update_hub_documents"),
        ):
            _cmd_pdf(ns, config)

        output = capsys.readouterr().out
        assert "ACME-CV.pdf" in output
        assert "ACME-CL.pdf" in output
        assert "Done." in output

    def test_missing_json_exits(self, config: Config) -> None:
        ns = argparse.Namespace(
            company="nonexistent", output_dir=None, cv_only=False, cl_only=False
        )
        with pytest.raises(SystemExit, match="1"):
            _cmd_pdf(ns, config)

    def test_cv_only_flag_passed(self, config: Config) -> None:
        company_dir = config.kanban_companies_dir / "Acme"
        company_dir.mkdir()
        (company_dir / "Acme.json").write_text("{}")

        mock_generator = MagicMock()
        mock_generator.generate.return_value = []

        ns = argparse.Namespace(company="Acme", output_dir=None, cv_only=True, cl_only=False)
        with (
            patch(_PATCH_COMPANY_DATA, return_value=MagicMock()),
            patch(_PATCH_PDF_GENERATOR, return_value=mock_generator),
            patch("jobbing.cli._update_hub_documents"),
        ):
            _cmd_pdf(ns, config)

        mock_generator.generate.assert_called_once()
        kwargs = mock_generator.generate.call_args
        assert kwargs[1]["cv_only"] is True
        assert kwargs[1]["cl_only"] is False

    def test_custom_output_dir(self, config: Config, tmp_path: Path) -> None:
        company_dir = config.kanban_companies_dir / "Acme"
        company_dir.mkdir()
        (company_dir / "Acme.json").write_text("{}")

        custom_output = tmp_path / "custom_out"
        custom_output.mkdir()

        mock_generator = MagicMock()
        mock_generator.generate.return_value = []

        ns = argparse.Namespace(
            company="Acme",
            output_dir=str(custom_output),
            cv_only=False,
            cl_only=False,
        )
        with (
            patch(_PATCH_COMPANY_DATA, return_value=MagicMock()),
            patch(_PATCH_PDF_GENERATOR, return_value=mock_generator),
            patch("jobbing.cli._update_hub_documents"),
        ):
            _cmd_pdf(ns, config)

        call_args = mock_generator.generate.call_args[0]
        assert call_args[1] == custom_output

    def test_company_name_lowercased(self, config: Config) -> None:
        """Company name is lowercased for directory lookup."""
        company_dir = config.kanban_companies_dir / "MixedCase"
        company_dir.mkdir()
        (company_dir / "MixedCase.json").write_text("{}")

        mock_generator = MagicMock()
        mock_generator.generate.return_value = []

        ns = argparse.Namespace(company="MixedCase", output_dir=None, cv_only=False, cl_only=False)
        with (
            patch(_PATCH_COMPANY_DATA, return_value=MagicMock()),
            patch(_PATCH_PDF_GENERATOR, return_value=mock_generator),
            patch("jobbing.cli._update_hub_documents"),
        ):
            _cmd_pdf(ns, config)

        mock_generator.generate.assert_called_once()

    def test_obsidian_backend_updates_hub_documents(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When backend is obsidian, _update_hub_documents is called."""
        config.tracker_backend = "obsidian"
        company_dir = config.kanban_companies_dir / "Acme"
        company_dir.mkdir()
        (company_dir / "Acme.json").write_text("{}")

        mock_path = MagicMock()
        mock_path.name = "ACME-CV.pdf"
        mock_path.stem = "ACME-CV"
        mock_path.stat.return_value.st_size = 100

        mock_generator = MagicMock()
        mock_generator.generate.return_value = [mock_path]

        with (
            patch(_PATCH_COMPANY_DATA, return_value=MagicMock()),
            patch(_PATCH_PDF_GENERATOR, return_value=mock_generator),
            patch("jobbing.cli._update_hub_documents") as mock_hub,
        ):
            ns = argparse.Namespace(company="Acme", output_dir=None, cv_only=False, cl_only=False)
            _cmd_pdf(ns, config)

        mock_hub.assert_called_once()
        assert mock_hub.call_args[0][0] == "Acme"


# ---------------------------------------------------------------------------
# Scan commands
# ---------------------------------------------------------------------------


class TestCmdScan:
    def test_dispatches_bookmarks(self, config: Config) -> None:
        ns = argparse.Namespace(scan_command="bookmarks", categories=None)
        with patch("jobbing.cli._scan_bookmarks") as mock_fn:
            _cmd_scan(ns, config)
            mock_fn.assert_called_once_with(ns, config)

    def test_dispatches_fetch(self, config: Config) -> None:
        ns = argparse.Namespace(scan_command="fetch", categories=None, limit=None)
        with patch("jobbing.cli._scan_fetch") as mock_fn:
            _cmd_scan(ns, config)
            mock_fn.assert_called_once_with(ns, config)

    def test_dispatches_existing(self, config: Config) -> None:
        ns = argparse.Namespace(scan_command="existing")
        with patch("jobbing.cli._scan_existing") as mock_fn:
            _cmd_scan(ns, config)
            mock_fn.assert_called_once_with(ns, config)

    def test_no_scan_command_exits(self, config: Config) -> None:
        ns = argparse.Namespace(scan_command=None)
        with pytest.raises(SystemExit, match="1"):
            _cmd_scan(ns, config)


class TestScanBookmarks:
    def test_lists_all_bookmarks(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        from jobbing.scanner import Bookmark

        bookmarks = [
            Bookmark(label="Board A", url="https://a.com", category="Climate / Impact"),
            Bookmark(label="Board B", url="https://b.com", category="Climate / Impact"),
            Bookmark(label="Board C", url="https://c.com", category="Startup / Tech"),
        ]
        ns = argparse.Namespace(categories=None)
        with patch(_PATCH_PARSE_BOOKMARKS, return_value=bookmarks):
            _scan_bookmarks(ns, config)

        output = capsys.readouterr().out
        assert "Bookmarks: 3 across 2 categories" in output
        assert "Climate / Impact (2)" in output
        assert "Board A" in output
        assert "Board B" in output
        assert "Startup / Tech (1)" in output
        assert "Board C" in output

    def test_filters_by_category(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        from jobbing.scanner import Bookmark

        bookmarks = [
            Bookmark(label="Board A", url="https://a.com", category="Climate / Impact"),
            Bookmark(label="Board B", url="https://b.com", category="Startup / Tech"),
        ]
        ns = argparse.Namespace(categories=["Climate / Impact"])
        with patch(_PATCH_PARSE_BOOKMARKS, return_value=bookmarks):
            _scan_bookmarks(ns, config)

        output = capsys.readouterr().out
        assert "Bookmarks: 1 across 1 categories" in output
        assert "Board A" in output
        assert "Board B" not in output


class TestScanFetch:
    def test_fetches_boards(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        from jobbing.scanner import Bookmark, FetchedBoard, FetchResult

        bookmarks = [
            Bookmark(label="Board A", url="https://a.com", category="Climate"),
        ]
        result = MagicMock(spec=FetchResult)
        result.boards_fetched = 1
        result.boards_requested = 1
        result.boards_failed = 0
        board = MagicMock(spec=FetchedBoard)
        board.bookmark = bookmarks[0]
        board.char_count = 5000
        board.error = ""
        result.boards = [board]

        filepath = Path("/tmp/scan_results/result.json")

        ns = argparse.Namespace(categories=None, limit=None)
        with (
            patch(_PATCH_PARSE_BOOKMARKS, return_value=bookmarks),
            patch(_PATCH_FETCH_BOARDS, return_value=result),
            patch(_PATCH_SAVE_FETCH, return_value=filepath),
        ):
            _scan_fetch(ns, config)

        output = capsys.readouterr().out
        assert "Fetching 1 boards..." in output
        assert "Fetch complete:" in output
        assert "Fetched: 1/1" in output
        assert "5,000 chars" in output

    def test_no_matching_bookmarks(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ns = argparse.Namespace(categories=["Nonexistent"], limit=None)
        with patch(_PATCH_PARSE_BOOKMARKS, return_value=[]):
            _scan_fetch(ns, config)

        assert "No bookmarks match the filter." in capsys.readouterr().out

    def test_limit_applied(self, config: Config) -> None:
        from jobbing.scanner import Bookmark

        bookmarks = [
            Bookmark(label=f"Board {i}", url=f"https://{i}.com", category="Cat") for i in range(10)
        ]
        result = MagicMock()
        result.boards_fetched = 3
        result.boards_requested = 3
        result.boards_failed = 0
        result.boards = []

        ns = argparse.Namespace(categories=None, limit=3)
        with (
            patch(_PATCH_PARSE_BOOKMARKS, return_value=bookmarks),
            patch(_PATCH_FETCH_BOARDS, return_value=result) as mock_fetch,
            patch(_PATCH_SAVE_FETCH, return_value=Path("/tmp/r.json")),
        ):
            _scan_fetch(ns, config)

        fetched_bookmarks = mock_fetch.call_args[0][0]
        assert len(fetched_bookmarks) == 3

    def test_failed_boards_shown(self, config: Config, capsys: pytest.CaptureFixture[str]) -> None:
        from jobbing.scanner import Bookmark, FetchedBoard

        bm = Bookmark(label="Bad Board", url="https://bad.com", category="Cat")
        result = MagicMock()
        result.boards_fetched = 0
        result.boards_requested = 1
        result.boards_failed = 1
        board = MagicMock(spec=FetchedBoard)
        board.bookmark = bm
        board.char_count = 0
        board.error = "Connection timeout"
        result.boards = [board]

        ns = argparse.Namespace(categories=None, limit=None)
        with (
            patch(_PATCH_PARSE_BOOKMARKS, return_value=[bm]),
            patch(_PATCH_FETCH_BOARDS, return_value=result),
            patch(_PATCH_SAVE_FETCH, return_value=Path("/tmp/r.json")),
        ):
            _scan_fetch(ns, config)

        output = capsys.readouterr().out
        assert "Failed: 1" in output
        assert "FAILED: Connection timeout" in output


class TestScanExisting:
    def test_lists_from_tracker(
        self,
        config: Config,
        mock_tracker: MagicMock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        ns = argparse.Namespace()
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _scan_existing(ns, config)

        output = capsys.readouterr().out
        assert "Existing applications (2, source: tracker)" in output
        assert "[Applied] Acme" in output
        assert "[Targeted] Globex" in output

    def test_falls_back_to_companies_dir(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        (config.kanban_companies_dir / "Acme").mkdir()
        (config.kanban_companies_dir / "globex").mkdir()
        (config.kanban_companies_dir / ".hidden").mkdir()

        ns = argparse.Namespace()
        with patch(_PATCH_GET_TRACKER, side_effect=Exception("No tracker")):
            _scan_existing(ns, config)

        output = capsys.readouterr().out
        assert "source: kanban/companies/" in output
        assert "Acme" in output
        assert "globex" in output
        assert ".hidden" not in output

    def test_no_applications_found(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_tracker = MagicMock()
        mock_tracker.list_all.return_value = []

        ns = argparse.Namespace()
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _scan_existing(ns, config)

        assert "No existing applications found." in capsys.readouterr().out

    def test_app_without_status_shows_question_mark(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        mock_tracker = MagicMock()
        mock_tracker.list_all.return_value = [Application(name="Mystery", status=None)]

        ns = argparse.Namespace()
        with patch(_PATCH_GET_TRACKER, return_value=mock_tracker):
            _scan_existing(ns, config)

        output = capsys.readouterr().out
        assert "[?] Mystery" in output
        assert "(no position)" in output


# ---------------------------------------------------------------------------
# Main dispatch
# ---------------------------------------------------------------------------


class TestMain:
    def test_dispatches_track_create(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._track_create") as mock_fn,
        ):
            ns = argparse.Namespace(command="track", track_command="create")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()

    def test_dispatches_track_update(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._track_update") as mock_fn,
        ):
            ns = argparse.Namespace(command="track", track_command="update")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()

    def test_dispatches_track_highlights(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._track_highlights") as mock_fn,
        ):
            ns = argparse.Namespace(command="track", track_command="highlights")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()

    def test_dispatches_track_research(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._track_research") as mock_fn,
        ):
            ns = argparse.Namespace(command="track", track_command="research")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()

    def test_dispatches_track_outreach(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._track_outreach") as mock_fn,
        ):
            ns = argparse.Namespace(command="track", track_command="outreach")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()

    def test_dispatches_track_followup(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._track_followup") as mock_fn,
        ):
            ns = argparse.Namespace(command="track", track_command="followup")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()

    def test_dispatches_pdf(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._cmd_pdf") as mock_fn,
        ):
            ns = argparse.Namespace(command="pdf")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()

    def test_dispatches_scan(self) -> None:
        with (
            patch("jobbing.cli._build_parser") as mock_parser,
            patch("jobbing.cli.Config.load") as mock_config,
            patch("jobbing.cli._cmd_scan") as mock_fn,
        ):
            ns = argparse.Namespace(command="scan")
            mock_parser.return_value.parse_args.return_value = ns
            mock_config.return_value = MagicMock()
            main()
            mock_fn.assert_called_once()


# ---------------------------------------------------------------------------
# Integration-style: parse real argv then call handler
# ---------------------------------------------------------------------------


class TestEndToEnd:
    """Lightweight integration tests that parse real argv and call handlers."""

    def test_track_create_dry_run_via_main(
        self, config: Config, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with (
            patch(
                "sys.argv",
                ["jobbing", "track", "create", "--name", "E2E Corp", "--dry-run"],
            ),
            patch("jobbing.cli.Config.load", return_value=config),
        ):
            main()

        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert parsed["name"] == "E2E Corp"
        assert parsed["status"] == "Targeted"
