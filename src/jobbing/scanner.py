"""Bookmark scanner utilities: parsing, fetching, and results persistence.

The heavy lifting (posting extraction and scoring) happens in-conversation
via Claude Code or Cowork — no API key needed. This module provides the
Python plumbing that Claude calls via the CLI.
"""

from __future__ import annotations

import json
import logging
import re
import ssl
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Max chars to keep per page after cleaning
MAX_PAGE_CHARS = 80_000

# Max concurrent HTTP fetches
MAX_FETCH_WORKERS = 10


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
    content: str  # cleaned HTML/text
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
# Board fetching
# ---------------------------------------------------------------------------


def _clean_html(html: str) -> str:
    """Strip scripts, styles, nav, footer, and comments. Keep job-relevant content."""
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


def _fetch_one(bookmark: Bookmark, timeout: int = 30) -> FetchedBoard:
    """Fetch a single board URL. Returns FetchedBoard with content or error."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(
            bookmark.url,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset, errors="replace")
            content = _clean_html(raw)
            return FetchedBoard(bookmark=bookmark, content=content, char_count=len(content))
    except Exception as e:
        return FetchedBoard(bookmark=bookmark, content="", char_count=0, error=str(e))


def fetch_boards(
    bookmarks: list[Bookmark],
    timeout: int = 30,
    workers: int = MAX_FETCH_WORKERS,
) -> FetchResult:
    """Fetch multiple boards concurrently. Returns FetchResult."""
    fetched: list[FetchedBoard] = []
    failed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_fetch_one, bm, timeout): bm for bm in bookmarks}
        for future in as_completed(futures):
            result = future.result()
            if result.error:
                failed += 1
                logger.warning("Failed: %s — %s", result.bookmark.label, result.error)
            else:
                logger.info("Fetched: %s (%d chars)", result.bookmark.label, result.char_count)
            fetched.append(result)

    # Sort by original bookmark order
    bookmark_order = {id(bm): i for i, bm in enumerate(bookmarks)}
    fetched.sort(key=lambda fb: bookmark_order.get(id(fb.bookmark), 999))

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
