# Strongbird Test Suite

This directory contains the test suite for the Strongbird web content extractor, with a focus on mathematical equation processing.

## Structure

```
test/
├── README.md                    # This file
├── test_suite.py                # Unified test runner (ALL TESTS)
└── fixtures/                    # Test HTML files
    ├── comprehensive-math-test.html  # Multi-format math test
    └── test-mathjax.html            # MathJax v3 test
```

## Running Tests

### Full Test Suite (Recommended)
```bash
cd strongbird
uv run python test/test_suite.py
```

### Verbose Mode
```bash
cd strongbird
uv run python test/test_suite.py --verbose
```

### Skip Integration Tests (Offline Mode)
```bash
cd strongbird
uv run python test/test_suite.py --skip-integration
```

### Individual File Testing
```bash
cd strongbird
# Test with local fixtures
uv run strongbird test/fixtures/comprehensive-math-test.html --process-math
uv run strongbird test/fixtures/test-mathjax.html --format markdown
```

## Test Coverage

The unified test suite includes three categories of tests:

### 📋 CLI Functionality Tests
- Help command functionality
- Local file extraction (text, markdown, JSON formats)
- Output to file capability
- Math processing via CLI
- Metadata handling (inclusion/exclusion)

### 🧮 Math Extraction Tests
- **comprehensive-math-test.html**: Tests KaTeX, MathML, MathJax v2 script tags, and fallback MathML conversion
- **test-mathjax.html**: Tests MathJax v3 inline and display math

### 🌐 Integration Tests
- **Wikipedia Quadratic Formula**: Tests Wikipedia's MediaWiki Math Extension
- **Wikipedia Euler's Identity**: Tests mathematical expressions in Wikipedia articles
- Network-dependent (can be skipped with `--skip-integration`)

## Expected Results

The test suite validates that strongbird can extract mathematical equations from various rendering engines and convert them to standardized TeX format:

- Inline math: `$equation$`
- Display math: `$$equation$$`

### Supported Math Formats
- ✅ KaTeX (with TeX annotations)
- ✅ MathJax v2/v3/v4
- ✅ MathML with TeX annotations
- ✅ MathML fallback conversion
- ✅ Wikipedia MediaWiki Math Extension
- ✅ Raw MathML elements

## Adding New Tests

1. **Add HTML fixture files** to `fixtures/` directory
2. **Update `test_suite.py`** with new test methods:
   - Add CLI tests to `run_cli_tests()` method
   - Add math tests to `run_math_tests()` method
   - Add integration tests to `run_integration_tests()` method
3. **Run the test suite** to validate: `uv run python test/test_suite.py`

### Test Result Structure
Each test returns a dictionary with:
- `name`: Test name
- `status`: PASS/FAIL/ERROR/SKIP
- `details`: Additional information

## Dependencies

The unified test suite requires:
- **Playwright** for browser automation
- **Strongbird package** and its dependencies
- **Internet connection** for integration tests (optional, can be skipped)
- **uv** package manager for running tests

## Test Output

The test suite provides:
- ✅ Clear pass/fail indicators
- 📊 Detailed summary statistics
- 🔍 Verbose mode for debugging
- 📋 Categorized test results (CLI, Math, Integration)
- 🎯 Success rate calculation
