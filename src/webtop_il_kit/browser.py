"""Browser management module for Webtop scraper.

Handles browser launching and configuration.
"""
import asyncio
import logging
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright

from .config import Config
from .selectors import Delays

logger = logging.getLogger(__name__)


class WebtopBrowser:
    """Handles browser lifecycle management."""

    @staticmethod
    async def launch_browser(playwright: Playwright) -> Browser:
        """
        Launch a browser with fallback options.

        Args:
            playwright: Playwright instance

        Returns:
            Browser instance

        Raises:
            Exception: If no browser could be launched
        """
        browser = None
        last_error = None

        browser_configs = [
            # Try system Chrome first (most stable on macOS)
            (
                "Chromium (Chrome channel)",
                lambda: playwright.chromium.launch(
                    headless=Config.HEADLESS_MODE,
                    channel="chrome",
                    slow_mo=Config.SLOW_MO,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-web-security",
                    ],
                ),
            ),
            # Then try regular Chromium
            (
                "Chromium",
                lambda: playwright.chromium.launch(
                    headless=Config.HEADLESS_MODE,
                    slow_mo=Config.SLOW_MO,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                    ],
                ),
            ),
            # Then WebKit (native macOS)
            (
                "WebKit",
                lambda: playwright.webkit.launch(headless=Config.HEADLESS_MODE, slow_mo=Config.SLOW_MO),
            ),
            # Then Firefox
            (
                "Firefox",
                lambda: playwright.firefox.launch(headless=Config.HEADLESS_MODE, slow_mo=Config.SLOW_MO),
            ),
        ]

        for browser_name, launch_func in browser_configs:
            browser: Optional[Browser] = None
            try:
                logger.debug(f"Trying {browser_name}...")
                browser = await launch_func()
                logger.info(f"{browser_name} launched successfully")
                await asyncio.sleep(Delays.LONG)
                contexts = browser.contexts
                logger.debug(f"Browser is alive, contexts: {len(contexts)}")
                return browser
            except Exception as e:
                last_error = e
                logger.debug(f"{browser_name} failed: {str(e)[:100]}")
                if browser:
                    try:
                        await browser.close()
                    except Exception as close_error:
                        logger.debug(f"Error closing browser: {close_error}")
                browser = None
                continue

        error_msg = f"Failed to launch any browser. Last error: {last_error}\n"
        error_msg += "\nTroubleshooting steps:\n"
        error_msg += "1. Update Playwright: pip install --upgrade playwright\n"
        error_msg += "2. Reinstall browsers: python -m playwright install --with-deps\n"
        error_msg += "3. Try running: python test_browser.py to diagnose\n"
        error_msg += "4. On macOS, you may need to allow browser in System Settings > Privacy & Security"
        raise Exception(error_msg)

    @staticmethod
    async def create_context(browser: Browser) -> BrowserContext:
        """
        Create a new browser context.

        Args:
            browser: Browser instance

        Returns:
            BrowserContext instance
        """
        return await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent=("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
            # Add extra headers to appear more like a real browser
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9,he;q=0.8",
                "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"),
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
        )

    @staticmethod
    async def create_page(context: BrowserContext) -> Page:
        """
        Create a new page in the context.

        Args:
            context: BrowserContext instance

        Returns:
            Page instance
        """
        page = await context.new_page()

        # Hide automation indicators
        await page.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'he']
            });
            """
        )

        logger.debug("Page created successfully")
        return page
