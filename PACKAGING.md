# Packaging Guide

This document explains how to build and distribute the `webtop-il-kit` package.

## Building the Package

### Prerequisites

```bash
pip install build setuptools wheel
```

### Build Distribution Packages

```bash
# Build both source distribution and wheel
python -m build

# Or build individually
python -m build --sdist    # Source distribution (.tar.gz)
python -m build --wheel    # Wheel distribution (.whl)
```

The built packages will be in the `dist/` directory.

## Installing Locally

### Development Installation (Editable)

```bash
pip install -e .
```

This installs the package in "editable" mode, so changes to the source code are immediately available.

### Regular Installation

```bash
pip install .
```

Or install from a built distribution:

```bash
pip install dist/webtop_il_kit-0.1.0-py3-none-any.whl
```

## Publishing to PyPI

### Test PyPI (Recommended First)

1. Create an account at https://test.pypi.org/
2. Create an API token
3. Upload to Test PyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

4. Test installation:

```bash
pip install --index-url https://test.pypi.org/simple/ webtop-il-kit
```

### Production PyPI

1. Create an account at https://pypi.org/
2. Create an API token
3. Upload to PyPI:

```bash
python -m twine upload dist/*
```

## Package Structure

```
webtop-il-kit/
├── src/
│   └── webtop_il_kit/   # Package source code
├── tests/               # Test suite
├── pyproject.toml       # Modern Python packaging config
├── setup.py             # Legacy setup script
├── MANIFEST.in          # Files to include in distribution
└── README.md            # Package description
```

## Version Management

Update the version in:
- `pyproject.toml` → `[project] version = "X.Y.Z"`
- `setup.py` → `version="X.Y.Z"`
- `src/webtop_il_kit/__init__.py` → `__version__ = "X.Y.Z"`

## Dependencies

### Core Dependencies
- `playwright>=1.48.0` - Browser automation
- `python-dotenv>=1.0.0` - Environment variable management
- `beautifulsoup4>=4.12.2` - HTML parsing

### Optional Dependencies

**Development extras** (`[dev]`):
- `pytest>=7.4.3` - Testing framework
- `pytest-asyncio>=0.21.1` - Async test support
- `pytest-mock>=3.12.0` - Mocking utilities

## Testing the Package

After building, test the package:

```bash
# Create a virtual environment
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install the package
pip install dist/webtop_il_kit-0.1.0-py3-none-any.whl

# Test import
python -c "from webtop_il_kit import WebtopScraper; print('✓ Package works!')"
```

## Distribution Checklist

Before publishing:

- [ ] Update version number in all files
- [ ] Update CHANGELOG.md (if exists)
- [ ] Run all tests: `pytest`
- [ ] Build package: `python -m build`
- [ ] Test installation: `pip install dist/webtop_il_kit-*.whl`
- [ ] Check package contents: `tar -tzf dist/webtop_il_kit-*.tar.gz`
- [ ] Update README.md with latest features
- [ ] Tag release in git: `git tag v0.1.0`
