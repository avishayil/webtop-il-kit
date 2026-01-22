"""Integration tests for auth and navigator modules working together."""
from unittest.mock import AsyncMock, MagicMock

import pytest
from webtop_il_kit.auth import WebtopAuth
from webtop_il_kit.navigator import WebtopNavigator


@pytest.mark.asyncio
class TestAuthNavigatorIntegration:
    """Integration tests for auth and navigator interaction."""

    @pytest.fixture
    def auth(self):
        """Create WebtopAuth instance."""
        return WebtopAuth("test_user", "test_pass")

    @pytest.fixture
    def navigator(self):
        """Create WebtopNavigator instance."""
        return WebtopNavigator()

    @pytest.fixture
    def mock_page(self):
        """Create mock page that transitions from login to dashboard."""
        page = AsyncMock()
        page.url = "https://webtop.smartschool.co.il/account/login"
        page.locator = MagicMock()
        page.get_by_role = MagicMock()
        page.goto = AsyncMock()
        page.wait_for_load_state = AsyncMock()
        page.wait_for_url = AsyncMock()
        return page

    async def test_login_then_navigate_to_homework(self, auth, navigator, mock_page):
        """Integration test: login flow followed by navigation."""
        # Setup login mocks
        cookie_button = AsyncMock()
        cookie_button.count = AsyncMock(return_value=1)

        # MOE button locator (page.locator returns a locator object)
        # All methods on AsyncMock are automatically async/awaitable
        moe_button_locator = AsyncMock()
        moe_button_locator.get_attribute = AsyncMock(side_effect=[None, None])  # First call returns None (not disabled)
        moe_button_locator.click = AsyncMock()

        username_field = AsyncMock()
        username_field.count = AsyncMock(return_value=1)
        username_field.wait_for = AsyncMock()
        password_field = AsyncMock()
        password_field.count = AsyncMock(return_value=1)
        password_field.wait_for = AsyncMock()
        login_button = AsyncMock()
        login_button.count = AsyncMock(return_value=1)
        login_button.wait_for = AsyncMock()

        # Setup navigation mocks
        student_card = AsyncMock()
        student_card.count = AsyncMock(return_value=1)
        student_card.wait_for = AsyncMock()
        homework_link = AsyncMock()
        homework_link.count = AsyncMock(return_value=1)
        homework_link.wait_for = AsyncMock()

        # Mock page URL changes
        async def url_changer(*args, **kwargs):
            if mock_page.url == ("https://webtop.smartschool.co.il/account/login"):
                mock_page.url = "https://webtop.smartschool.co.il/dashboard"
            elif "dashboard" in mock_page.url:
                mock_page.url = "https://webtop.smartschool.co.il/Student_Card/11"

        mock_page.wait_for_url.side_effect = url_changer

        # Mock locator calls - page.locator() returns a locator object
        # For MOE button, we need to return the AsyncMock directly
        # (not wrapped in MagicMock)
        def locator_side_effect(selector):
            # Track call order
            if not hasattr(locator_side_effect, "call_count"):
                locator_side_effect.call_count = 0
            locator_side_effect.call_count += 1

            if locator_side_effect.call_count == 1:
                return MagicMock(return_value=cookie_button)
            elif locator_side_effect.call_count == 2:
                # MOE button locator - return AsyncMock directly
                return moe_button_locator
            elif locator_side_effect.call_count == 3:
                return MagicMock(return_value=username_field)
            elif locator_side_effect.call_count == 4:
                return MagicMock(return_value=password_field)
            elif locator_side_effect.call_count == 5:
                return MagicMock(return_value=login_button)
            elif locator_side_effect.call_count == 6:
                return MagicMock(return_value=student_card)
            else:
                return MagicMock(return_value=homework_link)

        mock_page.locator = MagicMock(side_effect=locator_side_effect)

        # Execute login (simplified - just verify components work together)
        await auth._accept_cookies(mock_page)
        await auth._click_moe_button(mock_page)

        # Update URL to dashboard after login (simulating successful login)
        mock_page.url = "https://webtop.smartschool.co.il/dashboard"

        # Verify navigation can work after login
        result = await navigator.navigate_to_homework(mock_page)
        assert result is True
