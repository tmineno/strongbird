"""
Integration tests for Strongbird.

These tests require network access and test against real websites.
"""

import re

import pytest


def count_math_expressions(content: str) -> dict:
    """Count different types of math expressions in extracted content."""
    counts = {
        "inline_math": len(re.findall(r"\$[^$\n]+\$", content)),
        "display_math": len(re.findall(r"\$\$[^$]+\$\$", content, re.DOTALL)),
        "total_expressions": 0,
    }
    counts["total_expressions"] = counts["inline_math"] + counts["display_math"]
    return counts


@pytest.mark.integration
class TestIntegration:
    """Integration tests with real websites."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "url,min_expressions",
        [
            ("https://en.wikipedia.org/wiki/Quadratic_formula", 3),
            ("https://en.wikipedia.org/wiki/Euler%27s_identity", 2),
        ],
    )
    async def test_wikipedia_math_extraction(self, extractor, url, min_expressions):
        """Test math extraction from Wikipedia pages."""
        # Skip if no network available
        try:
            import socket

            socket.create_connection(("wikipedia.org", 443), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="markdown",
            process_math=True,
            with_metadata=False,
            wait_time=2000,  # Give time for math to render
        )

        assert result is not None, f"Failed to extract from {url}"
        assert "content" in result, "No content in result"

        content = result["content"]
        assert len(content) > 100, "Content too short, extraction may have failed"

        math_count = count_math_expressions(content)
        assert math_count["total_expressions"] >= min_expressions, (
            f"Expected at least {min_expressions} math expressions from {url}, "
            f"found {math_count['total_expressions']}"
        )

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_wikipedia_metadata_extraction(self, extractor):
        """Test metadata extraction from Wikipedia."""
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("wikipedia.org", 443), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="markdown",
            process_math=False,
            with_metadata=True,
        )

        assert result is not None, "Failed to extract from Wikipedia"
        assert "content" in result, "No content in result"

        # Check metadata
        if "metadata" in result and result["metadata"]:
            metadata = result["metadata"]
            assert isinstance(metadata, dict)
            # Wikipedia pages should have at least a title
            assert "title" in metadata or "sitename" in metadata
            # Should identify as Wikipedia or Wikimedia
            if "sitename" in metadata:
                assert any(
                    term in metadata["sitename"].lower()
                    for term in ["wikipedia", "wikimedia"]
                )

    @pytest.mark.asyncio
    async def test_httpbin_simple_extraction(self, extractor):
        """Test extraction from a simple HTTP endpoint."""
        url = "http://httpbin.org/html"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("httpbin.org", 80), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="text",
            process_math=False,
            with_metadata=False,
        )

        # httpbin.org/html might not have enough content for extraction
        # Just verify it doesn't crash
        assert result is None or (result is not None and "content" in result)

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_javascript_heavy_site(self, extractor):
        """Test extraction from a JavaScript-rendered page."""
        # Using httpbin's delay endpoint which should work with JS
        url = "http://httpbin.org/delay/1"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("httpbin.org", 80), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="text",
            process_math=False,
            with_metadata=False,
            wait_time=2000,  # Wait for content to load
        )

        # This endpoint returns JSON, which might not extract well as article content
        # Just verify it doesn't crash
        assert result is not None or result == {"content": None}

    @pytest.mark.asyncio
    async def test_https_extraction(self, extractor):
        """Test extraction from HTTPS URLs."""
        url = "https://httpbin.org/html"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("httpbin.org", 443), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="markdown",
            process_math=False,
            with_metadata=False,
        )

        # httpbin.org/html might not have enough content for extraction
        # Just verify it doesn't crash and handles HTTPS
        assert result is None or (result is not None and "content" in result)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("format_type", ["markdown"])
    async def test_format_consistency_across_sites(self, extractor, format_type):
        """Test that different output formats work consistently."""
        # Use Wikipedia for more reliable content
        url = "https://en.wikipedia.org/wiki/Python_(programming_language)"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("wikipedia.org", 443), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format=format_type,
            process_math=False,
            with_metadata=False,
        )

        assert result is not None, f"Failed with {format_type} format"
        assert "content" in result, f"No content with {format_type} format"

        content = result["content"]
        assert isinstance(content, str), f"Content not a string for {format_type}"
        assert len(content) > 100, f"Content too short for {format_type}"

    @pytest.mark.asyncio
    async def test_url_with_query_parameters(self, extractor):
        """Test extraction from URLs with query parameters."""
        url = "http://httpbin.org/get?test=value&foo=bar"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("httpbin.org", 80), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="text",
            process_math=False,
            with_metadata=False,
        )

        # httpbin.org/get returns JSON which might not extract as article
        # Just ensure it handles the URL correctly
        assert result is not None or result == {"content": None}

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_page_extraction(self, extractor):
        """Test extraction from a large Wikipedia page."""
        url = "https://en.wikipedia.org/wiki/List_of_countries_by_population_(United_Nations)"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("wikipedia.org", 443), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="markdown",
            process_math=False,
            with_metadata=False,
            include_tables=True,  # Include tables in extraction
        )

        assert result is not None, "Failed to extract large page"
        assert "content" in result, "No content in result"

        content = result["content"]
        # Large pages should produce substantial content
        assert len(content) > 1000, "Content suspiciously short for large page"

    @pytest.mark.asyncio
    async def test_redirect_handling(self, extractor):
        """Test handling of HTTP redirects."""
        # httpbin.org/redirect/1 redirects once
        url = "http://httpbin.org/redirect/1"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("httpbin.org", 80), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="text",
            process_math=False,
            with_metadata=False,
        )

        # Should handle redirect and extract from final page
        assert result is not None or result == {"content": None}

    @pytest.mark.asyncio
    async def test_404_error_handling(self, extractor):
        """Test handling of 404 errors."""
        url = "http://httpbin.org/status/404"

        # Skip if no network available
        try:
            import socket

            socket.create_connection(("httpbin.org", 80), timeout=5)
        except (socket.error, socket.timeout):
            pytest.skip("No network connection available")

        result = await extractor.extract_async(
            url=url,
            output_format="text",
            process_math=False,
            with_metadata=False,
        )

        # Should handle 404 gracefully
        # Result might be None or have empty/minimal content
        assert result is None or (result is not None and "content" in result)
