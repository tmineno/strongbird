"""CLI orchestrator for managing different extraction workflows."""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import (
    BrowserConfig,
    CrawlConfig,
    ExtractionConfig,
    OutputConfig,
    PlaywrightConfig,
)
from .formatter import format_output
from .services import CrawlService, ExtractionService

console = Console()
error_console = Console(stderr=True)


class CLIOrchestrator:
    """Orchestrate different extraction workflows."""

    def __init__(
        self,
        browser_config: BrowserConfig,
        extraction_config: ExtractionConfig,
        playwright_config: PlaywrightConfig,
        crawl_config: CrawlConfig,
        output_config: OutputConfig,
    ):
        """
        Initialize CLI orchestrator.

        Args:
            browser_config: Browser configuration
            extraction_config: Extraction configuration
            playwright_config: Playwright configuration
            crawl_config: Crawl configuration
            output_config: Output configuration
        """
        self.browser_config = browser_config
        self.extraction_config = extraction_config
        self.playwright_config = playwright_config
        self.crawl_config = crawl_config
        self.output_config = output_config

        # Initialize services
        self.extraction_service = ExtractionService(extraction_config, browser_config)
        self.crawl_service = CrawlService(
            self.extraction_service, crawl_config, extraction_config
        )

    def validate_source(self, source: str) -> tuple[bool, Optional[Path]]:
        """
        Validate input source and determine type.

        Args:
            source: Input source (URL or file path)

        Returns:
            Tuple of (is_url, file_path)
        """
        is_url = source.startswith(("http://", "https://", "file://"))

        if not is_url:
            file_path = Path(source)
            if not file_path.exists():
                error_console.print(f"[red]Error:[/red] File not found: {source}")
                return False, None
            return False, file_path

        return True, None

    async def handle_single_extraction(self, source: str) -> Optional[Dict[str, Any]]:
        """
        Handle single page/file extraction.

        Args:
            source: URL or file path to extract from

        Returns:
            Extraction result or None
        """
        is_url, file_path = self.validate_source(source)
        if is_url is False and file_path is None:
            return None

        try:
            if is_url:
                # Handle screenshot if requested
                screenshot_path = self.output_config.screenshot_path
                if screenshot_path and self.browser_config.javascript:
                    if not self.output_config.quiet:
                        console.print("Taking screenshot...")
                    await self.extraction_service.take_screenshot(
                        source,
                        self.output_config.screenshot_path,
                        self.playwright_config.wait_for_selector,
                    )
                    if not self.output_config.quiet:
                        msg = "[green]✓[/green] Screenshot saved to "
                        msg += str(self.output_config.screenshot_path)
                        console.print(msg)

                # Extract from URL
                result = await self.extraction_service.extract_from_url(
                    source,
                    self.playwright_config,
                    use_playwright=self.browser_config.javascript,
                )
            else:
                # Extract from file
                result = await self.extraction_service.extract_from_file(str(file_path))

            return result

        except Exception as e:
            error_console.print(f"[red]Error during extraction:[/red] {e}")
            return None

    async def handle_crawl_extraction(self, seed_url: str) -> List[Dict[str, Any]]:
        """
        Handle multi-page crawling extraction.

        Args:
            seed_url: Starting URL for crawling

        Returns:
            List of extraction results
        """
        try:
            results = await self.crawl_service.crawl_pages(
                seed_url, self.playwright_config
            )
            return results
        except Exception as e:
            error_console.print(f"[red]Error during crawling:[/red] {e}")
            return []

    def handle_output(
        self, results: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> None:
        """
        Handle output formatting and saving.

        Args:
            results: Single result or list of results from extraction
        """
        if not results:
            error_console.print("[red]Failed to extract content from the source.[/red]")
            return

        # Handle single result
        if isinstance(results, dict):
            self._output_single_result(results)
        # Handle multiple results from crawling
        else:
            self._output_crawl_results(results)

    def _output_single_result(self, result: Dict[str, Any]) -> None:
        """Output a single extraction result."""
        formatted_output = format_output(
            result,
            self.extraction_config.output_format,
            self.extraction_config.with_metadata,
        )

        if self.output_config.output_path:
            output_path = Path(self.output_config.output_path)
            output_path.write_text(formatted_output, encoding="utf-8")
            if not self.output_config.quiet:
                console.print(f"[green]✓[/green] Output saved to {output_path}")
        else:
            console.print(formatted_output)

    def _output_crawl_results(self, results: List[Dict[str, Any]]) -> None:
        """Output multiple crawl results."""
        if self.output_config.output_path:
            # If output path is a directory, save individual files
            output_path = Path(self.output_config.output_path)
            if output_path.suffix == "":
                self._save_crawl_results_to_directory(results, output_path)
            else:
                # Save all results to single file
                self._save_crawl_results_to_single_file(results, output_path)
        else:
            # Output all results to stdout
            for i, result in enumerate(results):
                if i > 0:
                    console.print("\n" + "=" * 60 + "\n")
                formatted_output = format_output(
                    result,
                    self.extraction_config.output_format,
                    self.extraction_config.with_metadata,
                )
                console.print(formatted_output)

    def _save_crawl_results_to_directory(
        self, results: List[Dict[str, Any]], output_dir: Path
    ) -> None:
        """Save crawl results as individual files in a directory."""
        import re
        from urllib.parse import urlparse

        output_dir.mkdir(parents=True, exist_ok=True)

        for i, result in enumerate(results):
            # Generate filename from URL
            url = result.get("url", f"page_{i}")
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
            path = parsed.path.strip("/")

            if path:
                path_clean = re.sub(r"[^\w\-_./]", "_", path).replace("/", "_")
                base_name = f"{domain}_{path_clean}"
            else:
                base_name = domain

            # Add order prefix and extension
            base_name = f"{i:03d}_{base_name}"[:150]  # Truncate if too long
            extensions = {
                "markdown": ".md",
                "text": ".txt",
                "xml": ".xml",
                "json": ".json",
                "csv": ".csv",
            }
            extension = extensions.get(self.extraction_config.output_format, ".txt")
            filename = f"{base_name}{extension}"

            # Write file
            file_path = output_dir / filename
            formatted_output = format_output(
                result,
                self.extraction_config.output_format,
                self.extraction_config.with_metadata,
            )
            file_path.write_text(formatted_output, encoding="utf-8")

            if not self.output_config.quiet:
                console.print(f"[green]✓[/green] Saved {file_path.name}")

        if not self.output_config.quiet:
            console.print(
                f"\n[green]✓[/green] Saved {len(results)} files to {output_dir}"
            )

    def _save_crawl_results_to_single_file(
        self, results: List[Dict[str, Any]], output_file: Path
    ) -> None:
        """Save all crawl results to a single file."""
        output_parts = []

        for i, result in enumerate(results):
            if i > 0:
                output_parts.append("\n" + "=" * 60 + "\n")
            formatted_output = format_output(
                result,
                self.extraction_config.output_format,
                self.extraction_config.with_metadata,
            )
            output_parts.append(formatted_output)

        combined_output = "\n".join(output_parts)
        output_file.write_text(combined_output, encoding="utf-8")

        if not self.output_config.quiet:
            console.print(
                f"[green]✓[/green] Saved {len(results)} pages to {output_file}"
            )

    async def run(self, source: str) -> None:
        """
        Run the extraction workflow.

        Args:
            source: Source URL or file path
        """
        # Check if crawling is requested
        if self.crawl_config.max_depth > 0:
            # Validate that source is a URL
            if not source.startswith(("http://", "https://")):
                error_console.print(
                    "[red]Error:[/red] Crawling requires a URL as the source"
                )
                sys.exit(1)

            # Run crawling workflow
            if not self.output_config.quiet:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True,
                ) as progress:
                    task = progress.add_task("Crawling pages...", total=None)
                    results = await self.handle_crawl_extraction(source)
                    progress.update(task, completed=True)
            else:
                results = await self.handle_crawl_extraction(source)

            self.handle_output(results)
        else:
            # Run single extraction workflow
            if not self.output_config.quiet:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=console,
                    transient=True,
                ) as progress:
                    task = progress.add_task("Extracting content...", total=None)
                    result = await self.handle_single_extraction(source)
                    progress.update(task, completed=True)
            else:
                result = await self.handle_single_extraction(source)

            if result:
                self.handle_output(result)
            else:
                sys.exit(1)
