"""Tests for jobbing.browser — Playwright+stealth page fetching."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jobbing.browser import BrowseResult, fetch_page, fetch_pages


# ---------------------------------------------------------------------------
# BrowseResult dataclass
# ---------------------------------------------------------------------------


class TestBrowseResult:
    def test_fields(self) -> None:
        r = BrowseResult(
            url="https://example.com",
            title="Example",
            company="Acme",
            description="A job posting",
            location="Remote",
            raw_text="Engineer needed",
            char_count=15,
        )
        assert r.url == "https://example.com"
        assert r.title == "Example"
        assert r.company == "Acme"
        assert r.error == ""

    def test_error_default(self) -> None:
        r = BrowseResult(
            url="https://fail.com",
            title="",
            company="",
            description="",
            location="",
            raw_text="",
            char_count=0,
            error="Timeout",
        )
        assert r.error == "Timeout"
        assert r.char_count == 0


# ---------------------------------------------------------------------------
# fetch_page() — mocked Playwright
# ---------------------------------------------------------------------------


def _mock_playwright_stack(evaluate_return: dict | None = None):
    """Build a nested mock that simulates async_playwright context."""
    if evaluate_return is None:
        evaluate_return = {
            "title": "Test Page",
            "company": "TestCo",
            "description": "A test description",
            "location": "",
            "raw_text": "Some job content here",
        }

    mock_page = AsyncMock()
    mock_page.goto = AsyncMock()
    mock_page.evaluate = AsyncMock(return_value=evaluate_return)
    mock_page.close = AsyncMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()

    mock_pw = MagicMock()
    mock_pw.chromium = MagicMock()
    mock_pw.chromium.launch = AsyncMock(return_value=mock_browser)

    # Make it work as async context manager
    mock_pw_cm = AsyncMock()
    mock_pw_cm.__aenter__ = AsyncMock(return_value=mock_pw)
    mock_pw_cm.__aexit__ = AsyncMock(return_value=False)

    return mock_pw_cm, mock_page


class TestFetchPage:
    def test_success(self) -> None:
        mock_pw_cm, mock_page = _mock_playwright_stack()

        with (
            patch("jobbing.browser.async_playwright", return_value=mock_pw_cm),
            patch("jobbing.browser._STEALTH") as mock_stealth,
        ):
            mock_stealth.apply_stealth_async = AsyncMock()
            result = asyncio.run(fetch_page("https://test.com/jobs"))

        assert result.url == "https://test.com/jobs"
        assert result.title == "Test Page"
        assert result.company == "TestCo"
        assert result.description == "A test description"
        assert result.char_count > 0
        assert result.error == ""

    def test_navigation_error(self) -> None:
        mock_pw_cm, mock_page = _mock_playwright_stack()
        mock_page.goto = AsyncMock(side_effect=Exception("net::ERR_NAME_NOT_RESOLVED"))

        with (
            patch("jobbing.browser.async_playwright", return_value=mock_pw_cm),
            patch("jobbing.browser._STEALTH") as mock_stealth,
        ):
            mock_stealth.apply_stealth_async = AsyncMock()
            result = asyncio.run(fetch_page("https://nonexistent.invalid"))

        assert result.error != ""
        assert "ERR_NAME_NOT_RESOLVED" in result.error
        assert result.char_count == 0

    def test_timeout_error(self) -> None:
        mock_pw_cm, mock_page = _mock_playwright_stack()
        mock_page.goto = AsyncMock(side_effect=Exception("Timeout 30000ms exceeded"))

        with (
            patch("jobbing.browser.async_playwright", return_value=mock_pw_cm),
            patch("jobbing.browser._STEALTH") as mock_stealth,
        ):
            mock_stealth.apply_stealth_async = AsyncMock()
            result = asyncio.run(fetch_page("https://slow.com", timeout_ms=100))

        assert "Timeout" in result.error
        assert result.char_count == 0


# ---------------------------------------------------------------------------
# fetch_pages() — mocked Playwright
# ---------------------------------------------------------------------------


class TestFetchPages:
    def test_empty_urls(self) -> None:
        result = asyncio.run(fetch_pages([]))
        assert result == []

    def test_multiple_urls(self) -> None:
        mock_pw_cm, mock_page = _mock_playwright_stack()

        with (
            patch("jobbing.browser.async_playwright", return_value=mock_pw_cm),
            patch("jobbing.browser._STEALTH") as mock_stealth,
        ):
            mock_stealth.apply_stealth_async = AsyncMock()
            results = asyncio.run(
                fetch_pages(["https://a.com", "https://b.com", "https://c.com"])
            )

        assert len(results) == 3
        # All should succeed with the mock
        for r in results:
            assert r.error == ""
            assert r.title == "Test Page"

    def test_mixed_success_and_failure(self) -> None:
        """One URL succeeds, another fails at navigation."""
        call_count = 0

        async def goto_side_effect(url, **kwargs):
            nonlocal call_count
            call_count += 1
            if "bad" in url:
                raise Exception("Connection refused")

        mock_pw_cm, mock_page = _mock_playwright_stack()
        mock_page.goto = AsyncMock(side_effect=goto_side_effect)

        with (
            patch("jobbing.browser.async_playwright", return_value=mock_pw_cm),
            patch("jobbing.browser._STEALTH") as mock_stealth,
        ):
            mock_stealth.apply_stealth_async = AsyncMock()
            results = asyncio.run(
                fetch_pages(["https://good.com", "https://bad.com"])
            )

        assert len(results) == 2
        # good.com succeeds (goto doesn't raise, evaluate returns mock data)
        assert results[0].error == ""
        # bad.com fails
        assert "Connection refused" in results[1].error
