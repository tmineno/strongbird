"""Content extraction module combining Playwright and Trafilatura."""

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

import trafilatura
from trafilatura import extract
from trafilatura.settings import use_config

from .browser import BrowserManager


class StrongbirdExtractor:
    """Extract content from web pages using Playwright and Trafilatura."""

    def __init__(
        self,
        browser_manager: Optional[BrowserManager] = None,
        use_playwright: bool = True,
        favor_precision: bool = False,
    ):
        """
        Initialize extractor.

        Args:
            browser_manager: BrowserManager instance
            use_playwright: Use Playwright for rendering
            favor_precision: Favor precision over recall in extraction
        """
        self.browser_manager = browser_manager or BrowserManager()
        self.use_playwright = use_playwright
        self.favor_precision = favor_precision

    async def extract_async(
        self,
        url: str,
        output_format: str = "markdown",
        include_comments: bool = False,
        include_tables: bool = True,
        include_links: bool = False,
        include_images: bool = False,
        include_formatting: bool = False,
        process_math: bool = False,
        deduplicate: bool = True,
        target_lang: Optional[str] = None,
        with_metadata: bool = True,
        wait_for_selector: Optional[str] = None,
        scroll_to_bottom: bool = False,
        wait_time: int = 0,
        execute_script: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content from URL asynchronously.

        Args:
            url: URL to extract from
            output_format: Output format (markdown, text, xml, json, csv)
            include_comments: Include comments in extraction
            include_tables: Include tables in extraction
            include_links: Include links in extraction
            include_images: Include images in extraction
            include_formatting: Include text formatting (bold, italic, etc.)
            process_math: Process mathematical equations to TeX format
            deduplicate: Remove duplicate content
            target_lang: Target language for extraction
            with_metadata: Include metadata in result
            wait_for_selector: CSS selector to wait for (Playwright)
            scroll_to_bottom: Scroll to bottom of page (Playwright)
            wait_time: Additional wait time in ms (Playwright)
            execute_script: JavaScript to execute (Playwright)

        Returns:
            Dictionary containing extracted content and metadata
        """
        # Get HTML content
        if self.use_playwright:
            html_content = await self.browser_manager.fetch_html(
                url=url,
                wait_for_selector=wait_for_selector,
                scroll_to_bottom=scroll_to_bottom,
                wait_time=wait_time,
                execute_script=execute_script,
                process_math=process_math,
            )
        else:
            # Fallback to trafilatura's fetch
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
            html_content = downloaded

        # Configure extraction
        config = use_config()
        if self.favor_precision:
            config.set("DEFAULT", "EXTRACTION_FAVOR", "precision")
        else:
            config.set("DEFAULT", "EXTRACTION_FAVOR", "recall")

        # Map output format
        trafilatura_format = self._map_format(output_format)

        # Extract content
        extracted = extract(
            html_content,
            url=url,
            include_comments=include_comments,
            include_tables=include_tables,
            include_links=include_links,
            include_images=include_images,
            include_formatting=include_formatting,
            deduplicate=deduplicate,
            target_language=target_lang,
            favor_precision=self.favor_precision,
            favor_recall=not self.favor_precision,
            output_format=trafilatura_format,
            with_metadata=with_metadata,
            config=config,
        )

        if not extracted:
            return None

        result = {
            "content": extracted,
            "format": output_format,
            "url": url,
        }

        # Extract metadata separately if needed
        if with_metadata and output_format in ["markdown", "text"]:
            metadata = trafilatura.metadata.extract_metadata(html_content)
            if metadata:
                result["metadata"] = {
                    "title": metadata.title,
                    "author": metadata.author,
                    "date": metadata.date,
                    "description": metadata.description,
                    "sitename": metadata.sitename,
                    "categories": metadata.categories,
                    "tags": metadata.tags,
                    "language": metadata.language,
                }
                # Remove None values
                result["metadata"] = {
                    k: v for k, v in result["metadata"].items() if v is not None
                }

        return result

    def extract(self, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Synchronous wrapper for extract_async.

        Args:
            url: URL to extract from
            **kwargs: Additional arguments for extract_async

        Returns:
            Dictionary containing extracted content and metadata
        """
        return asyncio.run(self.extract_async(url, **kwargs))

    async def extract_from_file_async(
        self,
        file_path: str,
        output_format: str = "markdown",
        include_comments: bool = False,
        include_tables: bool = True,
        include_links: bool = False,
        include_images: bool = False,
        include_formatting: bool = False,
        process_math: bool = False,
        deduplicate: bool = True,
        target_lang: Optional[str] = None,
        with_metadata: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content from local HTML file.

        Args:
            file_path: Path to HTML file
            output_format: Output format
            include_comments: Include comments
            include_tables: Include tables
            include_links: Include links
            include_images: Include images
            include_formatting: Include text formatting
            process_math: Process mathematical equations (for local files with rendered math)
            deduplicate: Remove duplicates
            target_lang: Target language
            with_metadata: Include metadata

        Returns:
            Dictionary containing extracted content and metadata
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Configure extraction
        config = use_config()
        if self.favor_precision:
            config.set("DEFAULT", "EXTRACTION_FAVOR", "precision")
        else:
            config.set("DEFAULT", "EXTRACTION_FAVOR", "recall")

        # Map output format
        trafilatura_format = self._map_format(output_format)

        # Extract content
        extracted = extract(
            html_content,
            include_comments=include_comments,
            include_tables=include_tables,
            include_links=include_links,
            include_images=include_images,
            include_formatting=include_formatting,
            deduplicate=deduplicate,
            target_language=target_lang,
            favor_precision=self.favor_precision,
            favor_recall=not self.favor_precision,
            output_format=trafilatura_format,
            with_metadata=with_metadata,
            config=config,
        )

        if not extracted:
            return None

        result = {
            "content": extracted,
            "format": output_format,
            "file": str(path.absolute()),
        }

        # Extract metadata if needed
        if with_metadata and output_format in ["markdown", "text"]:
            metadata = trafilatura.metadata.extract_metadata(html_content)
            if metadata:
                result["metadata"] = {
                    "title": metadata.title,
                    "author": metadata.author,
                    "date": metadata.date,
                    "description": metadata.description,
                    "sitename": metadata.sitename,
                    "categories": metadata.categories,
                    "tags": metadata.tags,
                    "language": metadata.language,
                }
                result["metadata"] = {
                    k: v for k, v in result["metadata"].items() if v is not None
                }

        return result

    def extract_from_file(self, file_path: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for extract_from_file_async."""
        return asyncio.run(self.extract_from_file_async(file_path, **kwargs))

    def _map_format(self, format_name: str) -> str:
        """Map format name to Trafilatura format."""
        format_map = {
            "markdown": "markdown",
            "md": "markdown",
            "text": "txt",
            "txt": "txt",
            "xml": "xml",
            "json": "json",
            "csv": "csv",
        }
        return format_map.get(format_name.lower(), "markdown")
