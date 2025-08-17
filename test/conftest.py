"""
Shared pytest configuration and fixtures for Strongbird tests.
"""

import re
from pathlib import Path
from typing import Dict

import pytest

from strongbird.browser import BrowserManager
from strongbird.extractor import StrongbirdExtractor

# ============================================================================
# Path Configuration
# ============================================================================


@pytest.fixture
def test_dir():
    """Get test directory path."""
    return Path(__file__).parent


@pytest.fixture
def fixtures_dir(test_dir):
    """Get fixtures directory path."""
    return test_dir / "fixtures"


@pytest.fixture
def project_root(test_dir):
    """Get project root directory path."""
    return test_dir.parent


# ============================================================================
# Browser and Extractor Fixtures
# ============================================================================


@pytest.fixture
def browser_manager():
    """Create a browser manager instance."""
    return BrowserManager(
        headless=True,
        browser_type="chromium",
        viewport_width=1920,
        viewport_height=1080,
        timeout=30000,
    )


@pytest.fixture
def extractor(browser_manager):
    """Create a strongbird extractor instance."""
    return StrongbirdExtractor(
        browser_manager=browser_manager,
        use_playwright=True,
        favor_precision=False,
    )


@pytest.fixture
def extractor_no_playwright():
    """Create a strongbird extractor without Playwright."""
    return StrongbirdExtractor(
        use_playwright=False,
        favor_precision=False,
    )


# ============================================================================
# Test Files Fixtures
# ============================================================================


@pytest.fixture
def mathjax_test_file(fixtures_dir):
    """Get path to MathJax test HTML file."""
    path = fixtures_dir / "test-mathjax.html"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def comprehensive_math_file(fixtures_dir):
    """Get path to comprehensive math test HTML file."""
    path = fixtures_dir / "comprehensive-math-test.html"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def simple_batch_file(fixtures_dir):
    """Get path to simple batch test file."""
    path = fixtures_dir / "test_batch_simple.txt"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def glob_batch_file(fixtures_dir):
    """Get path to glob pattern batch test file."""
    path = fixtures_dir / "test_batch_glob.txt"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def mixed_batch_file(fixtures_dir):
    """Get path to mixed content batch test file."""
    path = fixtures_dir / "test_batch_mixed.txt"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


@pytest.fixture
def empty_batch_file(fixtures_dir):
    """Get path to empty batch test file."""
    path = fixtures_dir / "test_batch_empty.txt"
    if not path.exists():
        pytest.skip(f"Test file not found: {path}")
    return path


# ============================================================================
# Helper Functions
# ============================================================================


def count_math_expressions(content: str) -> Dict[str, int]:
    """
    Count different types of math expressions in extracted content.

    Args:
        content: The extracted content string

    Returns:
        Dictionary with counts of inline_math, display_math, and total_expressions
    """
    counts = {
        "inline_math": len(re.findall(r"\$[^$\n]+\$", content)),
        "display_math": len(re.findall(r"\$\$[^$]+\$\$", content, re.DOTALL)),
        "total_expressions": 0,
    }
    counts["total_expressions"] = counts["inline_math"] + counts["display_math"]
    return counts


# ============================================================================
# Custom Markers
# ============================================================================


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (requires network)"
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "cli: mark test as a CLI test")
    config.addinivalue_line("markers", "math: mark test as a math extraction test")
    config.addinivalue_line("markers", "batch: mark test as a batch mode test")


# ============================================================================
# Async Support
# ============================================================================

# This ensures that pytest-asyncio is properly configured
pytest_plugins = ("pytest_asyncio",)
