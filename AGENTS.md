# Strongbird Design Intentions & Architecture

This document captures the design intentions and architectural decisions of Strongbird for future development and AI agents working on this codebase.

## Project Overview

**Strongbird** is a sophisticated web content extractor that combines Playwright (for JavaScript rendering) with Trafilatura (for content extraction) to provide high-quality extraction of web content, with specialized support for mathematical equations.

## Core Design Principles

### 1. Hybrid Architecture
- **Playwright + Trafilatura**: Best of both worlds - JavaScript rendering capability with content extraction expertise
- **Conditional rendering**: Use Playwright for URLs, direct processing for local files
- **Fallback support**: Graceful degradation when browser automation isn't available

### 2. Mathematical Content as First-Class Citizen
- **Multi-format support**: KaTeX, MathJax v2/v3/v4, MathML, Wikipedia MediaWiki Math Extension
- **Standardized output**: Convert all math to TeX format (`$inline$` and `$$display$$`)
- **Content preservation**: Ensure math equations are recognized as content by extraction engines

### 3. Flexible Output Formats
- **Multiple formats**: Markdown, text, XML, JSON, CSV
- **Metadata support**: Optional inclusion of page metadata
- **Configurable extraction**: Control over links, images, tables, formatting

## Architecture Components

### Browser Management (`browser.py`)
- **Purpose**: Unified interface for Playwright browser automation
- **Key features**: 
  - Context manager pattern for resource cleanup
  - Configurable browsers (Chromium, Firefox, WebKit)
  - Viewport and user agent customization
  - Screenshot capabilities

### Math Processing (`math.py`)
- **Purpose**: Convert mathematical equations from various rendering engines to TeX
- **Design philosophy**: 
  - **Unified JavaScript approach**: Single script handles multiple math formats
  - **Content integration**: Ensure converted math is recognized by content extractors
  - **Fallback conversion**: MathML-to-TeX converter for unsupported formats

### Content Extraction (`extractor.py`)
- **Purpose**: Orchestrate the full extraction pipeline
- **Pipeline**: Browser rendering → Math processing → Content extraction → Formatting
- **Configuration**: Trafilatura settings for precision vs recall balance

### CLI Interface (`cli.py`)
- **Purpose**: User-friendly command-line interface
- **Design**: Rich terminal output, comprehensive options, progress indicators

## Key Technical Decisions

