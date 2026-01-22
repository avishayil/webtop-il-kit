"""Integration tests for main scraper class.

Tests the orchestrator coordinating multiple modules.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from webtop_il_kit.scraper import WebtopScraper


@pytest.mark.asyncio
class TestWebtopScraperIntegration:
    """Integration tests for WebtopScraper orchestrator."""

    @pytest.fixture
    def scraper(self):
        """Create WebtopScraper instance."""
        with patch("webtop_il_kit.config.Config.USERNAME", "test_user"), patch("webtop_il_kit.config.Config.PASSWORD", "test_pass"):
            return WebtopScraper()

    @pytest.fixture
    def mock_playwright(self):
        """Create mock Playwright instance."""
        playwright = MagicMock()
        browser = AsyncMock()
        browser.contexts = []
        browser.new_context = AsyncMock()
        browser.close = AsyncMock()

        context = AsyncMock()
        context.new_page = AsyncMock()
        context.close = AsyncMock()
        browser.new_context.return_value = context

        page = AsyncMock()
        page.url = "https://webtop.smartschool.co.il/dashboard"
        context.new_page.return_value = page

        playwright.chromium.launch = AsyncMock(return_value=browser)
        return playwright, browser, context, page

    async def test_init_integration(self, scraper):
        """Integration test: scraper initialization with all modules."""
        assert scraper.username == "test_user"
        assert scraper.password == "test_pass"
        assert scraper.auth is not None
        assert scraper.navigator is not None
        assert scraper.extractor is not None

    async def test_get_today_homework_full_flow(self, scraper, mock_playwright):
        """Integration test: full flow from login to extraction."""
        playwright, browser, context, page = mock_playwright

        # Mock successful login and navigation
        scraper.auth.login = AsyncMock(return_value=True)
        scraper.navigator.navigate_to_homework = AsyncMock(return_value=True)
        scraper.extractor.extract_homework = AsyncMock(
            return_value=[
                {
                    "subject": "מתמטיקה",
                    "homework": "עמוד 45",
                    "date": "21/01/2026",
                }
            ]
        )

        with patch("playwright.async_api.async_playwright", return_value=playwright):
            result = await scraper.get_today_homework(date="21-01-2026")

        assert len(result) == 1
        assert result[0]["subject"] == "מתמטיקה"
        scraper.auth.login.assert_called_once()
        scraper.navigator.navigate_to_homework.assert_called_once()
        scraper.extractor.extract_homework.assert_called_once()

    async def test_get_today_homework_no_credentials(self):
        """Integration test: error handling when credentials are missing."""
        with patch("webtop_il_kit.config.Config.USERNAME", None), patch("webtop_il_kit.config.Config.PASSWORD", None):
            scraper = WebtopScraper()
            with pytest.raises(ValueError, match="MINISTRY_OF_EDUCATION_USERNAME"):
                await scraper.get_today_homework()

    async def test_get_today_homework_login_fails(self, scraper, mock_playwright):
        """Integration test: error handling when login fails."""
        playwright, browser, context, page = mock_playwright

        scraper.auth.login = AsyncMock(return_value=False)

        with patch("playwright.async_api.async_playwright", return_value=playwright):
            with pytest.raises(Exception, match="Failed to login"):
                await scraper.get_today_homework()

    async def test_get_today_homework_navigation_fails(self, scraper, mock_playwright):
        """Integration test: error handling when navigation fails."""
        playwright, browser, context, page = mock_playwright

        scraper.auth.login = AsyncMock(return_value=True)
        scraper.navigator.navigate_to_homework = AsyncMock(return_value=False)

        with patch("playwright.async_api.async_playwright", return_value=playwright):
            with pytest.raises(Exception, match="Failed to navigate"):
                await scraper.get_today_homework()

    async def test_get_today_homework_invalid_date(self, scraper):
        """Integration test: error handling for invalid date format."""
        with pytest.raises(ValueError):
            await scraper.get_today_homework(date="invalid-date")
