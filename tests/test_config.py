"""Tests for jobbing.config — key loading cascade and Config dataclass."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

from jobbing.config import Config, _load_key_from_dotenv, _load_key_from_env


class TestLoadKeyFromEnv:
    def test_present(self) -> None:
        with patch.dict(os.environ, {"TEST_KEY": "abc123"}):
            assert _load_key_from_env("TEST_KEY") == "abc123"

    def test_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert _load_key_from_env("NONEXISTENT") is None

    def test_empty(self) -> None:
        with patch.dict(os.environ, {"EMPTY_KEY": ""}):
            assert _load_key_from_env("EMPTY_KEY") is None


class TestLoadKeyFromDotenv:
    def test_present(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text('MY_KEY="secret"\n')
        assert _load_key_from_dotenv("MY_KEY", env) == "secret"

    def test_present_unquoted(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("MY_KEY=secret\n")
        assert _load_key_from_dotenv("MY_KEY", env) == "secret"

    def test_missing_key(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("OTHER_KEY=val\n")
        assert _load_key_from_dotenv("MY_KEY", env) is None

    def test_missing_file(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        assert _load_key_from_dotenv("MY_KEY", env) is None

    def test_empty_value(self, tmp_path: Path) -> None:
        env = tmp_path / ".env"
        env.write_text("MY_KEY=\n")
        assert _load_key_from_dotenv("MY_KEY", env) is None


class TestConfig:
    def test_load_from_dotenv(self, tmp_project: Path) -> None:
        with patch.dict(os.environ, {}, clear=True):
            config = Config.load(project_dir=tmp_project)
        assert config.notion_api_key == "test-key-123"
        assert config.project_dir == tmp_project

    def test_derived_paths(self, config: Config) -> None:
        assert config.companies_dir == config.project_dir / "companies"
        assert config.queue_dir == config.project_dir / "notion_queue"
        assert config.queue_results_dir == config.project_dir / "notion_queue_results"
        assert config.env_path == config.project_dir / ".env"

    def test_defaults(self, config: Config) -> None:
        assert config.tracker_backend == "notion"
        assert config.score_threshold == 60
        assert config.followup_threshold_days == 5

    def test_env_overrides(self, tmp_project: Path) -> None:
        with patch.dict(
            os.environ,
            {
                "TRACKER_BACKEND": "json",
                "SCORE_THRESHOLD": "80",
            },
        ):
            config = Config.load(project_dir=tmp_project)
        assert config.tracker_backend == "json"
        assert config.score_threshold == 80

    def test_missing_notion_key_is_empty(self, tmp_path: Path) -> None:
        """Config doesn't crash when Notion key is unavailable."""
        (tmp_path / ".env").write_text("# empty\n")
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("jobbing.config._load_key_from_secrets", return_value=None),
        ):
            config = Config.load(project_dir=tmp_path)
        assert config.notion_api_key == ""
