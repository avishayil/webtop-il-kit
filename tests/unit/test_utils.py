"""Tests for utility functions."""
from datetime import datetime

import pytest
from webtop_il_kit.utils import parse_date


class TestParseDate:
    """Tests for date parsing utility."""

    def test_parse_date_dd_mm_yyyy_dash(self):
        """Test parsing DD-MM-YYYY format."""
        result = parse_date("21-01-2026")
        assert result == datetime(2026, 1, 21)

    def test_parse_date_dd_mm_yyyy_slash(self):
        """Test parsing DD/MM/YYYY format."""
        result = parse_date("21/01/2026")
        assert result == datetime(2026, 1, 21)

    def test_parse_date_yyyy_mm_dd_dash(self):
        """Test parsing YYYY-MM-DD format."""
        result = parse_date("2026-01-21")
        assert result == datetime(2026, 1, 21)

    def test_parse_date_yyyy_mm_dd_slash(self):
        """Test parsing YYYY/MM/DD format."""
        result = parse_date("2026/01/21")
        assert result == datetime(2026, 1, 21)

    def test_parse_date_dd_mm_yyyy_dot(self):
        """Test parsing DD.MM.YYYY format."""
        result = parse_date("21.01.2026")
        assert result == datetime(2026, 1, 21)

    def test_parse_date_with_whitespace(self):
        """Test parsing date with whitespace."""
        result = parse_date("  21-01-2026  ")
        assert result == datetime(2026, 1, 21)

    def test_parse_date_none(self):
        """Test parsing None returns None."""
        result = parse_date(None)
        assert result is None

    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Could not parse date"):
            parse_date("invalid-date")

    def test_parse_date_invalid_date(self):
        """Test parsing invalid date (e.g., 32nd day) raises ValueError."""
        with pytest.raises(ValueError):
            parse_date("32-01-2026")

    def test_parse_date_wrong_separator(self):
        """Test parsing date with wrong separator raises ValueError."""
        with pytest.raises(ValueError):
            parse_date("21_01_2026")
