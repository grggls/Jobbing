"""Tracker backends for application tracking storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from jobbing.config import Config
    from jobbing.models import Application, Contact


@runtime_checkable
class TrackerBackend(Protocol):
    """Interface for application tracking storage."""

    def create(self, app: Application) -> tuple[str, list[str]]:
        """Create a tracker entry. Returns (ID, list of sections written)."""
        ...

    def update(self, app: Application) -> None:
        """Update an existing tracker entry."""
        ...

    def find_by_name(self, name: str) -> Application | None:
        """Find an application by company name."""
        ...

    def set_highlights(self, app_id: str, highlights: list[str]) -> None:
        """Replace highlights section on a tracker entry."""
        ...

    def set_research(self, app_id: str, research: list[str]) -> None:
        """Replace research section on a tracker entry."""
        ...

    def set_contacts(self, app_id: str, contacts: list[Contact]) -> None:
        """Replace outreach contacts on a tracker entry."""
        ...

    def list_all(self) -> list[Application]:
        """List all tracked applications."""
        ...


def get_tracker(backend: str, config: Config) -> TrackerBackend:
    """Factory: instantiate the configured tracker backend."""
    if backend == "notion":
        from jobbing.tracker.notion import NotionTracker

        return NotionTracker(config)
    if backend == "json":
        from jobbing.tracker.json_file import JsonFileTracker

        return JsonFileTracker(config)
    raise ValueError(f"Unknown tracker backend: {backend!r}")
