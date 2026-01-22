#!/usr/bin/env python3
"""Script to capture HTML fixtures from Webtop for recorded tests.

Usage:
    python scripts/capture_fixtures.py

This will:
1. Launch a browser
2. Navigate to Webtop (requires credentials)
3. Save HTML pages as fixtures
4. Save them to tests/recorded/fixtures/
"""
import asyncio
import os
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from webtop_il_kit.auth import WebtopAuth
from webtop_il_kit.browser import WebtopBrowser
from webtop_il_kit.navigator import WebtopNavigator

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "recorded" / "fixtures"


def anonymize_html(html_content: str) -> str:
    """Anonymize personal information from HTML content.

    Removes names, initials, and other personal identifiers while preserving
    the HTML structure for testing purposes.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove text from short-name-span elements (initials like "בא")
    for elem in soup.find_all(class_=re.compile(r"short-name-span")):
        if elem.string:
            elem.string = ""

    # Remove text from user name elements (class contains "title" and "bold-text")
    for elem in soup.find_all(class_=re.compile(r"bold-text.*title|title.*bold-text")):
        text = elem.get_text(strip=True)
        # If it looks like a name (2+ Hebrew words), remove it
        if re.search(r"^[\u0590-\u05FF]{2,}(\s+[\u0590-\u05FF]{2,})+$", text):
            elem.string = ""

    # Remove names from aria-label attributes
    for elem in soup.find_all(attrs={"aria-label": True}):
        aria_label = elem.get("aria-label", "")
        # Check if aria-label contains what looks like a name
        # Pattern: 2-4 Hebrew words (typical name format)
        name_match = re.search(r"([\u0590-\u05FF]{2,}\s+[\u0590-\u05FF]{2,})", aria_label)
        if name_match:
            # Remove the name part, keep the prefix if it exists
            if " - " in aria_label:
                # Keep the prefix (like "פרופיל אישי"), remove the name
                parts = aria_label.split(" - ")
                elem["aria-label"] = parts[0]
            elif name_match.group(1) == aria_label.strip():
                # If it's just a name, remove it entirely
                elem["aria-label"] = ""
            else:
                # Remove the name from the middle/end
                elem["aria-label"] = re.sub(r"[\u0590-\u05FF]{2,}\s+[\u0590-\u05FF]{2,}", "", aria_label).strip()

    # Remove user details text (like "כניסה אחרונה: 22/01/2026 (10:23)")
    for elem in soup.find_all(class_=re.compile(r"bold-text")):
        text = elem.get_text(strip=True)
        # Remove text that contains login timestamps
        if "כניסה אחרונה" in text or re.search(r"\d{2}/\d{2}/\d{4}\s*\(\d{1,2}:\d{2}\)", text):
            elem.string = ""

    # Remove school names from user-type elements
    # Pattern: "תלמיד ב בית החינוך ע ש שמעון פרס" -> "תלמיד"
    for elem in soup.find_all(class_=re.compile(r"user-type")):
        text = elem.get_text(strip=True)
        if "תלמיד" in text:
            # Keep just "תלמיד" part, remove school name
            parts = text.split(" ב ")
            if len(parts) > 1:
                elem.string = parts[0]

    # Remove text content from divs with user-details or text-padding-right
    # that contain names
    for elem in soup.find_all(class_=re.compile(r"user-details|text-padding-right")):
        for child in elem.find_all(class_=re.compile(r"bold-text|title")):
            text = child.get_text(strip=True)
            # If it's a name (2+ Hebrew words, not system text), remove it
            if re.search(r"^[\u0590-\u05FF]{2,}(\s+[\u0590-\u05FF]{2,})+$", text):
                # Don't remove if it's a system label
                if text not in ["ריכוז מידע", "תיבת הודעות", "כרטיס תלמיד"]:
                    child.string = ""

    # Remove student name from print-only header
    # Pattern: "נושאי שיעור ושיעורי-בית עבור בר אגם, מחצית א - תשפ״ו"
    for elem in soup.find_all(class_=re.compile(r"print-only-flex")):
        text = elem.get_text(strip=True)
        if "עבור" in text:
            # Remove name part: "עבור בר אגם," -> remove entire "עבור [name]," part
            text = re.sub(r"עבור\s+[\u0590-\u05FF]{2,}\s+[\u0590-\u05FF]{2,},?\s*", "", text)
            elem.string = text

    # Remove names from table cells (teacher names in homework table)
    # Handle both <table> elements and divs with role="table"
    tables = soup.find_all("table") + soup.find_all(attrs={"role": re.compile(r"table")})
    for table in tables:
        # Handle both <tr> and divs with role="row"
        rows = table.find_all("tr") + table.find_all(attrs={"role": re.compile(r"row")})
        for row in rows:
            # Get both td/th and span/div elements with role="cell"
            cells = row.find_all(["td", "th"]) + row.find_all(attrs={"role": re.compile(r"cell")})
            # Skip header rows
            if any(cell.name == "th" for cell in cells):
                continue
            # If this looks like a data row, anonymize potential name cells
            for _, cell in enumerate(cells):
                text = cell.get_text(strip=True)
                # If cell contains what looks like a name (2+ Hebrew words)
                # and it's not a subject name or system text
                if re.search(r"^[\u0590-\u05FF]{2,}(\s+[\u0590-\u05FF]{2,})+$", text):
                    # Don't remove if it's a known subject or system term
                    system_terms = [
                        "מתמטיקה",
                        "אנגלית",
                        "עברית",
                        "היסטוריה",
                        "גיאוגרפיה",
                        "מדעים",
                        "נוכח",
                        "נעדר",
                        "התקיים",
                        "טרם הוזנו נתונים",
                        "חנ``ג",
                        "מולדת",
                        "מוזיקה",
                        "אומנות",
                        "ספריה",
                        "חינוך",
                        "כישורי חיים",
                        "בשבילי המורשת",
                        "למידה חוץ כיתתית",
                    ]
                    if text not in system_terms:
                        # Clear all text content from the cell
                        cell.string = ""
                        # Also clear any nested text
                        for child in cell.descendants:
                            if hasattr(child, "string") and child.string:
                                if re.search(
                                    r"[\u0590-\u05FF]{2,}\s+[\u0590-\u05FF]{2,}",
                                    child.string,
                                ):
                                    child.string = ""

    # Remove names from any standalone text nodes that contain names
    # This handles text between elements (but be careful not to remove too much)
    for elem in soup.find_all(string=True):
        if elem.parent and elem.strip():
            text = elem.strip()
            # Only process if it's a standalone text node (not inside other tags)
            # Check if it's a name (2+ Hebrew words, not system text)
            if re.search(r"^[\u0590-\u05FF]{2,}(\s+[\u0590-\u05FF]{2,})+$", text):
                # Don't remove if it's a known system term
                system_terms = [
                    "ריכוז מידע",
                    "תיבת הודעות",
                    "כרטיס תלמיד",
                    "מתמטיקה",
                    "אנגלית",
                    "עברית",
                    "היסטוריה",
                    "גיאוגרפיה",
                    "מדעים",
                ]
                if text not in system_terms:
                    # Check if parent is not a system element
                    parent = elem.parent
                    parent_class = parent.get("class", [])
                    parent_class_str = " ".join(parent_class) if parent_class else ""
                    # Only remove if it's not in a navigation or system element
                    if "navText" not in parent_class_str and parent.name not in [
                        "script",
                        "style",
                    ]:
                        elem.replace_with("")

    return str(soup)


async def capture_homework_page(page, date_str: str = None):
    """Capture a homework page and save it as a fixture file."""
    # Navigate to homework page
    navigator = WebtopNavigator()
    success = await navigator.navigate_to_homework(page)
    if not success:
        print("Failed to navigate to homework page")
        return None

    # Wait for content to load
    await page.wait_for_load_state("networkidle")
    await asyncio.sleep(2)

    # Get HTML content
    html_content = await page.content()

    # Anonymize personal information
    print("Anonymizing personal information...")
    html_content = anonymize_html(html_content)

    # Generate filename
    if date_str:
        filename = f"homework_page_{date_str.replace('-', '_')}.html"
    else:
        today = datetime.now().strftime("%Y_%m_%d")
        filename = f"homework_page_{today}.html"

    # Save to fixtures directory
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    fixture_path = FIXTURES_DIR / filename
    fixture_path.write_text(html_content, encoding="utf-8")

    print(f"✓ Saved fixture: {fixture_path}")
    return fixture_path


async def main():
    """Capture HTML fixtures from Webtop for recorded tests."""
    # Check credentials
    username = os.getenv("MINISTRY_OF_EDUCATION_USERNAME")
    password = os.getenv("MINISTRY_OF_EDUCATION_PASSWORD")

    if not username or not password:
        print("ERROR: MINISTRY_OF_EDUCATION_USERNAME and")
        print("MINISTRY_OF_EDUCATION_PASSWORD must be set")
        return

    print("Capturing Webtop HTML fixtures...")
    print(f"Fixtures will be saved to: {FIXTURES_DIR}")

    async with async_playwright() as playwright:
        browser = await WebtopBrowser.launch_browser(playwright)
        context = await WebtopBrowser.create_context(browser)
        page = await WebtopBrowser.create_page(context)

        try:
            # Login
            print("Logging in...")
            auth = WebtopAuth(username, password)
            login_success = await auth.login(page)
            if not login_success:
                print("Failed to login")
                return

            print("Login successful")

            # Capture today's homework page
            print("\nCapturing today's homework page...")
            await capture_homework_page(page)

            # Optionally capture other dates
            # Uncomment to capture specific dates:
            # from datetime import timedelta
            # yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%m-%Y")
            # await capture_homework_page(page, yesterday)

            print("\n✓ Fixture capture complete!")

        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
