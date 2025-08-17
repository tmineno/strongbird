#!/usr/bin/env python3
"""Test suite for parallel processing functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from strongbird.browser import BrowserManager
from strongbird.config import PlaywrightConfig
from strongbird.parallel import ParallelProcessor, ProgressTracker


class TestParallelProcessor:
    """Test the parallel processor functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.browser_manager = MagicMock(spec=BrowserManager)
        self.processor = ParallelProcessor(
            browser_manager=self.browser_manager, max_workers=2, use_playwright=True
        )
        self.playwright_config = PlaywrightConfig(
            wait_for_selector=None,
            scroll_to_bottom=False,
            wait_time=0,
            execute_script=None,
        )

    @pytest.mark.asyncio
    async def test_process_urls_sequential_fallback(self):
        """Test that sequential processing is used when max_workers=1."""
        processor = ParallelProcessor(
            browser_manager=self.browser_manager, max_workers=1, use_playwright=True
        )

        with patch.object(processor, "_process_urls_sequential") as mock_sequential:
            mock_sequential.return_value = [{"content": "test"}]

            urls = ["http://example.com"]
            result = await processor.process_urls_parallel(urls, self.playwright_config)

            mock_sequential.assert_called_once()
            assert result == [{"content": "test"}]

    @pytest.mark.asyncio
    async def test_process_urls_sequential_no_playwright(self):
        """Test that sequential processing is used when playwright is disabled."""
        processor = ParallelProcessor(
            browser_manager=self.browser_manager, max_workers=3, use_playwright=False
        )

        with patch.object(processor, "_process_urls_sequential") as mock_sequential:
            mock_sequential.return_value = [{"content": "test"}]

            urls = ["http://example.com"]
            result = await processor.process_urls_parallel(urls, self.playwright_config)

            mock_sequential.assert_called_once()
            assert result == [{"content": "test"}]

    @pytest.mark.asyncio
    async def test_parallel_processing_with_context_pool(self):
        """Test parallel processing using context pool."""
        # Mock context pool context manager
        mock_contexts = [AsyncMock(), AsyncMock()]
        mock_context_pool = AsyncMock()
        mock_context_pool.__aenter__.return_value = mock_contexts
        mock_context_pool.__aexit__.return_value = None

        self.browser_manager.get_context_pool.return_value = mock_context_pool

        # Mock the single URL processing method
        with patch.object(
            self.processor, "_process_single_url_with_context"
        ) as mock_process:
            mock_process.return_value = {"content": "test", "url": "http://example.com"}

            urls = ["http://example1.com", "http://example2.com"]
            result = await self.processor.process_urls_parallel(
                urls, self.playwright_config
            )

            # Should call get_context_pool with max_workers
            self.browser_manager.get_context_pool.assert_called_once_with(2)

            # Should process each URL
            assert mock_process.call_count == 2
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_parallel_processing_exception_handling(self):
        """Test that exceptions in parallel processing are handled gracefully."""
        # Mock context pool
        mock_contexts = [AsyncMock()]
        mock_context_pool = AsyncMock()
        mock_context_pool.__aenter__.return_value = mock_contexts
        mock_context_pool.__aexit__.return_value = None

        self.browser_manager.get_context_pool.return_value = mock_context_pool

        # Mock one successful and one failing processing
        with patch.object(
            self.processor, "_process_single_url_with_context"
        ) as mock_process:

            def side_effect(*args, **kwargs):
                if "example1" in args[0]:
                    return {"content": "success"}
                else:
                    raise Exception("Test error")

            mock_process.side_effect = side_effect

            urls = ["http://example1.com", "http://example2.com"]
            result = await self.processor.process_urls_parallel(
                urls, self.playwright_config
            )

            # Should have one successful result and one None
            assert len(result) == 2
            assert result[0] == {"content": "success"}
            assert result[1] is None

    @pytest.mark.asyncio
    async def test_process_single_url_with_page(self):
        """Test processing a single URL with a page instance."""
        mock_page = AsyncMock()

        # Mock the extraction method directly
        with patch.object(self.processor, "_extract_with_page") as mock_extract:
            mock_extract.return_value = {
                "content": "extracted",
                "url": "http://example.com",
            }

            result = await self.processor._process_single_url_with_page(
                "http://example.com", mock_page, self.playwright_config
            )

            # Should call extract_with_page
            mock_extract.assert_called_once()
            assert result == {"content": "extracted", "url": "http://example.com"}

    @pytest.mark.asyncio
    async def test_extract_with_page_success(self):
        """Test successful content extraction with page."""
        mock_page = AsyncMock()
        mock_extractor = MagicMock()

        # Mock HTML fetch
        self.browser_manager.fetch_html_with_page.return_value = "<html>test</html>"

        # Mock trafilatura extraction (imported dynamically in the method)
        with (
            patch("trafilatura.extract") as mock_extract,
            patch("trafilatura.extract_metadata") as mock_extract_metadata,
            patch("trafilatura.settings.use_config") as mock_config,
        ):

            mock_extract.return_value = "Extracted content"
            mock_metadata = MagicMock()
            mock_metadata.title = "Test Title"
            mock_metadata.author = "Test Author"
            mock_metadata.date = "2023-01-01"
            mock_metadata.description = "Test Description"
            mock_metadata.sitename = "Test Site"
            mock_metadata.hostname = "example.com"
            mock_extract_metadata.return_value = mock_metadata

            mock_config_obj = MagicMock()
            mock_config.return_value = mock_config_obj

            result = await self.processor._extract_with_page(
                mock_extractor,
                mock_page,
                "http://example.com",
                self.playwright_config,
                with_metadata=True,
            )

            assert result is not None
            assert result["content"] == "Extracted content"
            assert result["url"] == "http://example.com"
            assert "metadata" in result
            assert result["metadata"]["title"] == "Test Title"

    @pytest.mark.asyncio
    async def test_extract_with_page_no_content(self):
        """Test extraction when no content is found."""
        mock_page = AsyncMock()
        mock_extractor = MagicMock()

        # Mock empty HTML fetch
        self.browser_manager.fetch_html_with_page.return_value = None

        result = await self.processor._extract_with_page(
            mock_extractor, mock_page, "http://example.com", self.playwright_config
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_semaphore_limits_concurrency(self):
        """Test that semaphore properly limits concurrency."""
        # Create processor with low worker count
        processor = ParallelProcessor(
            browser_manager=self.browser_manager, max_workers=1, use_playwright=True
        )

        # Track concurrent executions
        concurrent_count = 0
        max_concurrent = 0

        async def mock_process(*args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)  # Simulate work
            concurrent_count -= 1
            return {"content": "test"}

        # Mock context pool
        mock_contexts = [AsyncMock()]
        mock_context_pool = AsyncMock()
        mock_context_pool.__aenter__.return_value = mock_contexts
        mock_context_pool.__aexit__.return_value = None

        processor.browser_manager.get_context_pool.return_value = mock_context_pool

        with patch.object(
            processor, "_process_single_url_with_context", side_effect=mock_process
        ):
            urls = ["http://example1.com", "http://example2.com", "http://example3.com"]
            await processor.process_urls_parallel(urls, self.playwright_config)

            # With max_workers=1, should never have more than 1 concurrent
            assert max_concurrent <= 1


class TestProgressTracker:
    """Test the progress tracker functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tracker = ProgressTracker(total_items=10, description="Test")

    def test_initial_state(self):
        """Test initial state of progress tracker."""
        assert self.tracker.total_items == 10
        assert self.tracker.description == "Test"
        assert self.tracker.completed_items == 0
        assert self.tracker.failed_items == 0
        assert not self.tracker.is_complete()

    def test_update_progress_success(self):
        """Test updating progress with successful item."""
        self.tracker.update_progress(success=True)

        assert self.tracker.completed_items == 1
        assert self.tracker.failed_items == 0

    def test_update_progress_failure(self):
        """Test updating progress with failed item."""
        self.tracker.update_progress(success=False)

        assert self.tracker.completed_items == 1
        assert self.tracker.failed_items == 1

    def test_progress_info(self):
        """Test getting progress information."""
        # Add some completed items
        self.tracker.update_progress(success=True)
        self.tracker.update_progress(success=True)
        self.tracker.update_progress(success=False)

        info = self.tracker.get_progress_info()

        assert info["total"] == 10
        assert info["completed"] == 3
        assert info["failed"] == 1
        assert info["success_rate"] == (2 / 3) * 100  # 66.67%
        assert info["percentage"] == 30.0  # 3/10 * 100

    def test_is_complete(self):
        """Test completion detection."""
        assert not self.tracker.is_complete()

        # Complete all items
        for _ in range(10):
            self.tracker.update_progress(success=True)

        assert self.tracker.is_complete()

    def test_success_rate_with_no_items(self):
        """Test success rate calculation with no completed items."""
        info = self.tracker.get_progress_info()
        assert info["success_rate"] == 0

    def test_percentage_with_no_total(self):
        """Test percentage calculation with zero total items."""
        tracker = ProgressTracker(total_items=0)
        info = tracker.get_progress_info()
        assert info["percentage"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
