"""CSS selectors and text patterns configuration for Webtop scraper.

Centralizes all selectors and text patterns for easier maintenance and
customization.

This module provides a centralized configuration for:
- CSS selectors used throughout the scraper
- Text patterns and labels (Hebrew and English)
- Timeout values
- Delay values

All hardcoded values have been extracted here to make the codebase more
maintainable and easier to adapt if the Webtop interface changes.
"""
import os


class Selectors:
    """CSS selectors and text patterns for Webtop scraper."""

    # ==================== Authentication Selectors ====================

    # Cookie acceptance
    COOKIE_BUTTON = 'button:has-text("אשר cookies")'

    # Ministry of Education button
    MOE_BUTTON = 'button:has-text("הזדהות משרד החינוך")'

    # Username field selectors (ordered by priority)
    USERNAME_SELECTORS = [
        'textbox[aria-label*="קוד המשתמש"]',
        'input[type="text"][formcontrolname*="username"]',
        'input[type="text"]',
    ]
    USERNAME_ROLE = {"role": "textbox", "name": "קוד המשתמש שלך"}

    # Password field selectors (ordered by priority)
    PASSWORD_SELECTORS = [
        'textbox[type="password"]',
        'input[type="password"]',
        'textbox[aria-label*="סיסמה"]',
    ]
    PASSWORD_ROLE = {"role": "textbox", "name": "סיסמה"}

    # Tab selection
    TAB_ROLE = '[role="tab"]'
    USERNAME_PASSWORD_TAB_TEXT = "קוד משתמש וסיסמה"
    MOBILE_TAB_EXCLUDE_TEXT = "חד פעמי"
    TAB_SELECTOR = '[role="tab"]:has-text("קוד משתמש וסיסמה"):not(:has-text("חד פעמי"))'

    # Login button selectors
    LOGIN_BUTTON_SUBMIT = 'button[type="submit"]'
    LOGIN_BUTTON_TEXT = 'button:has-text("כניסה")'
    LOGIN_BUTTON_ROLE = {"role": "button", "name": "כניסה"}
    LOGIN_BUTTON_TEXT_PATTERN = "כניסה"

    # ==================== Navigation Selectors ====================

    # Student Card link selectors
    STUDENT_CARD_SELECTORS = [
        'a[href*="Student_Card"]:has-text("כרטיס תלמיד")',
        'link:has-text("כרטיס תלמיד")',
        'a:has-text("כרטיס תלמיד")',
    ]
    STUDENT_CARD_TEXT = "כרטיס תלמיד"
    STUDENT_CARD_URL_PATTERN = "**/Student_Card**"

    # Homework link selectors
    HOMEWORK_SELECTORS = [
        'a[href*="Student_Card/11"]:has-text("נושאי שיעור ושיעורי-בית")',
        'a[href*="Student_Card/11"]',
        'link:has-text("נושאי שיעור ושיעורי-בית")',
        'a:has-text("נושאי שיעור ושיעורי-בית")',
        'nav a[href*="Student_Card/11"]',
    ]
    HOMEWORK_TEXT = "נושאי שיעור ושיעורי-בית"
    HOMEWORK_URL_PATTERN = "**/Student_Card/11**"

    # Dashboard indicators
    DASHBOARD_INDICATORS = [
        "text=ריכוז מידע",
        "text=כרטיס תלמיד",
        "text=תיבת הודעות",
        'heading:has-text("ריכוז מידע")',
    ]

    # ==================== Extraction Selectors ====================

    # Date heading
    # The page uses span[role="heading"] with class "card-title", not h2
    DATE_HEADING = 'span[role="heading"].card-title, span[role="heading"], h2'
    DATE_REGEX_PATTERN = r"(\d{2})/(\d{2})/(\d{4})"

    # Table selectors
    # Support both regular HTML tables and ARIA div-based tables
    TABLE_SELECTOR = "table, div[role='table']"
    TABLE_ARIA_LABEL_PATTERN = '[aria-label*="{date}"]'
    # For HTML tables: tbody tr
    # For ARIA tables: div[role="row"] with lesson-homework class (skip header)
    TABLE_BODY_ROWS = "tbody tr, tbody > * > tr, div[role='row'].lesson-homework, div[role='rowgroup'] > div[role='row'].lesson-homework"
    # For HTML tables: td
    # For ARIA tables: span[role="cell"]
    TABLE_CELLS = 'td, span[role="cell"]'

    # Subject extraction
    # Subject can be in a button or an <a> tag with role="button"
    SUBJECT_BUTTON = 'button, a[role="button"], a.link-text'

    # File attachments
    FILE_LINKS = "a"
    FILE_IMAGES = "img"

    # ==================== Pagination Selectors ====================

    # Forward navigation
    NEXT_BUTTON_SELECTORS = [
        'button:has-text("הבא")',
        'button:has-text("Next")',
        'a:has-text("הבא")',
        'a:has-text("Next")',
        '[aria-label*="הבא"]',
        '[aria-label*="Next"]',
        'button[aria-label*="הבא"]',
        ".pagination button:last-child",
        ".pagination a:last-child",
        '[class*="next"]',
        '[class*="Next"]',
    ]
    NEXT_BUTTON_TEXT_PATTERNS = ["הבא", "Next"]

    # Backward navigation
    PREV_BUTTON_SELECTORS = [
        'button:has-text("הקודם")',
        'button:has-text("Previous")',
        'button:has-text("קודם")',
        'a:has-text("הקודם")',
        'a:has-text("Previous")',
        'a:has-text("קודם")',
        '[aria-label*="הקודם"]',
        '[aria-label*="Previous"]',
        '[aria-label*="קודם"]',
        'button[aria-label*="הקודם"]',
        ".pagination button:first-child",
        ".pagination a:first-child",
        '[class*="prev"]',
        '[class*="Prev"]',
        '[class*="previous"]',
    ]
    PREV_BUTTON_TEXT_PATTERNS = ["הקודם", "Previous", "קודם"]

    # ==================== Error Detection ====================

    # Error keywords (Hebrew and English)
    ERROR_KEYWORDS = ["שגיאה", "error", "לא נכון", "לא תקין", "נכשל", "כושל"]
    ERROR_REGEX_PATTERN = r"/שגיאה|לא נכון|נכשל/i"

    # reCAPTCHA detection
    RECAPTCHA_IFRAME = 'iframe[src*="recaptcha"], iframe[title*="reCAPTCHA"]'

    # ==================== URL Patterns ====================

    MOE_LOGIN_URL_PATTERN = "**/lgn.edu.gov.il/**"
    WEBTOP_DOMAIN = "webtop.smartschool.co.il"
    MOE_DOMAIN = "lgn.edu.gov.il"
    LOGIN_PAGE_INDICATOR = "login"

    # ==================== Date Formats ====================

    DATE_FORMAT_DISPLAY = "%d/%m/%Y"  # Format used on the page
    DATE_FORMAT_INPUT = "%d-%m-%Y"  # Format for user input


