"""Pytest configuration and shared fixtures."""
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def mock_page():
    """Create a mock Playwright page object."""
    page = AsyncMock()
    page.url = "https://webtop.smartschool.co.il/dashboard"
    page.locator = MagicMock(return_value=AsyncMock())
    page.get_by_role = MagicMock(return_value=AsyncMock())
    page.wait_for_load_state = AsyncMock()
    page.wait_for_url = AsyncMock()
    page.goto = AsyncMock()
    page.title = AsyncMock(return_value="Webtop - Dashboard")
    page.screenshot = AsyncMock()
    return page


@pytest.fixture
def mock_browser():
    """Create a mock Playwright browser object."""
    browser = AsyncMock()
    browser.contexts = []
    browser.new_context = AsyncMock(return_value=AsyncMock())
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_context(mock_browser):
    """Create a mock browser context."""
    context = AsyncMock()
    context.new_page = AsyncMock(return_value=AsyncMock())
    context.close = AsyncMock()
    context.cookies = AsyncMock(return_value=[])
    mock_browser.new_context.return_value = context
    return context


@pytest.fixture
def mock_playwright(mock_browser):
    """Create a mock Playwright instance."""
    playwright = MagicMock()
    playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    playwright.webkit.launch = AsyncMock(return_value=mock_browser)
    playwright.firefox.launch = AsyncMock(return_value=mock_browser)
    return playwright


@pytest.fixture
def sample_homework_data():
    """Sample homework data for testing."""
    return [
        {
            "hour": "1",
            "subject": "מתמטיקה",
            "teacher": "מורה שם",
            "lesson_topic": "פרק 5 - אלגברה",
            "homework": "עמוד 45 תרגילים 1-10",
            "combined": "פרק 5 - אלגברה | עמוד 45 תרגילים 1-10",
            "status": "נוכח",
            "attached_files": [],
            "date": "21/01/2026",
        },
        {
            "hour": "2",
            "subject": "אנגלית",
            "teacher": "מורה אחר",
            "lesson_topic": "Unit 3",
            "homework": "Read pages 20-25",
            "combined": "Unit 3 | Read pages 20-25",
            "status": "נוכח",
            "attached_files": [
                {
                    "type": "link",
                    "href": "https://example.com/file.pdf",
                    "text": "קובץ PDF",
                }
            ],
            "date": "21/01/2026",
        },
    ]


@pytest.fixture
def today_date():
    """Get today's date as datetime."""
    return datetime.now()


@pytest.fixture
def sample_date():
    """Get a sample date for testing."""
    return datetime(2026, 1, 21)
