"""Bookmark scanner utilities: parsing, fetching, and results persistence.

The heavy lifting (posting extraction and scoring) happens in-conversation
via Claude Code or Cowork — no API key needed. This module provides the
Python plumbing that Claude calls via the CLI.

Fetching uses headless Playwright via jobbing.browser — handles JS rendering,
bot detection (via playwright-stealth), and concurrent page loading.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Max chars to keep per page after cleaning
MAX_PAGE_CHARS = 80_000

# Max concurrent browser pages
MAX_FETCH_WORKERS = 8


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class Bookmark:
    """A parsed bookmark from BOOKMARKS.md."""

    label: str
    url: str
    category: str


@dataclass
class FetchedBoard:
    """A fetched board page with its content."""

    bookmark: Bookmark
    content: str  # cleaned page text
    char_count: int
    error: str = ""


@dataclass
class FetchResult:
    """Output of a fetch run."""

    timestamp: str
    boards_requested: int
    boards_fetched: int
    boards_failed: int
    boards: list[FetchedBoard] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Bookmark parsing
# ---------------------------------------------------------------------------


def parse_bookmarks(bookmarks_path: Path) -> list[Bookmark]:
    """Parse BOOKMARKS.md — extract [label](url) links grouped by ## Category headings."""
    text = bookmarks_path.read_text()
    bookmarks: list[Bookmark] = []
    current_category = "Uncategorized"

    link_re = re.compile(r"-\s*\[([^\]]+)\]\(([^)]+)\)")

    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            current_category = stripped[3:].strip()
        else:
            m = link_re.match(stripped)
            if m:
                bookmarks.append(
                    Bookmark(label=m.group(1), url=m.group(2), category=current_category)
                )

    return bookmarks


# ---------------------------------------------------------------------------
# Board fetching (via headless Playwright)
# ---------------------------------------------------------------------------


def _clean_html(html: str) -> str:
    """Strip scripts, styles, nav, footer, and comments. Keep job-relevant content.

    Retained for compatibility — Playwright's innerText is already clean,
    but this is useful if raw HTML needs processing elsewhere.
    """
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<footer[^>]*>.*?</footer>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Strip all HTML tags, keep text
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:MAX_PAGE_CHARS]


def fetch_boards(
    bookmarks: list[Bookmark],
    timeout: int = 30,
    workers: int = MAX_FETCH_WORKERS,
) -> FetchResult:
    """Fetch multiple boards via headless Playwright+stealth. Returns FetchResult."""
    from jobbing.browser import fetch_pages

    if not bookmarks:
        return FetchResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            boards_requested=0,
            boards_fetched=0,
            boards_failed=0,
        )

    url_to_bookmark = {bm.url: bm for bm in bookmarks}
    urls = [bm.url for bm in bookmarks]

    browse_results = asyncio.run(
        fetch_pages(urls, timeout_ms=timeout * 1000, concurrency=workers)
    )

    fetched: list[FetchedBoard] = []
    failed = 0

    for br in browse_results:
        bm = url_to_bookmark[br.url]
        if br.error:
            failed += 1
            logger.warning("Failed: %s — %s", bm.label, br.error)
            fetched.append(FetchedBoard(bookmark=bm, content="", char_count=0, error=br.error))
        else:
            logger.info("Fetched: %s (%d chars)", bm.label, br.char_count)
            fetched.append(FetchedBoard(bookmark=bm, content=br.raw_text, char_count=br.char_count))

    # Restore original bookmark order
    bookmark_order = {bm.url: i for i, bm in enumerate(bookmarks)}
    fetched.sort(key=lambda fb: bookmark_order.get(fb.bookmark.url, 999))

    return FetchResult(
        timestamp=datetime.now(timezone.utc).isoformat(),
        boards_requested=len(bookmarks),
        boards_fetched=len(bookmarks) - failed,
        boards_failed=failed,
        boards=fetched,
    )


# ---------------------------------------------------------------------------
# Results persistence
# ---------------------------------------------------------------------------


def save_fetch_results(result: FetchResult, results_dir: Path) -> Path:
    """Save fetched board contents to scan_results/ for Claude to process."""
    results_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{ts}_fetch.json"
    filepath = results_dir / filename

    data = {
        "timestamp": result.timestamp,
        "boards_requested": result.boards_requested,
        "boards_fetched": result.boards_fetched,
        "boards_failed": result.boards_failed,
        "boards": [
            {
                "label": fb.bookmark.label,
                "url": fb.bookmark.url,
                "category": fb.bookmark.category,
                "char_count": fb.char_count,
                "error": fb.error,
                "content": fb.content,
            }
            for fb in result.boards
        ],
    }

    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return filepath