### Math Processing Strategy
**Problem**: Different websites use different math rendering engines (KaTeX, MathJax, MathML, Wikipedia's custom system).

**Solution**: 
1. **Unified JavaScript processor** that runs in the browser context
2. **Multi-format detection**: Automatically detect and process various math formats
3. **Content preservation**: Replace math elements with text nodes or proper HTML elements that Trafilatura recognizes as content
4. **TeX standardization**: Convert everything to consistent TeX notation

### Wikipedia Math Extraction Fix
**Issue**: Wikipedia's MediaWiki Math Extension uses `.mwe-math-element` containers that weren't being extracted properly.

**Root cause**: Trafilatura was filtering out the converted `.math-converted` elements as non-content.

**Solution**: 
- For inline math: Convert to text nodes within existing paragraphs
- For display math: Use `<p>` tags instead of generic `<div>` elements
- Add semantic attributes (`data-math`, `role="math"`) for better content recognition

### Browser Context Management
**Design**: Use async context managers throughout to ensure proper resource cleanup and prevent memory leaks.

```python
async with browser_manager.get_browser() as browser:
    async with browser_manager.get_page(browser) as page:
        # Operations
```

## Testing Strategy

### Test Suite Structure
- **Local fixtures**: HTML files testing specific math formats (KaTeX, MathJax, MathML)
- **Integration tests**: Real Wikipedia pages testing MediaWiki Math Extension
- **Regression testing**: Ensure fixes don't break existing functionality

### Math Extraction Validation
- **Count-based validation**: Verify expected number of math expressions
- **Content sampling**: Extract and display sample equations for manual verification
- **Format coverage**: Test inline vs display math, various TeX commands

## Extension Points

### Adding New Math Formats
1. Add detection logic to `UNIFIED_MATH_JS` in `math.py`
2. Ensure proper TeX conversion
3. Add test cases to the test suite
4. Update documentation

### Supporting New Content Types
1. Extend Trafilatura configuration in `extractor.py`
2. Add CLI options in `cli.py`
3. Update output formatting logic

### Browser Capabilities
1. Extend `BrowserManager` with new features
2. Add corresponding CLI options
3. Ensure proper error handling and fallbacks

## Performance Considerations

### Browser Optimization
- **Headless by default**: Faster execution, lower resource usage
- **Configurable timeouts**: Balance between speed and reliability
- **Image/JS disabling**: Optional performance optimizations

### Math Processing Efficiency
- **Single-pass processing**: Process all math formats in one JavaScript execution
- **WeakSet guards**: Prevent double-processing of elements
- **Batch conversion**: Process multiple equations simultaneously

## Security Considerations

### JavaScript Execution
- **Sandboxed environment**: All JavaScript runs within Playwright's controlled browser context
- **No external dependencies**: Math processing JavaScript is self-contained
- **Input validation**: Proper handling of malformed HTML/math content

### Content Extraction
- **Trafilatura safety**: Leverage Trafilatura's built-in content safety features
- **HTML sanitization**: Automatic handling of potentially malicious content

## Future Development Guidelines

### Code Organization
- **Separation of concerns**: Keep browser management, math processing, and content extraction as distinct modules
- **Configuration centralization**: Use the CLI as the primary configuration interface
- **Error handling**: Provide detailed error messages and graceful degradation

### Backward Compatibility
- **CLI interface stability**: Maintain existing CLI options and behavior
- **Output format consistency**: Ensure new features don't break existing output formats
- **Test coverage**: Add tests for new features to prevent regressions

### Documentation
- **Code comments**: Focus on explaining *why* decisions were made, not just *what* the code does
- **Architecture decisions**: Document significant technical choices in this file
- **User documentation**: Keep README and help text up to date

## Lessons Learned

### Math Extraction Challenges
1. **Content vs Presentation**: Math rendering libraries focus on presentation; content extraction requires understanding the semantic structure
2. **Format diversity**: Different websites use vastly different math rendering approaches
3. **Trafilatura limitations**: General-purpose content extractors may filter out specialized content types

### Integration Complexities
1. **Timing issues**: Math rendering happens asynchronously; need proper wait strategies
2. **Context preservation**: Important to maintain the relationship between math and surrounding text
3. **Resource management**: Browser automation requires careful resource cleanup

### Testing Insights
1. **Real-world validation**: Local test files don't capture all edge cases; need real website testing
2. **Quantitative validation**: Counting extracted expressions provides objective success metrics
3. **Regression prevention**: Comprehensive test suite essential for maintaining quality during development

## Contributing Guidelines

When working on Strongbird:

1. **Understand the pipeline**: Browser → Math → Extract → Format
2. **Test thoroughly**: Use both local fixtures and real websites
3. **Preserve existing functionality**: Run the full test suite before submitting changes
4. **Document decisions**: Update this file when making significant architectural changes
5. **Consider performance**: Browser automation is expensive; optimize where possible

## Contact & Context

This codebase was developed with heavy emphasis on mathematical content extraction, particularly for academic and technical websites. The design prioritizes accuracy and completeness of mathematical notation over raw extraction speed.

Key stakeholder needs:
- Accurate extraction of complex mathematical equations
- Support for diverse math rendering formats
- Reliable processing of academic content (Wikipedia, research papers, technical documentation)
- Command-line friendly for automation and scripting

The architecture reflects these priorities through its specialized math processing pipeline and comprehensive format support.