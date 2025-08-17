"""Web crawler module for multi-page content extraction."""

import asyncio
import time
from collections import deque
from typing import Any, Dict, List, Set
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

from bs4 import BeautifulSoup

from .extractor import StrongbirdExtractor


class WebCrawler:
    """Web crawler for extracting content from multiple linked pages."""

    def __init__(
        self,
        extractor: StrongbirdExtractor,
        max_depth: int = 1,
        max_pages: int = 10,
        delay: float = 1.0,
        respect_robots_txt: bool = True,
        same_domain_only: bool = True,
        include_external_links: bool = False,
    ):
        """
        Initialize the web crawler.

        Args:
            extractor: StrongbirdExtractor instance for content extraction
            max_depth: Maximum crawling depth (0 = seed page only)
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
            respect_robots_txt: Whether to respect robots.txt
            same_domain_only: Only crawl pages on the same domain
            include_external_links: Include external links in extraction
        """
        self.extractor = extractor
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.respect_robots_txt = respect_robots_txt
        self.same_domain_only = same_domain_only
        self.include_external_links = include_external_links

        # Crawling state
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.last_request_time: Dict[str, float] = {}

    async def crawl_async(
        self, seed_url: str, **extract_kwargs
    ) -> List[Dict[str, Any]]:
        """
        Crawl pages starting from seed URL.

        Args:
            seed_url: Starting URL for crawling
            **extract_kwargs: Additional arguments for extraction

        Returns:
            List of extracted content from all crawled pages
        """
        # Initialize crawling queue: (url, depth)
        crawl_queue = deque([(seed_url, 0)])
        results = []

        # Parse seed domain for domain filtering
        seed_domain = urlparse(seed_url).netloc

        while crawl_queue and len(results) < self.max_pages:
            current_url, current_depth = crawl_queue.popleft()

            # Skip if already visited
            if current_url in self.visited_urls:
                continue

            # Skip if depth exceeded
            if current_depth > self.max_depth:
                continue

            # Skip if domain filtering is enabled and URL is external
            if self.same_domain_only:
                current_domain = urlparse(current_url).netloc
                if current_domain != seed_domain:
                    continue

            # Check robots.txt
            if self.respect_robots_txt and not await self._can_fetch(current_url):
                continue

            # Respect delay
            await self._respect_delay(current_url)

            # Extract content from current page
            try:
                result = await self.extractor.extract_async(
                    url=current_url, **extract_kwargs
                )

                if result:
                    result["crawl_depth"] = current_depth
                    result["crawl_order"] = len(results) + 1
                    results.append(result)

                    # Mark as visited
                    self.visited_urls.add(current_url)

                    # Find links for next depth level
                    if current_depth < self.max_depth:
                        links = await self._extract_links(
                            current_url, result.get("content", "")
                        )

                        # Add links to queue for next depth
                        for link in links:
                            if link not in self.visited_urls:
                                crawl_queue.append((link, current_depth + 1))
                else:
                    # Mark as visited even if extraction failed to avoid infinite loops
                    self.visited_urls.add(current_url)
                    print(f"Warning: No content extracted from {current_url}")

            except Exception as e:
                # Log error but continue crawling
                print(f"Error extracting from {current_url}: {e}")
                # Mark as visited to avoid retrying
                self.visited_urls.add(current_url)
                continue

        return results

    def crawl(self, seed_url: str, **extract_kwargs) -> List[Dict[str, Any]]:
        """Synchronous wrapper for crawl_async."""
        return asyncio.run(self.crawl_async(seed_url, **extract_kwargs))

    async def _extract_links(self, base_url: str, content: str) -> List[str]:
        """
        Extract links from page content.

        Args:
            base_url: Base URL for resolving relative links
            content: Page content (HTML or extracted text)

        Returns:
            List of absolute URLs found in the content
        """
        links = []

        # If content is extracted text/markdown, we need to get the original HTML
        # For now, we'll fetch the HTML again to extract links
        try:
            if self.extractor.use_playwright:
                html_content = await self.extractor.browser_manager.fetch_html(
                    url=base_url,
                    process_math=False,  # Don't need math processing for link extraction
                )
            else:
                import trafilatura

                html_content = trafilatura.fetch_url(base_url)

            if html_content:
                soup = BeautifulSoup(html_content, "html.parser")

                # Extract links from anchor tags
                for link in soup.find_all("a", href=True):
                    href = link["href"].strip()
                    if href and not href.startswith(("#", "javascript:", "mailto:")):
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(base_url, href)

                        # Clean URL (remove fragments)
                        parsed = urlparse(absolute_url)
                        clean_url = urlunparse(
                            (
                                parsed.scheme,
                                parsed.netloc,
                                parsed.path,
                                parsed.params,
                                parsed.query,
                                "",
                            )
                        )

                        # Basic URL validation
                        if self._is_valid_url(clean_url):
                            links.append(clean_url)

        except Exception as e:
            print(f"Error extracting links from {base_url}: {e}")

        return list(set(links))  # Remove duplicates

    def _is_valid_url(self, url: str) -> bool:
        """
        Validate if URL is crawlable.

        Args:
            url: URL to validate

        Returns:
            True if URL is valid for crawling
        """
        try:
            parsed = urlparse(url)

            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False

            # Only HTTP/HTTPS
            if parsed.scheme not in ("http", "https"):
                return False

            # Skip common non-content files
            excluded_extensions = {
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".ppt",
                ".pptx",
                ".zip",
                ".rar",
                ".tar",
                ".gz",
                ".exe",
                ".dmg",
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".svg",
                ".ico",
                ".mp3",
                ".mp4",
                ".avi",
                ".mov",
                ".wmv",
                ".flv",
                ".css",
                ".js",
                ".xml",
                ".rss",
                ".json",
            }

            path_lower = parsed.path.lower()
            for ext in excluded_extensions:
                if path_lower.endswith(ext):
                    return False

            return True

        except Exception:
            return False

    async def _can_fetch(self, url: str) -> bool:
        """
        Check if URL can be fetched according to robots.txt.

        Args:
            url: URL to check

        Returns:
            True if URL can be fetched
        """
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"

            # Get robots.txt parser for domain
            if domain not in self.robots_cache:
                rp = RobotFileParser()
                robots_url = urljoin(domain, "/robots.txt")
                rp.set_url(robots_url)

                try:
                    rp.read()
                    self.robots_cache[domain] = rp
                except Exception:
                    # If can't fetch robots.txt, assume allowed
                    return True

            rp = self.robots_cache[domain]
            return rp.can_fetch("*", url)

        except Exception:
            # If error checking robots.txt, assume allowed
            return True

    async def _respect_delay(self, url: str) -> None:
        """
        Implement polite crawling delay.

        Args:
            url: URL being accessed
        """
        parsed = urlparse(url)
        domain = parsed.netloc

        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.delay:
                await asyncio.sleep(self.delay - elapsed)

        self.last_request_time[domain] = time.time()


