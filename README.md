# Strongbird

A powerful web page extractor that combines Playwright for JavaScript rendering and Trafilatura for content extraction. Extract clean, readable content from any webpage, including JavaScript-heavy sites.

## Features

- **JavaScript Rendering**: Uses Playwright to render JavaScript-heavy pages before extraction
- **Multiple Browsers**: Support for Chromium, Firefox, and WebKit
- **Smart Extraction**: Leverages Trafilatura for intelligent content extraction
- **Multiple Output Formats**: Markdown, Text, JSON, XML, CSV
- **Advanced Options**: Wait for selectors, scroll loading, custom scripts
- **Performance Optimizations**: Disable images/JavaScript for faster extraction
- **Metadata Extraction**: Automatic extraction of title, author, date, and more
- **Screenshot Capture**: Take screenshots while extracting content

## Installation

This project uses `uv` for dependency management:

```bash
cd strongbird
uv sync
uv run playwright install chromium  # Install browser
```

## Usage

### Basic Extraction

```bash
# Extract from URL (with JavaScript rendering)
uv run strongbird https://example.com

# Extract from local HTML file
uv run strongbird ./article.html

# Disable Playwright (simple HTTP fetch)
uv run strongbird https://example.com --no-playwright
```

### Output Formats

```bash
# Markdown (default)
uv run strongbird https://example.com -f markdown

# Plain text
uv run strongbird https://example.com -f text

# JSON
uv run strongbird https://example.com -f json -o output.json

# XML
uv run strongbird https://example.com -f xml

# CSV
uv run strongbird https://example.com -f csv
```

### JavaScript-Heavy Sites

```bash
# Wait for specific element
uv run strongbird https://spa-app.com --wait-for ".content-loaded"

# Scroll to trigger lazy loading
uv run strongbird https://infinite-scroll.com --scroll

# Additional wait time
uv run strongbird https://slow-app.com --wait-time 5000

# Execute custom JavaScript
uv run strongbird https://app.com --execute-script "document.querySelector('.modal').remove()"
```

### Performance Optimization

```bash
# Disable images for faster loading
uv run strongbird https://example.com --no-images

# Disable JavaScript (when not needed)
uv run strongbird https://example.com --no-javascript

# Use different browser
uv run strongbird https://example.com --browser firefox
```

### Advanced Options

```bash
# Custom viewport size
uv run strongbird https://example.com --viewport 1280x720

# Custom user agent
uv run strongbird https://example.com --user-agent "MyBot 1.0"

# Take screenshot
uv run strongbird https://example.com --screenshot screenshot.png

# Extract with specific language
uv run strongbird https://example.com --target-lang en

# Include additional content
uv run strongbird https://example.com --include-links --include-comments

# Preserve text formatting
uv run strongbird https://example.com --include-formatting

# Process mathematical equations (convert KaTeX/MathJax/MathML to TeX)
uv run strongbird https://math-heavy-site.com --process-math
```

## Options

### Core Options
- `-o, --output PATH`: Save output to file
- `-f, --format`: Output format (markdown, text, xml, json, csv)
- `--no-playwright`: Disable Playwright rendering

### Browser Options
- `--headless/--no-headless`: Run browser in headless mode
- `--browser`: Browser to use (chromium, firefox, webkit)
- `--viewport`: Viewport size (WIDTHxHEIGHT)
- `--user-agent`: Custom user agent
- `--timeout`: Page load timeout in milliseconds

### JavaScript Rendering
- `--wait-for`: CSS selector to wait for
- `--scroll`: Scroll to bottom for lazy loading
- `--wait-time`: Additional wait time in milliseconds
- `--execute-script`: JavaScript to execute before extraction
- `--no-javascript`: Disable JavaScript
- `--no-images`: Disable image loading

### Content Options
- `--with-metadata/--no-metadata`: Include metadata
- `--include-comments`: Include comments
- `--include-links`: Include links
- `--include-images`: Include images
- `--include-formatting`: Include text formatting (bold, italic, etc.)
- `--process-math`: Process mathematical equations to TeX format ($$...$$ and $...$)
- `--no-tables`: Exclude tables
- `--no-deduplicate`: Disable deduplication
- `--target-lang`: Target language
- `--favor-precision`: Favor precision over recall

