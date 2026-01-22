"""Unit tests for pagination module methods.

Tests individual methods in isolation with heavy mocking.
"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from webtop_il_kit.pagination import WebtopPagination


@pytest.mark.asyncio
class TestWebtopPaginationMethods:
    """Unit tests for individual WebtopPagination methods."""

    @pytest.fixture
    def pagination(self):
        """Create WebtopPagination instance."""
        return WebtopPagination()

    @pytest.fixture
    def mock_page(self):
        """Create mock page."""
        page = AsyncMock()
        page.url = "https://webtop.smartschool.co.il/Student_Card/11"
        page.wait_for_load_state = AsyncMock()
        page.locator = MagicMock()
        return page

    async def test_find_date_on_page_found(self, pagination, mock_page):
        """Unit test: finding date on current page."""
        heading = AsyncMock()
        heading.text_content = AsyncMock(return_value="יום רביעי | 21/01/2026 | ג׳ שְׁבָט תשפ״ו")
        mock_page.locator.return_value.all = AsyncMock(return_value=[heading])

        result = await pagination.find_date_on_page(mock_page, "21/01/2026")
        assert result is True

    async def test_find_date_on_page_not_found(self, pagination, mock_page):
        """Unit test: when date is not on current page."""
        heading = AsyncMock()
        heading.text_content = AsyncMock(return_value="יום שלישי | 20/01/2026 | ב׳ שְׁבָט תשפ״ו")
        mock_page.locator.return_value.all = AsyncMock(return_value=[heading])

        result = await pagination.find_date_on_page(mock_page, "21/01/2026")
        assert result is False

    async def test_get_dates_on_page(self, pagination, mock_page):
        """Unit test: extracting dates from page."""
        heading1 = AsyncMock()
        heading1.text_content = AsyncMock(return_value="יום שלישי | 20/01/2026 | ב׳ שְׁבָט תשפ״ו")
        heading2 = AsyncMock()
        heading2.text_content = AsyncMock(return_value="יום רביעי | 21/01/2026 | ג׳ שְׁבָט תשפ״ו")
        mock_page.locator.return_value.all = AsyncMock(return_value=[heading1, heading2])

        dates = await pagination.get_dates_on_page(mock_page)
        assert len(dates) == 2
        assert dates[0] == datetime(2026, 1, 20)
        assert dates[1] == datetime(2026, 1, 21)

    async def test_get_dates_on_page_no_dates(self, pagination, mock_page):
        """Unit test: when no dates found on page."""
        heading = AsyncMock()
        heading.text_content = AsyncMock(return_value="No date here")
        mock_page.locator.return_value.all = AsyncMock(return_value=[heading])

        dates = await pagination.get_dates_on_page(mock_page)
        assert len(dates) == 0

    async def test_find_navigation_button_forward(self, pagination, mock_page):
        """Unit test: finding forward navigation button."""
        next_button = AsyncMock()
        next_button.count = AsyncMock(return_value=1)
        next_button.is_visible = AsyncMock(return_value=True)
        next_button.get_attribute = AsyncMock(return_value=None)
        mock_page.locator.return_value.first = next_button

        result = await pagination._find_navigation_button(mock_page, "forward")
        assert result is not None

    async def test_find_navigation_button_backward(self, pagination, mock_page):
        """Unit test: finding backward navigation button."""
        prev_button = AsyncMock()
        prev_button.count = AsyncMock(return_value=1)
        prev_button.is_visible = AsyncMock(return_value=True)
        prev_button.get_attribute = AsyncMock(return_value=None)
        mock_page.locator.return_value.first = prev_button

        result = await pagination._find_navigation_button(mock_page, "backward")
        assert result is not None

    async def test_find_navigation_button_disabled(self, pagination, mock_page):
        """Unit test: when navigation button is disabled."""
        disabled_button = AsyncMock()
        disabled_button.count = AsyncMock(return_value=1)
        disabled_button.is_visible = AsyncMock(return_value=True)
        disabled_button.get_attribute = AsyncMock(return_value="true")
        mock_page.locator.return_value.first = disabled_button

        result = await pagination._find_navigation_button(mock_page, "forward")
        assert result is None
