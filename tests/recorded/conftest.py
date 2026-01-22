"""Fixtures for recorded tests."""
from pathlib import Path

import pytest
from playwright.async_api import async_playwright
from webtop_il_kit.extractor import WebtopExtractor
from webtop_il_kit.pagination import WebtopPagination


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def extractor():
    """Create a WebtopExtractor instance."""
    return WebtopExtractor()


@pytest.fixture
def pagination():
    """Create a WebtopPagination instance."""
    return WebtopPagination()


@pytest.fixture
async def mock_page_with_html(fixtures_dir):
    """Create a Playwright page loaded with HTML from a fixture file."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        yield page, fixtures_dir

        await context.close()
        await browser.close()


async def load_html_fixture(page, fixtures_dir, filename):
    """Load HTML from a fixture file into a Playwright page."""
    fixture_path = fixtures_dir / filename
    if not fixture_path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    html_content = fixture_path.read_text(encoding="utf-8")
    await page.set_content(html_content, wait_until="networkidle")
    return page
