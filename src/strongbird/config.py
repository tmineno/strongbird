"""Configuration classes for Strongbird."""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class BrowserConfig:
    """Browser configuration settings."""

    headless: bool = True
    browser_type: str = "chromium"
    viewport: Tuple[int, int] = (1920, 1080)
    user_agent: Optional[str] = None
    timeout: int = 30000
    javascript: bool = True
    images: bool = True

    @classmethod
    def from_cli_args(cls, **kwargs) -> "BrowserConfig":
        """Create BrowserConfig from CLI arguments."""
        # Parse viewport string
        viewport = (1920, 1080)
        if "viewport" in kwargs and kwargs["viewport"]:
            try:
                width, height = map(int, kwargs["viewport"].split("x"))
                viewport = (width, height)
            except ValueError:
                pass  # Use default

        return cls(
            headless=kwargs.get("headless", True),
            browser_type=kwargs.get("browser", "chromium"),
            viewport=viewport,
            user_agent=kwargs.get("user_agent"),
            timeout=kwargs.get("timeout", 30000),
            javascript=not kwargs.get("no_javascript", False),
            images=not kwargs.get("no_images", False),
        )


@dataclass
class ExtractionConfig:
    """Content extraction configuration."""

    output_format: str = "markdown"
    include_comments: bool = False
    include_tables: bool = True
    include_links: bool = False
    include_images: bool = False
    include_formatting: bool = False
    process_math: bool = False
    deduplicate: bool = True
    target_lang: Optional[str] = None
    with_metadata: bool = True
    favor_precision: bool = False

    @classmethod
    def from_cli_args(cls, **kwargs) -> "ExtractionConfig":
        """Create ExtractionConfig from CLI arguments."""
        return cls(
            output_format=kwargs.get("format", "markdown"),
            include_comments=kwargs.get("include_comments", False),
            include_tables=not kwargs.get("no_tables", False),
            include_links=kwargs.get("include_links", False),
            include_images=kwargs.get("include_images", False),
            include_formatting=kwargs.get("include_formatting", False),
            process_math=kwargs.get("process_math", False),
            deduplicate=not kwargs.get("no_deduplicate", False),
            target_lang=kwargs.get("target_lang"),
            with_metadata=kwargs.get("with_metadata", True),
            favor_precision=kwargs.get("favor_precision", False),
        )


@dataclass
class PlaywrightConfig:
    """Playwright-specific page interaction configuration."""

    wait_for_selector: Optional[str] = None
    scroll_to_bottom: bool = False
    wait_time: int = 0
    execute_script: Optional[str] = None

    @classmethod
    def from_cli_args(cls, **kwargs) -> "PlaywrightConfig":
        """Create PlaywrightConfig from CLI arguments."""
        return cls(
            wait_for_selector=kwargs.get("wait_for"),
            scroll_to_bottom=kwargs.get("scroll", False),
            wait_time=kwargs.get("wait_time", 0),
            execute_script=kwargs.get("execute_script"),
        )


@dataclass
class CrawlConfig:
    """Web crawling configuration."""

    max_depth: int = 0
    max_pages: int = 10
    delay: float = 1.0
    same_domain_only: bool = True
    respect_robots_txt: bool = True

    @classmethod
    def from_cli_args(cls, **kwargs) -> "CrawlConfig":
        """Create CrawlConfig from CLI arguments."""
        return cls(
            max_depth=kwargs.get("crawl_depth", 0),
            max_pages=kwargs.get("max_pages", 10),
            delay=kwargs.get("crawl_delay", 1.0),
            same_domain_only=kwargs.get("same_domain_only", True),
            respect_robots_txt=kwargs.get("respect_robots_txt", True),
        )


@dataclass
class OutputConfig:
    """Output handling configuration."""

    output_path: Optional[str] = None
    screenshot_path: Optional[str] = None
    quiet: bool = False

    @classmethod
    def from_cli_args(cls, **kwargs) -> "OutputConfig":
        """Create OutputConfig from CLI arguments."""
        return cls(
            output_path=kwargs.get("output"),
            screenshot_path=kwargs.get("screenshot"),
            quiet=kwargs.get("quiet", False),
        )


class ConfigBuilder:
    """Build all configuration objects from CLI arguments."""

    @staticmethod
    def build_all_configs(
        **kwargs,
    ) -> Tuple[
        BrowserConfig, ExtractionConfig, PlaywrightConfig, CrawlConfig, OutputConfig
    ]:
        """
        Build all configuration objects from CLI arguments.

        Returns:
            Tuple of all configuration objects
        """
        return (
            BrowserConfig.from_cli_args(**kwargs),
            ExtractionConfig.from_cli_args(**kwargs),
            PlaywrightConfig.from_cli_args(**kwargs),
            CrawlConfig.from_cli_args(**kwargs),
            OutputConfig.from_cli_args(**kwargs),
        )