### Other Options
- `--screenshot`: Save screenshot to path
- `-q, --quiet`: Suppress progress messages
- `--version`: Show version
- `--help`: Show help

## Examples

### Extract article from news site
```bash
uv run strongbird https://news.site/article \
  --wait-for "article" \
  --format markdown \
  -o article.md
```

### Extract from JavaScript SPA
```bash
uv run strongbird https://spa-app.com \
  --wait-for "[data-loaded='true']" \
  --scroll \
  --wait-time 3000 \
  -f json
```

### Fast extraction without rendering
```bash
uv run strongbird https://simple-site.com \
  --no-playwright \
  --format text \
  --no-metadata
```

### Extract with screenshot
```bash
uv run strongbird https://example.com \
  --screenshot page.png \
  --format markdown \
  -o content.md
```

## Architecture

Strongbird combines two powerful tools:

1. **Playwright**: Handles browser automation, JavaScript rendering, and dynamic content loading
2. **Trafilatura**: Performs intelligent content extraction and cleaning

The workflow:
1. Playwright renders the page (if enabled)
2. Mathematical equations are processed (if `--process-math` is enabled)
3. HTML is passed to Trafilatura for extraction
4. Content is formatted according to the specified output format
5. Metadata is preserved and included (if requested)

## Mathematical Equation Processing

Strongbird includes advanced support for mathematical equations through the `--process-math` option. This feature converts various math rendering formats to standardized TeX notation.

### Supported Math Formats

- **KaTeX**: Extracts TeX from `.katex-mathml` annotations
- **MathJax v2/v3/v4**: Uses MathJax API and script tags
- **MathML**: Extracts TeX from `annotation[encoding="application/x-tex"]`
- **Wikipedia MediaWiki Math Extension**: Processes `.mwe-math-element` containers
- **LaTeXML**: Processes semantic annotations
- **Fallback**: Converts basic MathML to TeX for unsupported cases

### Wikipedia Math Support

Strongbird has specialized support for Wikipedia's math rendering system:

```bash
# Extract mathematical content from Wikipedia articles
uv run strongbird "https://en.wikipedia.org/wiki/Poisson_distribution" --process-math
uv run strongbird "https://en.wikipedia.org/wiki/Fourier_transform" --process-math
uv run strongbird "https://en.wikipedia.org/wiki/Quadratic_formula" --process-math
```

### Math Processing Examples

```bash
# Extract from academic paper with equations
uv run strongbird https://arxiv.org/abs/2301.00001 --process-math -f markdown

# Process site with KaTeX rendering
uv run strongbird https://khan-academy.org/article --process-math

# Extract with both formatting and math
uv run strongbird https://math-site.com --include-formatting --process-math
```

### Output Format

Mathematical equations are converted to standard TeX notation:
- Inline math: `$equation$`
- Display math: `$$equation$$`

This ensures compatibility with Markdown processors, LaTeX, and other document systems that support TeX math notation.

## Testing

Strongbird includes a comprehensive test suite to ensure reliable math extraction and content processing.

### Running Tests

```bash
# Run all tests
uv run python test/run_tests.py

# Run math extraction tests only
uv run python test/test_math_extraction.py

# Test individual fixtures
uv run strongbird "file://$(pwd)/test/fixtures/comprehensive-math-test.html" --process-math
```

### Test Coverage

The test suite validates:
- Local HTML fixtures with various math formats (KaTeX, MathJax, MathML)
- Wikipedia integration tests (MediaWiki Math Extension)
- Regression testing for math extraction improvements
- Content extraction accuracy and completeness

### Test Results

Expected test results include:
- ✅ Comprehensive math test: ~9 equations
- ✅ MathJax v3 test: ~8 equations  
- ✅ Wikipedia articles: 200+ equations per complex math page
- ✅ All math formats properly converted to TeX notation

## Development

See `AGENTS.md` for detailed architecture documentation and development guidelines.

## Dependencies

- [Playwright](https://playwright.dev/): Browser automation
- [Trafilatura](https://trafilatura.readthedocs.io/): Content extraction
- [Click](https://click.palletsprojects.com/): CLI framework
- [Rich](https://github.com/Textualize/rich): Terminal formatting

## License

ISC