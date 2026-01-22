"""
Webtop scraper package.

A Python library to scrape and retrieve homework from the Webtop platform
(webtop.smartschool.co.il).

Example usage:
    >>> from webtop_il_kit import WebtopScraper
    >>> scraper = WebtopScraper()
    >>> homework = await scraper.get_today_homework(date="21-01-2026")
"""
import logging
import os
import sys

__version__ = "0.1.0"

# Configure logging for the package
# Default to INFO level to show user-facing operations, but allow override via environment variable
_log_level = os.getenv("WEBTOP_LOG_LEVEL", "INFO").upper()
_log_level_value = getattr(logging, _log_level, logging.INFO)

# Get the root logger for this package
_package_name = __name__.split(".")[0]  # 'webtop_il_kit'
_logger = logging.getLogger(_package_name)

# Only configure if no handlers exist (avoid duplicate handlers)
if not _logger.handlers:
    _logger.setLevel(_log_level_value)

    # Create console handler with stdout
    _console_handler = logging.StreamHandler(sys.stdout)
    _console_handler.setLevel(_log_level_value)

    # Create formatter
    _formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _console_handler.setFormatter(_formatter)

    # Add handler to logger
    _logger.addHandler(_console_handler)

    # Allow propagation so child loggers inherit the configuration
    # but set propagate to False to avoid duplicate logs if root logger is configured
    _logger.propagate = False

    # Ensure all child loggers of this package inherit the level
    # This makes loggers like 'webtop_il_kit.extractor' inherit the level
    for _ in logging.root.handlers:
        # If root logger has handlers, we might get duplicates
        # So we keep propagate=False
        pass

# Lazy import to avoid loading playwright dependencies when only
# importing utilities


def __getattr__(name):
    """Lazy import for WebtopScraper."""
    if name == "WebtopScraper":
        from .scraper import WebtopScraper

        return WebtopScraper
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["WebtopScraper", "__version__"]
