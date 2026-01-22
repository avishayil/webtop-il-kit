# Webtop IL Kit

A Python library to scrape and retrieve homework from the Webtop platform (webtop.smartschool.co.il).

## Features

- Automated login using Ministry of Education authentication
- Navigation to homework section
- Extraction of homework assignments for any date
- Support for pagination to find historical homework
- Modular, maintainable codebase with centralized configuration

## Installation

### From PyPI (when published)

```bash
pip install webtop-il-kit
```

### From Source

```bash
git clone https://github.com/avishayil/webtop-il-kit.git
cd webtop-il-kit
pip install -e ".[dev]"
python -m playwright install --with-deps chromium
```

### Prerequisites

- Python 3.8+
- Playwright browsers (installed automatically)

## Configuration

### Environment Variables

Create a `.env` file:

```bash
MINISTRY_OF_EDUCATION_USERNAME=your_username
MINISTRY_OF_EDUCATION_PASSWORD=your_password
```

### Logging

The library uses Python's `logging` module and automatically configures logging to stdout. By default, **INFO level and above** are shown, which includes:

- High-level operations (launching browser, login, navigation, extraction)
- Success messages (found homework items, successful navigation)
- Warnings and errors

To see more detailed logs:

```bash
# Set log level to DEBUG for detailed troubleshooting
export WEBTOP_LOG_LEVEL=DEBUG

# Or in Python
import logging
logging.getLogger('webtop_il_kit').setLevel(logging.DEBUG)
```

To see only warnings and errors:

```bash
export WEBTOP_LOG_LEVEL=WARNING
```

## Usage

```python
import asyncio
from webtop_il_kit import WebtopScraper

async def main():
    scraper = WebtopScraper()

    # Get today's homework
    homework = await scraper.get_today_homework()

    # Get homework for a specific date
    homework = await scraper.get_today_homework(date="21-01-2026")

    for item in homework:
        print(f"Subject: {item['subject']}")
        print(f"Content: {item['combined']}")
        print(f"Date: {item['date']}")

asyncio.run(main())
```

## Project Structure

```
webtop-il-kit/
├── src/webtop_il_kit/
│   ├── __init__.py          # Package entry point
│   ├── scraper.py           # Main orchestrator
│   ├── auth.py              # Authentication & login
│   ├── browser.py           # Browser management
│   ├── navigator.py         # Site navigation
│   ├── extractor.py         # Data extraction from DOM
│   ├── pagination.py        # Date pagination
│   ├── selectors.py         # CSS selectors, timeouts, delays
│   ├── config.py            # Configuration constants
│   └── utils.py             # Utility functions (date parsing)
├── tests/
│   ├── unit/                # Unit tests (isolated, fast)
│   ├── integration/         # Integration tests (module interactions)
│   ├── recorded/            # Recorded tests (HTML fixtures, CI-friendly)
│   └── e2e/                 # E2E tests (require RUN_WEBTOP_E2E=1)
├── scripts/
│   └── capture_fixtures.py  # Script to capture HTML fixtures
└── .github/workflows/ci.yml # CI/CD pipeline
```

## Development

### Running Tests

```bash
# All tests (unit, integration, recorded)
pytest

# By category
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/recorded/      # Recorded tests (use HTML fixtures)

# E2E tests (require credentials and network)
# These are NOT run in CI to avoid Cloudflare issues
RUN_WEBTOP_E2E=1 pytest tests/e2e/ -v -s

# With markers
pytest -m unit
pytest -m integration
pytest -m recorded
pytest -m e2e  # Only runs if RUN_WEBTOP_E2E=1

# With coverage
pytest --cov=src/webtop_il_kit --cov-report=html
```

### Recorded Tests

Recorded tests use pre-recorded HTML fixtures to test the parsing pipeline
without network access or credentials. They verify extraction logic, pagination,
and schema validation.

**Creating Fixtures:**
```bash
export MINISTRY_OF_EDUCATION_USERNAME=your_username
export MINISTRY_OF_EDUCATION_PASSWORD=your_password
python scripts/capture_fixtures.py
```

This saves HTML to `tests/recorded/fixtures/`. Fixture naming:
- `homework_page_YYYY_MM_DD.html` - Page with homework for a date
- `homework_page_empty.html` - Page with no homework
- `homework_page_multiple_dates.html` - Page showing multiple dates

### Code Quality

```bash
# Install pre-commit hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### CI/CD

- **Pull Requests**: Run pre-commit checks, unit tests, and integration tests
- **Push to main**: Run recorded tests
- **Releases**: Automatically publish to PyPI when a GitHub release is published (using OpenID Connect)
- **E2E Tests**: Not run in CI (require `RUN_WEBTOP_E2E=1` to run locally)

#### PyPI Publishing Setup

The release workflow uses PyPI's Trusted Publisher (OpenID Connect) for secure authentication. To enable publishing:

1. Go to https://pypi.org/manage/project/webtop-il-kit/settings/publishing/
2. Click "Add a new trusted publisher"
3. Configure:
   - **Publisher**: GitHub
   - **Owner**: `avishayil` (or your GitHub username/org)
   - **Repository name**: `webtop-il-kit`
   - **Workflow filename**: `.github/workflows/release.yml`
4. Save the configuration

No API tokens or secrets are needed - authentication is handled automatically via OIDC.

#### Creating a Release

To publish a new version to PyPI:

1. Update the version in `pyproject.toml` and `setup.py` (or let the workflow update it from the tag)
2. Create a GitHub release with a version tag (e.g., `v1.2.3` or `1.2.3`)
3. The workflow will automatically:
   - Extract the version from the tag
   - Update version files if needed
   - Build the package
   - Publish to PyPI

## Troubleshooting

### Browser Issues

If you see `TargetClosedError`:

1. Update Playwright:
   ```bash
   pip install --upgrade playwright
   python -m playwright install --with-deps
   ```

2. The scraper automatically tries multiple browsers (Chrome, Chromium, WebKit, Firefox)

### Login Issues

- Verify credentials in `.env` file
- reCAPTCHA may require manual solving
- Run with `headless=False` for debugging

### No Homework Found

- Check if homework exists for the target date
- Verify date format: `DD-MM-YYYY`
- Check browser console for errors

## License

MIT
