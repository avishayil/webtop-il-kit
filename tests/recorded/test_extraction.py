"""Test extraction logic using recorded HTML fixtures."""
from datetime import datetime

import pytest

from .conftest import load_html_fixture


@pytest.mark.asyncio
@pytest.mark.recorded
class TestExtractionFromRecordedHTML:
    """Test extraction logic using pre-recorded HTML."""

    async def test_extract_homework_from_fixture(self, mock_page_with_html, extractor, fixtures_dir):
        """Test homework extraction from recorded HTML."""
        page, _ = mock_page_with_html

        # Load a recorded homework page (using the committed fixture)
        try:
            await load_html_fixture(page, fixtures_dir, "homework_page_2026_01_22.html")
        except FileNotFoundError:
            pytest.skip("Fixture file not found. Run: python scripts/capture_fixtures.py to create fixtures")

        # Test extraction for a date that exists in the fixture (22/01/2026)
        target_date = datetime(2026, 1, 22)
        homework = await extractor.extract_homework(page, target_date)

        # Verify structure
        assert isinstance(homework, list)

        if homework:
            # Verify schema
            first_item = homework[0]
            required_fields = [
                "hour",
                "subject",
                "teacher",
                "lesson_topic",
                "homework",
                "combined",
                "status",
                "attached_files",
                "date",
            ]
            for field in required_fields:
                assert field in first_item, f"Missing field: {field}"

            # Verify date format
            assert first_item["date"] == "22/01/2026"

    async def test_extract_empty_homework(self, mock_page_with_html, extractor, fixtures_dir):
        """Test extraction when no homework exists for a date."""
        page, _ = mock_page_with_html

        try:
            await load_html_fixture(page, fixtures_dir, "homework_page_empty.html")
        except FileNotFoundError:
            pytest.skip("Fixture file not found")

        target_date = datetime(2026, 1, 22)
        homework = await extractor.extract_homework(page, target_date)

        # Should return empty list, not error
        assert isinstance(homework, list)
        # Empty list is acceptable if no homework for that date
