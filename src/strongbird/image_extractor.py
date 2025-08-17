"""Image extraction and download module for Strongbird."""

import asyncio
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup


class ImageExtractor:
    """Extract and download images from web pages."""

    def __init__(self, download_timeout: int = 30, max_retries: int = 2):
        """
        Initialize image extractor.

        Args:
            download_timeout: Timeout for image downloads in seconds
            max_retries: Maximum number of retry attempts for downloads
        """
        self.download_timeout = download_timeout
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.download_timeout)
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def extract_image_urls(
        self, html_content: str, base_url: str
    ) -> List[Dict[str, str]]:
        """
        Extract image URLs from HTML content.

        Args:
            html_content: HTML content to extract images from
            base_url: Base URL to resolve relative URLs

        Returns:
            List of image dictionaries with url, alt, title, and local_filename
        """
        # Ensure base_url ends with / if it's not a file
        # This helps urljoin correctly resolve relative URLs
        if not base_url.endswith("/"):
            # Check if URL looks like a file (has common file extension)
            parsed = urlparse(base_url)
            path = parsed.path
            if not any(
                path.endswith(ext) for ext in [".html", ".htm", ".php", ".asp", ".jsp"]
            ):
                # Appears to be a directory, add trailing slash
                base_url = base_url + "/"

        soup = BeautifulSoup(html_content, "html.parser")
        images = []
        seen_urls: Set[str] = set()

        # Find all img tags
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src:
                continue

            # Resolve relative URLs
            absolute_url = urljoin(base_url, src)

            # Skip data URLs and duplicates
            if absolute_url.startswith("data:") or absolute_url in seen_urls:
                continue

            seen_urls.add(absolute_url)

            # Generate local filename
            local_filename = self._generate_filename(absolute_url)

            images.append(
                {
                    "url": absolute_url,
                    "alt": img.get("alt", ""),
                    "title": img.get("title", ""),
                    "local_filename": local_filename,
                    "original_src": src,
                }
            )

        return images

    def _generate_filename(self, url: str) -> str:
        """
        Generate a unique filename for an image URL.

        Args:
            url: Image URL

        Returns:
            Generated filename
        """
        # Parse URL to get original filename
        parsed = urlparse(url)
        path = parsed.path
        original_name = Path(path).name if path else "image"

        # Remove query parameters and get extension
        base_name = original_name.split("?")[0]
        if "." in base_name:
            name, ext = base_name.rsplit(".", 1)
        else:
            name, ext = base_name, "jpg"

        # Create hash from URL for uniqueness
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

        # Clean filename
        name = re.sub(r"[^\w\-_.]", "_", name)[:50]  # Limit length
        ext = re.sub(r"[^\w]", "", ext.lower())[:10]  # Clean extension

        # Ensure we have a valid extension
        if not ext:
            ext = "jpg"

        return f"{name}_{url_hash}.{ext}"

    async def download_images(
        self,
        images: List[Dict[str, str]],
        img_folder: Path,
        concurrent_limit: int = 5,
    ) -> Dict[str, str]:
        """
        Download images to the specified folder.

        Args:
            images: List of image dictionaries from extract_image_urls
            img_folder: Directory to save images
            concurrent_limit: Maximum concurrent downloads

        Returns:
            Dictionary mapping original URLs to local relative paths
        """
        if not self.session:
            raise RuntimeError("ImageExtractor must be used as async context manager")

        # Create img folder
        img_folder.mkdir(parents=True, exist_ok=True)

        # Create semaphore for limiting concurrent downloads
        semaphore = asyncio.Semaphore(concurrent_limit)

        # Download tasks
        tasks = []
        for image in images:
            task = self._download_single_image(semaphore, image, img_folder)
            tasks.append(task)

        # Execute downloads concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build URL mapping
        url_mapping = {}
        for image, result in zip(images, results):
            if isinstance(result, Exception):
                print(f"Warning: Failed to download {image['url']}: {result}")
                continue

            if result:  # Successful download
                # Store relative path for Markdown links
                relative_path = f"img/{image['local_filename']}"
                url_mapping[image["url"]] = relative_path
                # Also map original src for replacement
                url_mapping[image["original_src"]] = relative_path

        return url_mapping

    async def _download_single_image(
        self,
        semaphore: asyncio.Semaphore,
        image: Dict[str, str],
        img_folder: Path,
    ) -> Optional[str]:
        """
        Download a single image with retry logic.

        Args:
            semaphore: Semaphore for concurrency control
            image: Image dictionary
            img_folder: Directory to save image

        Returns:
            Local filename if successful, None if failed
        """
        async with semaphore:
            for attempt in range(self.max_retries + 1):
                try:
                    async with self.session.get(image["url"]) as response:
                        if response.status == 200:
                            content = await response.read()
                            file_path = img_folder / image["local_filename"]

                            with open(file_path, "wb") as f:
                                f.write(content)

                            return image["local_filename"]
                        else:
                            if attempt == self.max_retries:
                                raise aiohttp.ClientError(f"HTTP {response.status}")

                except Exception as e:
                    if attempt == self.max_retries:
                        raise e
                    await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff

        return None

    async def extract_and_download_images(
        self,
        html_content: str,
        base_url: str,
        img_folder: Path,
        concurrent_limit: int = 5,
    ) -> Tuple[List[Dict[str, str]], Dict[str, str]]:
        """
        Extract and download images in one operation.

        Args:
            html_content: HTML content to extract images from
            base_url: Base URL to resolve relative URLs
            img_folder: Directory to save images
            concurrent_limit: Maximum concurrent downloads

        Returns:
            Tuple of (extracted_images, url_mapping)
        """
        # Extract image URLs
        images = self.extract_image_urls(html_content, base_url)

        if not images:
            return [], {}

        # Download images
        url_mapping = await self.download_images(images, img_folder, concurrent_limit)

        return images, url_mapping