class TextPatterns:
    """Text patterns and labels used in the Webtop interface."""

    # Authentication
    COOKIE_BUTTON_TEXT = "אשר cookies"
    MOE_BUTTON_TEXT = "הזדהות משרד החינוך"
    USERNAME_LABEL = "קוד המשתמש"
    PASSWORD_LABEL = "סיסמה"
    LOGIN_BUTTON_TEXT = "כניסה"
    USERNAME_PASSWORD_TAB = "כניסה עם קוד משתמש וסיסמה"
    MOBILE_TAB = "כניסה עם קוד חד פעמי לנייד"

    # Navigation
    STUDENT_CARD_TEXT = "כרטיס תלמיד"
    HOMEWORK_TEXT = "נושאי שיעור ושיעורי-בית"

    # Dashboard
    DASHBOARD_INFO_CENTER = "ריכוז מידע"
    DASHBOARD_STUDENT_CARD = "כרטיס תלמיד"
    DASHBOARD_MESSAGES = "תיבת הודעות"

    # Pagination
    NEXT_BUTTON_HEBREW = "הבא"
    NEXT_BUTTON_ENGLISH = "Next"
    PREV_BUTTON_HEBREW = "הקודם"
    PREV_BUTTON_ALT_HEBREW = "קודם"
    PREV_BUTTON_ENGLISH = "Previous"

    # Placeholders
    NO_HOMEWORK_PLACEHOLDER = "אין"
    EMPTY_LESSON_PLACEHOLDER = "---"


class Timeouts:
    """Timeout values in milliseconds."""

    # Element visibility
    ELEMENT_VISIBLE = 5000
    ELEMENT_WAIT = 10000

    # Page navigation
    PAGE_LOAD = 15000
    URL_WAIT = 10000
    NETWORK_IDLE = 10000

    # Login flow
    # Increase timeout in CI environments (60s) vs local (30s)
    _is_ci = os.getenv("CI", "").lower() == "true"
    LOGIN_REDIRECT = 60000 if _is_ci else 30000
    RECAPTCHA_CHECK_DELAY = 5  # seconds before checking reCAPTCHA
    RECAPTCHA_WAIT = 10  # seconds to wait for reCAPTCHA

    # Button enablement
    BUTTON_ENABLE_MAX_WAIT = 10  # iterations
    BUTTON_ENABLE_DELAY = 0.5  # seconds

    # Tab selection
    TAB_CLICK_DELAY = 2  # seconds


class Delays:
    """Delay values in seconds for various operations."""

    # General delays
    SHORT = 0.3
    MEDIUM = 0.5
    LONG = 1
    VERY_LONG = 2
    EXTRA_LONG = 3

    # Specific operation delays
    AFTER_CLICK = 1
    AFTER_FILL = 0.5
    AFTER_TAB_SWITCH = 2
    AFTER_PAGE_LOAD = 2
    AFTER_NAVIGATION = 3
    AFTER_LOGIN = 2
    RECAPTCHA_CHECK = 2
