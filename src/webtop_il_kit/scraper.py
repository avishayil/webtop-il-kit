"""Main Webtop scraper orchestrator.

Coordinates authentication, navigation, and extraction.
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional

from playwright.async_api import async_playwright

from .auth import WebtopAuth
from .browser import WebtopBrowser
from .config import Config
from .extractor import WebtopExtractor
from .navigator import WebtopNavigator
from .selectors import Selectors
from .utils import parse_date

logger = logging.getLogger(__name__)


class WebtopScraper:
    """Main scraper class for Webtop homework system."""

    def __init__(self):
        """Initialize the scraper.

        Sets up authentication, navigation, and extraction components.
        """
        self.username = Config.USERNAME
        self.password = Config.PASSWORD
        self.auth = WebtopAuth(self.username, self.password)
        self.navigator = WebtopNavigator()
        self.extractor = WebtopExtractor()

    async def get_today_homework(self, date: Optional[str] = None) -> List[Dict]:
        """
        Get homework for a specific date or today.

        Args:
            date: Optional date string in format "DD-MM-YYYY"
                (e.g., "21-01-2026"). If None, uses today's date.

        Returns:
            List of homework items for the specified date
        """
        if not self.username or not self.password:
            raise ValueError("MINISTRY_OF_EDUCATION_USERNAME and MINISTRY_OF_EDUCATION_PASSWORD must be set in environment variables")

        # Parse the date if provided
        target_date: Optional[datetime] = None
        if date:
            target_date = parse_date(date)
            logger.info(f"Fetching homework for date: {target_date.strftime(Selectors.DATE_FORMAT_DISPLAY)}")
        else:
            target_date = datetime.now()
            logger.info(f"Fetching homework for today: {target_date.strftime(Selectors.DATE_FORMAT_DISPLAY)}")

        # Use async context manager for Playwright
        async with async_playwright() as playwright:
            browser = None
            context = None
            try:
                logger.info("Launching browser...")
                browser = await WebtopBrowser.launch_browser(playwright)

                context = await WebtopBrowser.create_context(browser)
                page = await WebtopBrowser.create_page(context)

                # Login
                logger.info("Attempting login...")
                logger.debug(f"Username configured: {bool(self.username)}")
                if not self.username or not self.password:
                    raise ValueError(
                        "Credentials not configured. "
                        "Set MINISTRY_OF_EDUCATION_USERNAME and "
                        "MINISTRY_OF_EDUCATION_PASSWORD environment variables."
                    )
                login_success = await self.auth.login(page)
                if not login_success:
                    error_msg = (
                        "Failed to login to Webtop. "
                        "Check login_debug.png screenshot for details. "
                        "Possible reasons: invalid credentials, "
                        "reCAPTCHA challenge, network timeout, or "
                        "browser automation detection."
                    )
                    raise Exception(error_msg)
                logger.info("Login successful")

                # Navigate to homework page
                logger.info("Navigating to homework page...")
                nav_success = await self.navigator.navigate_to_homework(page)
                if not nav_success:
                    raise Exception("Failed to navigate to homework page")

                # Extract homework
                logger.info("Extracting homework...")
                homework = await self.extractor.extract_homework(page, target_date=target_date)
                logger.info(f"Found {len(homework)} homework items")

                if context:
                    await context.close()
                if browser:
                    await browser.close()
                return homework

            except Exception as e:
                logger.error(f"Error in get_today_homework: {e}", exc_info=True)
                # Clean up resources
                try:
                    if context:
                        await context.close()
                    if browser:
                        await browser.close()
                except Exception as cleanup_error:
                    logger.debug(f"Error during cleanup: {cleanup_error}")
                raise
