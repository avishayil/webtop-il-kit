"""Integration tests for pagination and extractor modules working together."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from webtop_il_kit.extractor import WebtopExtractor
from webtop_il_kit.pagination import WebtopPagination


@pytest.mark.asyncio
class TestPaginationExtractorIntegration:
    """Integration tests for pagination and extractor interaction."""

    @pytest.fixture
    def pagination(self):
        """Create WebtopPagination instance."""
        return WebtopPagination()

    @pytest.fixture
    def extractor(self):
        """Create WebtopExtractor instance."""
        return WebtopExtractor()

    @pytest.fixture
    def mock_page(self):
        """Create mock page with pagination and table structure."""
        page = AsyncMock()
        page.url = "https://webtop.smartschool.co.il/Student_Card/11"
        page.wait_for_load_state = AsyncMock()
        page.locator = MagicMock()
        return page

    async def test_pagination_then_extraction(self, pagination, extractor, mock_page):
        """Integration test: pagination to find date, then extract homework."""
        target_date = datetime(2026, 1, 21)

        # First page - date not found
        heading1 = AsyncMock()
        heading1.text_content = AsyncMock(return_value="יום שני | 20/01/2026")
        mock_page.locator.return_value.all = AsyncMock(return_value=[heading1])

        found = await pagination.find_date_on_page(mock_page, "21/01/2026")
        assert found is False

        # Second page - date found
        heading2 = AsyncMock()
        heading2.text_content = AsyncMock(return_value="יום רביעי | 21/01/2026 | ג׳ שְׁבָט תשפ״ו")
        mock_page.locator.return_value.all = AsyncMock(return_value=[heading2])

        found = await pagination.find_date_on_page(mock_page, "21/01/2026")
        assert found is True

        # Now extractor can find the table
        table = AsyncMock()
        table.wait_for = AsyncMock()
        table.locator.return_value.all = AsyncMock(return_value=[])

        # Mock extractor's pagination check
        extractor.pagination.find_date_on_page = AsyncMock(return_value=True)
        mock_page.locator.side_effect = [
            MagicMock(return_value=[heading2]),  # Heading
            MagicMock(return_value=table),  # Table
        ]

        result = await extractor.extract_homework(mock_page, target_date)
        assert isinstance(result, list)

    async def test_pagination_navigation_then_extraction(self, pagination, extractor, mock_page):
        """Integration test: navigate to date via pagination, then extract."""
        target_date = datetime(2026, 1, 25)

        # Mock pagination navigation
        pagination.find_date_on_page = AsyncMock(side_effect=[False, True])
        pagination.get_dates_on_page = AsyncMock(return_value=[datetime(2026, 1, 20), datetime(2026, 1, 21)])
        nav_button = AsyncMock()
        pagination._find_navigation_button = AsyncMock(return_value=nav_button)
        pagination._click_navigation_button = AsyncMock(return_value=(True, "forward"))

        # Navigate to target date
        result = await pagination.navigate_to_date_page(mock_page, target_date)
        assert result is True

        # Now extractor can work
        heading = AsyncMock()
        heading.text_content = AsyncMock(return_value="יום שני | 25/01/2026")
        table = AsyncMock()
        table.wait_for = AsyncMock()
        table.locator.return_value.all = AsyncMock(return_value=[])

        extractor.pagination.find_date_on_page = AsyncMock(return_value=True)
        mock_page.locator.side_effect = [
            MagicMock(return_value=[heading]),
            MagicMock(return_value=table),
        ]

        homework = await extractor.extract_homework(mock_page, target_date)
        assert isinstance(homework, list)
