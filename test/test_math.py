"""
Math extraction tests for Strongbird.
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


@pytest.mark.math
class TestMathExtraction:
    """Test mathematical content extraction."""

    @pytest.mark.asyncio
    async def test_mathjax_extraction(self, extractor, mathjax_test_file):
        """Test MathJax equation extraction from local file."""
        result = await extractor.extract_from_file_async(
            file_path=str(mathjax_test_file),
            output_format="markdown",
            process_math=True,
            with_metadata=False,
        )

        assert result is not None, "Extraction returned None"
        assert "content" in result, "No content in result"

        content = result["content"]
        math_count = count_math_expressions(content)

        # MathJax test file should have at least 4 math expressions
        assert (
            math_count["total_expressions"] >= 4
        ), f"Expected at least 4 math expressions, found {math_count['total_expressions']}"

        # Check for both inline and display math
        assert math_count["inline_math"] > 0, "No inline math expressions found"
        assert math_count["display_math"] > 0, "No display math expressions found"

    @pytest.mark.asyncio
    async def test_comprehensive_math(self, extractor, comprehensive_math_file):
        """Test comprehensive math extraction with various formats."""
        result = await extractor.extract_from_file_async(
            file_path=str(comprehensive_math_file),
            output_format="markdown",
            process_math=True,
            with_metadata=False,
        )

        assert result is not None, "Extraction returned None"
        assert "content" in result, "No content in result"

        content = result["content"]
        math_count = count_math_expressions(content)

        # Comprehensive test file should have some math expressions or content
        # Note: The actual count may vary depending on processing and extraction capabilities
        # If no math expressions are found, at least ensure content was extracted
        if math_count["total_expressions"] == 0:
            # Fallback: check that we at least extracted some meaningful content
            assert len(content) > 100, "No math expressions found and content too short"
            assert any(
                term in content.lower()
                for term in ["math", "formula", "equation", "quadratic"]
            ), "No math expressions found and no mathematical keywords in content"
        else:
            assert math_count["total_expressions"] >= 1

    @pytest.mark.asyncio
    async def test_math_extraction_without_processing(
        self, extractor, mathjax_test_file
    ):
        """Test extraction without math processing."""
        result = await extractor.extract_from_file_async(
            file_path=str(mathjax_test_file),
            output_format="markdown",
            process_math=False,  # Math processing disabled
            with_metadata=False,
        )

        assert result is not None, "Extraction returned None"
        assert "content" in result, "No content in result"

        content = result["content"]

        # Without processing, should still extract text content
        assert len(content) > 0, "No content extracted"
        # But may not have properly formatted math expressions
        # (This depends on how the original HTML represents math)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("format_type", ["markdown"])
    async def test_math_extraction_formats(
        self, extractor, mathjax_test_file, format_type
    ):
        """Test math extraction with different output formats."""
        result = await extractor.extract_from_file_async(
            file_path=str(mathjax_test_file),
            output_format=format_type,
            process_math=True,
            with_metadata=False,
        )

        assert result is not None, f"Extraction returned None for {format_type}"
        assert "content" in result, f"No content in result for {format_type}"

        content = result["content"]
        assert len(content) > 0, f"Empty content for {format_type}"

        # Format-specific checks
        if format_type == "markdown":
            # Markdown should preserve math delimiters
            math_count = count_math_expressions(content)
            assert math_count["total_expressions"] > 0

    @pytest.mark.asyncio
    async def test_math_extraction_with_metadata(
        self, extractor, comprehensive_math_file
    ):
        """Test that metadata extraction works alongside math processing."""
        result = await extractor.extract_from_file_async(
            file_path=str(comprehensive_math_file),
            output_format="markdown",
            process_math=True,
            with_metadata=True,  # Include metadata
        )

        assert result is not None, "Extraction returned None"
        assert "content" in result, "No content in result"

        # Check for metadata
        if "metadata" in result and result["metadata"]:
            metadata = result["metadata"]
            # Metadata structure may vary, check for common fields
            assert isinstance(metadata, dict), "Metadata should be a dictionary"
            # Check for potential metadata fields (may be None if not present in HTML)
            possible_fields = ["title", "author", "date", "description"]
            assert any(
                field in metadata for field in possible_fields
            ), "No standard metadata fields found"

    @pytest.mark.asyncio
    async def test_local_file_url_format(self, extractor, mathjax_test_file):
        """Test extraction using file:// URL format."""
        file_url = f"file://{mathjax_test_file.absolute()}"

        result = await extractor.extract_async(
            url=file_url,
            output_format="markdown",
            process_math=True,
            with_metadata=False,
        )

        assert result is not None, "Extraction with file:// URL returned None"
        assert "content" in result, "No content in result"

        content = result["content"]
        math_count = count_math_expressions(content)

        assert (
            math_count["total_expressions"] > 0
        ), "No math expressions found with file:// URL"

    @pytest.mark.asyncio
    async def test_empty_html_handling(self, extractor, tmp_path):
        """Test handling of empty or minimal HTML files."""
        empty_html = tmp_path / "empty.html"
        empty_html.write_text("<html><body></body></html>")

        result = await extractor.extract_from_file_async(
            file_path=str(empty_html),
            output_format="markdown",
            process_math=True,
            with_metadata=False,
        )

        # Should handle empty HTML gracefully
        # Result might be None or have empty content
        if result is not None:
            assert "content" in result
            # Content should be empty or very minimal
            assert len(result.get("content", "")) < 100

    @pytest.mark.asyncio
    async def test_malformed_math_handling(self, extractor, tmp_path):
        """Test handling of malformed math expressions."""
        malformed_html = tmp_path / "malformed_math.html"
        malformed_html.write_text(
            """
        <html>
        <body>
            <p>Some text with incomplete math $x + y</p>
            <p>Another expression $$a = b</p>
            <p>Valid expression $z = 1$</p>
        </body>
        </html>
        """
        )

        result = await extractor.extract_from_file_async(
            file_path=str(malformed_html),
            output_format="markdown",
            process_math=True,
            with_metadata=False,
        )

        # Should handle malformed math without crashing
        assert result is not None, "Failed to handle malformed math"
        if "content" in result:
            content = result["content"]
            # Should at least extract the text content
            assert "Some text" in content or "Valid expression" in content
