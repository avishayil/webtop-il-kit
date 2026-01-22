"""Unit tests for extraction module methods.

Tests individual methods in isolation with heavy mocking.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from webtop_il_kit.extractor import WebtopExtractor


@pytest.mark.asyncio
class TestWebtopExtractorMethods:
    """Unit tests for individual WebtopExtractor methods."""

    @pytest.fixture
    def extractor(self):
        """Create WebtopExtractor instance."""
        return WebtopExtractor()

    @pytest.fixture
    def mock_page(self):
        """Create mock page with table structure."""
        page = AsyncMock()
        page.locator = MagicMock()
        return page

    async def test_extract_subject_from_button(self, extractor, mock_page):
        """Unit test: extracting subject from button in cell."""
        subject_cell = AsyncMock()
        subject_btn = AsyncMock()
        subject_btn.count = AsyncMock(return_value=1)
        subject_btn.text_content = AsyncMock(return_value="מתמטיקה")

        # Mock the locator chain: locator('button').first
        locator_mock = MagicMock()
        locator_mock.first = subject_btn
        subject_cell.locator = MagicMock(return_value=locator_mock)

        result = await extractor._extract_subject(subject_cell)
        assert result == "מתמטיקה"

    async def test_extract_attached_files(self, extractor, mock_page):
        """Unit test: extracting attached files."""
        file_cell = AsyncMock()

        # Mock link
        link = AsyncMock()
        link.get_attribute = AsyncMock(side_effect=lambda attr: "https://example.com/file.pdf" if attr == "href" else None)
        link.text_content = AsyncMock(return_value="קובץ PDF")

        # Mock image
        img = AsyncMock()
        img.get_attribute = AsyncMock(side_effect=lambda attr: "https://example.com/image.png" if attr == "src" else ("" if attr == "alt" else None))

        # Mock locator calls: locator('a').all() and locator('img').all()
        def locator_side_effect(selector):
            locator_mock = AsyncMock()
            if selector == "a":
                locator_mock.all = AsyncMock(return_value=[link])
            elif selector == "img":
                locator_mock.all = AsyncMock(return_value=[img])
            else:
                locator_mock.all = AsyncMock(return_value=[])
            return locator_mock

        file_cell.locator = MagicMock(side_effect=locator_side_effect)

        result = await extractor._extract_attached_files(file_cell)
        assert len(result) == 2
        assert result[0]["type"] == "link"
        assert result[1]["type"] == "image"

    def test_combine_content(self, extractor):
        """Unit test: combining lesson topic and homework."""
        result = extractor._combine_content("פרק 5", "עמוד 45")
        assert result == "פרק 5 | עמוד 45"

    def test_combine_content_empty_homework(self, extractor):
        """Unit test: combining when homework is empty."""
        result = extractor._combine_content("פרק 5", "")
        assert result == "פרק 5"

    def test_combine_content_empty_lesson_topic(self, extractor):
        """Unit test: combining when lesson topic is empty."""
        result = extractor._combine_content("", "עמוד 45")
        assert result == "עמוד 45"

    def test_combine_content_placeholder_values(self, extractor):
        """Unit test: combining with placeholder values."""
        result = extractor._combine_content("---", "אין")
        assert result == ""

    def test_combine_content_both_empty(self, extractor):
        """Unit test: combining when both are empty."""
        result = extractor._combine_content("", "")
        assert result == ""
