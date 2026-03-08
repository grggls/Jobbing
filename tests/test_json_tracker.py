"""Tests for jobbing.tracker.json_file — JSON file-based tracker backend."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from jobbing.config import Config
from jobbing.models import Application, Contact, LinkedInStatus, Status
from jobbing.tracker.json_file import JsonFileTracker

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tracker(tmp_path: Path) -> JsonFileTracker:
    """Create a JsonFileTracker with a temporary project directory."""
    config = Config(project_dir=tmp_path)
    return JsonFileTracker(config)


@pytest.fixture()
def sample_app() -> Application:
    """A sample Application for testing."""
    return Application(
        name="Acme Corp",
        position="Senior Engineer",
        status=Status.TARGETED,
        start_date=date(2026, 3, 1),
        url="https://acme.com/jobs/1",
        environment=["Remote", "Berlin"],
        salary="120k-150k EUR",
        focus=["Platform", "Infrastructure"],
        vision="Build the future",
        mission="Ship reliable systems",
        highlights=["Led migration", "Built CI/CD"],
        research=["Series B", "200 employees"],
    )


# ---------------------------------------------------------------------------
# Initialization and persistence
# ---------------------------------------------------------------------------


class TestJsonFileTrackerInit:
    def test_creates_empty_tracker(self, tmp_path: Path) -> None:
        config = Config(project_dir=tmp_path)
        tracker = JsonFileTracker(config)
        assert tracker.list_all() == []

    def test_loads_existing_file(self, tmp_path: Path) -> None:
        tracker_file = tmp_path / "tracker.json"
        data = {
            "applications": {
                "abc123": {
                    "name": "Pre-Existing",
                    "position": "Engineer",
                    "status": "Targeted",
                    "start_date": None,
                    "url": "",
                    "environment": [],
                    "salary": "",
                    "focus": [],
                    "vision": "",
                    "mission": "",
                    "linkedin": "n/a",
                    "conclusion": "",
                    "highlights": [],
                    "research": [],
                    "contacts": [],
                }
            }
        }
        with open(tracker_file, "w") as f:
            json.dump(data, f)

        config = Config(project_dir=tmp_path)
        tracker = JsonFileTracker(config)
        apps = tracker.list_all()
        assert len(apps) == 1
        assert apps[0].name == "Pre-Existing"

    def test_persists_to_disk(self, tracker: JsonFileTracker, tmp_path: Path) -> None:
        app = Application(name="DiskTest", position="Engineer")
        tracker.create(app)

        tracker_file = tmp_path / "tracker.json"
        assert tracker_file.is_file()

        with open(tracker_file) as f:
            data = json.load(f)
        assert len(data["applications"]) == 1


# ---------------------------------------------------------------------------
# create()
# ---------------------------------------------------------------------------


class TestCreate:
    def test_create_returns_id_and_sections(
        self, tracker: JsonFileTracker, sample_app: Application
    ) -> None:
        app_id, sections = tracker.create(sample_app)
        assert isinstance(app_id, str)
        assert len(app_id) == 12
        assert "properties" in sections

    def test_create_stores_all_fields(
        self, tracker: JsonFileTracker, sample_app: Application
    ) -> None:
        app_id, _ = tracker.create(sample_app)
        retrieved = tracker.find_by_name("Acme Corp")
        assert retrieved is not None
        assert retrieved.name == "Acme Corp"
        assert retrieved.position == "Senior Engineer"
        assert retrieved.status == Status.TARGETED
        assert retrieved.start_date == date(2026, 3, 1)
        assert retrieved.url == "https://acme.com/jobs/1"
        assert retrieved.environment == ["Remote", "Berlin"]
        assert retrieved.salary == "120k-150k EUR"
        assert retrieved.focus == ["Platform", "Infrastructure"]
        assert retrieved.vision == "Build the future"
        assert retrieved.mission == "Ship reliable systems"
        assert retrieved.highlights == ["Led migration", "Built CI/CD"]
        assert retrieved.research == ["Series B", "200 employees"]

    def test_create_deduplicates_by_name(self, tracker: JsonFileTracker) -> None:
        app1 = Application(name="DupeCo", position="Engineer V1")
        app2 = Application(name="DupeCo", position="Engineer V2")

        id1, _ = tracker.create(app1)
        id2, _ = tracker.create(app2)

        assert id1 == id2  # same ID — updated in place
        apps = tracker.list_all()
        assert len(apps) == 1
        assert apps[0].position == "Engineer V2"

    def test_create_deduplication_case_insensitive(self, tracker: JsonFileTracker) -> None:
        app1 = Application(name="Acme Corp", position="Role A")
        app2 = Application(name="acme corp", position="Role B")

        id1, _ = tracker.create(app1)
        id2, _ = tracker.create(app2)

        assert id1 == id2
        assert tracker.list_all()[0].position == "Role B"

    def test_create_multiple_distinct(self, tracker: JsonFileTracker) -> None:
        app1 = Application(name="Alpha", position="Engineer")
        app2 = Application(name="Beta", position="Manager")

        tracker.create(app1)
        tracker.create(app2)

        apps = tracker.list_all()
        assert len(apps) == 2
        names = {a.name for a in apps}
        assert names == {"Alpha", "Beta"}


# ---------------------------------------------------------------------------
# update()
# ---------------------------------------------------------------------------


class TestUpdate:
    def test_update_existing(self, tracker: JsonFileTracker) -> None:
        app = Application(name="UpdateCo", position="Engineer", status=Status.TARGETED)
        app_id, _ = tracker.create(app)

        updated = Application(
            name="UpdateCo",
            position="Senior Engineer",
            status=Status.APPLIED,
            page_id=app_id,
        )
        tracker.update(updated)

        result = tracker.find_by_name("UpdateCo")
        assert result is not None
        assert result.position == "Senior Engineer"
        assert result.status == Status.APPLIED

    def test_update_nonexistent_raises(self, tracker: JsonFileTracker) -> None:
        app = Application(name="Ghost", page_id="nonexistent_id")
        with pytest.raises(ValueError, match="Application not found"):
            tracker.update(app)

    def test_update_none_page_id_raises(self, tracker: JsonFileTracker) -> None:
        app = Application(name="NullId", page_id=None)
        with pytest.raises(ValueError, match="Application not found"):
            tracker.update(app)

    def test_update_persists(self, tracker: JsonFileTracker, tmp_path: Path) -> None:
        app = Application(name="PersistCo", position="Eng")
        app_id, _ = tracker.create(app)

        updated = Application(name="PersistCo", position="Staff Eng", page_id=app_id)
        tracker.update(updated)

        # Reload from disk
        config = Config(project_dir=tmp_path)
        fresh = JsonFileTracker(config)
        result = fresh.find_by_name("PersistCo")
        assert result is not None
        assert result.position == "Staff Eng"


# ---------------------------------------------------------------------------
# find_by_name()
# ---------------------------------------------------------------------------


class TestFindByName:
    def test_finds_existing(self, tracker: JsonFileTracker) -> None:
        tracker.create(Application(name="FindMe", position="Eng"))
        result = tracker.find_by_name("FindMe")
        assert result is not None
        assert result.name == "FindMe"

    def test_case_insensitive(self, tracker: JsonFileTracker) -> None:
        tracker.create(Application(name="CaseCo", position="Eng"))
        result = tracker.find_by_name("caseco")
        assert result is not None
        assert result.name == "CaseCo"

    def test_returns_none_for_missing(self, tracker: JsonFileTracker) -> None:
        result = tracker.find_by_name("Nonexistent")
        assert result is None

    def test_returned_app_has_page_id(self, tracker: JsonFileTracker) -> None:
        app_id, _ = tracker.create(Application(name="WithId", position="Eng"))
        result = tracker.find_by_name("WithId")
        assert result is not None
        assert result.page_id == app_id


# ---------------------------------------------------------------------------
# set_highlights()
# ---------------------------------------------------------------------------


class TestSetHighlights:
    def test_set_highlights(self, tracker: JsonFileTracker) -> None:
        app_id, _ = tracker.create(Application(name="HighCo"))
        tracker.set_highlights(app_id, ["Bullet A", "Bullet B"])

        result = tracker.find_by_name("HighCo")
        assert result is not None
        assert result.highlights == ["Bullet A", "Bullet B"]

    def test_replace_existing_highlights(self, tracker: JsonFileTracker) -> None:
        app = Application(name="ReplaceCo", highlights=["Old"])
        app_id, _ = tracker.create(app)
        tracker.set_highlights(app_id, ["New A", "New B"])

        result = tracker.find_by_name("ReplaceCo")
        assert result is not None
        assert result.highlights == ["New A", "New B"]

    def test_nonexistent_raises(self, tracker: JsonFileTracker) -> None:
        with pytest.raises(ValueError, match="Application not found"):
            tracker.set_highlights("fake_id", ["Bullet"])


# ---------------------------------------------------------------------------
# set_research()
# ---------------------------------------------------------------------------


class TestSetResearch:
    def test_set_research(self, tracker: JsonFileTracker) -> None:
        app_id, _ = tracker.create(Application(name="ResCo"))
        tracker.set_research(app_id, ["Series C", "500 employees"])

        result = tracker.find_by_name("ResCo")
        assert result is not None
        assert result.research == ["Series C", "500 employees"]

    def test_replace_existing_research(self, tracker: JsonFileTracker) -> None:
        app = Application(name="ReplaceRes", research=["Old data"])
        app_id, _ = tracker.create(app)
        tracker.set_research(app_id, ["Fresh data"])

        result = tracker.find_by_name("ReplaceRes")
        assert result is not None
        assert result.research == ["Fresh data"]

    def test_nonexistent_raises(self, tracker: JsonFileTracker) -> None:
        with pytest.raises(ValueError, match="Application not found"):
            tracker.set_research("fake_id", ["Data"])


# ---------------------------------------------------------------------------
# set_contacts()
# ---------------------------------------------------------------------------


class TestSetContacts:
    def test_set_contacts(self, tracker: JsonFileTracker) -> None:
        app_id, _ = tracker.create(Application(name="ContactCo"))
        contacts = [
            Contact(
                name="Jane Smith",
                title="VP Eng",
                linkedin="https://linkedin.com/in/jane",
                note="Ex-Google",
                message="Hi Jane",
            ),
        ]
        tracker.set_contacts(app_id, contacts)

        result = tracker.find_by_name("ContactCo")
        assert result is not None
        assert len(result.contacts) == 1
        assert result.contacts[0].name == "Jane Smith"
        assert result.contacts[0].title == "VP Eng"
        assert result.contacts[0].linkedin == "https://linkedin.com/in/jane"
        assert result.contacts[0].note == "Ex-Google"
        assert result.contacts[0].message == "Hi Jane"

    def test_replace_existing_contacts(self, tracker: JsonFileTracker) -> None:
        app = Application(
            name="ReplContacts",
            contacts=[Contact(name="Old", title="Old Title", linkedin="old")],
        )
        app_id, _ = tracker.create(app)

        new_contacts = [Contact(name="New", title="New Title", linkedin="new")]
        tracker.set_contacts(app_id, new_contacts)

        result = tracker.find_by_name("ReplContacts")
        assert result is not None
        assert len(result.contacts) == 1
        assert result.contacts[0].name == "New"

    def test_nonexistent_raises(self, tracker: JsonFileTracker) -> None:
        with pytest.raises(ValueError, match="Application not found"):
            tracker.set_contacts("fake_id", [])


# ---------------------------------------------------------------------------
# list_all()
# ---------------------------------------------------------------------------


class TestListAll:
    def test_empty(self, tracker: JsonFileTracker) -> None:
        assert tracker.list_all() == []

    def test_multiple(self, tracker: JsonFileTracker) -> None:
        tracker.create(Application(name="A"))
        tracker.create(Application(name="B"))
        tracker.create(Application(name="C"))
        apps = tracker.list_all()
        assert len(apps) == 3

    def test_returns_applications(self, tracker: JsonFileTracker) -> None:
        tracker.create(Application(name="TypeCheck", position="Eng"))
        apps = tracker.list_all()
        assert all(isinstance(a, Application) for a in apps)


# ---------------------------------------------------------------------------
# Serialization edge cases
# ---------------------------------------------------------------------------


class TestSerializationEdgeCases:
    def test_invalid_status_falls_back(self, tmp_path: Path) -> None:
        """Unknown status value in JSON falls back to TARGETED."""
        tracker_file = tmp_path / "tracker.json"
        data = {
            "applications": {
                "abc": {
                    "name": "BadStatus",
                    "status": "InvalidValue",
                    "linkedin": "n/a",
                    "contacts": [],
                }
            }
        }
        with open(tracker_file, "w") as f:
            json.dump(data, f)

        config = Config(project_dir=tmp_path)
        tracker = JsonFileTracker(config)
        apps = tracker.list_all()
        assert apps[0].status == Status.TARGETED

    def test_invalid_linkedin_falls_back(self, tmp_path: Path) -> None:
        """Unknown LinkedIn status falls back to NA."""
        tracker_file = tmp_path / "tracker.json"
        data = {
            "applications": {
                "abc": {
                    "name": "BadLinkedIn",
                    "status": "Targeted",
                    "linkedin": "BadValue",
                    "contacts": [],
                }
            }
        }
        with open(tracker_file, "w") as f:
            json.dump(data, f)

        config = Config(project_dir=tmp_path)
        tracker = JsonFileTracker(config)
        apps = tracker.list_all()
        assert apps[0].linkedin == LinkedInStatus.NA

    def test_missing_fields_use_defaults(self, tmp_path: Path) -> None:
        """Missing fields in JSON use sensible defaults."""
        tracker_file = tmp_path / "tracker.json"
        data = {"applications": {"abc": {"name": "Minimal"}}}
        with open(tracker_file, "w") as f:
            json.dump(data, f)

        config = Config(project_dir=tmp_path)
        tracker = JsonFileTracker(config)
        apps = tracker.list_all()
        app = apps[0]
        assert app.name == "Minimal"
        assert app.position == ""
        assert app.status == Status.TARGETED
        assert app.start_date is None
        assert app.highlights == []
        assert app.contacts == []

    def test_contacts_roundtrip(self, tracker: JsonFileTracker) -> None:
        """Contacts survive a create -> disk -> reload cycle."""
        app = Application(
            name="ContactRT",
            contacts=[
                Contact(name="Alice", title="CTO", linkedin="https://li.com/alice"),
                Contact(name="Bob", title="VP", linkedin="https://li.com/bob", note="Met at conf"),
            ],
        )
        app_id, _ = tracker.create(app)

        result = tracker.find_by_name("ContactRT")
        assert result is not None
        assert len(result.contacts) == 2
        assert result.contacts[0].name == "Alice"
        assert result.contacts[1].note == "Met at conf"

    def test_date_roundtrip(self, tracker: JsonFileTracker) -> None:
        """Date fields survive serialization and deserialization."""
        app = Application(name="DateCo", start_date=date(2026, 6, 15))
        tracker.create(app)

        result = tracker.find_by_name("DateCo")
        assert result is not None
        assert result.start_date == date(2026, 6, 15)
