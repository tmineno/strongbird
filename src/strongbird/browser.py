"""Browser management module for Playwright."""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from playwright.async_api import Browser, Page, async_playwright


class BrowserManager:
    """Manages Playwright browser instances and pages."""

    def __init__(
        self,
        headless: bool = True,
        browser_type: str = "chromium",
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        user_agent: Optional[str] = None,
        timeout: int = 30000,
        wait_until: str = "networkidle",
        javascript: bool = True,
        images: bool = True,
        cookies: Optional[list] = None,
    ):
        """
        Initialize browser manager.

        Args:
            headless: Run browser in headless mode
            browser_type: Browser to use (chromium, firefox, webkit)
            viewport_width: Viewport width
            viewport_height: Viewport height
            user_agent: Custom user agent string
            timeout: Default timeout in milliseconds
            wait_until: Wait strategy (load, domcontentloaded, networkidle)
            javascript: Enable JavaScript
            images: Load images
            cookies: List of cookies to set
        """
        self.headless = headless
        self.browser_type = browser_type
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.user_agent = user_agent or self._default_user_agent()
        self.timeout = timeout
        self.wait_until = wait_until
        self.javascript = javascript
        self.images = images
        self.cookies = cookies or []

    def _default_user_agent(self) -> str:
        """Return default user agent string."""
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    @asynccontextmanager
    async def get_browser(self):
        """Context manager for browser instance."""
        async with async_playwright() as p:
            browser_launcher = getattr(p, self.browser_type)

            launch_options = {
                "headless": self.headless,
            }

            # Add browser-specific options
            if self.browser_type == "chromium":
                launch_options["args"] = [
                    "--disable-blink-features=AutomationControlled",
                    "--disable-dev-shm-usage",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ]

            browser = await browser_launcher.launch(**launch_options)

            try:
                yield browser
            finally:
                await browser.close()

    @asynccontextmanager
    async def get_page(self, browser: Browser):
        """Context manager for page instance."""
        context_options = {
            "viewport": {
                "width": self.viewport_width,
                "height": self.viewport_height,
            },
            "user_agent": self.user_agent,
            "java_script_enabled": self.javascript,
        }

        # Disable images if requested
        if not self.images:
            context_options["bypass_csp"] = True

        context = await browser.new_context(**context_options)

        # Set cookies if provided
        if self.cookies:
            await context.add_cookies(self.cookies)

        page = await context.new_page()
        page.set_default_timeout(self.timeout)

        # Block image requests if images are disabled
        if not self.images:
            await page.route(
                "**/*",
                lambda route: (
                    route.abort()
                    if route.request.resource_type == "image"
                    else route.continue_()
                ),
            )

        try:
            yield page
        finally:
            await page.close()
            await context.close()

    async def fetch_html(
        self,
        url: str,
        wait_for_selector: Optional[str] = None,
        scroll_to_bottom: bool = False,
        wait_time: int = 0,
        execute_script: Optional[str] = None,
        process_math: bool = False,
    ) -> str:
        """
        Fetch HTML content from URL using Playwright.

        Args:
            url: URL to fetch
            wait_for_selector: CSS selector to wait for
            scroll_to_bottom: Scroll to bottom of page
            wait_time: Additional wait time in milliseconds
            execute_script: JavaScript to execute before getting HTML
            process_math: Process mathematical equations to TeX format

        Returns:
            HTML content as string
        """
        async with self.get_browser() as browser:
            async with self.get_page(browser) as page:
                # Navigate to URL
                await page.goto(url, wait_until=self.wait_until)

                # Wait for specific selector if provided
                if wait_for_selector:
                    await page.wait_for_selector(
                        wait_for_selector, timeout=self.timeout
                    )

                # Execute custom JavaScript if provided
                if execute_script:
                    await page.evaluate(execute_script)

                # Scroll to bottom if requested
                if scroll_to_bottom:
                    await self._scroll_to_bottom(page)

                # Additional wait time
                if wait_time > 0:
                    await asyncio.sleep(wait_time / 1000)

                # Process math equations if requested
                if process_math:
                    from .math import MathProcessor

                    math_processor = MathProcessor()
                    await math_processor.normalize_math_equations(page)

                # Get page content
                html = await page.content()

                return html

    async def _scroll_to_bottom(self, page: Page, step: int = 500):
        """
        Scroll page to bottom to trigger lazy loading.

        Args:
            page: Playwright page instance
            step: Scroll step in pixels
        """
        previous_height = 0
        current_height = await page.evaluate("document.body.scrollHeight")

        while current_height != previous_height:
            previous_height = current_height

            # Scroll down by steps
            for y in range(0, current_height, step):
                await page.evaluate(f"window.scrollTo(0, {y})")
                await asyncio.sleep(0.1)

            # Wait for new content to load
            await asyncio.sleep(0.5)
            current_height = await page.evaluate("document.body.scrollHeight")

    async def take_screenshot(
        self,
        url: str,
        path: str,
        full_page: bool = True,
        wait_for_selector: Optional[str] = None,
    ):
        """
        Take screenshot of webpage.

        Args:
            url: URL to screenshot
            path: Path to save screenshot
            full_page: Capture full page
            wait_for_selector: CSS selector to wait for
        """
        async with self.get_browser() as browser:
            async with self.get_page(browser) as page:
                await page.goto(url, wait_until=self.wait_until)

                if wait_for_selector:
                    await page.wait_for_selector(
                        wait_for_selector, timeout=self.timeout
                    )

                await page.screenshot(path=path, full_page=full_page)

    @asynccontextmanager
    async def get_page_pool(self, pool_size: int):
        """
        Context manager for managing a pool of pages within a single browser context.

        Args:
            pool_size: Number of pages to create in the pool

        Yields:
            Tuple of (context, list_of_pages)
        """
        async with self.get_browser() as browser:
            context_options = {
                "viewport": {
                    "width": self.viewport_width,
                    "height": self.viewport_height,
                },
                "user_agent": self.user_agent,
                "java_script_enabled": self.javascript,
            }

            # Disable images if requested
            if not self.images:
                context_options["bypass_csp"] = True

            context = await browser.new_context(**context_options)

            # Set cookies if provided
            if self.cookies:
                await context.add_cookies(self.cookies)

            # Create pool of pages
            pages = []
            try:
                for _ in range(pool_size):
                    page = await context.new_page()
                    page.set_default_timeout(self.timeout)

                    # Block image requests if images are disabled
                    if not self.images:
                        await page.route(
                            "**/*",
                            lambda route: (
                                route.abort()
                                if route.request.resource_type == "image"
                                else route.continue_()
                            ),
                        )

                    pages.append(page)

                yield context, pages

            finally:
                # Clean up all pages
                for page in pages:
                    await page.close()
                await context.close()

    async def fetch_html_with_page(
        self,
        page: Page,
        url: str,
        wait_for_selector: Optional[str] = None,
        scroll_to_bottom: bool = False,
        wait_time: int = 0,
        execute_script: Optional[str] = None,
        process_math: bool = False,
    ) -> str:
        """
        Fetch HTML content from URL using an existing page instance.

        Args:
            page: Existing page instance to use
            url: URL to fetch
            wait_for_selector: CSS selector to wait for
            scroll_to_bottom: Scroll to bottom of page
            wait_time: Additional wait time in milliseconds
            execute_script: JavaScript to execute before getting HTML
            process_math: Process mathematical equations to TeX format

        Returns:
            HTML content as string
        """
        # Navigate to URL
        await page.goto(url, wait_until=self.wait_until)

        # Wait for specific selector if provided
        if wait_for_selector:
            await page.wait_for_selector(wait_for_selector, timeout=self.timeout)

        # Execute custom JavaScript if provided
        if execute_script:
            await page.evaluate(execute_script)

        # Process mathematical equations if requested
        if process_math:
            from .math import MathProcessor

            processor = MathProcessor()
            await processor.normalize_math_equations(page)

        # Scroll to bottom if requested
        if scroll_to_bottom:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Additional wait time if specified
        if wait_time > 0:
            await page.wait_for_timeout(wait_time)

        # Get the final HTML content
        return await page.content()
