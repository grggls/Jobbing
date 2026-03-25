"""Tests for jobbing.scanner — bookmark parsing, board fetching, and results persistence."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from jobbing.browser import BrowseResult
from jobbing.scanner import (
    Bookmark,
    FetchedBoard,
    FetchResult,
    _clean_html,
    fetch_boards,
    parse_bookmarks,
    save_fetch_results,
)

# ---------------------------------------------------------------------------
# Bookmark dataclass
# ---------------------------------------------------------------------------


class TestBookmark:
    def test_fields(self) -> None:
        bm = Bookmark(label="Acme Jobs", url="https://acme.com/jobs", category="Tech")
        assert bm.label == "Acme Jobs"
        assert bm.url == "https://acme.com/jobs"
        assert bm.category == "Tech"

    def test_equality(self) -> None:
        a = Bookmark(label="A", url="https://a.com", category="Cat")
        b = Bookmark(label="A", url="https://a.com", category="Cat")
        assert a == b

    def test_inequality(self) -> None:
        a = Bookmark(label="A", url="https://a.com", category="Cat")
        b = Bookmark(label="B", url="https://b.com", category="Cat")
        assert a != b


# ---------------------------------------------------------------------------
# FetchedBoard / FetchResult dataclasses
# ---------------------------------------------------------------------------


class TestFetchedBoard:
    def test_success(self) -> None:
        bm = Bookmark(label="Board", url="https://board.com", category="Cat")
        fb = FetchedBoard(bookmark=bm, content="job listing text", char_count=16)
        assert fb.error == ""
        assert fb.char_count == 16

    def test_error(self) -> None:
        bm = Bookmark(label="Board", url="https://board.com", category="Cat")
        fb = FetchedBoard(bookmark=bm, content="", char_count=0, error="Timeout")
        assert fb.error == "Timeout"


class TestFetchResult:
    def test_defaults(self) -> None:
        fr = FetchResult(
            timestamp="2026-03-08T12:00:00+00:00",
            boards_requested=5,
            boards_fetched=4,
            boards_failed=1,
        )
        assert fr.boards == []
        assert fr.boards_requested == 5


# ---------------------------------------------------------------------------
# parse_bookmarks()
# ---------------------------------------------------------------------------


class TestParseBookmarks:
    def test_basic_parsing(self, tmp_path: Path) -> None:
        bookmarks_md = tmp_path / "BOOKMARKS.md"
        bookmarks_md.write_text(
            "# Job Boards\n"
            "\n"
            "## Climate / Impact\n"
            "\n"
            "- [ClimateBase](https://climatebase.org/jobs)\n"
            "- [WorkOnClimate](https://workonclimate.org)\n"
            "\n"
            "## Startup / Tech\n"
            "\n"
            "- [YC Jobs](https://ycombinator.com/jobs)\n"
        )
        result = parse_bookmarks(bookmarks_md)
        assert len(result) == 3

        assert result[0].label == "ClimateBase"
        assert result[0].url == "https://climatebase.org/jobs"
        assert result[0].category == "Climate / Impact"

        assert result[1].label == "WorkOnClimate"
        assert result[1].url == "https://workonclimate.org"
        assert result[1].category == "Climate / Impact"

        assert result[2].label == "YC Jobs"
        assert result[2].category == "Startup / Tech"

    def test_uncategorized_links(self, tmp_path: Path) -> None:
        """Links appearing before any ## heading use 'Uncategorized'."""
        bookmarks_md = tmp_path / "BOOKMARKS.md"
        bookmarks_md.write_text("- [TopLink](https://top.com)\n")
        result = parse_bookmarks(bookmarks_md)
        assert len(result) == 1
        assert result[0].category == "Uncategorized"

    def test_empty_file(self, tmp_path: Path) -> None:
        bookmarks_md = tmp_path / "BOOKMARKS.md"
        bookmarks_md.write_text("")
        result = parse_bookmarks(bookmarks_md)
        assert result == []

    def test_no_links(self, tmp_path: Path) -> None:
        bookmarks_md = tmp_path / "BOOKMARKS.md"
        bookmarks_md.write_text("## Some Category\n\nJust text, no links.\n")
        result = parse_bookmarks(bookmarks_md)
        assert result == []

    def test_ignores_non_link_lines(self, tmp_path: Path) -> None:
        bookmarks_md = tmp_path / "BOOKMARKS.md"
        bookmarks_md.write_text(
            "## Cat\n\nSome paragraph text here.\n- [Valid](https://v.com)\nAnother paragraph.\n"
        )
        result = parse_bookmarks(bookmarks_md)
        assert len(result) == 1
        assert result[0].label == "Valid"

    def test_multiple_categories(self, tmp_path: Path) -> None:
        bookmarks_md = tmp_path / "BOOKMARKS.md"
        bookmarks_md.write_text(
            "## Alpha\n"
            "- [A1](https://a1.com)\n"
            "## Beta\n"
            "- [B1](https://b1.com)\n"
            "## Gamma\n"
            "- [G1](https://g1.com)\n"
        )
        result = parse_bookmarks(bookmarks_md)
        categories = [bm.category for bm in result]
        assert categories == ["Alpha", "Beta", "Gamma"]


