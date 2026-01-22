"""
Setup script for webtop-il-kit package.

This file is kept for backward compatibility but pyproject.toml is the
primary configuration.
"""
from setuptools import setup

# Read the README file
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "A Python library to scrape and retrieve homework from the Webtop platform"

setup(
    name="webtop-il-kit",
    version="0.1.0",
    author="Avishay Bar",
    description="A Python library to scrape and retrieve homework from the Webtop platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/avishayil/webtop-il-kit",
    package_dir={"": "src"},
    packages=["webtop_il_kit"],
    python_requires=">=3.8",
    install_requires=[
        "playwright>=1.48.0",
        "python-dotenv>=1.0.0",
        "beautifulsoup4>=4.12.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-mock>=3.12.0",
            "pre-commit>=3.0.0",
            # Pre-commit hook dependencies
            "flake8>=4.0.1",
            "flake8-blind-except>=0.1.1",
            "flake8-docstrings>=1.6.0",
            "flake8-bugbear>=22.7.1",
            "flake8-comprehensions>=3.10.0",
            "flake8-implicit-str-concat>=0.3.0",
            "black>=22.6.0",
            "isort>=5.11.5",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
