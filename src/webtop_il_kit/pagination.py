"""Pagination module for Webtop scraper.

Handles navigation through paginated homework pages.
"""
import asyncio
import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple

from playwright.async_api import Locator, Page

from .config import Config
from .selectors import Delays, Selectors, Timeouts

logger = logging.getLogger(__name__)


class WebtopPagination:
    """Handles pagination to find specific dates."""

    async def find_date_on_page(self, page: Page, target_date_str: str) -> bool:
        """
        Check if a specific date is visible on the current page.

        Args:
            page: Playwright page object
            target_date_str: Date string in format "DD/MM/YYYY"

        Returns:
            True if date is found on page, False otherwise
        """
        try:
            # Wait for page to be fully loaded and scroll to ensure all content is visible
            await page.wait_for_load_state("networkidle", timeout=Timeouts.NETWORK_IDLE)

            # Scroll to bottom to ensure all content is loaded (lazy loading)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)  # Wait for any lazy-loaded content

            # Scroll back to top
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            # Wait for date headings to be visible
            try:
                await page.wait_for_selector(
                    Selectors.DATE_HEADING,
                    state="visible",
                    timeout=Timeouts.ELEMENT_VISIBLE,
                )
            except Exception:
                # If selector doesn't match, continue anyway
                pass

            headings = await page.locator(Selectors.DATE_HEADING).all()
            for heading in headings:
                # Scroll element into view to ensure it's loaded
                try:
                    await heading.scroll_into_view_if_needed()
                    await page.wait_for_timeout(200)  # Small delay after scrolling
                except Exception:
                    pass

                heading_text = await heading.text_content()
                if heading_text and target_date_str in heading_text:
                    logger.info(f"Found date {target_date_str} on page")
                    return True
            logger.debug(f"Date {target_date_str} not found on current page")
            return False
        except Exception as e:
            logger.debug(f"Error finding date on page: {e}")
            return False

    async def get_dates_on_page(self, page: Page) -> List[datetime]:
        """
        Get all dates visible on the current page.

        Args:
            page: Playwright page object

        Returns:
            List of datetime objects for dates found on page
        """
        dates = []
        try:
            # Wait for page to be fully loaded and scroll to ensure all content is visible
            await page.wait_for_load_state("networkidle", timeout=Timeouts.NETWORK_IDLE)

            # Scroll to bottom to ensure all content is loaded (lazy loading)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)  # Wait for any lazy-loaded content

            # Wait for date headings to be visible
            try:
                await page.wait_for_selector(
                    Selectors.DATE_HEADING,
                    state="visible",
                    timeout=Timeouts.ELEMENT_VISIBLE,
                )
            except Exception:
                # If selector doesn't match, continue anyway
                pass

            headings = await page.locator(Selectors.DATE_HEADING).all()
            for heading in headings:
                # Scroll element into view to ensure it's loaded
                try:
                    await heading.scroll_into_view_if_needed()
                    await page.wait_for_timeout(200)  # Small delay after scrolling
                except Exception:
                    pass

                heading_text = await heading.text_content()
                if heading_text:
                    # Extract date from heading format:
                    # "יום רביעי | 21/01/2026 | ג׳ שְׁבָט תשפ״ו"
                    date_match = re.search(Selectors.DATE_REGEX_PATTERN, heading_text)
                    if date_match:
                        day, month, year = date_match.groups()
                        try:
                            date_obj = datetime(int(year), int(month), int(day))
                            dates.append(date_obj)
                        except (ValueError, TypeError) as e:
                            logger.debug(f"Error parsing date from heading '{heading_text}': {e}")
        except Exception as e:
            logger.debug(f"Error getting dates from page: {e}")
        logger.debug(f"Found {len(dates)} dates on page: {[d.strftime('%d/%m/%Y') for d in sorted(dates)]}")
        return sorted(dates)

    async def navigate_to_date_page(self, page: Page, target_date: datetime) -> bool:
        """Navigate through pagination to find the target date page.

        Handles both forward (future dates) and backward (past dates)
        navigation.

        Args:
            page: Playwright page object
            target_date: Target date to find

        Returns:
            True if date was found, False otherwise
        """
        target_date_str = target_date.strftime(Selectors.DATE_FORMAT_DISPLAY)
        max_pages = Config.MAX_PAGINATION_PAGES
        pages_checked = 0
        visited_pages = set()

        # First check if date is already on current page
        if await self.find_date_on_page(page, target_date_str):
            logger.info(f"Target date {target_date_str} found on current page")
            return True

        logger.info(f"Target date {target_date_str} not on current page, searching through pagination...")

        # Get dates on current page to determine navigation direction
        current_dates = await self.get_dates_on_page(page)
        if current_dates:
            if target_date < current_dates[0]:
                logger.info("Target date is older than current page, navigating backwards...")
                direction = "backward"
            elif target_date > current_dates[-1]:
                logger.info("Target date is newer than current page, navigating forwards...")
                direction = "forward"
            else:
                logger.warning("Target date should be on current page but not found")
                return False
        else:
            logger.debug("No dates found on current page, defaulting to forward navigation")
            direction = "forward"

        # Navigate through pages
        while pages_checked < max_pages:
            pages_checked += 1

            current_url = page.url
            if current_url in visited_pages:
                logger.debug("Already visited this page, trying opposite direction or stopping")
                if direction == "forward":
                    direction = "backward"
                    visited_pages.clear()
                    continue
                else:
                    logger.debug("Already visited page in both directions, stopping")
                    break
            visited_pages.add(current_url)

            # Get navigation button based on direction
            nav_button = await self._find_navigation_button(page, direction)

            # Check current page again
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(Delays.LONG)

            if await self.find_date_on_page(page, target_date_str):
                logger.info(f"Target date {target_date_str} found after navigating")
                return True

            # Click navigation button if found
            if nav_button:
                found, new_direction = await self._click_navigation_button(page, nav_button, direction, pages_checked, target_date)
                if found:
                    return True
                if new_direction != direction:
                    direction = new_direction
                    visited_pages.clear()
                    continue
            else:
                # Try switching direction or stop
                if direction == "forward":
                    logger.debug("No forward button found, trying backward navigation...")
                    direction = "backward"
                    visited_pages.clear()
                    continue
                else:
                    logger.debug("No navigation button found, reached end of pagination")
                    break

        logger.warning(f"Could not find date {target_date_str} after checking {pages_checked} pages")
        return False

    async def _find_navigation_button(self, page: Page, direction: str) -> Optional[Locator]:
        """Find the navigation button for the given direction.

        Args:
            page: Playwright page object
            direction: "forward" or "backward"

        Returns:
            Button locator if found, None otherwise
        """
        # Scroll to top to ensure navigation buttons are visible
        # The buttons are in the toolbar at the top of the page
        try:
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)  # Wait for scroll to complete
            logger.debug("Scrolled to top to find navigation buttons")

            # Wait for toolbar to be visible
            try:
                await page.wait_for_selector("app-tool-bar", state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                logger.debug("Toolbar is visible")
            except Exception:
                logger.debug("Toolbar not found, continuing anyway")
        except Exception as e:
            logger.debug(f"Error scrolling to top: {e}")

        if direction == "forward":
            button_selectors = [
                # Webtop-specific: Next week button in toolbar (most specific, highest priority)
                "#main app-multi-cards-view app-lesson-homework app-lesson-homework-view app-tool-bar span:nth-child(3) > a",
                "app-tool-bar span:nth-child(3) > a",
                "app-tool-bar div > div > span:nth-child(3) > a",
                "#main app-tool-bar span:nth-child(3) > a",
                # Webtop-specific: Next week button with mat-icon
                'a[role="button"]:has-text("שבוע הבא")',
                'a[role="button"]:has(mat-icon[svgicon="navigate_next"])',
                'a:has(mat-icon[svgicon="navigate_next"])',
                'a.link-text:has(mat-icon[svgicon="navigate_next"])',
                # Generic selectors (fallback)
                'button:has-text("הבא")',
                'button:has-text("Next")',
                'a:has-text("הבא")',
                'a:has-text("Next")',
                '[aria-label*="הבא"]',
                '[aria-label*="Next"]',
                'button[aria-label*="הבא"]',
                ".pagination button:last-child",
                ".pagination a:last-child",
                '[class*="next"]',
                '[class*="Next"]',
            ]
        else:  # backward
            button_selectors = [
                # Webtop-specific: Previous week button in toolbar (most specific, highest priority)
                "#main app-multi-cards-view app-lesson-homework app-lesson-homework-view app-tool-bar span:nth-child(1) > a",
                "app-tool-bar span:nth-child(1) > a",
                "app-tool-bar div > div > span:nth-child(1) > a",
                "#main app-tool-bar span:nth-child(1) > a",
                # Webtop-specific: Previous week button with mat-icon
                'a[role="button"]:has-text("שבוע קודם")',
                'a[role="button"]:has(mat-icon[svgicon="navigate_before"])',
                'a:has(mat-icon[svgicon="navigate_before"])',
                'a.link-text:has(mat-icon[svgicon="navigate_before"])',
                # Generic selectors (fallback)
                'button:has-text("הקודם")',
                'button:has-text("Previous")',
                'button:has-text("קודם")',
                'a:has-text("הקודם")',
                'a:has-text("Previous")',
                'a:has-text("קודם")',
                '[aria-label*="הקודם"]',
                '[aria-label*="Previous"]',
                '[aria-label*="קודם"]',
                'button[aria-label*="הקודם"]',
                ".pagination button:first-child",
                ".pagination a:first-child",
                '[class*="prev"]',
                '[class*="Prev"]',
                '[class*="previous"]',
            ]

        for selector in button_selectors:
            try:
                btn = page.locator(selector).first
                count = await btn.count()
                logger.debug(f"Trying selector '{selector}': found {count} elements")

                if count > 0:
                    is_visible = await btn.is_visible()
                    logger.debug(f"  Element visible: {is_visible}")

                    # For <a role="button">, check if it's disabled by checking for 'empty' class or disabled attribute
                    is_disabled = await btn.get_attribute("disabled")
                    aria_disabled = await btn.get_attribute("aria-disabled")

                    # Check if the link has the 'empty' class (which indicates it's disabled in Webtop)
                    has_empty_class = False
                    try:
                        class_attr = await btn.get_attribute("class")
                        if class_attr:
                            logger.debug(f"  Element class: {class_attr}")
                            if "empty" in class_attr:
                                has_empty_class = True
                                logger.debug("  Element has 'empty' class - disabled")
                    except Exception as e:
                        logger.debug(f"  Could not get class attribute: {e}")

                    if is_visible and not is_disabled and aria_disabled != "true" and not has_empty_class:
                        logger.info(f"Found {direction} navigation button with selector: {selector}")
                        return btn
                    else:
                        logger.debug(
                            f"  Button not usable: visible={is_visible}, "
                            f"disabled={is_disabled}, aria_disabled={aria_disabled}, "
                            f"has_empty_class={has_empty_class}"
                        )
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        logger.warning(f"No {direction} navigation button found after trying {len(button_selectors)} selectors")
        return None

    async def _click_navigation_button(
        self,
        page: Page,
        nav_button: Locator,
        direction: str,
        pages_checked: int,
        target_date: datetime,
    ) -> Tuple[bool, str]:
        """Click navigation button and check if target date is found."""
        target_date_str = target_date.strftime(Selectors.DATE_FORMAT_DISPLAY)
        try:
            direction_text = "forward" if direction == "forward" else "backward"
            logger.info(f"Clicking {direction_text} button (attempt {pages_checked})...")

            # Scroll button into view and wait for it to be ready
            await nav_button.scroll_into_view_if_needed()
            await page.wait_for_timeout(300)  # Small delay after scrolling

            # Wait for button to be visible and enabled
            await nav_button.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)

            # Click the button - try force click if regular click doesn't work
            try:
                await nav_button.click(timeout=Timeouts.ELEMENT_VISIBLE)
            except Exception as click_error:
                logger.debug(f"Regular click failed, trying force click: {click_error}")
                await nav_button.click(force=True, timeout=Timeouts.ELEMENT_VISIBLE)

            # Wait for page to update after click
            await page.wait_for_load_state("networkidle", timeout=Timeouts.NETWORK_IDLE)
            await asyncio.sleep(Delays.AFTER_PAGE_LOAD)

            # Check if date is now on page
            if await self.find_date_on_page(page, target_date_str):
                logger.info(f"Target date {target_date_str} found after {pages_checked} navigation steps")
                return True, direction

            # Update direction if needed based on new dates on page
            new_dates = await self.get_dates_on_page(page)
            if new_dates:
                if target_date < new_dates[0] and direction == "forward":
                    logger.debug("Switching to backward navigation")
                    direction = "backward"
                elif target_date > new_dates[-1] and direction == "backward":
                    logger.debug("Switching to forward navigation")
                    direction = "forward"
        except Exception as e:
            logger.warning(f"Error clicking navigation button: {e}", exc_info=True)
            if direction == "forward":
                direction = "backward"
            else:
                direction = "forward"
        return False, direction