# ---------------------------------------------------------------------------
# _clean_html()
# ---------------------------------------------------------------------------


class TestCleanHtml:
    def test_strips_scripts(self) -> None:
        html = '<p>Job</p><script>alert("x")</script><p>listing</p>'
        cleaned = _clean_html(html)
        assert "alert" not in cleaned
        assert "Job" in cleaned
        assert "listing" in cleaned

    def test_strips_styles(self) -> None:
        html = "<style>body{color:red}</style><p>Content</p>"
        cleaned = _clean_html(html)
        assert "color:red" not in cleaned
        assert "Content" in cleaned

    def test_strips_nav_footer(self) -> None:
        html = "<nav>menu</nav><main>Jobs</main><footer>copyright</footer>"
        cleaned = _clean_html(html)
        assert "menu" not in cleaned
        assert "copyright" not in cleaned
        assert "Jobs" in cleaned

    def test_strips_html_comments(self) -> None:
        html = "<!-- comment --><p>Visible</p>"
        cleaned = _clean_html(html)
        assert "comment" not in cleaned
        assert "Visible" in cleaned

    def test_strips_tags_keeps_text(self) -> None:
        html = "<div><b>Bold</b> text</div>"
        cleaned = _clean_html(html)
        assert "Bold" in cleaned
        assert "text" in cleaned
        assert "<div>" not in cleaned

    def test_collapses_whitespace(self) -> None:
        html = "<p>Too    much      space</p>"
        cleaned = _clean_html(html)
        assert "  " not in cleaned

    def test_truncates_long_content(self) -> None:
        html = "<p>" + "x" * 100_000 + "</p>"
        cleaned = _clean_html(html)
        assert len(cleaned) <= 80_000


# ---------------------------------------------------------------------------
# fetch_boards() — mock browser.fetch_pages
# ---------------------------------------------------------------------------


def _make_browse_result(url: str, *, error: str = "") -> BrowseResult:
    """Helper to create a BrowseResult for testing."""
    if error:
        return BrowseResult(
            url=url, title="", company="", description="",
            location="", raw_text="", char_count=0, error=error,
        )
    return BrowseResult(
        url=url, title="Test Page", company="TestCo",
        description="A job listing", location="Remote",
        raw_text="Engineer needed at TestCo", char_count=25,
    )


