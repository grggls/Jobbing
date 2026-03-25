"""Headless browser fetching via Playwright + stealth.

Single-URL and batch fetching with structured JSON output.
No LLM calls — deterministic page fetch and metadata extraction.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

logger = logging.getLogger(__name__)

# Defaults
DEFAULT_TIMEOUT_MS = 30_000
DEFAULT_EXTRA_WAIT_S = 2.0
DEFAULT_CONCURRENCY = 8
MAX_PAGE_CHARS = 80_000

_STEALTH = Stealth()


@dataclass
class BrowseResult:
    """Structured output from a single page fetch."""

    url: str
    title: str
    company: str  # from og:site_name
    description: str  # from og:description or meta description
    location: str  # best-effort (usually empty)
    raw_text: str  # body.innerText, truncated to MAX_PAGE_CHARS
    char_count: int
    error: str = ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_page(
    url: str,
    *,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    extra_wait_s: float = DEFAULT_EXTRA_WAIT_S,
    wait_until: str = "domcontentloaded",
) -> BrowseResult:
    """Fetch a single URL with a fresh browser instance.

    Launches and closes its own browser — clean for one-off CLI calls.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        await _STEALTH.apply_stealth_async(context)
        page = await context.new_page()

        try:
            await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
            if extra_wait_s > 0:
                await asyncio.sleep(extra_wait_s)
            result = await _extract(page, url)
        except Exception as e:
            result = BrowseResult(
                url=url,
                title="",
                company="",
                description="",
                location="",
                raw_text="",
                char_count=0,
                error=str(e),
            )
        finally:
            await browser.close()

    return result


async def fetch_pages(
    urls: list[str],
    *,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    extra_wait_s: float = DEFAULT_EXTRA_WAIT_S,
    wait_until: str = "domcontentloaded",
    concurrency: int = DEFAULT_CONCURRENCY,
) -> list[BrowseResult]:
    """Fetch multiple URLs concurrently using a shared browser.

    Uses asyncio.Semaphore to limit concurrent pages.
    Returns results in the same order as the input URLs.
    """
    if not urls:
        return []

    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        await _STEALTH.apply_stealth_async(context)

        async def _fetch_one(url: str) -> BrowseResult:
            async with semaphore:
                page = await context.new_page()
                try:
                    await page.goto(url, wait_until=wait_until, timeout=timeout_ms)
                    if extra_wait_s > 0:
                        await asyncio.sleep(extra_wait_s)
                    return await _extract(page, url)
                except Exception as e:
                    return BrowseResult(
                        url=url,
                        title="",
                        company="",
                        description="",
                        location="",
                        raw_text="",
                        char_count=0,
                        error=str(e),
                    )
                finally:
                    await page.close()

        results = await asyncio.gather(*[_fetch_one(u) for u in urls])
        await browser.close()

    return list(results)


# ---------------------------------------------------------------------------
# Internal
# ---------------------------------------------------------------------------

_EXTRACT_JS = """() => {
    const meta = (name) => {
        const el = document.querySelector(
            `meta[property="${name}"], meta[name="${name}"]`
        );
        return el ? (el.content || '') : '';
    };
    return {
        title: document.title || '',
        company: meta('og:site_name') || '',
        description: meta('og:description') || meta('description') || '',
        location: '',
        raw_text: document.body ? document.body.innerText : '',
    };
}"""


async def _extract(page: object, url: str) -> BrowseResult:
    """Extract structured data from a loaded page via a single JS evaluation."""
    data = await page.evaluate(_EXTRACT_JS)  # type: ignore[union-attr]

    raw_text = (data.get("raw_text") or "")[:MAX_PAGE_CHARS]
    # Normalize whitespace runs but preserve newlines for readability
    raw_text = re.sub(r"[^\S\n]+", " ", raw_text)
    raw_text = re.sub(r"\n{3,}", "\n\n", raw_text)
    raw_text = raw_text.strip()

    return BrowseResult(
        url=url,
        title=data.get("title", ""),
        company=data.get("company", ""),
        description=data.get("description", ""),
        location=data.get("location", ""),
        raw_text=raw_text,
        char_count=len(raw_text),
    )
