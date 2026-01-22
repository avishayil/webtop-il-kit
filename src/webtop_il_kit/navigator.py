"""Navigation module for Webtop scraper.

Handles navigation to homework pages.
"""
import asyncio
import logging

from playwright.async_api import Page

from .config import Config
from .selectors import Delays, Selectors, Timeouts

logger = logging.getLogger(__name__)


class WebtopNavigator:
    """Handles navigation within Webtop."""

    def __init__(self):
        """Initialize navigator.

        Sets up base URLs for navigation.
        """
        self.base_url = Config.BASE_URL
        self.student_card_url = Config.STUDENT_CARD_URL
        self.homework_url = Config.HOMEWORK_URL

    async def navigate_to_homework(self, page: Page) -> bool:
        """
        Navigate to homework section.

        Dashboard -> כרטיס תלמיד -> נושאי שיעור ושיעורי-בית

        Args:
            page: Playwright page object

        Returns:
            True if navigation successful, False otherwise
        """
        try:
            # Wait for page to load and ensure we're logged in
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(Delays.AFTER_PAGE_LOAD)

            # Check if we're still logged in
            current_url = page.url
            if Selectors.LOGIN_PAGE_INDICATOR in current_url.lower():
                logger.warning("Redirected to login page, session may have expired")
                return False

            # Step 1: Click on Student Card
            student_card_clicked = await self._click_student_card(page)

            if not student_card_clicked:
                # Try direct navigation
                logger.debug("Direct navigation to Student Card...")
                await page.goto(self.student_card_url, wait_until="networkidle")
                await asyncio.sleep(Delays.EXTRA_LONG)

                # Check if we were redirected to login
                current_url = page.url
                if Selectors.LOGIN_PAGE_INDICATOR in current_url.lower():
                    logger.error("Redirected to login when accessing Student Card")
                    return False

            # Step 2: Click on homework link
            homework_clicked = await self._click_homework_link(page)

            if not homework_clicked:
                # Try direct navigation
                logger.debug("Direct navigation to homework page...")
                await page.goto(self.homework_url, wait_until="networkidle")
                await asyncio.sleep(Delays.EXTRA_LONG)

            # Verify we're on the homework page
            return await self._verify_homework_page(page)

        except Exception as e:
            logger.error(f"Navigation error: {e}", exc_info=True)
            return False

    async def _click_student_card(self, page: Page) -> bool:
        """Click on Student Card link.

        Args:
            page: Playwright page object

        Returns:
            True if clicked successfully, False otherwise
        """
        logger.info("Clicking on Student Card...")
        for selector in Selectors.STUDENT_CARD_SELECTORS:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    await element.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                    await element.click()
                    try:
                        await page.wait_for_url(
                            Selectors.STUDENT_CARD_URL_PATTERN,
                            timeout=Timeouts.URL_WAIT,
                        )
                    except Exception as e:
                        logger.debug(f"URL wait timeout: {e}")
                    await page.wait_for_load_state("networkidle", timeout=Timeouts.NETWORK_IDLE)
                    await asyncio.sleep(Delays.AFTER_PAGE_LOAD)
                    logger.info("Successfully clicked Student Card")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        logger.debug("Could not click Student Card with any selector")
        return False

    async def _click_homework_link(self, page: Page) -> bool:
        """Click on homework link.

        Args:
            page: Playwright page object

        Returns:
            True if clicked successfully, False otherwise
        """
        logger.info("Clicking on Lesson topics and homework...")
        for selector in Selectors.HOMEWORK_SELECTORS:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    await element.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                    await element.click()
                    try:
                        await page.wait_for_url(
                            Selectors.HOMEWORK_URL_PATTERN,
                            timeout=Timeouts.URL_WAIT,
                        )
                    except Exception as e:
                        logger.debug(f"URL wait timeout: {e}")
                    await page.wait_for_load_state("networkidle", timeout=Timeouts.NETWORK_IDLE)
                    await asyncio.sleep(Delays.AFTER_PAGE_LOAD)
                    logger.info("Successfully clicked homework link")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        logger.debug("Could not click homework link with any selector")
        return False

    async def _verify_homework_page(self, page: Page) -> bool:
        """Verify we're on the homework page.

        Args:
            page: Playwright page object

        Returns:
            True if on homework page, False otherwise
        """
        current_url = page.url
        logger.debug(f"Final URL after navigation: {current_url}")

        if Selectors.LOGIN_PAGE_INDICATOR in current_url.lower():
            logger.error("Redirected to login page - session may have expired")
            return False

        if "Student_Card/11" in current_url or "Student_Card" in current_url:
            logger.info("Successfully navigated to homework page")
            return True
        else:
            logger.warning(f"Expected Student_Card/11, but got: {current_url}")
            try:
                await page.wait_for_selector("h2, table", timeout=Timeouts.ELEMENT_VISIBLE)
                logger.debug("Found page content, assuming navigation successful")
                return True
            except Exception as e:
                logger.debug(f"Could not verify page content: {e}")
                return False
