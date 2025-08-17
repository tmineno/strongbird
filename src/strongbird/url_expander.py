#!/usr/bin/env python3
"""URL expansion module with curl-style globbing support."""

import re
import string
from typing import Iterator, List, Tuple
from urllib.parse import urlparse


class CurlGlobParser:
    """Parser for curl-style URL globbing patterns."""

    def __init__(self):
        """Initialize the parser."""
        # Regex patterns for detecting globbing
        self.numeric_range_pattern = re.compile(r"\[(\d+)-(\d+)(?::(\d+))?\]")
        self.alpha_range_pattern = re.compile(
            r"\[([a-z])-([a-z])\]|\[([A-Z])-([A-Z])\]"
        )
        self.list_pattern = re.compile(r"\{([^}]+)\}")

    def has_globbing_pattern(self, url: str) -> bool:
        """
        Check if URL contains any globbing patterns.

        Args:
            url: URL string to check

        Returns:
            True if URL contains globbing patterns
        """
        return (
            bool(self.numeric_range_pattern.search(url))
            or bool(self.alpha_range_pattern.search(url))
            or bool(self.list_pattern.search(url))
        )

    def parse_patterns(self, url: str) -> List[Tuple[str, str, dict]]:
        """
        Parse all globbing patterns in URL.

        Args:
            url: URL string containing patterns

        Returns:
            List of (pattern_string, pattern_type, pattern_data) tuples
        """
        patterns = []

        # Find numeric ranges
        for match in self.numeric_range_pattern.finditer(url):
            start, end, step = match.groups()
            pattern_data = {
                "start": int(start),
                "end": int(end),
                "step": int(step) if step else 1,
                "zero_pad": len(start),  # Detect zero padding from start digit count
            }
            patterns.append((match.group(0), "numeric_range", pattern_data))

        # Find alphabetic ranges
        for match in self.alpha_range_pattern.finditer(url):
            groups = match.groups()
            if groups[0] and groups[1]:  # lowercase range
                start_char, end_char = groups[0], groups[1]
            else:  # uppercase range
                start_char, end_char = groups[2], groups[3]

            pattern_data = {
                "start": start_char,
                "end": end_char,
                "case": "lower" if start_char.islower() else "upper",
            }
            patterns.append((match.group(0), "alpha_range", pattern_data))

        # Find list patterns
        for match in self.list_pattern.finditer(url):
            items = [item.strip() for item in match.group(1).split(",")]
            pattern_data = {"items": items}
            patterns.append((match.group(0), "list", pattern_data))

        return patterns


class PatternGenerator:
    """Generates values from parsed patterns."""

    @staticmethod
    def generate_numeric_range(
        start: int, end: int, step: int = 1, zero_pad: int = 0
    ) -> Iterator[str]:
        """
        Generate numeric sequence.

        Args:
            start: Starting number
            end: Ending number (inclusive)
            step: Step size
            zero_pad: Number of digits for zero padding

        Yields:
            Formatted number strings
        """
        for i in range(start, end + 1, step):
            if zero_pad > 0:
                yield str(i).zfill(zero_pad)
            else:
                yield str(i)

    @staticmethod
    def generate_alpha_range(
        start: str, end: str, case: str = "lower"
    ) -> Iterator[str]:
        """
        Generate alphabetic sequence.

        Args:
            start: Starting character
            end: Ending character (inclusive)
            case: 'lower' or 'upper'

        Yields:
            Character strings
        """
        if case == "lower":
            chars = string.ascii_lowercase
        else:
            chars = string.ascii_uppercase

        start_idx = chars.index(start)
        end_idx = chars.index(end)

        for i in range(start_idx, end_idx + 1):
            yield chars[i]

    @staticmethod
    def generate_list(items: List[str]) -> Iterator[str]:
        """
        Generate items from list.

        Args:
            items: List of items

        Yields:
            Items from the list
        """
        for item in items:
            yield item


class URLExpander:
    """Main URL expansion functionality."""

    def __init__(self):
        """Initialize the URL expander."""
        self.parser = CurlGlobParser()
        self.generator = PatternGenerator()

    def is_expandable_url(self, url: str) -> bool:
        """
        Check if URL can be expanded.

        Args:
            url: URL to check

        Returns:
            True if URL contains expandable patterns
        """
        return self.parser.has_globbing_pattern(url)

    def expand_url(self, url: str) -> List[str]:
        """
        Expand URL with globbing patterns into list of URLs.

        Args:
            url: URL containing globbing patterns

        Returns:
            List of expanded URLs
        """
        if not self.is_expandable_url(url):
            return [url]

        patterns = self.parser.parse_patterns(url)
        if not patterns:
            return [url]

        # Start with the original URL
        current_urls = [url]

        # Process each pattern in order
        for pattern_string, pattern_type, pattern_data in patterns:
            new_urls = []

            for current_url in current_urls:
                if pattern_string not in current_url:
                    new_urls.append(current_url)
                    continue

                # Generate values for this pattern
                if pattern_type == "numeric_range":
                    values = list(
                        self.generator.generate_numeric_range(
                            pattern_data["start"],
                            pattern_data["end"],
                            pattern_data["step"],
                            pattern_data["zero_pad"],
                        )
                    )
                elif pattern_type == "alpha_range":
                    values = list(
                        self.generator.generate_alpha_range(
                            pattern_data["start"],
                            pattern_data["end"],
                            pattern_data["case"],
                        )
                    )
                elif pattern_type == "list":
                    values = pattern_data["items"]
                else:
                    values = [pattern_string]  # Fallback

                # Replace pattern with each value
                for value in values:
                    new_url = current_url.replace(pattern_string, value, 1)
                    new_urls.append(new_url)

            current_urls = new_urls

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for url in current_urls:
            if url not in seen:
                seen.add(url)
                result.append(url)

        return result

    def validate_expanded_urls(self, urls: List[str]) -> List[str]:
        """
        Validate expanded URLs.

        Args:
            urls: List of URLs to validate

        Returns:
            List of valid URLs
        """
        valid_urls = []

        for url in urls:
            try:
                parsed = urlparse(url)
                if parsed.scheme and parsed.netloc:
                    valid_urls.append(url)
            except Exception:
                continue

        return valid_urls


def expand_urls(url: str, ignore_glob: bool = False) -> List[str]:
    """
    Convenience function to expand URLs.

    Args:
        url: URL that may contain globbing patterns
        ignore_glob: If True, disable globbing expansion

    Returns:
        List of expanded URLs (single URL if no patterns or if ignored)
    """
    if ignore_glob:
        return [url]

    expander = URLExpander()
    expanded = expander.expand_url(url)
    return expander.validate_expanded_urls(expanded)
