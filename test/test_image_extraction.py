"""Tests for image extraction functionality."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from strongbird.image_extractor import ImageExtractor


class TestImageExtractor:
    """Test the ImageExtractor class."""

    def test_extract_image_urls_basic(self):
        """Test basic image URL extraction from HTML."""
        html_content = """
        <html>
        <body>
            <h1>Test Page</h1>
            <img src="https://example.com/image1.jpg" alt="Test image" title="Image 1">
            <p>Some text</p>
            <img src="/relative/image2.png" alt="Another image">
            <figure>
                <img src="https://example.com/figure.jpg" alt="Figure">
                <figcaption>Caption</figcaption>
            </figure>
        </body>
        </html>
        """

        extractor = ImageExtractor()
        images = extractor.extract_image_urls(html_content, "https://example.com/page")

        assert len(images) == 3

        # Check first image
        assert images[0]["url"] == "https://example.com/image1.jpg"
        assert images[0]["alt"] == "Test image"
        assert images[0]["title"] == "Image 1"
        assert images[0]["original_src"] == "https://example.com/image1.jpg"

        # Check relative URL resolution
        assert images[1]["url"] == "https://example.com/relative/image2.png"
        assert images[1]["alt"] == "Another image"
        assert images[1]["original_src"] == "/relative/image2.png"

        # Check figure image
        assert images[2]["url"] == "https://example.com/figure.jpg"
        assert images[2]["alt"] == "Figure"

    def test_extract_image_urls_skip_data_urls(self):
        """Test that data URLs are skipped."""
        html_content = """
        <html>
        <body>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA" alt="Base64 image">
            <img src="https://example.com/real.jpg" alt="Real image">
        </body>
        </html>
        """

        extractor = ImageExtractor()
        images = extractor.extract_image_urls(html_content, "https://example.com/page")

        assert len(images) == 1
        assert images[0]["url"] == "https://example.com/real.jpg"

    def test_extract_image_urls_skip_duplicates(self):
        """Test that duplicate URLs are skipped."""
        html_content = """
        <html>
        <body>
            <img src="https://example.com/image.jpg" alt="First">
            <img src="https://example.com/image.jpg" alt="Duplicate">
            <img src="https://example.com/other.jpg" alt="Different">
        </body>
        </html>
        """

        extractor = ImageExtractor()
        images = extractor.extract_image_urls(html_content, "https://example.com/page")

        assert len(images) == 2
        assert images[0]["url"] == "https://example.com/image.jpg"
        assert images[1]["url"] == "https://example.com/other.jpg"

    def test_generate_filename(self):
        """Test filename generation from URLs."""
        extractor = ImageExtractor()

        # Test with normal URL
        filename = extractor._generate_filename("https://example.com/images/photo.jpg")
        assert filename.endswith(".jpg")
        assert "photo" in filename
        assert len(filename.split("_")[-1].split(".")[0]) == 8  # Hash length

        # Test with query parameters
        filename = extractor._generate_filename(
            "https://example.com/photo.jpg?size=large&format=webp"
        )
        assert filename.endswith(".jpg")
        assert "photo" in filename

        # Test with no extension
        filename = extractor._generate_filename("https://example.com/images/photo")
        assert filename.endswith(".jpg")  # Default extension

        # Test with special characters in filename but valid extension
        filename = extractor._generate_filename("https://example.com/my%20photo.png")
        assert filename.endswith(".png")
        assert "my" in filename

    @pytest.mark.asyncio
    async def test_download_images_success(self):
        """Test successful image download."""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_folder = Path(temp_dir) / "img"

            images = [
                {
                    "url": "https://example.com/image1.jpg",
                    "local_filename": "image1_12345678.jpg",
                    "original_src": "https://example.com/image1.jpg",
                }
            ]

            # Mock the HTTP response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read.return_value = b"fake image data"

            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response

                async with ImageExtractor() as extractor:
                    url_mapping = await extractor.download_images(images, img_folder)

                # Check results
                assert (
                    len(url_mapping) == 1
                )  # Same URL for both mappings when original_src == url
                assert (
                    url_mapping["https://example.com/image1.jpg"]
                    == "img/image1_12345678.jpg"
                )

                # Check file was created
                assert (img_folder / "image1_12345678.jpg").exists()
                assert (
                    img_folder / "image1_12345678.jpg"
                ).read_bytes() == b"fake image data"

    @pytest.mark.asyncio
    async def test_download_images_failure(self):
        """Test handling of download failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            img_folder = Path(temp_dir) / "img"

            images = [
                {
                    "url": "https://example.com/image1.jpg",
                    "local_filename": "image1_12345678.jpg",
                    "original_src": "https://example.com/image1.jpg",
                }
            ]

            # Mock a failed HTTP response
            mock_response = AsyncMock()
            mock_response.status = 404

            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_get.return_value.__aenter__.return_value = mock_response

                async with ImageExtractor() as extractor:
                    url_mapping = await extractor.download_images(images, img_folder)

                # Should return empty mapping for failed downloads
                assert len(url_mapping) == 0

                # File should not exist
                assert not (img_folder / "image1_12345678.jpg").exists()

    def test_no_images_in_html(self):
        """Test extraction from HTML with no images."""
        html_content = """
        <html>
        <body>
            <h1>No Images Here</h1>
            <p>Just text content</p>
        </body>
        </html>
        """

        extractor = ImageExtractor()
        images = extractor.extract_image_urls(html_content, "https://example.com/page")

        assert len(images) == 0

    def test_url_resolution_with_directory_base(self):
        """Test URL resolution when base URL looks like a directory."""
        html_content = """
        <html>
        <body>
            <img src="extracted/folder/image1.png" alt="Relative image">
            <img src="x1.png" alt="Simple relative">
        </body>
        </html>
        """

        extractor = ImageExtractor()

        # Test with URL that looks like a directory (no trailing slash, no extension)
        images = extractor.extract_image_urls(
            html_content, "https://arxiv.org/html/1706.03762v7"
        )

        assert len(images) == 2
        # Should resolve correctly with trailing slash added
        assert (
            images[0]["url"]
            == "https://arxiv.org/html/1706.03762v7/extracted/folder/image1.png"
        )
        assert images[1]["url"] == "https://arxiv.org/html/1706.03762v7/x1.png"

    def test_url_resolution_with_file_base(self):
        """Test URL resolution when base URL looks like a file."""
        html_content = """
        <html>
        <body>
            <img src="image1.png" alt="Relative image">
        </body>
        </html>
        """

        extractor = ImageExtractor()

        # Test with URL that looks like a file (has .html extension)
        images = extractor.extract_image_urls(
            html_content, "https://example.com/page.html"
        )

        assert len(images) == 1
        # Should resolve correctly without adding trailing slash
        assert images[0]["url"] == "https://example.com/image1.png"

    def test_url_resolution_with_trailing_slash(self):
        """Test URL resolution when base URL already has trailing slash."""
        html_content = """
        <html>
        <body>
            <img src="subfolder/image1.png" alt="Relative image">
        </body>
        </html>
        """

        extractor = ImageExtractor()

        # Test with URL that already has trailing slash
        images = extractor.extract_image_urls(html_content, "https://example.com/path/")

        assert len(images) == 1
        # Should resolve correctly
        assert images[0]["url"] == "https://example.com/path/subfolder/image1.png"
