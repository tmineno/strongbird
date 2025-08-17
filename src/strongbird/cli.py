#!/usr/bin/env python3
"""CLI interface for Strongbird web extractor."""

import sys
import asyncio
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .browser import BrowserManager
from .extractor import StrongbirdExtractor
from .formatter import format_output

console = Console()


@click.command()
@click.argument('source', type=str)
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Output file path (default: stdout)'
)
@click.option(
    '-f', '--format',
    type=click.Choice(['markdown', 'text', 'xml', 'json', 'csv'], case_sensitive=False),
    default='markdown',
    help='Output format (default: markdown)'
)
@click.option(
    '--no-playwright',
    is_flag=True,
    help='Disable Playwright rendering (use simple HTTP fetch)'
)
@click.option(
    '--headless/--no-headless',
    default=True,
    help='Run browser in headless mode (default: True)'
)
@click.option(
    '--browser',
    type=click.Choice(['chromium', 'firefox', 'webkit']),
    default='chromium',
    help='Browser to use (default: chromium)'
)
@click.option(
    '--wait-for',
    type=str,
    help='CSS selector to wait for before extraction'
)
@click.option(
    '--scroll',
    is_flag=True,
    help='Scroll to bottom of page to trigger lazy loading'
)
@click.option(
    '--wait-time',
    type=int,
    default=0,
    help='Additional wait time in milliseconds after page load'
)
@click.option(
    '--execute-script',
    type=str,
    help='JavaScript code to execute before extraction'
)
@click.option(
    '--timeout',
    type=int,
    default=30000,
    help='Page load timeout in milliseconds (default: 30000)'
)
@click.option(
    '--viewport',
    type=str,
    default='1920x1080',
    help='Viewport size as WIDTHxHEIGHT (default: 1920x1080)'
)
@click.option(
    '--user-agent',
    type=str,
    help='Custom user agent string'
)
@click.option(
    '--no-javascript',
    is_flag=True,
    help='Disable JavaScript execution'
)
@click.option(
    '--no-images',
    is_flag=True,
    help='Disable image loading for faster extraction'
)
@click.option(
    '--with-metadata/--no-metadata',
    default=True,
    help='Include metadata in output (default: True)'
)
@click.option(
    '--include-comments',
    is_flag=True,
    help='Include comments in extraction'
)
@click.option(
    '--include-links',
    is_flag=True,
    help='Include links in extraction'
)
@click.option(
    '--include-images',
    is_flag=True,
    help='Include images in extraction'
)
@click.option(
    '--include-formatting',
    is_flag=True,
    help='Include formatting (bold, italic, etc.) in extraction'
)
@click.option(
    '--process-math',
    is_flag=True,
    help='Process mathematical equations to TeX format ($$...$$, $...$)'
)
@click.option(
    '--no-tables',
    is_flag=True,
    help='Exclude tables from extraction'
)
@click.option(
    '--no-deduplicate',
    is_flag=True,
    help='Disable content deduplication'
)
@click.option(
    '--target-lang',
    type=str,
    help='Target language for extraction (e.g., en, de, fr)'
)
@click.option(
    '--favor-precision',
    is_flag=True,
    help='Favor precision over recall in extraction'
)
@click.option(
    '--screenshot',
    type=click.Path(),
    help='Save screenshot to specified path'
)
@click.option(
    '--quiet', '-q',
    is_flag=True,
    help='Suppress progress messages'
)
@click.version_option()
def main(
    source: str,
    output: Optional[str],
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
    quiet: bool
):
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
        
        # Performance optimizations
        strongbird https://example.com --no-images --no-javascript
    """
    try:
        # Parse viewport
        try:
            width, height = map(int, viewport.split('x'))
        except ValueError:
            console.print("[red]Invalid viewport format. Use WIDTHxHEIGHT (e.g., 1920x1080)[/red]", file=sys.stderr)
            sys.exit(1)
        
        # Determine if source is URL or file
        is_url = source.startswith(('http://', 'https://', 'file://'))
        
        if not is_url and not Path(source).exists():
            console.print(f"[red]Error:[/red] File not found: {source}", file=sys.stderr)
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
        
        # Extract content
        if not quiet:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("Extracting content...", total=None)
                
                if is_url:
                    # Take screenshot if requested
                    if screenshot and not no_playwright:
                        progress.update(task, description="Taking screenshot...")
                        asyncio.run(browser_manager.take_screenshot(
                            url=source,
                            path=screenshot,
                            wait_for_selector=wait_for,
                        ))
                        if not quiet:
                            console.print(f"[green]✓[/green] Screenshot saved to {screenshot}")
                    
                    progress.update(task, description="Extracting content...")
                    result = asyncio.run(extractor.extract_async(
                        url=source,
                        output_format=format,
                        include_comments=include_comments,
                        include_tables=not no_tables,
                        include_links=include_links,
                        include_images=include_images,
                        include_formatting=include_formatting,
                        process_math=process_math,
                        deduplicate=not no_deduplicate,
                        target_lang=target_lang,
                        with_metadata=with_metadata,
                        wait_for_selector=wait_for,
                        scroll_to_bottom=scroll,
                        wait_time=wait_time,
                        execute_script=execute_script,
                    ))
                else:
                    result = asyncio.run(extractor.extract_from_file_async(
                        file_path=source,
                        output_format=format,
                        include_comments=include_comments,
                        include_tables=not no_tables,
                        include_links=include_links,
                        include_images=include_images,
                        include_formatting=include_formatting,
                        process_math=process_math,
                        deduplicate=not no_deduplicate,
                        target_lang=target_lang,
                        with_metadata=with_metadata,
                    ))
                
                progress.update(task, completed=True)
        else:
            if is_url:
                if screenshot and not no_playwright:
                    asyncio.run(browser_manager.take_screenshot(
                        url=source,
                        path=screenshot,
                        wait_for_selector=wait_for,
                    ))
                
                result = asyncio.run(extractor.extract_async(
                    url=source,
                    output_format=format,
                    include_comments=include_comments,
                    include_tables=not no_tables,
                    include_links=include_links,
                    include_images=include_images,
                    include_formatting=include_formatting,
                    process_math=process_math,
                    deduplicate=not no_deduplicate,
                    target_lang=target_lang,
                    with_metadata=with_metadata,
                    wait_for_selector=wait_for,
                    scroll_to_bottom=scroll,
                    wait_time=wait_time,
                    execute_script=execute_script,
                ))
            else:
                result = asyncio.run(extractor.extract_from_file_async(
                    file_path=source,
                    output_format=format,
                    include_comments=include_comments,
                    include_tables=not no_tables,
                    include_links=include_links,
                    include_images=include_images,
                    include_formatting=include_formatting,
                    process_math=process_math,
                    deduplicate=not no_deduplicate,
                    target_lang=target_lang,
                    with_metadata=with_metadata,
                ))
        
        if not result:
            console.print("[red]Failed to extract content from the source.[/red]", file=sys.stderr)
            sys.exit(1)
        
        # Format output
        formatted_output = format_output(result, format, with_metadata)
        
        # Write output
        if output:
            output_path = Path(output)
            output_path.write_text(formatted_output, encoding='utf-8')
            if not quiet:
                console.print(f"[green]✓[/green] Output saved to {output}")
        else:
            click.echo(formatted_output)
            
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()