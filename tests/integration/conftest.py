"""Shared fixtures for integration tests."""
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


@pytest.fixture
def mock_integrated_page():
    """Create a mock page for integration testing.

    Includes realistic state transitions.
    """
    page = AsyncMock()
    page.url = "https://webtop.smartschool.co.il/dashboard"
    page.locator = MagicMock()
    page.get_by_role = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_url = AsyncMock()
    page.wait_for_selector = AsyncMock()
    return page
