"""Authentication module for Webtop login."""
import asyncio
import logging

from playwright.async_api import Page

from .config import Config
from .selectors import Delays, Selectors, TextPatterns, Timeouts

logger = logging.getLogger(__name__)


class WebtopAuth:
    """Handles authentication to Webtop."""

    def __init__(self, username: str, password: str):
        """
        Initialize authentication handler.

        Args:
            username: Ministry of Education username
            password: Ministry of Education password
        """
        self.username = username
        self.password = password
        self.login_url = Config.LOGIN_URL

    async def login(self, page: Page) -> bool:
        """
        Login to Webtop using Ministry of Education authentication.

        Args:
            page: Playwright page object

        Returns:
            True if login successful, False otherwise
        """
        try:
            # Navigate to login page with a small delay to appear more natural
            await asyncio.sleep(Delays.SHORT)
            await page.goto(self.login_url, wait_until="networkidle", timeout=60000)

            # Wait a bit for any Cloudflare checks to complete
            await asyncio.sleep(Delays.MEDIUM)

            # Check for Cloudflare blocking
            page_title = await page.title()
            if "could not be satisfied" in page_title.lower() or "cloudflare" in page_title.lower():
                logger.warning("Cloudflare is blocking the request")
                logger.debug("Waiting longer and retrying...")
                await asyncio.sleep(Delays.EXTRA_LONG * 3)
                await page.reload(wait_until="networkidle", timeout=60000)
                await asyncio.sleep(Delays.MEDIUM)
                page_title = await page.title()
                if "could not be satisfied" in page_title.lower():
                    logger.error("Still blocked by Cloudflare after retry")
                    await self._debug_login_failure(page)
                    return False

            # Accept cookies if present
            await self._accept_cookies(page)

            # Click Ministry of Education authentication button
            await self._click_moe_button(page)

            # Wait for redirect and handle tab selection
            await self._handle_moe_login_page(page)

            # Fill credentials and submit
            await self._fill_credentials(page)
            await self._click_login_button(page)

            # Wait for redirect and verify login
            login_success = await self._verify_login_success(page)
            if not login_success:
                logger.warning("Login verification failed, attempting to debug...")
                await self._debug_login_failure(page)
            return login_success

        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            try:
                await self._debug_login_failure(page)
            except Exception as debug_error:
                logger.debug(f"Could not save debug info: {debug_error}")
            return False

    async def _accept_cookies(self, page: Page):
        """Accept cookies if present."""
        try:
            cookie_button = page.locator(Selectors.COOKIE_BUTTON)
            if await cookie_button.count() > 0:
                await cookie_button.click(timeout=Timeouts.ELEMENT_VISIBLE // 5)  # Short timeout for cookie button
                await asyncio.sleep(Delays.AFTER_CLICK)
        except Exception:
            pass

    async def _click_moe_button(self, page: Page):
        """Click the Ministry of Education authentication button."""
        logger.info("Clicking Ministry of Education authentication button...")
        moe_button = page.locator(Selectors.MOE_BUTTON)
        await moe_button.wait_for(state="visible", timeout=Timeouts.ELEMENT_WAIT)

        # Wait for button to be enabled
        for _ in range(Timeouts.BUTTON_ENABLE_MAX_WAIT):
            is_disabled = await moe_button.get_attribute("disabled")
            aria_disabled = await moe_button.get_attribute("aria-disabled")
            if is_disabled is None and aria_disabled != "true":
                break
            await asyncio.sleep(Timeouts.BUTTON_ENABLE_DELAY)
        await moe_button.click()

    async def _handle_moe_login_page(self, page: Page):
        """Handle the Ministry of Education login page."""
        logger.debug("Waiting for redirect to Ministry of Education page...")
        try:
            await page.wait_for_url(Selectors.MOE_LOGIN_URL_PATTERN, timeout=Timeouts.PAGE_LOAD)
        except Exception:
            pass
        await page.wait_for_load_state("networkidle", timeout=Timeouts.PAGE_LOAD)
        await asyncio.sleep(Delays.EXTRA_LONG)

        current_url = page.url
        if Selectors.MOE_DOMAIN not in current_url:
            logger.warning(f"Expected Ministry of Education page, but got: {current_url}")

        # Select the username/password tab
        await self._select_username_password_tab(page)

    async def _select_username_password_tab(self, page: Page):
        """Select the username/password tab on the MOE login page."""
        logger.info("Switching to username/password tab...")
        await asyncio.sleep(Timeouts.TAB_CLICK_DELAY)

        # Check if already selected
        if await self._is_tab_already_selected(page):
            logger.debug("Correct tab is already selected, skipping tab click")
            await asyncio.sleep(Delays.AFTER_TAB_SWITCH)
            return

        # Try to click the correct tab
        tab_clicked = await self._click_correct_tab(page)
        if not tab_clicked:
            logger.warning("Could not click tab, but continuing - tab might already be selected")

    async def _is_tab_already_selected(self, page: Page) -> bool:
        """Check if the username/password tab is already selected."""
        # Method 1: Check if username field is visible
        try:
            for selector in Selectors.USERNAME_SELECTORS:
                username_field = page.locator(selector).first
                if await username_field.count() > 0 and await username_field.is_visible():
                    logger.debug("Username field is visible - correct tab appears to be already selected")
                    return True
        except Exception:
            pass

        # Method 2: Check aria-selected attribute
        try:
            all_tabs = await page.locator(Selectors.TAB_ROLE).all()
            for tab in all_tabs:
                tab_text = await tab.text_content()
                if tab_text and TextPatterns.USERNAME_PASSWORD_TAB in tab_text and TextPatterns.MOBILE_TAB not in tab_text:
                    aria_selected = await tab.get_attribute("aria-selected")
                    class_attr = await tab.get_attribute("class")
                    if aria_selected == "true" or (class_attr and ("selected" in class_attr.lower() or "active" in class_attr.lower())):
                        logger.debug(f"Correct tab is already selected: {tab_text}")
                        return True
        except Exception:
            pass

        # Method 3: Check password field
        try:
            for selector in Selectors.PASSWORD_SELECTORS:
                password_field = page.locator(selector).first
                if await password_field.count() > 0 and await password_field.is_visible():
                    aria_label = await password_field.get_attribute("aria-label")
                    if aria_label and TextPatterns.PASSWORD_LABEL in aria_label and TextPatterns.MOBILE_TAB not in aria_label:
                        logger.debug("Password field is visible - correct tab appears to be already selected")
                        return True
        except Exception:
            pass

        return False

    async def _click_correct_tab(self, page: Page) -> bool:
        """Click the username/password tab."""
        # Method 1: Find by text content
        try:
            all_tabs = await page.locator(Selectors.TAB_ROLE).all()
            for tab in all_tabs:
                tab_text = await tab.text_content()
                if tab_text and TextPatterns.USERNAME_PASSWORD_TAB in tab_text and TextPatterns.MOBILE_TAB not in tab_text:
                    logger.debug(f"Found correct tab: {tab_text.strip()}")
                    await tab.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                    await tab.click()
                    await asyncio.sleep(Timeouts.TAB_CLICK_DELAY)
                    logger.debug("Tab clicked successfully")
                    return True
        except Exception as e:
            logger.debug(f"Method 1 failed: {e}")

        # Method 2: get_by_role
        try:
            tab = page.get_by_role("tab", name=TextPatterns.USERNAME_PASSWORD_TAB, exact=True)
            await tab.wait_for(state="visible", timeout=Timeouts.ELEMENT_WAIT)
            tab_text = await tab.text_content()
            if tab_text and TextPatterns.USERNAME_PASSWORD_TAB in tab_text and TextPatterns.MOBILE_TAB not in tab_text:
                logger.debug(f"Found correct tab via get_by_role: {tab_text}")
                await tab.click()
                await asyncio.sleep(Timeouts.TAB_CLICK_DELAY)
                logger.debug("Tab clicked using get_by_role")
                return True
        except Exception as e:
            logger.debug(f"get_by_role failed: {e}")

        # Method 3: Specific selector
        try:
            tab = page.locator(Selectors.TAB_SELECTOR).first
            if await tab.count() > 0:
                tab_text = await tab.text_content()
                logger.debug(f"Found tab with specific selector: {tab_text}")
                await tab.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                await tab.click()
                await asyncio.sleep(Timeouts.TAB_CLICK_DELAY)
                logger.debug("Tab clicked using specific selector")
                return True
        except Exception as e:
            logger.debug(f"Specific selector failed: {e}")

        return False

    async def _fill_credentials(self, page: Page):
        """Fill in username and password."""
        # Fill username
        logger.info("Filling username...")
        username_field = await self._find_username_field(page)
        await username_field.fill(self.username)
        await asyncio.sleep(Delays.AFTER_FILL)

        # Fill password
        logger.info("Filling password...")
        password_field = await self._find_password_field(page)
        await password_field.click()  # Remove readonly attribute
        await asyncio.sleep(Delays.SHORT)
        await password_field.fill(self.password)
        await asyncio.sleep(Delays.AFTER_FILL)
        await asyncio.sleep(Delays.VERY_LONG)  # Wait for reCAPTCHA if needed

    async def _find_username_field(self, page: Page):
        """Find and return the username field."""
        for selector in Selectors.USERNAME_SELECTORS:
            try:
                field = page.locator(selector).first
                if await field.count() > 0:
                    await field.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                    return field
            except Exception:
                continue

        # Try get_by_role
        try:
            return page.get_by_role(**Selectors.USERNAME_ROLE)
        except Exception:
            raise Exception("Could not find username field")

    async def _find_password_field(self, page: Page):
        """Find and return the password field."""
        for selector in Selectors.PASSWORD_SELECTORS:
            try:
                field = page.locator(selector).first
                if await field.count() > 0:
                    await field.wait_for(state="visible", timeout=Timeouts.ELEMENT_VISIBLE)
                    return field
            except Exception:
                continue

        # Try get_by_role
        try:
            return page.get_by_role(**Selectors.PASSWORD_ROLE)
        except Exception:
            raise Exception("Could not find password field")

    async def _click_login_button(self, page: Page):
        """Click the login button (not a tab)."""
        logger.info("Clicking login button...")
        login_button = await self._find_login_button(page)

        # Wait for button to be enabled
        for _ in range(Timeouts.BUTTON_ENABLE_MAX_WAIT):
            is_disabled = await login_button.get_attribute("disabled")
            aria_disabled = await login_button.get_attribute("aria-disabled")
            if is_disabled is None and aria_disabled != "true":
                break
            await asyncio.sleep(Timeouts.BUTTON_ENABLE_DELAY)
        else:
            logger.warning("Login button still disabled, attempting to click anyway")

        btn_text = await login_button.text_content()
        logger.debug(f"Clicking login button with text: {btn_text}")
        await login_button.click()

    async def _find_login_button(self, page: Page):
        """Find the login button (not a tab)."""
        # Method 1: Submit buttons
        try:
            submit_buttons = await page.locator(Selectors.LOGIN_BUTTON_SUBMIT).all()
            for btn in submit_buttons:
                btn_text = await btn.text_content()
                if btn_text and TextPatterns.LOGIN_BUTTON_TEXT in btn_text:
                    role = await btn.get_attribute("role")
                    if role != "tab":
                        try:
                            parent = btn.locator("xpath=..").first
                            parent_role = await parent.get_attribute("role")
                            if parent_role != "tablist" and parent_role != "tabpanel":
                                logger.debug(f"Found login button (submit): {btn_text}")
                                return btn
                        except Exception:
                            logger.debug(f"Found login button (submit, parent check skipped): {btn_text}")
                            return btn
        except Exception as e:
            logger.debug(f"Method 1 (submit button) failed: {e}")

        # Method 2: Buttons with login text
        try:
            all_buttons = await page.locator(Selectors.LOGIN_BUTTON_TEXT).all()
            for btn in all_buttons:
                role = await btn.get_attribute("role")
                if role != "tab":
                    try:
                        tablist_parent = await btn.locator('xpath=ancestor::*[@role="tablist"]').count()
                        if tablist_parent == 0:
                            btn_text = await btn.text_content()
                            logger.debug(f"Found login button: {btn_text}")
                            return btn
                    except Exception:
                        btn_type = await btn.get_attribute("type")
                        if btn_type == "submit":
                            logger.debug(f"Found login button (submit type): {await btn.text_content()}")
                            return btn
        except Exception as e:
            logger.debug(f"Method 2 (button search) failed: {e}")

        # Method 3: get_by_role
        try:
            all_buttons = await page.get_by_role(**Selectors.LOGIN_BUTTON_ROLE).all()
            for btn in all_buttons:
                role = await btn.get_attribute("role")
                if role != "tab":
                    logger.debug("Found login button via get_by_role")
                    return btn
        except Exception as e:
            logger.debug(f"Method 3 (get_by_role) failed: {e}")

        # Method 4: Form context
        try:
            forms = await page.locator("form").all()
            for form in forms:
                submit_btn = form.locator(Selectors.LOGIN_BUTTON_SUBMIT).first
                if await submit_btn.count() > 0:
                    btn_text = await submit_btn.text_content()
                    if btn_text and TextPatterns.LOGIN_BUTTON_TEXT in btn_text:
                        logger.debug(f"Found login button in form: {btn_text}")
                        return submit_btn
        except Exception as e:
            logger.debug(f"Method 4 (form search) failed: {e}")

        raise Exception("Could not find login button (may have matched a tab instead)")

    async def _verify_login_success(self, page: Page) -> bool:
        """Verify that login was successful."""
        logger.debug("Waiting for redirect to Webtop...")
        max_wait_time = Timeouts.LOGIN_REDIRECT / 1000  # Convert to seconds
        start_time = asyncio.get_event_loop().time()
        recaptcha_checked = False  # Only check reCAPTCHA once, after a delay

        while True:
            current_url = page.url
            elapsed = asyncio.get_event_loop().time() - start_time

            # Check if redirected to Webtop
            if Selectors.WEBTOP_DOMAIN in current_url and Selectors.LOGIN_PAGE_INDICATOR not in current_url.lower():
                logger.info(f"Redirected to Webtop after {elapsed:.1f}s")
                break

            # Check for errors (always check)
            if Selectors.MOE_DOMAIN in current_url:
                if await self._check_for_errors(page):
                    return False

                # Only check for reCAPTCHA after delay (to avoid false
                # positives). reCAPTCHA iframe might be present but not
                # blocking when using Ministry auth
                if not recaptcha_checked and elapsed > Timeouts.RECAPTCHA_CHECK_DELAY:
                    recaptcha_checked = True
                    if await self._handle_recaptcha(page):
                        break

            # Timeout
            if elapsed > max_wait_time:
                logger.warning(f"Timeout waiting for redirect after {max_wait_time}s")
                await self._debug_login_failure(page)
                break

            await asyncio.sleep(Delays.LONG)

        # Wait for networkidle, but don't fail if it times out
        # (some pages have continuous background requests)
        # We've already verified the redirect was successful above
        try:
            await page.wait_for_load_state("networkidle", timeout=Timeouts.NETWORK_IDLE)
            logger.debug("Page reached networkidle state")
        except Exception as e:
            logger.debug(f"Networkidle timeout (this is OK if page has background requests): {e}")
            # Continue anyway - we've already verified the redirect was successful

        await asyncio.sleep(Delays.EXTRA_LONG)

        # Final verification
        current_url = page.url
        logger.debug(f"Current URL after login: {current_url}")

        if Selectors.LOGIN_PAGE_INDICATOR not in current_url.lower() and Selectors.MOE_DOMAIN not in current_url.lower():
            logger.info("Login successful - redirected to dashboard")
            await asyncio.sleep(Delays.AFTER_LOGIN)
            return True

        # Check for dashboard elements
        for indicator in Selectors.DASHBOARD_INDICATORS:
            try:
                await page.wait_for_selector(indicator, timeout=Timeouts.ELEMENT_VISIBLE)
                logger.info(f"Login successful - found dashboard element: {indicator}")
                await asyncio.sleep(Delays.AFTER_LOGIN)
                return True
            except Exception:
                continue

        # Check for errors
        if Selectors.MOE_DOMAIN in current_url:
            if await self._check_for_errors(page):
                return False

        logger.warning("Login status unclear")
        return False

    async def _check_for_errors(self, page: Page) -> bool:
        """Check for error messages on the page."""
        try:
            page_text = await page.locator("body").text_content()
            if page_text:
                for keyword in Selectors.ERROR_KEYWORDS:
                    if keyword.lower() in page_text.lower():
                        error_elem = page.locator(f"text=/{keyword}/i").first
                        if await error_elem.count() > 0:
                            error_text = await error_elem.text_content()
                            logger.debug(f"Login error detected: {error_text}")
                            return True
        except Exception:
            pass
        return False

    async def _handle_recaptcha(self, page: Page) -> bool:
        """Handle reCAPTCHA if present and actually blocking.

        Note: reCAPTCHA iframe may be present on the page even when using
        Ministry of Education authentication, but it may not be blocking.
        Only wait if we're actually stuck and not redirecting.
        """
        try:
            recaptcha = page.locator(Selectors.RECAPTCHA_IFRAME)
            if await recaptcha.count() > 0:
                # Check if reCAPTCHA is actually visible/blocking
                is_visible = await recaptcha.first.is_visible()
                if is_visible:
                    logger.warning("reCAPTCHA detected and visible - waiting for it to be solved...")
                    # Only wait a short time - if login is working, redirect
                    # will happen quickly
                    for _ in range(Timeouts.RECAPTCHA_WAIT):
                        await asyncio.sleep(Delays.LONG)
                        current_url = page.url
                        if Selectors.WEBTOP_DOMAIN in current_url:
                            logger.info("reCAPTCHA solved, redirect successful")
                            return True
                    logger.warning("reCAPTCHA may require manual intervention")
                else:
                    # reCAPTCHA iframe exists but is hidden - not blocking,
                    # continue normally
                    pass
        except Exception:
            pass
        return False

    async def _debug_login_failure(self, page: Page):
        """Debug login failure by taking screenshot and logging info."""
        current_url = page.url
        logger.debug(f"Final URL: {current_url}")
        try:
            page_title = await page.title()
            logger.debug(f"Page title: {page_title}")

            # Check for Cloudflare blocking
            if "could not be satisfied" in page_title.lower() or "cloudflare" in page_title.lower():
                logger.warning("Cloudflare is blocking the request")
                logger.debug("This is likely due to bot detection. Possible solutions:")
                logger.debug("  - Add delays between requests")
                logger.debug("  - Use a different user agent")
                logger.debug("  - Run in non-headless mode (if possible)")

            body_text = await page.locator("body").text_content()
            if body_text:
                # Check for error keywords in text (not using CSS selector)
                for keyword in Selectors.ERROR_KEYWORDS[:3]:
                    if keyword.lower() in body_text.lower():
                        logger.debug(f"Error keyword detected: {keyword}")
                        # Try to find the error element using text locator
                        try:
                            error_elem = page.locator(f"text={keyword}").first
                            if await error_elem.count() > 0:
                                error_text = await error_elem.text_content()
                                logger.debug(f"Error text: {error_text[:200]}")
                        except Exception:
                            pass
        except Exception as e:
            logger.debug(f"Could not get page info: {e}")

        try:
            await page.screenshot(path="login_debug.png", full_page=True)
            logger.debug("Screenshot saved to login_debug.png for debugging")
        except Exception as e:
            logger.debug(f"Could not save screenshot: {e}")
