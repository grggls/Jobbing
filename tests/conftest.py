"""Shared fixtures for the Jobbing test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from jobbing.config import Config


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a minimal project directory structure for testing."""
    (tmp_path / ".env").write_text('NOTION_API_KEY="test-key-123"\n')
    (tmp_path / "companies").mkdir()
    (tmp_path / "notion_queue").mkdir()
    (tmp_path / "notion_queue_results").mkdir()
    return tmp_path


@pytest.fixture()
def config(tmp_project: Path) -> Config:
    """Load a Config pointing at the temporary project directory."""
    return Config.load(project_dir=tmp_project)
