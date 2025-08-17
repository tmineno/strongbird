#!/usr/bin/env python3
"""Refactored CLI interface for Strongbird web extractor."""

import asyncio
import sys

import click

from .cli_orchestrator import CLIOrchestrator
from .config import ConfigBuilder


@click.command()
@click.argument("source", type=str)
# Output Options
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    help="Output file path or directory for crawling (default: stdout)",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["markdown", "text", "xml", "json", "csv"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
# Browser Options
@click.option(
    "--no-playwright",
    is_flag=True,
    help="Disable Playwright rendering (use simple HTTP fetch)",
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Run browser in headless mode (default: True)",
)
@click.option(
    "--browser",
    type=click.Choice(["chromium", "firefox", "webkit"]),
    default="chromium",
    help="Browser to use (default: chromium)",
)
@click.option(
    "--timeout",
    type=int,
    default=30000,
    help="Page load timeout in milliseconds (default: 30000)",
)
@click.option(
    "--viewport",
    type=str,
    default="1920x1080",
    help="Viewport size as WIDTHxHEIGHT (default: 1920x1080)",
)
@click.option("--user-agent", type=str, help="Custom user agent string")
# JavaScript & Loading Options
@click.option("--wait-for", type=str, help="CSS selector to wait for before extraction")
@click.option(
    "--scroll", is_flag=True, help="Scroll to bottom of page to trigger lazy loading"
)
@click.option(
    "--wait-time",
    type=int,
    default=0,
    help="Additional wait time in milliseconds after page load",
)
@click.option(
    "--execute-script", type=str, help="JavaScript code to execute before extraction"
)
@click.option("--no-javascript", is_flag=True, help="Disable JavaScript execution")
@click.option(
    "--no-images", is_flag=True, help="Disable image loading for faster extraction"
)
# Content Extraction Options
@click.option(
    "--with-metadata/--no-metadata",
    default=True,
    help="Include metadata in output (default: True)",
)
@click.option("--include-comments", is_flag=True, help="Include comments in extraction")
@click.option("--include-links", is_flag=True, help="Include links in extraction")
@click.option("--include-images", is_flag=True, help="Include images in extraction")
@click.option(
    "--include-formatting",
    is_flag=True,
    help="Include formatting (bold, italic, etc.) in extraction",
)
@click.option(
    "--process-math",
    is_flag=True,
    help="Process mathematical equations to TeX format ($$...$$, $...$)",
)
@click.option("--no-tables", is_flag=True, help="Exclude tables from extraction")
@click.option("--no-deduplicate", is_flag=True, help="Disable content deduplication")
@click.option(
    "--target-lang", type=str, help="Target language for extraction (e.g., en, de, fr)"
)
@click.option(
    "--favor-precision", is_flag=True, help="Favor precision over recall in extraction"
)
# Crawling Options
@click.option(
    "--crawl-depth",
    type=int,
    default=0,
    help="Maximum crawling depth (0=current page only, 1=include linked pages, etc.)",
)
@click.option(
    "--max-pages",
    type=int,
    default=10,
    help="Maximum number of pages to crawl (default: 10)",
)
@click.option(
    "--crawl-delay",
    type=float,
    default=1.0,
    help="Delay between crawl requests in seconds (default: 1.0)",
)
@click.option(
    "--same-domain-only/--allow-external-domains",
    default=True,
    help="Only crawl pages on the same domain (default: True)",
)
@click.option(
    "--respect-robots-txt/--ignore-robots-txt",
    default=True,
    help="Respect robots.txt files (default: True)",
)
# Other Options
@click.option(
    "--screenshot", type=click.Path(), help="Save screenshot to specified path"
)
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress messages")
@click.option(
    "--ignore-glob",
    is_flag=True,
    help="Disable URL globbing expansion (treat patterns literally)",
)
@click.option(
    "-j",
    "--proc",
    type=click.IntRange(1, 10),
    default=1,
    help="Number of parallel processes for URL processing (default: 1, max: 10)",
)
@click.version_option()
def main(**kwargs):
    """
    Extract content from web pages using Playwright and Trafilatura.

    SOURCE can be a URL or a local HTML file path.

    Examples:

        # Basic extraction
        strongbird https://example.com

        # With JavaScript rendering disabled
        strongbird https://example.com --no-playwright

        # Wait for specific element and scroll
        strongbird https://example.com --wait-for ".content" --scroll

        # Save as different formats
        strongbird https://example.com -f json -o output.json
        strongbird https://example.com -f text --no-metadata

        # Crawl multiple pages
        strongbird https://example.com --crawl-depth 2 --max-pages 10

        # Performance optimizations
        strongbird https://example.com --no-images --no-javascript
    """
    try:
        # Build configuration objects from CLI arguments
        config_builder = ConfigBuilder()
        (
            browser_config,
            extraction_config,
            playwright_config,
            crawl_config,
            output_config,
            parallel_config,
        ) = config_builder.build_all_configs(**kwargs)

        # Override browser config if no-playwright is specified
        if kwargs.get("no_playwright"):
            browser_config.javascript = False

        # Create and run orchestrator
        orchestrator = CLIOrchestrator(
            browser_config=browser_config,
            extraction_config=extraction_config,
            playwright_config=playwright_config,
            crawl_config=crawl_config,
            output_config=output_config,
            parallel_config=parallel_config,
            ignore_glob=kwargs.get("ignore_glob", False),
        )

        # Run the extraction workflow
        asyncio.run(orchestrator.run(kwargs["source"]))

    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
