#!/usr/bin/env python3
"""CLI interface for Strongbird web extractor."""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .browser import BrowserManager
from .crawler import CrawlResults, WebCrawler
from .extractor import StrongbirdExtractor
from .formatter import format_output

console = Console()
error_console = Console(stderr=True)


def generate_filename(url: str, crawl_order: int, format_type: str) -> str:
    """
    Generate a safe filename for a crawled page.

    Args:
        url: The URL of the page
        crawl_order: The order in which the page was crawled
        format_type: The output format (markdown, text, etc.)

    Returns:
        A safe filename for the page
    """
    import re
    from urllib.parse import urlparse

    parsed = urlparse(url)

    # Create base name from domain and path
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/")

    if path:
        # Clean path: remove invalid filename characters
        path_clean = re.sub(r"[^\w\-_./]", "_", path)
        path_clean = path_clean.replace("/", "_")
        base_name = f"{domain}_{path_clean}"
    else:
        base_name = domain

    # Add crawl order prefix for sorting
    base_name = f"{crawl_order:03d}_{base_name}"

    # Truncate if too long (keep under 200 chars)
    if len(base_name) > 150:
        base_name = base_name[:150]

    # Add appropriate extension
    extensions = {
        "markdown": ".md",
        "text": ".txt",
        "xml": ".xml",
        "json": ".json",
        "csv": ".csv",
    }

    extension = extensions.get(format_type, ".txt")
    return f"{base_name}{extension}"


def save_crawl_results_to_directory(
    results: List[Dict[str, Any]],
    output_dir: str,
    format_type: str,
    with_metadata: bool,
    quiet: bool,
):
    """
    Save crawl results as individual files in a directory.

    Args:
        results: List of crawl results
        output_dir: Directory to save files
        format_type: Output format
        with_metadata: Include metadata
        quiet: Suppress output messages
    """
    from pathlib import Path

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save individual files
    for result in results:
        filename = generate_filename(
            result.get("url", "unknown"), result.get("crawl_order", 0), format_type
        )
        file_path = output_path / filename

        # Format individual result
        formatted_content = format_output(result, format_type, with_metadata)

        # Write file
        file_path.write_text(formatted_content, encoding="utf-8")

        if not quiet:
            console.print(f"  → {file_path}")

    # Generate index file
    index_filename = f"000_index.{get_extension(format_type)}"
    index_path = output_path / index_filename

    if format_type == "markdown":
        index_content = "# Crawl Index\n\n"
        index_content += "## Pages Crawled\n\n"
        for result in results:
            filename = generate_filename(
                result.get("url", "unknown"), result.get("crawl_order", 0), format_type
            )
            url = result.get("url", "Unknown URL")
            depth = result.get("crawl_depth", 0)
            title = (
                result.get("metadata", {}).get("title", "Untitled")
                if result.get("metadata")
                else "Untitled"
            )

            index_content += f"- [{title}](./{filename}) - Depth {depth}\n"
            index_content += f"  - URL: {url}\n\n"
    else:
        index_content = "Crawl Index\n" + "=" * 50 + "\n\n"
        for result in results:
            filename = generate_filename(
                result.get("url", "unknown"), result.get("crawl_order", 0), format_type
            )
            url = result.get("url", "Unknown URL")
            depth = result.get("crawl_depth", 0)
            title = (
                result.get("metadata", {}).get("title", "Untitled")
                if result.get("metadata")
                else "Untitled"
            )

            index_content += f"File: {filename}\n"
            index_content += f"Title: {title}\n"
            index_content += f"URL: {url}\n"
            index_content += f"Depth: {depth}\n\n"

    index_path.write_text(index_content, encoding="utf-8")

    if not quiet:
        console.print(f"[green]✓[/green] Saved {len(results)} files to {output_dir}")
        console.print(f"[green]✓[/green] Index file: {index_path}")


def get_extension(format_type: str) -> str:
    """Get file extension for format type."""
    extensions = {
        "markdown": "md",
        "text": "txt",
        "xml": "xml",
        "json": "json",
        "csv": "csv",
    }
    return extensions.get(format_type, "txt")


