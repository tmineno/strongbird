#!/usr/bin/env python3
"""Parallel processing module for concurrent URL extraction."""

import asyncio
from typing import Any, Dict, List, Optional

from playwright.async_api import Page

from .browser import BrowserManager
from .config import PlaywrightConfig
from .extractor import StrongbirdExtractor


class ParallelProcessor:
    """Manages parallel processing of URLs with page pooling."""

    def __init__(
        self,
        browser_manager: BrowserManager,
        max_workers: int = 1,
        use_playwright: bool = True,
    ):
        """
        Initialize parallel processor.

        Args:
            browser_manager: Browser manager instance
            max_workers: Maximum number of concurrent workers
            use_playwright: Whether to use Playwright for extraction
        """
        self.browser_manager = browser_manager
        self.max_workers = max_workers
        self.use_playwright = use_playwright
        self.semaphore = asyncio.Semaphore(max_workers)

    async def process_urls_parallel(
        self,
        urls: List[str],
        playwright_config: PlaywrightConfig,
        **extract_kwargs,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Process multiple URLs in parallel using page pooling.

        Args:
            urls: List of URLs to process
            playwright_config: Playwright configuration
            **extract_kwargs: Additional extraction arguments

        Returns:
            List of extraction results (None for failed extractions)
        """
        if not self.use_playwright or self.max_workers == 1:
            # Fall back to sequential processing
            return await self._process_urls_sequential(
                urls, playwright_config, **extract_kwargs
            )

        # Use parallel processing with context pool
        async with self.browser_manager.get_context_pool(self.max_workers) as contexts:
            # Create tasks for parallel processing
            tasks = []
            for i, url in enumerate(urls):
                context_index = i % len(contexts)
                context = contexts[context_index]
                task = self._process_single_url_with_context(
                    url, context, playwright_config, **extract_kwargs
                )
                tasks.append(task)

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to None values
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    processed_results.append(None)
                else:
                    processed_results.append(result)

            return processed_results

    async def _process_single_url_with_context(
        self,
        url: str,
        context,
        playwright_config: PlaywrightConfig,
        **extract_kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single URL using the provided browser context.

        Args:
            url: URL to process
            context: Browser context to use
            playwright_config: Playwright configuration
            **extract_kwargs: Additional extraction arguments

        Returns:
            Extraction result or None if failed
        """
        async with self.semaphore:
            try:
                # Create a page from the context
                page = await self.browser_manager.create_page_from_context(context)

                try:
                    # Create a separate extractor for this context
                    extractor = StrongbirdExtractor(
                        browser_manager=self.browser_manager,
                        use_playwright=True,
                        favor_precision=extract_kwargs.get("favor_precision", False),
                    )

                    # Use a custom extraction method that uses the provided page
                    result = await self._extract_with_page(
                        extractor, page, url, playwright_config, **extract_kwargs
                    )

                    return result

                finally:
                    # Always close the page when done
                    await page.close()

            except Exception as e:
                # Log error but don't fail the entire batch
                print(f"Error processing {url}: {e}")
                return None

    async def _process_single_url_with_page(
        self,
        url: str,
        page: Page,
        playwright_config: PlaywrightConfig,
        **extract_kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single URL using the provided page instance.

        This method is kept for backward compatibility and testing.

        Args:
            url: URL to process
            page: Page instance to use
            playwright_config: Playwright configuration
            **extract_kwargs: Additional extraction arguments

        Returns:
            Extraction result or None if failed
        """
        async with self.semaphore:
            try:
                # Create a separate extractor for this page
                extractor = StrongbirdExtractor(
                    browser_manager=self.browser_manager,
                    use_playwright=True,
                    favor_precision=extract_kwargs.get("favor_precision", False),
                )

                # Use a custom extraction method that uses the provided page
                result = await self._extract_with_page(
                    extractor, page, url, playwright_config, **extract_kwargs
                )

                return result

            except Exception as e:
                # Log error but don't fail the entire batch
                print(f"Error processing {url}: {e}")
                return None

    async def _process_urls_sequential(
        self,
        urls: List[str],
        playwright_config: PlaywrightConfig,
        **extract_kwargs,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Process URLs sequentially (fallback method).

        Args:
            urls: List of URLs to process
            playwright_config: Playwright configuration
            **extract_kwargs: Additional extraction arguments

        Returns:
            List of extraction results
        """
        results = []
        extractor = StrongbirdExtractor(
            browser_manager=self.browser_manager,
            favor_precision=extract_kwargs.get("favor_precision", False),
        )

        for url in urls:
            try:
                # Filter kwargs to only include parameters accepted by extract_async
                filtered_kwargs = {
                    k: v
                    for k, v in extract_kwargs.items()
                    if k
                    in [
                        "output_format",
                        "include_comments",
                        "include_tables",
                        "include_links",
                        "include_images",
                        "include_formatting",
                        "process_math",
                        "deduplicate",
                        "target_lang",
                        "with_metadata",
                        "wait_for_selector",
                        "scroll_to_bottom",
                        "wait_time",
                        "execute_script",
                    ]
                }

                # Use the extractor's existing extract_async method
                result = await extractor.extract_async(url=url, **filtered_kwargs)

                results.append(result)
            except Exception as e:
                print(f"Error processing {url}: {e}")
                results.append(None)

        return results

    async def _extract_with_page(
        self,
        extractor: StrongbirdExtractor,
        page: Page,
        url: str,
        playwright_config: PlaywrightConfig,
        **extract_kwargs,
    ) -> Optional[Dict[str, Any]]:
        """
        Extract content using the provided page instance.

        Args:
            extractor: StrongbirdExtractor instance
            page: Page instance to use
            url: URL to extract from
            playwright_config: Playwright configuration
            **extract_kwargs: Additional extraction arguments

        Returns:
            Extraction result or None if failed
        """
        try:
            # Fetch HTML using the page
            html_content = await self.browser_manager.fetch_html_with_page(
                page=page,
                url=url,
                wait_for_selector=playwright_config.wait_for_selector,
                scroll_to_bottom=playwright_config.scroll_to_bottom,
                wait_time=playwright_config.wait_time,
                execute_script=playwright_config.execute_script,
                process_math=extract_kwargs.get("process_math", False),
            )

            if not html_content:
                return None

            # Extract content using trafilatura
            import trafilatura
            from trafilatura.settings import use_config

            # Configure trafilatura settings
            config = use_config()
            if extract_kwargs.get("favor_precision", False):
                config.set("DEFAULT", "EXTRACTION_FAVOR", "precision")
            else:
                config.set("DEFAULT", "EXTRACTION_FAVOR", "recall")

            # Set extraction options
            extraction_options = {
                "output_format": extract_kwargs.get("output_format", "markdown"),
                "include_comments": extract_kwargs.get("include_comments", False),
                "include_tables": extract_kwargs.get("include_tables", True),
                "include_links": extract_kwargs.get("include_links", False),
                "include_images": extract_kwargs.get("include_images", False),
                "include_formatting": extract_kwargs.get("include_formatting", False),
                "deduplicate": extract_kwargs.get("deduplicate", True),
                "target_language": extract_kwargs.get("target_lang"),
            }

            # Extract content
            extracted_content = trafilatura.extract(
                html_content, config=config, **extraction_options
            )

            if not extracted_content:
                return None

            # Build result similar to the original extractor
            result = {
                "content": extracted_content,
                "url": url,
            }

            # Add metadata if requested
            if extract_kwargs.get("with_metadata", True):
                metadata = trafilatura.extract_metadata(html_content)
                if metadata:
                    result["metadata"] = {
                        "title": metadata.title,
                        "author": metadata.author,
                        "date": metadata.date,
                        "description": metadata.description,
                        "sitename": metadata.sitename,
                        "hostname": metadata.hostname,
                    }

            return result

        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None


class ProgressTracker:
    """Track progress for parallel operations."""

    def __init__(self, total_items: int, description: str = "Processing"):
        """
        Initialize progress tracker.

        Args:
            total_items: Total number of items to process
            description: Description for progress display
        """
        self.total_items = total_items
        self.description = description
        self.completed_items = 0
        self.failed_items = 0

    def update_progress(self, success: bool = True) -> None:
        """
        Update progress counters.

        Args:
            success: Whether the item was processed successfully
        """
        self.completed_items += 1
        if not success:
            self.failed_items += 1

    def get_progress_info(self) -> Dict[str, Any]:
        """
        Get current progress information.

        Returns:
            Dictionary with progress details
        """
        return {
            "total": self.total_items,
            "completed": self.completed_items,
            "failed": self.failed_items,
            "success_rate": (
                (self.completed_items - self.failed_items) / self.completed_items * 100
                if self.completed_items > 0
                else 0
            ),
            "percentage": (
                self.completed_items / self.total_items * 100
                if self.total_items > 0
                else 0
            ),
        }

    def is_complete(self) -> bool:
        """Check if all items have been processed."""
        return self.completed_items >= self.total_items