class CrawlResults:
    """Container for crawl results with aggregation capabilities."""

    def __init__(self, results: List[Dict[str, Any]]):
        """
        Initialize crawl results.

        Args:
            results: List of extraction results from crawler
        """
        self.results = results

    def get_all_content(self, format_type: str = "markdown") -> str:
        """
        Get aggregated content from all crawled pages.

        Args:
            format_type: Output format for aggregation

        Returns:
            Combined content from all pages
        """
        if not self.results:
            return ""

        contents = []
        for result in self.results:
            if result.get("content"):
                # Add page header
                url = result.get("url", "Unknown URL")
                depth = result.get("crawl_depth", 0)
                order = result.get("crawl_order", 0)

                if format_type == "markdown":
                    header = f"\n\n# Page {order} (Depth {depth}): {url}\n\n"
                else:
                    header = f"\n\nPage {order} (Depth {depth}): {url}\n{'='*50}\n\n"

                contents.append(header + result["content"])

        return "\n".join(contents)

    def get_page_count(self) -> int:
        """Get total number of crawled pages."""
        return len(self.results)

    def get_urls(self) -> List[str]:
        """Get list of all crawled URLs."""
        return [result.get("url", "") for result in self.results if result.get("url")]

    def get_by_depth(self, depth: int) -> List[Dict[str, Any]]:
        """Get results from specific crawl depth."""
        return [r for r in self.results if r.get("crawl_depth") == depth]

    def get_metadata_summary(self) -> Dict[str, Any]:
        """Get summary of metadata from all pages."""
        summary = {
            "total_pages": len(self.results),
            "depths": {},
            "domains": set(),
            "titles": [],
        }

        for result in self.results:
            # Count by depth
            depth = result.get("crawl_depth", 0)
            summary["depths"][depth] = summary["depths"].get(depth, 0) + 1

            # Collect domains
            url = result.get("url", "")
            if url:
                domain = urlparse(url).netloc
                summary["domains"].add(domain)

            # Collect titles
            metadata = result.get("metadata", {})
            if metadata and metadata.get("title"):
                summary["titles"].append(metadata["title"])

        summary["domains"] = list(summary["domains"])
        return summary