@click.command()
@click.argument("source", type=str)
# Output Options
@click.option(
    "-o", "--output", type=click.Path(), help="Output file path (default: stdout)"
)
@click.option(
    "--output-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True),
    help="Output directory for multiple files when crawling (depth >= 1)",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["markdown", "text", "xml", "json", "csv"], case_sensitive=False),
    default="markdown",
    help="Output format (default: markdown)",
)
# Browser & Rendering Options
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
@click.version_option()
def main(
    source: str,
    output: Optional[str],
    output_dir: Optional[str],
    format: str,
    no_playwright: bool,
    headless: bool,
    browser: str,
    wait_for: Optional[str],
    scroll: bool,
    wait_time: int,
    execute_script: Optional[str],
    timeout: int,
    viewport: str,
    user_agent: Optional[str],
    no_javascript: bool,
    no_images: bool,
    with_metadata: bool,
    include_comments: bool,
    include_links: bool,
    include_images: bool,
    include_formatting: bool,
    process_math: bool,
    no_tables: bool,
    no_deduplicate: bool,
    target_lang: Optional[str],
    favor_precision: bool,
    screenshot: Optional[str],
    quiet: bool,
    crawl_depth: int,
    max_pages: int,
    crawl_delay: float,
    same_domain_only: bool,
    respect_robots_txt: bool,
):
    """Extract content from web pages using Playwright and Trafilatura.

    SOURCE can be a URL or a local HTML file path.

    \b
    EXAMPLES:

    \b
    Basic extraction:
    \b
      strongbird https://example.com
      strongbird ./page.html --format text

    \b
    Crawling (multiple pages):
    \b
      strongbird https://example.com --crawl-depth 1 --output-dir ./results
      strongbird https://example.com --crawl-depth 2 --max-pages 10 -o combined.md

    \b
    Advanced options:
    \b
      strongbird https://site.com --wait-for ".content" --scroll --process-math
      strongbird https://dlmf.nist.gov/1.3 --crawl-depth 1 --process-math
        --ignore-robots-txt --output-dir ./math_pages

    \b
    Performance optimization:
    \b
      strongbird https://example.com --no-images --no-javascript --no-playwright
    """
    try:
        # Validate output options
        if crawl_depth > 0 and output and output_dir:
            error_console.print(
                "[red]Error:[/red] Cannot use both --output and --output-dir when crawling (depth > 0)"
            )
            sys.exit(1)

        if crawl_depth > 0 and output:
            error_console.print(
                "[yellow]Warning:[/yellow] Using --output with crawling will combine all pages into one file. Consider using --output-dir for separate files."
            )

        if crawl_depth == 0 and output_dir:
            error_console.print(
                "[yellow]Warning:[/yellow] --output-dir is only useful when crawling (depth > 0). Using single file output."
            )
            output_dir = None
        # Parse viewport
        try:
            width, height = map(int, viewport.split("x"))
        except ValueError:
            error_console.print(
                "[red]Invalid viewport format. Use WIDTHxHEIGHT (e.g., 1920x1080)[/red]"
            )
            sys.exit(1)

        # Determine if source is URL or file
        is_url = source.startswith(("http://", "https://", "file://"))

        if not is_url and not Path(source).exists():
            error_console.print(f"[red]Error:[/red] File not found: {source}")
            sys.exit(1)

        # Create browser manager
        browser_manager = BrowserManager(
            headless=headless,
            browser_type=browser,
            viewport_width=width,
            viewport_height=height,
            user_agent=user_agent,
            timeout=timeout,
            javascript=not no_javascript,
            images=not no_images,
        )

        # Create extractor
        extractor = StrongbirdExtractor(
            browser_manager=browser_manager,
            use_playwright=not no_playwright and is_url,
            favor_precision=favor_precision,
        )

        # Prepare extraction arguments
        extract_args = {
            "output_format": format,
            "include_comments": include_comments,
            "include_tables": not no_tables,
            "include_links": include_links,
            "include_images": include_images,
            "include_formatting": include_formatting,
            "process_math": process_math,
            "deduplicate": not no_deduplicate,
            "target_lang": target_lang,
            "with_metadata": with_metadata,
            "wait_for_selector": wait_for,
            "scroll_to_bottom": scroll,
            "wait_time": wait_time,
            "execute_script": execute_script,
        }

        # Extract content
        if not quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("Extracting content...", total=None)

                if is_url:
                    # Take screenshot if requested
                    if screenshot and not no_playwright:
                        progress.update(task, description="Taking screenshot...")
                        asyncio.run(
                            browser_manager.take_screenshot(
                                url=source,
                                path=screenshot,
                                wait_for_selector=wait_for,
                            )
                        )
                        if not quiet:
                            console.print(
                                f"[green]✓[/green] Screenshot saved to {screenshot}"
                            )

                    # Check if crawling is requested
                    if crawl_depth > 0:
                        progress.update(
                            task, description=f"Crawling up to depth {crawl_depth}..."
                        )

                        # Create crawler
                        crawler = WebCrawler(
                            extractor=extractor,
                            max_depth=crawl_depth,
                            max_pages=max_pages,
                            delay=crawl_delay,
                            respect_robots_txt=respect_robots_txt,
                            same_domain_only=same_domain_only,
                        )

                        # Crawl pages
                        results = asyncio.run(
                            crawler.crawl_async(source, **extract_args)
                        )

                        if not results:
                            error_console.print(
                                "[red]Failed to extract content from any pages.[/red]"
                            )
                            sys.exit(1)

                        # Handle output based on --output-dir vs --output
                        if output_dir:
                            # Save multiple files to directory
                            save_crawl_results_to_directory(
                                results, output_dir, format, with_metadata, quiet
                            )
                            formatted_output = None  # No single output needed
                        else:
                            # Create crawl results wrapper for combined output
                            crawl_results = CrawlResults(results)

                            # Format aggregated output
                            formatted_output = crawl_results.get_all_content(format)

                            # Add crawl summary
                            if with_metadata:
                                summary = crawl_results.get_metadata_summary()
                                if format == "markdown":
                                    summary_text = f"\n\n---\n\n## Crawl Summary\n\n"
                                    summary_text += f"- **Total pages crawled:** {summary['total_pages']}\n"
                                    summary_text += f"- **Domains:** {', '.join(summary['domains'])}\n"
                                    summary_text += f"- **Depth distribution:** {dict(summary['depths'])}\n"
                                    if summary["titles"]:
                                        summary_text += f"- **Page titles:** {len(summary['titles'])} found\n"
                                else:
                                    summary_text = f"\n\nCrawl Summary:\n"
                                    summary_text += (
                                        f"Total pages: {summary['total_pages']}\n"
                                    )
                                    summary_text += (
                                        f"Domains: {', '.join(summary['domains'])}\n"
                                    )
                                    summary_text += f"Depth distribution: {dict(summary['depths'])}\n"

                                formatted_output += summary_text

                        if not quiet:
                            console.print(
                                f"[green]✓[/green] Crawled {len(results)} pages successfully"
                            )
                    else:
                        progress.update(task, description="Extracting content...")
                        result = asyncio.run(
                            extractor.extract_async(url=source, **extract_args)
                        )

                        if not result:
                            error_console.print(
                                "[red]Failed to extract content from the source.[/red]"
                            )
                            sys.exit(1)

                        # Format output
                        formatted_output = format_output(result, format, with_metadata)
                else:
                    # File extraction (no crawling support for local files)
                    if crawl_depth > 0:
                        error_console.print(
                            "[yellow]Warning:[/yellow] Crawling not supported for local files. Processing single file."
                        )

                    result = asyncio.run(
                        extractor.extract_from_file_async(
                            file_path=source, **extract_args
                        )
                    )

                    if not result:
                        error_console.print(
                            "[red]Failed to extract content from the source.[/red]"
                        )
                        sys.exit(1)

                    # Format output
                    formatted_output = format_output(result, format, with_metadata)

                progress.update(task, completed=True)
        else:
            # Quiet mode
            if is_url:
                if screenshot and not no_playwright:
                    asyncio.run(
                        browser_manager.take_screenshot(
                            url=source,
                            path=screenshot,
                            wait_for_selector=wait_for,
                        )
                    )

                # Check if crawling is requested
                if crawl_depth > 0:
                    # Create crawler
                    crawler = WebCrawler(
                        extractor=extractor,
                        max_depth=crawl_depth,
                        max_pages=max_pages,
                        delay=crawl_delay,
                        respect_robots_txt=respect_robots_txt,
                        same_domain_only=same_domain_only,
                    )

                    # Crawl pages
                    results = asyncio.run(crawler.crawl_async(source, **extract_args))

                    if not results:
                        error_console.print(
                            "[red]Failed to extract content from any pages.[/red]"
                        )
                        sys.exit(1)

                    # Handle output based on --output-dir vs --output
                    if output_dir:
                        # Save multiple files to directory
                        save_crawl_results_to_directory(
                            results, output_dir, format, with_metadata, quiet
                        )
                        formatted_output = None  # No single output needed
                    else:
                        # Create crawl results wrapper for combined output
                        crawl_results = CrawlResults(results)

                        # Format aggregated output
                        formatted_output = crawl_results.get_all_content(format)

                        # Add crawl summary
                        if with_metadata:
                            summary = crawl_results.get_metadata_summary()
                            if format == "markdown":
                                summary_text = f"\n\n---\n\n## Crawl Summary\n\n"
                                summary_text += f"- **Total pages crawled:** {summary['total_pages']}\n"
                                summary_text += (
                                    f"- **Domains:** {', '.join(summary['domains'])}\n"
                                )
                                summary_text += f"- **Depth distribution:** {dict(summary['depths'])}\n"
                            else:
                                summary_text = f"\n\nCrawl Summary:\n"
                                summary_text += (
                                    f"Total pages: {summary['total_pages']}\n"
                                )
                                summary_text += (
                                    f"Domains: {', '.join(summary['domains'])}\n"
                                )
                                summary_text += (
                                    f"Depth distribution: {dict(summary['depths'])}\n"
                                )

                            formatted_output += summary_text
                else:
                    result = asyncio.run(
                        extractor.extract_async(url=source, **extract_args)
                    )

                    if not result:
                        error_console.print(
                            "[red]Failed to extract content from the source.[/red]"
                        )
                        sys.exit(1)

                    # Format output
                    formatted_output = format_output(result, format, with_metadata)
            else:
                result = asyncio.run(
                    extractor.extract_from_file_async(file_path=source, **extract_args)
                )

                if not result:
                    error_console.print(
                        "[red]Failed to extract content from the source.[/red]"
                    )
                    sys.exit(1)

                # Format output
                formatted_output = format_output(result, format, with_metadata)

        # Write output (only if we have single-file output)
        if formatted_output is not None:
            if output:
                output_path = Path(output)
                output_path.write_text(formatted_output, encoding="utf-8")
                if not quiet:
                    console.print(f"[green]✓[/green] Output saved to {output}")
            else:
                click.echo(formatted_output)

    except Exception as e:
        error_console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
