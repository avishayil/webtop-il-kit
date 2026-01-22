"""Unit tests for navigation module methods.

Tests individual methods in isolation with heavy mocking.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from webtop_il_kit.navigator import WebtopNavigator


@pytest.mark.asyncio
class TestWebtopNavigatorMethods:
    """Unit tests for individual WebtopNavigator methods."""

    @pytest.fixture
    def navigator(self):
        """Create WebtopNavigator instance."""
        return WebtopNavigator()

    @pytest.fixture
    def mock_page(self):
        """Create mock page."""
        page = AsyncMock()
        page.url = "https://webtop.smartschool.co.il/dashboard"
        page.locator = MagicMock()
        page.goto = AsyncMock()
        return page

    async def test_click_student_card_success(self, navigator, mock_page):
        """Unit test: clicking student card successfully."""
        student_card = AsyncMock()
        student_card.count = AsyncMock(return_value=1)
        student_card.wait_for = AsyncMock()
        student_card.click = AsyncMock()
        mock_page.locator.return_value.first = student_card

        result = await navigator._click_student_card(mock_page)
        assert result is True
        student_card.click.assert_called_once()

    async def test_click_homework_link_success(self, navigator, mock_page):
        """Unit test: clicking homework link successfully."""
        homework_link = AsyncMock()
        homework_link.count = AsyncMock(return_value=1)
        homework_link.wait_for = AsyncMock()
        homework_link.click = AsyncMock()
        mock_page.locator.return_value.first = homework_link

        result = await navigator._click_homework_link(mock_page)
        assert result is True
        homework_link.click.assert_called_once()

    async def test_verify_homework_page_success(self, navigator, mock_page):
        """Unit test: verification of homework page."""
        mock_page.url = "https://webtop.smartschool.co.il/Student_Card/11"
        mock_page.wait_for_selector = AsyncMock()

        result = await navigator._verify_homework_page(mock_page)
        assert result is True

    async def test_verify_homework_page_redirected_to_login(self, navigator, mock_page):
        """Unit test: verification fails when redirected to login."""
        mock_page.url = "https://webtop.smartschool.co.il/account/login"

        result = await navigator._verify_homework_page(mock_page)
        assert result is False
