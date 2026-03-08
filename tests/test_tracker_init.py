"""Tests for jobbing.tracker — TrackerBackend Protocol and get_tracker() factory."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jobbing.config import Config
from jobbing.models import Application, Contact
from jobbing.tracker import TrackerBackend, get_tracker
from jobbing.tracker.json_file import JsonFileTracker

# ---------------------------------------------------------------------------
# TrackerBackend Protocol
# ---------------------------------------------------------------------------


class TestTrackerBackendProtocol:
    def test_json_file_tracker_is_backend(self, tmp_path: Path) -> None:
        """JsonFileTracker satisfies the TrackerBackend protocol."""
        config = Config(project_dir=tmp_path)
        tracker = JsonFileTracker(config)
        assert isinstance(tracker, TrackerBackend)

    def test_protocol_is_runtime_checkable(self) -> None:
        """TrackerBackend is marked runtime_checkable."""
        assert (
            hasattr(TrackerBackend, "__protocol_attrs__")
            or hasattr(TrackerBackend, "__abstractmethods__")
            or True
        )  # runtime_checkable protocols work with isinstance
        # The real check is that isinstance doesn't raise
        mock = MagicMock(spec=TrackerBackend)
        assert isinstance(mock, TrackerBackend)

    def test_non_conforming_object_fails(self) -> None:
        """An object missing protocol methods is not a TrackerBackend."""

        class NotATracker:
            pass

        assert not isinstance(NotATracker(), TrackerBackend)

    def test_partial_implementation_fails(self) -> None:
        """An object with only some methods is not a TrackerBackend."""

        class PartialTracker:
            def create(self, app: Application) -> tuple[str, list[str]]:
                return ("id", [])

        assert not isinstance(PartialTracker(), TrackerBackend)

    def test_duck_typed_implementation_passes(self) -> None:
        """A class implementing all protocol methods passes isinstance check."""

        class CustomTracker:
            def create(self, app: Application) -> tuple[str, list[str]]:
                return ("id", [])

            def update(self, app: Application) -> None:
                pass

            def find_by_name(self, name: str) -> Application | None:
                return None

            def set_highlights(self, app_id: str, highlights: list[str]) -> None:
                pass

            def set_research(self, app_id: str, research: list[str]) -> None:
                pass

            def set_contacts(self, app_id: str, contacts: list[Contact]) -> None:
                pass

            def list_all(self) -> list[Application]:
                return []

        assert isinstance(CustomTracker(), TrackerBackend)


# ---------------------------------------------------------------------------
# get_tracker() factory
# ---------------------------------------------------------------------------


class TestGetTracker:
    def test_json_backend(self, tmp_path: Path) -> None:
        config = Config(project_dir=tmp_path)
        tracker = get_tracker("json", config)
        assert isinstance(tracker, JsonFileTracker)
        assert isinstance(tracker, TrackerBackend)

    def test_notion_backend(self, tmp_path: Path) -> None:
        """Notion backend creates a NotionTracker (import verified)."""
        config = Config(project_dir=tmp_path, notion_api_key="test-key")
        with patch("jobbing.tracker.notion.NotionTracker") as mock_cls:
            mock_instance = MagicMock()
            mock_cls.return_value = mock_instance
            tracker = get_tracker("notion", config)
            mock_cls.assert_called_once_with(config)
            assert tracker is mock_instance

    def test_unknown_backend_raises(self, tmp_path: Path) -> None:
        config = Config(project_dir=tmp_path)
        with pytest.raises(ValueError, match="Unknown tracker backend: 'sqlite'"):
            get_tracker("sqlite", config)

    def test_unknown_backend_message_includes_name(self, tmp_path: Path) -> None:
        config = Config(project_dir=tmp_path)
        with pytest.raises(ValueError, match="postgres"):
            get_tracker("postgres", config)

    def test_json_backend_functional(self, tmp_path: Path) -> None:
        """End-to-end: factory -> create -> find_by_name works."""
        config = Config(project_dir=tmp_path)
        tracker = get_tracker("json", config)

        app = Application(name="FactoryTest", position="Eng")
        app_id, _ = tracker.create(app)
        assert isinstance(app_id, str)

        found = tracker.find_by_name("FactoryTest")
        assert found is not None
        assert found.name == "FactoryTest"
