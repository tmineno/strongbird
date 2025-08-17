"""Service classes for extraction and crawling operations."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import trafilatura
from trafilatura import extract
from trafilatura.settings import use_config

from .browser import BrowserManager
from .config import BrowserConfig, CrawlConfig, ExtractionConfig, PlaywrightConfig
from .crawler import WebCrawler
from .extractor import StrongbirdExtractor


class ExtractionService:
    """Unified service for content extraction operations."""

    def __init__(
        self, extraction_config: ExtractionConfig, browser_config: BrowserConfig
    ):
        """
        Initialize extraction service.

        Args:
            extraction_config: Extraction configuration
            browser_config: Browser configuration
        """
        self.extraction_config = extraction_config
        self.browser_config = browser_config
        self.browser_manager = BrowserManager(
            headless=browser_config.headless,
            browser_type=browser_config.browser_type,
            viewport_width=browser_config.viewport[0],
            viewport_height=browser_config.viewport[1],
            user_agent=browser_config.user_agent,
            timeout=browser_config.timeout,
            javascript=browser_config.javascript,
            images=browser_config.images,
        )
        self.extractor = StrongbirdExtractor(
            browser_manager=self.browser_manager,
            favor_precision=extraction_config.favor_precision,
        )

    def _configure_trafilatura(self) -> Any:
        """Configure trafilatura settings based on extraction config."""
        config = use_config()
        if self.extraction_config.favor_precision:
            config.set("DEFAULT", "EXTRACTION_FAVOR", "precision")
        else:
            config.set("DEFAULT", "EXTRACTION_FAVOR", "recall")
        return config

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

    def _build_metadata_dict(self, metadata: Any) -> Dict[str, Any]:
        """Build metadata dictionary from trafilatura metadata object."""
        if not metadata:
            return {}

        metadata_dict = {
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
        return {k: v for k, v in metadata_dict.items() if v is not None}

    def _extract_with_trafilatura(
        self, html_content: str, url: Optional[str] = None
    ) -> Optional[str]:
        """
        Unified trafilatura extraction method.

        Args:
            html_content: HTML content to extract from
            url: Optional source URL

        Returns:
            Extracted content or None
        """
        config = self._configure_trafilatura()
        trafilatura_format = self._map_format(self.extraction_config.output_format)

        return extract(
            html_content,
            url=url,
            include_comments=self.extraction_config.include_comments,
            include_tables=self.extraction_config.include_tables,
            include_links=self.extraction_config.include_links,
            include_images=self.extraction_config.include_images,
            include_formatting=self.extraction_config.include_formatting,
            deduplicate=self.extraction_config.deduplicate,
            target_language=self.extraction_config.target_lang,
            favor_precision=self.extraction_config.favor_precision,
            favor_recall=not self.extraction_config.favor_precision,
            output_format=trafilatura_format,
            with_metadata=self.extraction_config.with_metadata,
            config=config,
        )

    def _build_result(
        self, content: str, source: str, html_content: str, is_url: bool = True
    ) -> Dict[str, Any]:
        """
        Build extraction result with metadata.

        Args:
            content: Extracted content
            source: Source URL or file path
            html_content: Original HTML content
            is_url: Whether source is a URL

        Returns:
            Result dictionary with content and metadata
        """
        result = {
            "content": content,
            "format": self.extraction_config.output_format,
        }

        if is_url:
            result["url"] = source
        else:
            result["file"] = source

        # Extract metadata if needed
        if (
            self.extraction_config.with_metadata
            and self.extraction_config.output_format in ["markdown", "text"]
        ):
            metadata = trafilatura.metadata.extract_metadata(html_content)
            metadata_dict = self._build_metadata_dict(metadata)
            if metadata_dict:
                result["metadata"] = metadata_dict

        return result

    async def extract_from_url(
        self,
        url: str,
        playwright_config: PlaywrightConfig,
        use_playwright: bool = True,
        img_folder: Optional[Path] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content from URL.

        Args:
            url: URL to extract from
            playwright_config: Playwright interaction configuration
            use_playwright: Whether to use Playwright for rendering
            img_folder: Folder to save images (if extract_images is enabled)

        Returns:
            Extraction result or None
        """
        # Check if non-playwright mode has content
        if not use_playwright:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None

        # Set browser manager to not use playwright if we fetched with trafilatura
        self.extractor.use_playwright = use_playwright

        # Use the main extractor for consistency and image support
        result = await self.extractor.extract_async(
            url=url,
            output_format=self.extraction_config.output_format,
            include_comments=self.extraction_config.include_comments,
            include_tables=self.extraction_config.include_tables,
            include_links=self.extraction_config.include_links,
            include_images=self.extraction_config.include_images,
            include_formatting=self.extraction_config.include_formatting,
            process_math=self.extraction_config.process_math,
            deduplicate=self.extraction_config.deduplicate,
            target_lang=self.extraction_config.target_lang,
            with_metadata=self.extraction_config.with_metadata,
            wait_for_selector=playwright_config.wait_for_selector,
            scroll_to_bottom=playwright_config.scroll_to_bottom,
            wait_time=playwright_config.wait_time,
            execute_script=playwright_config.execute_script,
            extract_images=self.extraction_config.extract_images,
            img_folder=img_folder,
        )

        return result

    async def extract_from_file(
        self, file_path: str, img_folder: Optional[Path] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content from local HTML file.

        Args:
            file_path: Path to HTML file
            img_folder: Folder to save images (if extract_images is enabled)

        Returns:
            Extraction result or None
        """
        # Use the main extractor for consistency and image support
        result = await self.extractor.extract_from_file_async(
            file_path=file_path,
            output_format=self.extraction_config.output_format,
            include_comments=self.extraction_config.include_comments,
            include_tables=self.extraction_config.include_tables,
            include_links=self.extraction_config.include_links,
            include_images=self.extraction_config.include_images,
            include_formatting=self.extraction_config.include_formatting,
            process_math=self.extraction_config.process_math,
            deduplicate=self.extraction_config.deduplicate,
            target_lang=self.extraction_config.target_lang,
            with_metadata=self.extraction_config.with_metadata,
            extract_images=self.extraction_config.extract_images,
            img_folder=img_folder,
        )

        return result

    async def take_screenshot(
        self, url: str, path: str, wait_for_selector: Optional[str] = None
    ) -> None:
        """
        Take screenshot of webpage.

        Args:
            url: URL to screenshot
            path: Path to save screenshot
            wait_for_selector: Optional CSS selector to wait for
        """
        await self.browser_manager.take_screenshot(
            url=url, path=path, wait_for_selector=wait_for_selector
        )


class CrawlService:
    """Service for web crawling operations."""

    def __init__(
        self,
        extraction_service: ExtractionService,
        crawl_config: CrawlConfig,
        extraction_config: ExtractionConfig,
    ):
        """
        Initialize crawl service.

        Args:
            extraction_service: ExtractionService instance
            crawl_config: Crawling configuration
            extraction_config: Extraction configuration
        """
        self.extraction_service = extraction_service
        self.crawl_config = crawl_config
        self.extraction_config = extraction_config

        # Create crawler with extractor
        self.crawler = WebCrawler(
            extractor=extraction_service.extractor,
            max_depth=crawl_config.max_depth,
            max_pages=crawl_config.max_pages,
            delay=crawl_config.delay,
            respect_robots_txt=crawl_config.respect_robots_txt,
            same_domain_only=crawl_config.same_domain_only,
        )

    async def crawl_pages(
        self,
        seed_url: str,
        playwright_config: PlaywrightConfig,
        img_folder: Optional[Path] = None,
    ) -> List[Dict[str, Any]]:
        """
        Crawl multiple pages starting from seed URL.

        Args:
            seed_url: Starting URL for crawling
            playwright_config: Playwright configuration

        Returns:
            List of extraction results from all crawled pages
        """
        # Build extraction kwargs
        extract_kwargs = {
            "output_format": self.extraction_config.output_format,
            "include_comments": self.extraction_config.include_comments,
            "include_tables": self.extraction_config.include_tables,
            "include_links": self.extraction_config.include_links,
            "include_images": self.extraction_config.include_images,
            "extract_images": self.extraction_config.extract_images,
            "include_formatting": self.extraction_config.include_formatting,
            "process_math": self.extraction_config.process_math,
            "deduplicate": self.extraction_config.deduplicate,
            "target_lang": self.extraction_config.target_lang,
            "with_metadata": self.extraction_config.with_metadata,
            "wait_for_selector": playwright_config.wait_for_selector,
            "scroll_to_bottom": playwright_config.scroll_to_bottom,
            "wait_time": playwright_config.wait_time,
            "execute_script": playwright_config.execute_script,
            "img_folder": img_folder,
        }

        return await self.crawler.crawl_async(seed_url, **extract_kwargs)
