# Strongbird Test Suite

This directory contains the comprehensive pytest-based test suite for the Strongbird web content extractor, with a focus on mathematical equation processing.

## Structure

```
test/
├── README.md             # This file
├── conftest.py          # Shared fixtures and configuration
├── test_cli.py          # CLI functionality tests (17 tests)
├── test_math.py         # Math extraction tests (9 tests)
├── test_integration.py  # Integration tests with real websites (11 tests)
├── test_parallel.py     # Parallel processing tests (15 tests)
├── test_url_expansion.py # URL expansion tests (27 tests)
└── fixtures/            # Test HTML files
    ├── comprehensive-math-test.html  # Multi-format math test
    └── test-mathjax.html            # MathJax v3 test
```

## Running Tests

### Quick Start
```bash
# Run all tests
pytest test/

# Run tests with verbose output
pytest test/ -v

# Run only local tests (skip network-dependent tests)
pytest test/ -m "not integration"
```

### Test Categories

Run specific test categories using markers:

```bash
# CLI functionality tests
pytest test/ -m cli

# Math extraction tests
pytest test/ -m math

# Integration tests (requires network)
pytest test/ -m integration

# Run only fast, local tests
pytest test/ -m "not integration and not slow"
```

### Specific Test Execution

```bash
# Run specific test file
pytest test/test_cli.py

# Run specific test class
pytest test/test_cli.py::TestCLI

# Run specific test method
pytest test/test_cli.py::TestCLI::test_help_command

# Run with pattern matching
pytest test/ -k "math"
pytest test/ -k "test_help"
```

### Parallel Execution

```bash
# Install pytest-xdist (if not already installed)
uv add --dev pytest-xdist

# Run tests in parallel (auto-detect CPUs)
pytest test/ -n auto

# Run with specific number of workers
pytest test/ -n 4
```

### Coverage Reports

```bash
# Install pytest-cov (if not already installed)
uv add --dev pytest-cov

# Run with coverage
pytest test/ --cov=strongbird

# Generate HTML coverage report
pytest test/ --cov=strongbird --cov-report=html

# View coverage in terminal with missing lines
pytest test/ --cov=strongbird --cov-report=term-missing
```

## Test Coverage

The test suite includes comprehensive coverage across all functionality:

### 📋 CLI Tests (`test_cli.py` - 17 tests)
- Help and version commands
- Local file extraction with different formats (text, markdown, JSON)
- Output to file functionality
- Math processing flags
- Metadata handling (inclusion/exclusion)
- Browser configuration options
- Parallel processing options (`-j`, `--proc`)
- URL globbing patterns

### 🧮 Math Extraction Tests (`test_math.py` - 9 tests)
- MathJax equation extraction from fixtures
- Comprehensive math format testing (KaTeX, MathML, MathJax v2/v3)
- Different output formats with math content
- Metadata inclusion with math processing
- Error handling for malformed math expressions

### 🌐 Integration Tests (`test_integration.py` - 11 tests)
- Wikipedia math extraction (Quadratic formula, Euler's identity)
- HTTP/HTTPS extraction from real websites
- Different output formats consistency
- Error handling (404, redirects)
- Large page extraction
- **Note**: Requires network connection (can be skipped with `-m "not integration"`)

### 🚀 Parallel Processing Tests (`test_parallel.py` - 15 tests)
- Page pool management
- Concurrent URL processing
- Semaphore concurrency control
- Error handling in parallel operations
- Progress tracking

### 🔗 URL Expansion Tests (`test_url_expansion.py` - 27 tests)
- Curl-style globbing patterns
- Numeric ranges (`[1-100]`, `[001-100]`)
- Alphabetic ranges (`[a-z]`, `[A-Z]`)
- List patterns (`{one,two,three}`)
- Complex multi-pattern URLs

## Expected Results

The test suite validates that strongbird can:

### Mathematical Equation Processing
- Extract equations from various rendering engines
- Convert them to standardized TeX format:
  - Inline math: `$equation$`
  - Display math: `$$equation$$`

### Supported Math Formats
- ✅ KaTeX (with TeX annotations)
- ✅ MathJax v2/v3/v4
- ✅ MathML with TeX annotations
- ✅ MathML fallback conversion
- ✅ Wikipedia MediaWiki Math Extension
- ✅ Raw MathML elements

## Fixtures

Test fixtures are located in `test/fixtures/`:
- **comprehensive-math-test.html**: Tests multiple math rendering formats
- **test-mathjax.html**: Focuses on MathJax v3 inline and display math

Common fixtures are defined in `conftest.py`:
- `browser_manager` - Browser manager instance
- `extractor` - Strongbird extractor with Playwright
- `test_dir`, `fixtures_dir`, `project_root` - Directory paths
- `mathjax_test_file` - Path to MathJax test HTML
- `comprehensive_math_file` - Path to comprehensive math test HTML

## Custom Markers

Tests are organized with markers for selective execution:
- `@pytest.mark.cli` - CLI functionality tests
- `@pytest.mark.math` - Math extraction tests
- `@pytest.mark.integration` - Integration tests (network required)
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.asyncio` - Async test functions

## CI/CD Integration

### GitHub Actions Example
```yaml
- name: Run tests
  run: |
    uv sync
    uv run pytest test/ -v --tb=short -m "not integration"
```

### GitLab CI Example
```yaml
test:
  script:
    - uv sync
    - uv run pytest test/ --cov=strongbird -m "not integration"
```

## Adding New Tests

1. **Create test file** following naming convention `test_*.py`
2. **Use appropriate markers** (`@pytest.mark.cli`, `@pytest.mark.math`, etc.)
3. **Add fixtures to conftest.py** if needed for shared setup
4. **Use descriptive test names** that explain what's being tested
5. **Include assertions** with clear failure messages

Example test structure:
```python
import pytest

@pytest.mark.cli
def test_new_feature():
    """Test description."""
    # Arrange
    # Act
    # Assert
    assert result == expected, "Helpful error message"
```

## Troubleshooting

### Common Issues

1. **Import errors**:
   ```bash
   uv sync  # Ensure project and dependencies are installed
   ```

2. **Async test failures**:
   ```bash
   uv add --dev pytest-asyncio  # Ensure pytest-asyncio is installed
   ```

3. **Network test failures**:
   ```bash
   pytest test/ -m "not integration"  # Skip network-dependent tests
   ```

4. **Fixture not found**:
   - Check that `conftest.py` exists in test directory
   - Verify fixture name matches exactly

5. **Test discovery issues**:
   ```bash
   pytest test/ --collect-only  # See what tests pytest finds
   ```

## Dependencies

Required test dependencies (in `pyproject.toml`):
- pytest >= 8.4.1
- pytest-asyncio >= 1.1.0

Optional dependencies for enhanced testing:
- pytest-xdist (parallel execution)
- pytest-cov (coverage reports)
- pytest-timeout (timeout handling)

## Test Output

The pytest test suite provides:
- ✅ Clear pass/fail indicators with colors
- 📊 Detailed test statistics and timing
- 🔍 Verbose mode for debugging (`-v` or `-vv`)
- 📋 Categorized test results by marker
- 🎯 Coverage reports with `--cov`
- ⚡ Parallel execution support
- 🚨 Detailed failure traceback with `--tb=long`

## Migration Note

The test suite has been migrated from the original monolithic `test_suite.py` to modular pytest format for better organization, parallel execution support, and standard pytest features. The original test functionality has been preserved and enhanced.
