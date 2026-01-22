"""Configuration constants for Webtop scraper."""
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for Webtop scraper."""

    # URLs
    BASE_URL = "https://webtop.smartschool.co.il"
    LOGIN_URL = f"{BASE_URL}/account/login"
    STUDENT_CARD_URL = f"{BASE_URL}/Student_Card"
    HOMEWORK_URL = f"{BASE_URL}/Student_Card/11"

    # Browser configuration
    # Allow override via environment variable (useful for CI)
    HEADLESS_MODE = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    SLOW_MO = 500  # Delay between actions in milliseconds

    # Credentials from environment
    USERNAME = os.getenv("MINISTRY_OF_EDUCATION_USERNAME")
    PASSWORD = os.getenv("MINISTRY_OF_EDUCATION_PASSWORD")

    # Pagination limits
    MAX_PAGINATION_PAGES = 100

    # Timeouts (in milliseconds)
    DEFAULT_TIMEOUT = 10000  # 10 seconds
    NAVIGATION_TIMEOUT = 30000  # 30 seconds
