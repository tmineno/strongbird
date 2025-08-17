# Strongbird Test Suite

This directory contains the test suite for the Strongbird web content extractor, with a focus on mathematical equation processing.

## Structure

```
test/
├── README.md                    # This file
├── run_tests.py                 # Main test runner
├── test_math_extraction.py      # Math extraction tests
└── fixtures/                    # Test HTML files
    ├── comprehensive-math-test.html  # Multi-format math test
    └── test-mathjax.html            # MathJax v3 test
```

## Running Tests

### Quick Test Run
```bash
cd strongbird
uv run python test/run_tests.py
```

### Math Extraction Tests Only
```bash
cd strongbird
uv run python test/test_math_extraction.py
```

### Individual File Testing
```bash
cd strongbird
uv run strongbird "file://$(pwd)/test/fixtures/comprehensive-math-test.html" --process-math
```

## Test Coverage

### Local HTML Fixtures
- **comprehensive-math-test.html**: Tests KaTeX, MathML, MathJax v2 script tags, and fallback MathML conversion
- **test-mathjax.html**: Tests MathJax v3 inline and display math

### Wikipedia Integration Tests
- **Quadratic Formula**: Tests Wikipedia's MediaWiki Math Extension
- **Euler's Identity**: Tests mathematical expressions in Wikipedia articles

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

1. Add HTML fixture files to `fixtures/` directory
2. Update `test_math_extraction.py` with new test cases
3. Run the test suite to validate

## Dependencies

The test suite requires:
- Playwright for browser automation
- The strongbird package and its dependencies
- Internet connection for Wikipedia tests (optional)