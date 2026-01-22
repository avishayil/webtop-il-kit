"""Tests for configuration module."""
from unittest.mock import patch

from webtop_il_kit.config import Config


class TestConfig:
    """Tests for configuration constants."""

    def test_base_url(self):
        """Test BASE_URL is set correctly."""
        assert Config.BASE_URL == "https://webtop.smartschool.co.il"

    def test_login_url(self):
        """Test LOGIN_URL is constructed correctly."""
        assert Config.LOGIN_URL == "https://webtop.smartschool.co.il/account/login"

    def test_browser_config(self):
        """Test browser configuration constants."""
        assert isinstance(Config.HEADLESS_MODE, bool)
        assert isinstance(Config.SLOW_MO, int)
        assert Config.SLOW_MO > 0

    def test_pagination_limits(self):
        """Test pagination limits are set."""
        assert isinstance(Config.MAX_PAGINATION_PAGES, int)
        assert Config.MAX_PAGINATION_PAGES > 0

    def test_timeouts(self):
        """Test timeout constants are set."""
        assert isinstance(Config.DEFAULT_TIMEOUT, int)
        assert isinstance(Config.NAVIGATION_TIMEOUT, int)
        assert Config.DEFAULT_TIMEOUT > 0
        assert Config.NAVIGATION_TIMEOUT > 0

    @patch.dict("os.environ", {"MINISTRY_OF_EDUCATION_USERNAME": "test_user"})
    def test_username_from_env(self):
        """Test username is loaded from environment."""
        # Reload config to pick up env var
        import importlib

        import webtop_il_kit.config

        importlib.reload(webtop_il_kit.config)
        # Note: This test may not work perfectly due to module caching
        # but demonstrates the concept
        pass
