# Strongbird

A powerful web page extractor that combines Playwright for JavaScript rendering and Trafilatura for content extraction. Extract clean, readable content from any webpage, including JavaScript-heavy sites.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Basic Extraction](#basic-extraction)
  - [Batch File Processing](#batch-file-processing)
  - [URL Expansion & Parallel Processing](#url-expansion--parallel-processing)
  - [Output Formats](#output-formats)
  - [Crawling Multiple Pages](#crawling-multiple-pages)
  - [JavaScript-Heavy Sites](#javascript-heavy-sites)
  - [Performance Optimization](#performance-optimization)
  - [Advanced Options](#advanced-options)
  - [Image Extraction](#image-extraction)
- [Options](#options)
  - [📄 Output Options](#-output-options)
  - [📋 Batch Processing Options](#-batch-processing-options)
  - [🕷️ Crawling Options](#️-crawling-options)
  - [🌐 Browser & Rendering Options](#-browser--rendering-options)
  - [⚡ JavaScript & Loading Options](#-javascript--loading-options)
  - [📋 Content Extraction Options](#-content-extraction-options)
  - [🚀 URL Expansion & Parallel Processing Options](#-url-expansion--parallel-processing-options)
  - [🔧 Other Options](#-other-options)
- [Examples](#examples)
  - [Extract article from news site](#extract-article-from-news-site)
  - [Extract from JavaScript SPA](#extract-from-javascript-spa)
  - [Fast extraction without rendering](#fast-extraction-without-rendering)
  - [Extract with screenshot](#extract-with-screenshot)
  - [Extract with images](#extract-with-images)
  - [Batch file processing](#batch-file-processing-1)
  - [Bulk extraction with URL expansion](#bulk-extraction-with-url-expansion)
- [Architecture](#architecture)
- [Mathematical Equation Processing](#mathematical-equation-processing)
  - [Supported Math Formats](#supported-math-formats)
  - [Math Processing Examples](#math-processing-examples)
  - [Wikipedia Math Support](#wikipedia-math-support)
  - [Output Format](#output-format)
- [Image Extraction](#image-extraction-1)
  - [How It Works](#how-it-works)
  - [Folder Structure](#folder-structure)
  - [Image Extraction Examples](#image-extraction-examples)
  - [Image Processing Features](#image-processing-features)
  - [Output Format](#output-format-1)
- [URL Expansion with Curl Globbing](#url-expansion-with-curl-globbing)
  - [Supported Patterns](#supported-patterns)
  - [URL Expansion Options](#url-expansion-options)
- [Batch File Processing](#batch-file-processing-2)
  - [Batch File Format](#batch-file-format)
  - [Batch Processing Features](#batch-processing-features)
  - [Batch Processing Examples](#batch-processing-examples)
- [Parallel Processing](#parallel-processing)
  - [Parallel Processing Examples](#parallel-processing-examples)
- [Testing](#testing)
  - [Running Tests](#running-tests)
- [Dependencies](#dependencies)

## Features

- **JavaScript Rendering**: Uses Playwright to render JavaScript-heavy pages before extraction
- **Multiple Browsers**: Support for Chromium, Firefox, and WebKit
- **Smart Extraction**: Leverages Trafilatura for intelligent content extraction
- **Multiple Output Formats**: Markdown, Text, JSON, XML, CSV
- **Advanced Options**: Wait for selectors, scroll loading, custom scripts
- **Performance Optimizations**: Disable images/JavaScript for faster extraction
- **Metadata Extraction**: Automatic extraction of title, author, date, and more
- **Screenshot Capture**: Take screenshots while extracting content
- **Image Extraction**: Download images from web pages and update links to local files
- **URL Expansion**: Support for curl-style URL globbing patterns for bulk extraction
- **Parallel Processing**: Process multiple URLs concurrently for improved performance
- **Batch File Processing**: Process multiple URLs from text files with glob pattern support

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

### Batch File Processing

```bash
# Process URLs from a batch file
uv run strongbird --batch urls.txt --output ./results -j 4

# Batch file with glob patterns and comments
uv run strongbird --batch sites.txt --output ./extracted --format json -j 3

# Example batch file format (urls.txt):
# # Comments are supported
# https://example.com/page1.html
# https://example.com/articles/[1-10].html  # Glob patterns work
# https://{docs,api}.example.com/index.html
#
# # Empty lines are ignored
# https://httpbin.org/json
```

### URL Expansion & Parallel Processing

```bash
# Extract from multiple URLs using curl globbing patterns
uv run strongbird "https://example.com/page-[1-10].html" --output ./pages

# Extract with zero-padded numbers
uv run strongbird "https://httpbin.org/status/[200-204]" -j 4

# Extract from multiple domains/endpoints
uv run strongbird "https://{docs,api,blog}.example.com/content.html" --output ./sites

# Disable URL expansion if needed
uv run strongbird "https://example.com/[literal-brackets].html" --ignore-glob

# Parallel processing (4 concurrent workers)
uv run strongbird "https://httpbin.org/status/[200-250]" -j 4 --output ./articles
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

### Crawling Multiple Pages

```bash
# Crawl linked pages and save as multiple files (recommended)
uv run strongbird https://example.com --crawl-depth 1 --output-dir ./crawl_results

# Crawl and combine into single file
uv run strongbird https://example.com --crawl-depth 1 -o combined.md

# Deep crawling with custom settings
uv run strongbird https://example.com --crawl-depth 2 --max-pages 20 --crawl-delay 2.0 --output-dir ./deep_crawl

# Crawl mathematical content from academic sites
uv run strongbird https://dlmf.nist.gov/1.3 --crawl-depth 1 --process-math --ignore-robots-txt --output-dir ./math_pages

# Domain-restricted crawling
uv run strongbird https://example.com --crawl-depth 1 --same-domain-only --output-dir ./same_domain
```

### JavaScript-Heavy Sites

```bash
# Wait for specific element
uv run strongbird https://httpbin.org/html --wait-for "body"

# Scroll to trigger lazy loading
uv run strongbird https://httpbin.org/html --scroll

# Additional wait time
uv run strongbird https://httpbin.org/delay/2 --wait-time 5000

# Execute custom JavaScript
uv run strongbird https://httpbin.org/html --execute-script "document.querySelector('h1').style.color='red'"
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
uv run strongbird https://en.wikipedia.org/wiki/Quadratic_formula --process-math

# Extract and download images to local img folder
uv run strongbird https://example.com --extract-images -o article.md
```

### Image Extraction

```bash
# Download images and update URLs in content
uv run strongbird https://example.com --extract-images -o article.md

# Extract from academic papers with images
uv run strongbird https://arxiv.org/html/1706.03762v7 --extract-images --process-math -o paper.md

# Bulk extraction with images
uv run strongbird "https://example.com/page-[1-5].html" --extract-images --output-dir ./pages

# Crawling with image extraction
uv run strongbird https://example.com --crawl-depth 1 --extract-images --output-dir ./crawl_results
```

## Options

### 📄 Output Options

- `-o, --output PATH`: Save output to file or directory
- `-f, --format`: Output format (markdown, text, xml, json, csv)

### 📋 Batch Processing Options

- `--batch FILE`: Read URLs from batch file (one URL per line, supports globbing patterns)

### 🕷️ Crawling Options

- `--crawl-depth INTEGER`: Maximum crawling depth (0=current page only, 1=include linked pages, etc.)
- `--max-pages INTEGER`: Maximum number of pages to crawl (default: 10)
- `--crawl-delay FLOAT`: Delay between crawl requests in seconds (default: 1.0)
- `--same-domain-only/--allow-external-domains`: Only crawl pages on the same domain (default: True)
- `--respect-robots-txt/--ignore-robots-txt`: Respect robots.txt files (default: True)

### 🌐 Browser & Rendering Options

- `--no-playwright`: Disable Playwright rendering (use simple HTTP fetch)
- `--headless/--no-headless`: Run browser in headless mode (default: True)
- `--browser`: Browser to use (chromium, firefox, webkit)
- `--viewport`: Viewport size (WIDTHxHEIGHT, default: 1920x1080)
- `--user-agent`: Custom user agent string
- `--timeout`: Page load timeout in milliseconds (default: 30000)

### ⚡ JavaScript & Loading Options

- `--wait-for`: CSS selector to wait for before extraction
- `--scroll`: Scroll to bottom for lazy loading
- `--wait-time`: Additional wait time in milliseconds after page load
- `--execute-script`: JavaScript to execute before extraction
- `--no-javascript`: Disable JavaScript execution
- `--no-images`: Disable image loading for faster extraction

### 📋 Content Extraction Options

- `--with-metadata/--no-metadata`: Include metadata (default: True)
- `--include-comments`: Include comments in extraction
- `--include-links`: Include links in extraction
- `--include-images`: Include images in extraction
- `--extract-images`: Download images to local img folder and update URLs in content
- `--include-formatting`: Include text formatting (bold, italic, etc.)
- `--process-math`: Process mathematical equations to TeX format ($$...$$ and $...$)
- `--no-tables`: Exclude tables from extraction
- `--no-deduplicate`: Disable content deduplication
- `--target-lang`: Target language for extraction (e.g., en, de, fr)
- `--favor-precision`: Favor precision over recall in extraction

### 🚀 URL Expansion & Parallel Processing Options

- `--ignore-glob`: Disable URL globbing expansion for URLs with literal brackets
- `-j, --proc INTEGER`: Number of parallel workers for concurrent processing (1-10, default: 1)

### 🔧 Other Options

- `--screenshot PATH`: Save screenshot to specified path
- `-q, --quiet`: Suppress progress messages
- `--version`: Show version
- `--help`: Show help

## Examples

### Extract article from news site

```bash
uv run strongbird https://httpbin.org/html \
  --wait-for "body" \
  --format markdown \
  -o article.md
```

### Extract from JavaScript SPA

```bash
uv run strongbird https://httpbin.org/html \
  --wait-for "body" \
  --scroll \
  --wait-time 3000 \
  -f json
```

### Fast extraction without rendering

```bash
uv run strongbird https://httpbin.org/html \
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

### Extract with images

```bash
# Download images and save locally
uv run strongbird https://arxiv.org/html/1706.03762v7 \
  --extract-images \
  --process-math \
  -o paper.md

# Images will be saved to img/ folder next to paper.md
# Markdown content will reference local images like: ![alt](img/image_abc123.png)
```

### Batch file processing

```bash
# Process URLs from batch file with parallel workers
uv run strongbird --batch urls.txt \
  --output ./results \
  -j 4 \
  --format markdown

# Process with different output formats
uv run strongbird --batch sites.txt \
  --output ./json_output \
  --format json \
  --no-playwright
```

### Bulk extraction with URL expansion

```bash
# Extract multiple pages with numeric range
uv run strongbird "https://httpbin.org/status/[200-225]" \
  --output ./chapters \
  -j 3

# Extract from multiple subdomains
uv run strongbird "https://{blog,docs,api}.example.com/content" \
  --output ./sites \
  --format json

# Extract with zero-padded numbers
uv run strongbird "https://httpbin.org/status/[200-250]" \
  --output ./archive \
  -j 5 \
  --wait-time 2000
```

## Architecture

Strongbird combines two powerful tools:

1. **Playwright**: Handles browser automation, JavaScript rendering, and dynamic content loading
2. **Trafilatura**: Performs intelligent content extraction and cleaning

The workflow:

1. **Input Processing**: URLs are sourced from command line arguments or batch files
2. **URL Expansion**: If globbing patterns are detected, URLs are expanded (e.g., `[1-10]` → 10 URLs)
3. **Parallel Processing**: Multiple URLs are processed concurrently using page pools (if `-j > 1`)
4. **Playwright Rendering**: Each page is rendered in a browser instance (if enabled)
5. **Mathematical Processing**: Equations are converted to TeX format (if `--process-math` is enabled)
6. **Content Extraction**: HTML is passed to Trafilatura for intelligent content extraction
7. **Output Generation**: Content is formatted and saved according to specified options
8. **Metadata Preservation**: Metadata is extracted and included (if requested)
9. **Image Extraction**: Images are downloaded and saved locally (if `--extract-images` is enabled)

## Mathematical Equation Processing

Strongbird includes advanced support for mathematical equations through the `--process-math` option. This feature converts various math rendering formats to standardized TeX notation.

### Supported Math Formats

- **KaTeX**: Extracts TeX from `.katex-mathml` annotations
- **MathJax v2/v3/v4**: Uses MathJax API and script tags
- **MathML**: Extracts TeX from `annotation[encoding="application/x-tex"]`
- **Wikipedia MediaWiki Math Extension**: Processes `.mwe-math-element` containers
- **LaTeXML**: Processes semantic annotations
- **Fallback**: Converts basic MathML to TeX for unsupported cases

### Math Processing Examples

```bash
# Extract from academic paper with equations
uv run strongbird https://arxiv.org/html/1706.03762v7 --process-math -f markdown

```

### Wikipedia Math Support

Strongbird has specialized support for Wikipedia's math rendering system:

```bash
# Extract mathematical content from Wikipedia articles
uv run strongbird "https://en.wikipedia.org/wiki/Poisson_distribution" --process-math
uv run strongbird "https://en.wikipedia.org/wiki/Fourier_transform" --process-math
uv run strongbird "https://en.wikipedia.org/wiki/Quadratic_formula" --process-math
```

### Output Format

Mathematical equations are converted to standard TeX notation:

- Inline math: `$equation$`
- Display math: `$$equation$$`

This ensures compatibility with Markdown processors, LaTeX, and other document systems that support TeX math notation.

## Image Extraction

Strongbird can automatically download images from web pages and save them to a local `img/` folder while updating the Markdown content to reference the local files.

### How It Works

1. **Image Discovery**: Scans HTML for `<img>` tags and extracts their `src` attributes
2. **URL Resolution**: Converts relative URLs to absolute URLs using the page's base URL
3. **Concurrent Downloads**: Downloads images asynchronously with configurable concurrency
4. **Local Storage**: Saves images with unique filenames to prevent conflicts
5. **Content Updates**: Replaces image URLs in Markdown output with local paths

### Folder Structure

- **Single file output**: `img/` folder created next to the output file
- **Directory output**: `img/` folder created inside the output directory
- **Crawling mode**: Shared `img/` folder for all pages

### Image Extraction Examples

```bash
# Basic image extraction
uv run strongbird https://example.com --extract-images -o article.md
# Creates: article.md and img/ folder with downloaded images

# Academic papers with figures
uv run strongbird https://arxiv.org/html/1706.03762v7 --extract-images --process-math -o paper.md

# Bulk extraction with images
uv run strongbird "https://example.com/page-[1-5].html" --extract-images --output-dir ./pages
# Creates: pages/img/ folder shared by all extracted pages

# Crawling with images
uv run strongbird https://example.com --crawl-depth 2 --extract-images --output-dir ./site
```

### Image Processing Features

- **Smart URL Resolution**: Handles relative paths correctly (fixes issues with sites like arXiv)
- **Unique Filenames**: Uses URL hash to generate conflict-free filenames
- **Error Handling**: Gracefully handles failed downloads without stopping extraction
- **Format Support**: Downloads all image formats (PNG, JPG, SVG, WebP, etc.)
- **Parallel Downloads**: Configurable concurrency for faster processing
- **Automatic Activation**: `--extract-images` automatically enables `--include-images`

### Output Format

Images in Markdown are referenced with relative paths:

```markdown
![Image description](img/filename_abc12345.jpg)
```

This ensures the Markdown files are portable and work when moved with their `img/` folders.

## URL Expansion with Curl Globbing

Strongbird supports curl-style URL globbing patterns for bulk extraction. This feature automatically detects patterns in URLs and expands them into multiple URLs for processing.

### Supported Patterns

#### Numeric Ranges

```bash
# Basic numeric range
uv run strongbird "https://example.com/page-[1-10].html"

# Zero-padded numbers
uv run strongbird "https://httpbin.org/status/[200-300]"

# Step intervals
uv run strongbird "https://httpbin.org/status/[200-300:10]"  # 200, 210, 220, ...
```

#### Alphabetic Ranges

```bash
# Lowercase letters
uv run strongbird "https://httpbin.org/anything/[a-z]"

# Uppercase letters
uv run strongbird "https://httpbin.org/anything/[A-Z]"
```

#### Lists/Alternatives

```bash
# Multiple options
uv run strongbird "https://{docs,api,blog}.example.com/content.html"

# Mixed patterns
uv run strongbird "https://httpbin.org/{get,post,put}/[1-5]"
```

#### Complex Combinations

```bash
# Multiple patterns in single URL
uv run strongbird "https://httpbin.org/{get,post}/v[1-3]/items/[a-c]"
# Expands to: httpbin.org/get/v1/items/a, httpbin.org/get/v1/items/b, etc.
```

### URL Expansion Options

- **Automatic Detection**: URL patterns are detected automatically without flags
- **Disable Expansion**: Use `--ignore-glob` to treat brackets as literal characters
- **Output Handling**: Use `--output-dir` for multiple files or `-o` for combined output

## Batch File Processing

Strongbird supports processing multiple URLs from text files, making it easy to handle large-scale extraction tasks with persistent URL lists.

### Batch File Format

Batch files are simple text files with one URL per line:

```
# Comments start with # and are ignored
https://example.com/page1.html
https://example.com/page2.html

# Empty lines are ignored
https://httpbin.org/json

# Glob patterns work in batch files
https://example.com/articles/[1-10].html
https://{docs,api,blog}.example.com/index.html

# File URLs are supported
file:///path/to/local/file.html
```

### Batch Processing Features

- **Comment Support**: Lines starting with `#` are treated as comments
- **Empty Line Handling**: Empty lines are automatically ignored
- **Glob Pattern Support**: Full URL expansion support within batch files
- **Unicode Support**: Handles international characters in URLs and comments
- **Error Resilience**: Invalid URLs generate warnings but don't stop processing
- **Parallel Processing**: Use `-j` flag for concurrent processing of batch URLs

### Batch Processing Examples

```bash
# Basic batch processing
uv run strongbird --batch urls.txt --output ./results

# Batch processing with parallel workers
uv run strongbird --batch sites.txt --output ./extracted -j 4

# Batch processing with different formats
uv run strongbird --batch pages.txt --output ./json_results --format json

# Combine batch processing with other options
uv run strongbird --batch academic_papers.txt \
  --output ./papers \
  --process-math \
  --format markdown \
  -j 3
```

## Parallel Processing

Strongbird can process multiple URLs concurrently, significantly improving performance for bulk extraction tasks.

### Parallel Processing Examples

```bash
# Process 4 URLs concurrently
uv run strongbird "https://httpbin.org/status/[200-220]" -j 4 --output ./articles

# Combine with crawling for maximum efficiency
uv run strongbird "https://httpbin.org/links/[1-10]" --crawl-depth 1 -j 3

# Process different sites in parallel
uv run strongbird "https://{docs,api,blog}.example.com" -j 3 --output ./sites
```

## Dependencies

- [Playwright](https://playwright.dev/): Browser automation
- [Trafilatura](https://trafilatura.readthedocs.io/): Content extraction
- [Click](https://click.palletsprojects.com/): CLI framework
- [Rich](https://github.com/Textualize/rich): Terminal formatting
- [aiohttp](https://docs.aiohttp.org/): Async HTTP client for image downloads
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/): HTML parsing for image extraction
