"""Extraction module for Webtop scraper.

Handles extraction of homework data from DOM.
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from playwright.async_api import Locator, Page

from .pagination import WebtopPagination
from .selectors import Delays, Selectors, TextPatterns, Timeouts

logger = logging.getLogger(__name__)


class WebtopExtractor:
    """Handles extraction of homework data from pages."""

    def __init__(self):
        """Initialize extractor."""
        self.pagination = WebtopPagination()

    async def extract_homework(self, page: Page, target_date: Optional[datetime] = None) -> List[Dict]:
        """Extract homework data by scraping the DOM table.

        Supports pagination to find older dates.

        Args:
            page: Playwright page object
            target_date: Optional datetime object for the date to extract.
                If None, uses today.

        Returns:
            List of homework items with details
        """
        homework_list = []

        try:
            # Wait for content to load
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(Delays.AFTER_PAGE_LOAD)

            # Get the target date (default to today)
            if target_date is None:
                target_date = datetime.now()

            # Format date in the format used on the page
            target_date_str = target_date.strftime(Selectors.DATE_FORMAT_DISPLAY)

            # Check if we need to navigate through pagination
            if not await self.pagination.find_date_on_page(page, target_date_str):
                logger.info(f"Date {target_date_str} not on current page, attempting pagination")
                # Try to navigate to the date using pagination
                if not await self.pagination.navigate_to_date_page(page, target_date):
                    logger.warning(f"Could not find date {target_date_str} after pagination")
                    return homework_list
                logger.info(f"Successfully navigated to page containing {target_date_str}")

            # Find the heading and table for the target date
            target_heading = await self._find_date_heading(page, target_date_str)
            if not target_heading:
                logger.warning(f"Could not find heading for date {target_date_str}")
                return homework_list
            logger.info(f"Found heading for date {target_date_str}")

            # Find the table for this date
            table = await self._find_date_table(page, target_date_str, target_heading)
            if not table:
                logger.warning(f"Could not find table for date {target_date_str}")
                return homework_list
            logger.info(f"Found table for date {target_date_str}")

            # Extract homework items from the table
            homework_list = await self._extract_table_data(page, table, target_date_str)
            logger.info(f"Extracted {len(homework_list)} homework items for {target_date_str}")

            return homework_list

        except Exception as e:
            logger.error(
                f"Extraction error for date {target_date_str if 'target_date_str' in locals() else 'unknown'}: {e}",
                exc_info=True,
            )
            return homework_list

    async def _find_date_heading(self, page: Page, target_date_str: str) -> Optional[Locator]:
        """Find the heading element for the target date.

        Args:
            page: Playwright page object
            target_date_str: Target date string in format "DD/MM/YYYY"

        Returns:
            Heading locator if found, None otherwise
        """
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
            if heading_text and target_date_str in heading_text:
                return heading
        return None

    async def _find_date_table(self, page: Page, target_date_str: str, target_heading: Locator) -> Optional[Locator]:
        """Find the table element for the target date.

        Args:
            page: Playwright page object
            target_date_str: Target date string in format "DD/MM/YYYY"
            target_heading: The heading element for the target date

        Returns:
            Table locator if found, None otherwise
        """
        # Scroll the heading into view first to ensure the table below it is loaded
        try:
            await target_heading.scroll_into_view_if_needed()
            await page.wait_for_timeout(500)  # Wait for content to load after scrolling
        except Exception as e:
            logger.debug(f"Could not scroll heading into view: {e}")

        # Method 1: Find table by aria-label
        try:
            table_selector = Selectors.TABLE_ARIA_LABEL_PATTERN.format(date=target_date_str)
            table = page.locator(table_selector).first
            await table.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
            logger.debug(f"Found table by aria-label for {target_date_str}")
            return table
        except Exception as e:
            logger.debug(f"Method 1 (aria-label) failed for {target_date_str}: {e}")

        # Method 2: Find table after the heading (scroll to heading first)
        try:
            # Scroll heading into view to ensure table below is loaded
            await target_heading.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)  # Wait for lazy-loaded content

            # Find all tables with role="table"
            all_tables = await page.locator(Selectors.TABLE_SELECTOR).all()
            heading_element = await target_heading.element_handle()

            if heading_element:
                for tab in all_tables:
                    # Scroll table into view to ensure it's loaded
                    try:
                        await tab.scroll_into_view_if_needed()
                        await page.wait_for_timeout(300)
                    except Exception:
                        pass

                    tab_aria = await tab.get_attribute("aria-label")
                    if tab_aria and target_date_str in tab_aria:
                        logger.debug(f"Found table by aria-label search for {target_date_str}")
                        return tab
        except Exception as e:
            logger.debug(f"Method 2 (heading-based search) failed for {target_date_str}: {e}")

        # Method 3: Find table by finding the parent card and then the table within it
        try:
            # Scroll heading into view first
            await target_heading.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)  # Wait for lazy-loaded content

            # The table is inside a mat-card-content, find the card that contains our heading
            # Find all mat-card elements and check which one contains our heading
            all_cards = page.locator("mat-card")
            card_count = await all_cards.count()
            logger.debug(f"Found {card_count} mat-card elements")

            for i in range(card_count):
                card = all_cards.nth(i)
                try:
                    # Check if this card contains our heading by looking for the heading text
                    heading_text = await target_heading.text_content()
                    if heading_text:
                        # Check if card contains a heading with our date
                        heading_in_card = card.locator(f'span[role="heading"]:has-text("{target_date_str}")')
                        if await heading_in_card.count() > 0:
                            # Found the card, now find the table within it
                            # Scroll the card into view to ensure table is loaded
                            await card.scroll_into_view_if_needed()
                            await page.wait_for_timeout(500)

                            # Find table within the card
                            table = card.locator('div[role="table"]').first
                            if await table.count() > 0:
                                await table.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                                logger.debug(f"Found table by parent card (method 3) for {target_date_str}")
                                return table
                except Exception as e:
                    logger.debug(f"Error checking card {i}: {e}")
                    continue
        except Exception as e:
            logger.debug(f"Method 3 (parent card) failed for {target_date_str}: {e}")

        # Method 4: Find table by searching for div[role="table"] near the heading
        try:
            # Scroll heading into view
            await target_heading.scroll_into_view_if_needed()
            await page.wait_for_timeout(1000)

            # Find all divs with role="table" and check their aria-label
            all_tables = page.locator('div[role="table"]')
            count = await all_tables.count()
            logger.debug(f"Found {count} div[role='table'] elements")

            for i in range(count):
                table = all_tables.nth(i)
                try:
                    await table.scroll_into_view_if_needed()
                    await page.wait_for_timeout(300)
                    aria_label = await table.get_attribute("aria-label")
                    if aria_label and target_date_str in aria_label:
                        logger.debug(f"Found table by div[role='table'] aria-label for {target_date_str}")
                        return table
                except Exception:
                    continue
        except Exception as e:
            logger.debug(f"Method 4 (div role=table) failed for {target_date_str}: {e}")

        logger.warning(f"Could not find table for date {target_date_str}")
        return None

    async def _extract_table_data(self, page: Page, table: Locator, target_date_str: str) -> List[Dict[str, any]]:
        """Extract homework data from the table."""
        homework_list = []

        # Wait for table to be visible
        try:
            await table.wait_for(state="visible", timeout=Timeouts.ELEMENT_WAIT)
        except Exception as e:
            logger.warning(f"Table found but not visible: {e}")

        # Get all data rows (skip header)
        rows = await table.locator(Selectors.TABLE_BODY_ROWS).all()
        logger.debug(f"Found {len(rows)} data rows in table")

        for row_idx, row in enumerate(rows):
            cells = await row.locator(Selectors.TABLE_CELLS).all()
            logger.debug(f"Row {row_idx} has {len(cells)} cells")

            if len(cells) >= 6:
                # Extract data from cells
                hour = await self._extract_cell_text(cells[0])

                # Subject is in a button/link within the second cell
                subject = await self._extract_subject(cells[1])

                teacher = await self._extract_cell_text(cells[2])
                status = await self._extract_cell_text(cells[3])
                lesson_topic = await self._extract_cell_text(cells[4])  # נושא שיעור
                homework = await self._extract_cell_text(cells[5])  # שיעורי בית

                # Check for attached files
                attached_files = []
                if len(cells) > 6:
                    attached_files = await self._extract_attached_files(cells[6])

                # Combine lesson topic and homework
                combined = self._combine_content(lesson_topic, homework)

                # Include row if it has a subject (even if lesson/homework are empty)
                # This ensures we capture all lessons, including those with "טרם הוזנו נתונים"
                if subject:
                    homework_item = {
                        "hour": hour,
                        "subject": subject,
                        "teacher": teacher,
                        "lesson_topic": lesson_topic,
                        "homework": homework,
                        "combined": combined,
                        "status": status,
                        "attached_files": attached_files,
                        "date": target_date_str,
                    }
                    homework_list.append(homework_item)
                    logger.debug(
                        f"Added homework item: {subject} - "
                        f"lesson: {lesson_topic[:50] if lesson_topic else '(empty)'}, "
                        f"homework: {homework[:50] if homework else '(empty)'}, "
                        f"status: {status}"
                    )
                else:
                    logger.debug(f"Skipping row {row_idx} - no subject found")

        return homework_list

    async def _extract_cell_text(self, cell: Locator) -> str:
        """Extract text content from a cell.

        Args:
            cell: Playwright locator for the cell

        Returns:
            Extracted text content, empty string on error
        """
        try:
            # Get all text, including nested elements
            text = await cell.text_content()
            if text:
                # Clean up the text - remove extra whitespace and newlines
                text = " ".join(text.split())
                # Remove common prefixes like "נושא שיעור: " and "שיעורי בית: "
                text = text.replace("נושא שיעור:", "").replace("שיעורי בית:", "").strip()
                # Handle edge cases like "-`" or other single-character placeholders
                if text in ["-`", "-", "`", "--"]:
                    text = ""
            return text if text else ""
        except Exception as e:
            logger.debug(f"Error extracting cell text: {e}")
            return ""

    async def _extract_subject(self, subject_cell: Locator) -> str:
        """Extract subject name from cell (may be in a button or link).

        Args:
            subject_cell: Playwright locator for the subject cell

        Returns:
            Subject name, empty string on error
        """
        try:
            # Try to find button or link first
            subject_btn = subject_cell.locator(Selectors.SUBJECT_BUTTON).first
            if await subject_btn.count() > 0:
                subject_text = await subject_btn.text_content()
                if subject_text:
                    return subject_text.strip()

            # Fallback to cell text content
            subject_text = await subject_cell.text_content()
            if subject_text:
                return subject_text.strip()
            return ""
        except Exception as e:
            logger.debug(f"Error extracting subject: {e}")
            return ""

    async def _extract_attached_files(self, file_cell: Locator) -> List[Dict[str, str]]:
        """Extract attached files (links and images) from cell.

        Args:
            file_cell: Playwright locator for the file attachment cell

        Returns:
            List of file dictionaries with type, href/src, and text/alt
        """
        attached_files: List[Dict[str, str]] = []

        try:
            # Check for links
            file_links = await file_cell.locator(Selectors.FILE_LINKS).all()
            for link in file_links:
                try:
                    href = await link.get_attribute("href")
                    text_content = await link.text_content()
                    text = text_content.strip() if text_content else ""
                    if href:
                        attached_files.append({"type": "link", "href": href, "text": text})
                except Exception as e:
                    logger.debug(f"Error extracting link: {e}")

            # Check for images
            file_imgs = await file_cell.locator(Selectors.FILE_IMAGES).all()
            for img in file_imgs:
                try:
                    src = await img.get_attribute("src")
                    alt_attr = await img.get_attribute("alt")
                    alt = alt_attr.strip() if alt_attr else ""
                    if src:
                        attached_files.append({"type": "image", "src": src, "alt": alt})
                except Exception as e:
                    logger.debug(f"Error extracting image: {e}")
        except Exception as e:
            logger.debug(f"Error extracting attached files: {e}")

        return attached_files

    def _combine_content(self, lesson_topic: str, homework: str) -> str:
        """Combine lesson topic and homework into a single string."""
        combined_content = []
        if lesson_topic and lesson_topic not in [
            TextPatterns.EMPTY_LESSON_PLACEHOLDER,
            "",
        ]:
            combined_content.append(lesson_topic)
        if homework and homework not in [
            "--",
            TextPatterns.NO_HOMEWORK_PLACEHOLDER,
            "",
        ]:
            combined_content.append(homework)
        return " | ".join(combined_content) if combined_content else ""
