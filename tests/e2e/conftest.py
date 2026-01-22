"""Shared fixtures for E2E tests."""
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


@pytest.fixture
def mock_e2e_browser_stack():
    """Create a complete mock browser stack for E2E testing."""
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
    page.url = "https://webtop.smartschool.co.il/account/login"
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_url = AsyncMock()
    page.locator = MagicMock()
    page.get_by_role = MagicMock()
    context.new_page.return_value = page

    playwright.chromium.launch = AsyncMock(return_value=browser)
    return playwright, browser, context, page