class TestFetchBoards:
    def test_all_succeed(self) -> None:
        bookmarks = [
            Bookmark(label="A", url="https://a.com", category="Cat"),
            Bookmark(label="B", url="https://b.com", category="Cat"),
        ]

        mock_results = [_make_browse_result(bm.url) for bm in bookmarks]

        with patch("jobbing.scanner.asyncio.run", return_value=mock_results):
            result = fetch_boards(bookmarks, timeout=10, workers=2)

        assert result.boards_requested == 2
        assert result.boards_fetched == 2
        assert result.boards_failed == 0
        assert len(result.boards) == 2
        assert result.timestamp  # non-empty ISO timestamp

    def test_mixed_success_and_failure(self) -> None:
        bookmarks = [
            Bookmark(label="Good", url="https://good.com", category="Cat"),
            Bookmark(label="Bad", url="https://bad.com", category="Cat"),
        ]

        mock_results = [
            _make_browse_result("https://good.com"),
            _make_browse_result("https://bad.com", error="Connection refused"),
        ]

        with patch("jobbing.scanner.asyncio.run", return_value=mock_results):
            result = fetch_boards(bookmarks, timeout=10, workers=2)

        assert result.boards_requested == 2
        assert result.boards_fetched == 1
        assert result.boards_failed == 1

    def test_empty_bookmarks(self) -> None:
        result = fetch_boards([], timeout=10, workers=2)
        assert result.boards_requested == 0
        assert result.boards_fetched == 0
        assert result.boards_failed == 0
        assert result.boards == []

    def test_single_bookmark(self) -> None:
        bookmarks = [Bookmark(label="Only", url="https://only.com", category="Solo")]
        mock_results = [_make_browse_result("https://only.com")]

        with patch("jobbing.scanner.asyncio.run", return_value=mock_results):
            result = fetch_boards(bookmarks, timeout=10, workers=1)

        assert result.boards_requested == 1
        assert result.boards_fetched == 1
        assert len(result.boards) == 1

    def test_preserves_bookmark_order(self) -> None:
        bookmarks = [
            Bookmark(label="C", url="https://c.com", category="Cat"),
            Bookmark(label="A", url="https://a.com", category="Cat"),
            Bookmark(label="B", url="https://b.com", category="Cat"),
        ]
        # Return in reversed order to test re-sorting
        mock_results = [_make_browse_result(bm.url) for bm in reversed(bookmarks)]

        with patch("jobbing.scanner.asyncio.run", return_value=mock_results):
            result = fetch_boards(bookmarks, timeout=10, workers=2)

        labels = [fb.bookmark.label for fb in result.boards]
        assert labels == ["C", "A", "B"]


# ---------------------------------------------------------------------------
# save_fetch_results()
# ---------------------------------------------------------------------------


class TestSaveFetchResults:
    def _make_result(self) -> FetchResult:
        bm = Bookmark(label="TestBoard", url="https://test.com", category="Tech")
        board = FetchedBoard(bookmark=bm, content="Job listings here", char_count=17)
        return FetchResult(
            timestamp="2026-03-08T12:00:00+00:00",
            boards_requested=1,
            boards_fetched=1,
            boards_failed=0,
            boards=[board],
        )

    def test_creates_directory(self, tmp_path: Path) -> None:
        results_dir = tmp_path / "scan_results"
        result = self._make_result()
        filepath = save_fetch_results(result, results_dir)
        assert results_dir.is_dir()
        assert filepath.is_file()

    def test_valid_json(self, tmp_path: Path) -> None:
        results_dir = tmp_path / "scan_results"
        result = self._make_result()
        filepath = save_fetch_results(result, results_dir)

        with open(filepath) as f:
            data = json.load(f)

        assert data["timestamp"] == "2026-03-08T12:00:00+00:00"
        assert data["boards_requested"] == 1
        assert data["boards_fetched"] == 1
        assert data["boards_failed"] == 0
        assert len(data["boards"]) == 1

    def test_board_fields(self, tmp_path: Path) -> None:
        results_dir = tmp_path / "scan_results"
        result = self._make_result()
        filepath = save_fetch_results(result, results_dir)

        with open(filepath) as f:
            data = json.load(f)

        board = data["boards"][0]
        assert board["label"] == "TestBoard"
        assert board["url"] == "https://test.com"
        assert board["category"] == "Tech"
        assert board["char_count"] == 17
        assert board["content"] == "Job listings here"
        assert board["error"] == ""

    def test_filename_format(self, tmp_path: Path) -> None:
        results_dir = tmp_path / "scan_results"
        result = self._make_result()
        filepath = save_fetch_results(result, results_dir)
        assert filepath.name.endswith("_fetch.json")

    def test_error_board_included(self, tmp_path: Path) -> None:
        bm = Bookmark(label="Bad", url="https://bad.com", category="Cat")
        board = FetchedBoard(bookmark=bm, content="", char_count=0, error="404")
        result = FetchResult(
            timestamp="2026-03-08T12:00:00+00:00",
            boards_requested=1,
            boards_fetched=0,
            boards_failed=1,
            boards=[board],
        )
        results_dir = tmp_path / "scan_results"
        filepath = save_fetch_results(result, results_dir)

        with open(filepath) as f:
            data = json.load(f)

        assert data["boards"][0]["error"] == "404"
        assert data["boards"][0]["content"] == ""
