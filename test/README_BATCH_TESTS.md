# Batch Mode Test Suite

This document describes the comprehensive test suite for Strongbird's batch mode functionality.

## Test Structure

The batch mode tests are organized into several test classes in `test_batch.py`:

### TestBatchFileReader
Tests the core `BatchFileReader` class functionality:
- Reading URLs from files
- Handling comments and empty lines
- Processing glob patterns
- URL validation and warnings
- Error handling for invalid files
- Unicode support
- Different line endings

### TestBatchModeCLI
Tests CLI integration for batch mode:
- CLI option presence in help
- Argument validation
- Error handling for invalid arguments
- Output requirements

### TestBatchModeIntegration
Network-dependent integration tests:
- End-to-end batch processing
- Glob pattern expansion
- Parallel processing
- Error handling with real URLs
- Different output formats
- File creation and naming

### TestBatchModeOrchestrator
Unit tests for the `CLIOrchestrator` batch functionality:
- Configuration validation
- URL expansion logic
- Mocked parallel processing

### TestBatchModeEdgeCases
Edge case and robustness tests:
- Unicode characters in URLs
- Very long URLs
- Different line ending formats
- Mixed line endings

## Test Fixtures

The test suite uses several fixture files in `test/fixtures/`:

- `test_batch_simple.txt` - Basic URLs without globbing
- `test_batch_glob.txt` - URLs with glob patterns
- `test_batch_mixed.txt` - Mixed content with comments, unicode, etc.
- `test_batch_empty.txt` - Empty file (comments only)

## Running Tests

### Run All Batch Tests
```bash
uv run pytest test/test_batch.py -v
```

### Run Specific Test Categories
```bash
# Unit tests only (no network required)
uv run pytest test/test_batch.py -m "not integration" -v

# Integration tests only (requires network)
uv run pytest test/test_batch.py -m "integration" -v

# CLI tests only
uv run pytest test/test_batch.py -m "cli" -v

# Batch-specific tests
uv run pytest test/test_batch.py -m "batch" -v
```

### Run Individual Test Classes
```bash
uv run pytest test/test_batch.py::TestBatchFileReader -v
uv run pytest test/test_batch.py::TestBatchModeCLI -v
uv run pytest test/test_batch.py::TestBatchModeIntegration -v
```

## Test Coverage

The test suite covers:

### Core Functionality
- ✅ Reading URLs from batch files
- ✅ Comment and empty line filtering
- ✅ URL validation and warnings
- ✅ File error handling
- ✅ CLI argument validation
- ✅ Output path requirements

### URL Expansion
- ✅ Numeric range patterns `[1-10]`
- ✅ Alphabetic range patterns `[a-z]`
- ✅ List patterns `{a,b,c}`
- ✅ Complex mixed patterns
- ✅ `--ignore-glob` option

### Parallel Processing
- ✅ Multiple worker configurations
- ✅ URL distribution across workers
- ✅ Error handling in parallel mode
- ✅ Result aggregation

### Output Handling
- ✅ Directory creation
- ✅ File naming conventions
- ✅ Multiple output formats
- ✅ Success/failure tracking

### Error Conditions
- ✅ Nonexistent batch files
- ✅ Invalid file permissions
- ✅ Empty batch files
- ✅ Network failures
- ✅ Extraction failures

### Edge Cases
- ✅ Unicode characters in URLs and comments
- ✅ Very long URLs
- ✅ Different line ending formats (Unix, Windows, Mac)
- ✅ Mixed line endings
- ✅ Special characters in URLs

## Test Markers

The tests use pytest markers for categorization:

- `@pytest.mark.batch` - Batch mode specific tests
- `@pytest.mark.cli` - CLI functionality tests
- `@pytest.mark.integration` - Network-dependent tests
- `@pytest.mark.asyncio` - Async tests

## Example Test Commands

### Development Workflow
```bash
# Quick unit tests during development
uv run pytest test/test_batch.py::TestBatchFileReader -v

# Full batch test suite
uv run pytest test/test_batch.py -v

# Integration tests for end-to-end validation
uv run pytest test/test_batch.py::TestBatchModeIntegration -v
```

### CI/CD Pipeline
```bash
# Run all tests except integration (for CI without network)
uv run pytest test/test_batch.py -m "not integration" -v

# Run all tests including integration (for full validation)
uv run pytest test/test_batch.py -v
```

## Test Data

### Valid Test URLs
- `https://httpbin.org/html` - Returns HTML content
- `https://httpbin.org/json` - Returns JSON data
- `https://httpbin.org/get` - Returns request info
- `https://httpbin.org/user-agent` - Returns user agent info

### Glob Pattern Examples
- `https://httpbin.org/status/[200-202]` - Numeric range
- `https://httpbin.org/{get,post}` - List expansion
- `https://httpbin.org/anything/[a-c]` - Alphabetic range

### Invalid Test URLs (for error testing)
- `https://invalid-domain-that-does-not-exist.com/test`
- `not-a-url`
- `invalid://protocol`

## Extending Tests

To add new batch mode tests:

1. Add test methods to appropriate test classes
2. Use existing fixtures or create new ones in `test/fixtures/`
3. Use proper pytest markers for categorization
4. Follow the existing naming conventions
5. Add both positive and negative test cases
6. Include edge cases and error conditions

## Performance Considerations

The test suite is designed to:
- Run quickly for development feedback
- Be comprehensive for CI validation
- Use network requests judiciously (marked with `integration`)
- Mock external dependencies where appropriate
- Test parallel processing without overwhelming test infrastructure
