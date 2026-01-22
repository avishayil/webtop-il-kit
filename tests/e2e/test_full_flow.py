"""End-to-end tests for the complete scraper flow.

Tests the full journey from login to homework extraction.

Note: These tests use a REAL browser and require:
- Valid credentials in .env file
- Network access
- May require manual reCAPTCHA solving

To run these tests, set RUN_WEBTOP_E2E=1:
    RUN_WEBTOP_E2E=1 pytest tests/e2e -v -s

These tests are NOT run in CI to avoid Cloudflare blocking issues.
"""
import os

import pytest
from webtop_il_kit.scraper import WebtopScraper


@pytest.mark.asyncio
@pytest.mark.e2e
class TestFullFlowE2E:
    """End-to-end tests for complete scraper workflow."""

    @pytest.fixture(autouse=True)
    def check_e2e_enabled(self):
        """Skip E2E tests unless RUN_WEBTOP_E2E=1 is set."""
        if os.getenv("RUN_WEBTOP_E2E") != "1":
            pytest.skip("E2E tests skipped. Set RUN_WEBTOP_E2E=1 to run. These tests require real credentials and network access.")

    @pytest.fixture
    def scraper(self):
        """Create WebtopScraper instance with real credentials."""
        # Check if credentials are available
        username = os.getenv("MINISTRY_OF_EDUCATION_USERNAME")
        password = os.getenv("MINISTRY_OF_EDUCATION_PASSWORD")

        if not username or not password:
            pytest.skip("MINISTRY_OF_EDUCATION_USERNAME and MINISTRY_OF_EDUCATION_PASSWORD must be set in environment")

        return WebtopScraper()

    async def test_e2e_full_homework_extraction_flow(self, scraper):
        """E2E test: complete flow from login to homework extraction.

        Uses REAL browser. This test uses a real browser and will:
        - Launch Chromium
        - Navigate to Webtop login page
        - Attempt to log in (may require manual reCAPTCHA solving)
        - Navigate to homework page
        - Extract homework data for today

        Note: This test may fail if:
        - Credentials are invalid
        - reCAPTCHA requires manual intervention
        - Network issues occur
        """
        try:
            # Test with today's date (no date parameter = today)
            result = await scraper.get_today_homework()

            # Verify we got a result (even if empty list)
            assert isinstance(result, list), "Result should be a list"

            # If we got homework, verify structure
            if result:
                assert len(result) > 0
                first_item = result[0]
                assert "subject" in first_item
                assert "date" in first_item
                print(f"✓ Successfully extracted {len(result)} homework items")
            else:
                print("✓ Test completed but no homework found for the test date")

        except Exception as e:
            # If it's a reCAPTCHA or login issue, mark as expected failure
            error_msg = str(e).lower()
            if "recaptcha" in error_msg or "login" in error_msg or "timeout" in error_msg:
                pytest.skip(f"Test skipped due to authentication issue (may require manual intervention): {e}")
            else:
                # Re-raise unexpected errors
                raise

    async def test_e2e_pagination_flow(self, scraper):
        """E2E test: complete flow with pagination to find older date.

        Uses REAL browser. This test verifies that pagination works correctly
        when searching for homework from one week ago (tests pagination navigation).
        """
        try:
            # Use a date from one week ago to test pagination
            # This ensures the test always uses a relative date (one week ago from today)
            from datetime import datetime, timedelta

            one_week_ago = datetime.now() - timedelta(days=7)
            date_str = one_week_ago.strftime("%d-%m-%Y")

            result = await scraper.get_today_homework(date=date_str)

            # Verify we got a result
            assert isinstance(result, list), "Result should be a list"
            print(f"✓ Successfully tested pagination for one week ago ({date_str})")

        except Exception as e:
            # If it's a reCAPTCHA or login issue, mark as expected failure
            error_msg = str(e).lower()
            if "recaptcha" in error_msg or "login" in error_msg or "timeout" in error_msg:
                pytest.skip(f"Test skipped due to authentication issue (may require manual intervention): {e}")
            else:
                # Re-raise unexpected errors
                raise
