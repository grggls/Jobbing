"""JSON file-based tracker backend.

Portable, zero-dependency fallback for testing and environments
where Notion is unavailable. Stores all applications in a single
JSON file at {project_dir}/tracker.json.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from jobbing.config import Config
from jobbing.models import Application, Contact, LinkedInStatus, Status


class JsonFileTracker:
    """JSON file tracker implementing TrackerBackend protocol."""

    def __init__(self, config: Config) -> None:
        self._path = config.project_dir / "tracker.json"
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        """Load the tracker file, creating it if needed."""
        if self._path.is_file():
            with open(self._path) as f:
                return json.load(f)
        return {"applications": {}}

    def _save(self) -> None:
        """Write the tracker file."""
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)
            f.write("\n")

    def _app_to_dict(self, app: Application) -> dict[str, Any]:
        """Serialize an Application to a JSON-safe dict."""
        d: dict[str, Any] = {
            "name": app.name,
            "position": app.position,
            "status": app.status.value,
            "start_date": app.start_date.isoformat() if app.start_date else None,
            "url": app.url,
            "environment": app.environment,
            "salary": app.salary,
            "focus": app.focus,
            "vision": app.vision,
            "mission": app.mission,
            "linkedin": app.linkedin.value,
            "conclusion": app.conclusion,
            "highlights": app.highlights,
            "research": app.research,
            "contacts": [
                {
                    "name": c.name,
                    "title": c.title,
                    "linkedin": c.linkedin,
                    "note": c.note,
                    "message": c.message,
                }
                for c in app.contacts
            ],
        }
        return d

    def _dict_to_app(self, app_id: str, d: dict[str, Any]) -> Application:
        """Deserialize a dict back to an Application."""
        try:
            status = Status(d.get("status", "Targeted"))
        except ValueError:
            status = Status.TARGETED

        try:
            linkedin = LinkedInStatus(d.get("linkedin", "n/a"))
        except ValueError:
            linkedin = LinkedInStatus.NA

        start_date = None
        if d.get("start_date"):
            start_date = date.fromisoformat(d["start_date"])

        contacts = [
            Contact(
                name=c.get("name", ""),
                title=c.get("title", ""),
                linkedin=c.get("linkedin", ""),
                note=c.get("note", ""),
                message=c.get("message", ""),
            )
            for c in d.get("contacts", [])
        ]

        return Application(
            name=d.get("name", ""),
            position=d.get("position", ""),
            status=status,
            start_date=start_date,
            url=d.get("url", ""),
            environment=d.get("environment", []),
            salary=d.get("salary", ""),
            focus=d.get("focus", []),
            vision=d.get("vision", ""),
            mission=d.get("mission", ""),
            linkedin=linkedin,
            conclusion=d.get("conclusion", ""),
            highlights=d.get("highlights", []),
            research=d.get("research", []),
            contacts=contacts,
            page_id=app_id,
        )

    # --- TrackerBackend protocol ---

    def create(self, app: Application) -> tuple[str, list[str]]:
        """Create a tracker entry. Returns (ID, list of sections written)."""
        # Check for existing entry with same name
        for app_id, data in self._data["applications"].items():
            if data.get("name", "").lower() == app.name.lower():
                # Update existing instead of duplicating
                self._data["applications"][app_id] = self._app_to_dict(app)
                self._save()
                return app_id, ["properties"]

        app_id = uuid.uuid4().hex[:12]
        self._data["applications"][app_id] = self._app_to_dict(app)
        self._save()
        return app_id, ["properties"]

    def update(self, app: Application) -> None:
        """Update an existing tracker entry."""
        if not app.page_id or app.page_id not in self._data["applications"]:
            raise ValueError(f"Application not found: {app.page_id}")
        self._data["applications"][app.page_id] = self._app_to_dict(app)
        self._save()

    def find_by_name(self, name: str) -> Application | None:
        """Find an application by company name (case-insensitive)."""
        for app_id, data in self._data["applications"].items():
            if data.get("name", "").lower() == name.lower():
                return self._dict_to_app(app_id, data)
        return None

    def set_highlights(self, app_id: str, highlights: list[str]) -> None:
        """Replace highlights on a tracker entry."""
        if app_id not in self._data["applications"]:
            raise ValueError(f"Application not found: {app_id}")
        self._data["applications"][app_id]["highlights"] = highlights
        self._save()

    def set_research(self, app_id: str, research: list[str]) -> None:
        """Replace research on a tracker entry."""
        if app_id not in self._data["applications"]:
            raise ValueError(f"Application not found: {app_id}")
        self._data["applications"][app_id]["research"] = research
        self._save()

    def set_contacts(self, app_id: str, contacts: list[Contact]) -> None:
        """Replace outreach contacts on a tracker entry."""
        if app_id not in self._data["applications"]:
            raise ValueError(f"Application not found: {app_id}")
        self._data["applications"][app_id]["contacts"] = [
            {
                "name": c.name,
                "title": c.title,
                "linkedin": c.linkedin,
                "note": c.note,
                "message": c.message,
            }
            for c in contacts
        ]
        self._save()

    def list_all(self) -> list[Application]:
        """List all tracked applications."""
        return [
            self._dict_to_app(app_id, data)
            for app_id, data in self._data["applications"].items()
        ]
