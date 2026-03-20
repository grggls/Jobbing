"""Configuration loading for the Jobbing package.

Consolidates API key loading and adds configuration for scoring and tracker.

Key loading cascade: environment variable → .env file → ~/.zshrc-secrets
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


def _load_key_from_env(name: str) -> str | None:
    """Check environment variable."""
    return os.environ.get(name) or None


def _load_key_from_dotenv(name: str, env_path: Path) -> str | None:
    """Parse a key from a .env file."""
    if not env_path.is_file():
        return None
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith(f"{name}="):
                value = line.split("=", 1)[1].strip().strip('"').strip("'")
                if value:
                    return value
    return None


def _load_key_from_secrets(name: str) -> str | None:
    """Source ~/.zshrc-secrets and extract a key."""
    secrets_path = Path.home() / ".zshrc-secrets"
    if not secrets_path.is_file():
        return None
    try:
        result = subprocess.run(
            ["bash", "-c", f"source {secrets_path} && echo ${name}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        value = result.stdout.strip()
        return value or None
    except (subprocess.TimeoutExpired, OSError):
        return None


def _load_key(name: str, env_path: Path) -> str:
    """Load a key using the cascade: env → .env → ~/.zshrc-secrets.

    Raises ValueError if the key is not found anywhere.
    """
    value = (
        _load_key_from_env(name)
        or _load_key_from_dotenv(name, env_path)
        or _load_key_from_secrets(name)
    )
    if not value:
        raise ValueError(f"{name} not found in environment, .env, or ~/.zshrc-secrets")
    return value


@dataclass
class Config:
    """Runtime configuration, loaded once.

    All paths are resolved relative to project_dir.
    API keys use the three-source cascade.
    """

    project_dir: Path

    # Notion
    notion_api_key: str = ""
    notion_database_id: str = "734d746c-43b1-4929-8993-464f5ccc23e7"

    # Tracker
    tracker_backend: str = "obsidian"  # "obsidian" | "notion" | "json"

    # Scoring
    score_threshold: int = 60

    # Follow-up cadence
    followup_threshold_days: int = 5

    @classmethod
    def load(cls, project_dir: Path | None = None) -> Config:
        """Load configuration from environment, .env, and defaults.

        API keys that are missing are left empty — callers should check
        before use (e.g., NotionTracker checks notion_api_key).
        """
        if project_dir is None:
            project_dir = Path(__file__).resolve().parent.parent.parent

        env_path = project_dir / ".env"

        # Load keys — allow missing (some features are optional)
        notion_key = ""

        try:
            notion_key = _load_key("NOTION_API_KEY", env_path)
        except ValueError:
            pass

        # Score threshold from env
        threshold = int(os.environ.get("SCORE_THRESHOLD", "60"))

        # Tracker backend from env
        backend = os.environ.get("TRACKER_BACKEND", "obsidian")

        # Follow-up cadence threshold
        followup_days = int(
            _load_key_from_env("FOLLOWUP_THRESHOLD_DAYS")
            or _load_key_from_dotenv("FOLLOWUP_THRESHOLD_DAYS", env_path)
            or "5"
        )

        return cls(
            project_dir=project_dir,
            notion_api_key=notion_key,
            notion_database_id=os.environ.get(
                "NOTION_DATABASE_ID", "734d746c-43b1-4929-8993-464f5ccc23e7"
            ),
            tracker_backend=backend,
            score_threshold=threshold,
            followup_threshold_days=followup_days,
        )

    # --- Derived paths ---

    @property
    def companies_dir(self) -> Path:
        return self.project_dir / "companies"

    @property
    def kanban_dir(self) -> Path:
        return self.project_dir / "kanban"

    @property
    def kanban_companies_dir(self) -> Path:
        return self.kanban_dir / "companies"

    @property
    def kanban_interviews_dir(self) -> Path:
        return self.kanban_dir / "interviews"

    @property
    def kanban_board_path(self) -> Path:
        return self.kanban_dir / "Job Tracker.md"

    @property
    def queue_dir(self) -> Path:
        return self.project_dir / "notion_queue"

    @property
    def queue_results_dir(self) -> Path:
        return self.project_dir / "notion_queue_results"

    @property
    def scan_results_dir(self) -> Path:
        return self.project_dir / "scan_results"

    @property
    def bookmarks_path(self) -> Path:
        return self.project_dir / "BOOKMARKS.md"

    @property
    def context_path(self) -> Path:
        return self.project_dir / "CONTEXT.md"

    @property
    def scoring_path(self) -> Path:
        return self.project_dir / "SCORING.md"

    @property
    def env_path(self) -> Path:
        return self.project_dir / ".env"
