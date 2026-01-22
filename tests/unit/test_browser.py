"""Unit tests for browser management module.

Tests individual methods in isolation with heavy mocking.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from webtop_il_kit.browser import WebtopBrowser


@pytest.mark.asyncio
class TestWebtopBrowser:
    """Unit tests for WebtopBrowser class methods."""

    @pytest.fixture
    def mock_browser(self):
        """Create mock browser."""
        browser = AsyncMock()
        browser.contexts = []
        browser.new_context = AsyncMock()
        browser.close = AsyncMock()
        return browser

    @pytest.fixture
    def mock_playwright(self, mock_browser):
        """Create mock Playwright instance."""
        playwright = MagicMock()
        playwright.chromium.launch = AsyncMock(return_value=mock_browser)
        playwright.webkit.launch = AsyncMock(return_value=mock_browser)
        playwright.firefox.launch = AsyncMock(return_value=mock_browser)
        return playwright

    async def test_launch_browser_success_chrome(self, mock_playwright, mock_browser):
        """Unit test: successful browser launch with Chrome."""
        result = await WebtopBrowser.launch_browser(mock_playwright)
        assert result == mock_browser
        mock_playwright.chromium.launch.assert_called_once()

    async def test_launch_browser_fallback_chromium(self, mock_playwright, mock_browser):
        """Unit test: browser launch with fallback to Chromium."""
        mock_playwright.chromium.launch.side_effect = [
            Exception("Chrome failed"),
            mock_browser,  # Chromium succeeds
        ]

        result = await WebtopBrowser.launch_browser(mock_playwright)
        assert result == mock_browser
        assert mock_playwright.chromium.launch.call_count == 2

    async def test_launch_browser_all_fail(self, mock_playwright):
        """Unit test: when all browsers fail to launch."""
        mock_playwright.chromium.launch.side_effect = Exception("Failed")
        mock_playwright.webkit.launch.side_effect = Exception("Failed")
        mock_playwright.firefox.launch.side_effect = Exception("Failed")

        with pytest.raises(Exception, match="Failed to launch any browser"):
            await WebtopBrowser.launch_browser(mock_playwright)

    async def test_create_context(self, mock_browser):
        """Unit test: creating browser context."""
        context = await WebtopBrowser.create_context(mock_browser)
        assert context is not None
        mock_browser.new_context.assert_called_once()

    async def test_create_page(self):
        """Unit test: creating page in context."""
        context = AsyncMock()
        page = AsyncMock()
        context.new_page = AsyncMock(return_value=page)

        result = await WebtopBrowser.create_page(context)
        assert result == page
        context.new_page.assert_called_once()
