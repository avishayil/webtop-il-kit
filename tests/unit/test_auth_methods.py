"""Unit tests for authentication module methods.

Tests individual methods in isolation with heavy mocking.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from webtop_il_kit.auth import WebtopAuth


@pytest.mark.asyncio
class TestWebtopAuthMethods:
    """Unit tests for individual WebtopAuth methods."""

    @pytest.fixture
    def auth(self):
        """Create WebtopAuth instance."""
        return WebtopAuth("test_user", "test_pass")

    @pytest.fixture
    def mock_page(self):
        """Create mock page with login elements."""
        page = AsyncMock()
        page.url = "https://webtop.smartschool.co.il/account/login"
        page.locator = MagicMock()
        page.get_by_role = MagicMock()
        return page

    async def test_accept_cookies(self, auth, mock_page):
        """Unit test: cookie acceptance."""
        cookie_button = AsyncMock()
        cookie_button.count = AsyncMock(return_value=1)
        mock_page.locator.return_value = cookie_button

        await auth._accept_cookies(mock_page)

        cookie_button.click.assert_called_once()

    async def test_accept_cookies_not_present(self, auth, mock_page):
        """Unit test: when cookie button is not present."""
        cookie_button = AsyncMock()
        cookie_button.count = AsyncMock(return_value=0)
        mock_page.locator.return_value = cookie_button

        # Should not raise exception
        await auth._accept_cookies(mock_page)

    async def test_click_moe_button(self, auth, mock_page):
        """Unit test: clicking Ministry of Education button."""
        moe_button = AsyncMock()
        moe_button.get_attribute = AsyncMock(return_value=None)
        moe_button.wait_for = AsyncMock()
        mock_page.locator.return_value = moe_button

        await auth._click_moe_button(mock_page)

        moe_button.click.assert_called_once()

    async def test_find_username_field(self, auth, mock_page):
        """Unit test: finding username field."""
        username_field = AsyncMock()
        username_field.count = AsyncMock(return_value=1)
        username_field.wait_for = AsyncMock()
        mock_page.locator.return_value.first = username_field

        result = await auth._find_username_field(mock_page)
        assert result is not None

    async def test_find_username_field_not_found(self, auth, mock_page):
        """Unit test: when username field is not found."""
        mock_page.locator.return_value.first.count = AsyncMock(return_value=0)
        mock_page.get_by_role.side_effect = Exception("Not found")

        with pytest.raises(Exception, match="Could not find username field"):
            await auth._find_username_field(mock_page)

    async def test_find_password_field(self, auth, mock_page):
        """Unit test: finding password field."""
        password_field = AsyncMock()
        password_field.count = AsyncMock(return_value=1)
        password_field.wait_for = AsyncMock()
        mock_page.locator.return_value.first = password_field

        result = await auth._find_password_field(mock_page)
        assert result is not None

    async def test_is_tab_already_selected_username_visible(self, auth, mock_page):
        """Unit test: tab selection check when username field is visible."""
        username_field = AsyncMock()
        username_field.count = AsyncMock(return_value=1)
        username_field.is_visible = AsyncMock(return_value=True)
        mock_page.locator.return_value.first = username_field

        result = await auth._is_tab_already_selected(mock_page)
        assert result is True

    async def test_is_tab_already_selected_aria_selected(self, auth, mock_page):
        """Unit test: tab selection check when tab has aria-selected."""
        tab = AsyncMock()
        tab.text_content = AsyncMock(return_value="כניסה עם קוד משתמש וסיסמה")
        tab.get_attribute = AsyncMock(side_effect=lambda attr: ("true" if attr == "aria-selected" else None))
        mock_page.locator.return_value.all = AsyncMock(return_value=[tab])

        result = await auth._is_tab_already_selected(mock_page)
        assert result is True

    async def test_click_correct_tab(self, auth, mock_page):
        """Unit test: clicking the correct tab."""
        tab = AsyncMock()
        tab.text_content = AsyncMock(return_value="כניסה עם קוד משתמש וסיסמה")
        tab.wait_for = AsyncMock()
        tab.click = AsyncMock()
        mock_page.locator.return_value.all = AsyncMock(return_value=[tab])

        result = await auth._click_correct_tab(mock_page)
        assert result is True
        tab.click.assert_called_once()

    async def test_click_correct_tab_excludes_mobile(self, auth, mock_page):
        """Unit test: that mobile tab is excluded."""
        mobile_tab = AsyncMock()
        mobile_tab.text_content = AsyncMock(return_value="כניסה עם קוד חד פעמי לנייד")
        username_tab = AsyncMock()
        username_tab.text_content = AsyncMock(return_value="כניסה עם קוד משתמש וסיסמה")
        username_tab.wait_for = AsyncMock()
        username_tab.click = AsyncMock()
        mock_page.locator.return_value.all = AsyncMock(return_value=[mobile_tab, username_tab])

        result = await auth._click_correct_tab(mock_page)
        assert result is True
        username_tab.click.assert_called_once()
        mobile_tab.click.assert_not_called()
