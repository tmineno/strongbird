#!/usr/bin/env python3
"""Test suite for URL expansion functionality."""

import pytest

from strongbird.url_expander import CurlGlobParser, URLExpander, expand_urls


class TestCurlGlobParser:
    """Test the curl glob pattern parser."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = CurlGlobParser()

    def test_has_globbing_pattern_numeric(self):
        """Test detection of numeric range patterns."""
        assert self.parser.has_globbing_pattern("http://example.com/[1-100].html")
        assert self.parser.has_globbing_pattern("http://example.com/[001-100].html")
        assert self.parser.has_globbing_pattern("http://example.com/[0-10:2].html")
        assert not self.parser.has_globbing_pattern("http://example.com/page.html")

    def test_has_globbing_pattern_alpha(self):
        """Test detection of alphabetic range patterns."""
        assert self.parser.has_globbing_pattern("http://example.com/[a-z].html")
        assert self.parser.has_globbing_pattern("http://example.com/[A-Z].html")
        assert not self.parser.has_globbing_pattern("http://example.com/page.html")

    def test_has_globbing_pattern_list(self):
        """Test detection of list patterns."""
        assert self.parser.has_globbing_pattern(
            "http://example.com/{one,two,three}.html"
        )
        assert self.parser.has_globbing_pattern("http://example.com/{a,b}.html")
        assert not self.parser.has_globbing_pattern("http://example.com/page.html")

    def test_parse_numeric_range_basic(self):
        """Test parsing basic numeric ranges."""
        patterns = self.parser.parse_patterns("http://example.com/[1-10].html")
        assert len(patterns) == 1
        pattern_str, pattern_type, data = patterns[0]
        assert pattern_str == "[1-10]"
        assert pattern_type == "numeric_range"
        assert data == {"start": 1, "end": 10, "step": 1, "zero_pad": 1}

    def test_parse_numeric_range_zero_pad(self):
        """Test parsing zero-padded numeric ranges."""
        patterns = self.parser.parse_patterns("http://example.com/[001-100].html")
        assert len(patterns) == 1
        pattern_str, pattern_type, data = patterns[0]
        assert pattern_str == "[001-100]"
        assert pattern_type == "numeric_range"
        assert data == {"start": 1, "end": 100, "step": 1, "zero_pad": 3}

    def test_parse_numeric_range_with_step(self):
        """Test parsing numeric ranges with step."""
        patterns = self.parser.parse_patterns("http://example.com/[0-10:2].html")
        assert len(patterns) == 1
        pattern_str, pattern_type, data = patterns[0]
        assert pattern_str == "[0-10:2]"
        assert pattern_type == "numeric_range"
        assert data == {"start": 0, "end": 10, "step": 2, "zero_pad": 1}

    def test_parse_alpha_range_lowercase(self):
        """Test parsing lowercase alphabetic ranges."""
        patterns = self.parser.parse_patterns("http://example.com/[a-e].html")
        assert len(patterns) == 1
        pattern_str, pattern_type, data = patterns[0]
        assert pattern_str == "[a-e]"
        assert pattern_type == "alpha_range"
        assert data == {"start": "a", "end": "e", "case": "lower"}

    def test_parse_alpha_range_uppercase(self):
        """Test parsing uppercase alphabetic ranges."""
        patterns = self.parser.parse_patterns("http://example.com/[A-E].html")
        assert len(patterns) == 1
        pattern_str, pattern_type, data = patterns[0]
        assert pattern_str == "[A-E]"
        assert pattern_type == "alpha_range"
        assert data == {"start": "A", "end": "E", "case": "upper"}

    def test_parse_list_pattern(self):
        """Test parsing list patterns."""
        patterns = self.parser.parse_patterns("http://example.com/{one,two,three}.html")
        assert len(patterns) == 1
        pattern_str, pattern_type, data = patterns[0]
        assert pattern_str == "{one,two,three}"
        assert pattern_type == "list"
        assert data == {"items": ["one", "two", "three"]}

    def test_parse_multiple_patterns(self):
        """Test parsing multiple patterns in one URL."""
        url = "http://example.com/{a,b}/[1-3].html"
        patterns = self.parser.parse_patterns(url)
        assert len(patterns) == 2

        # Check list pattern
        list_pattern = next(p for p in patterns if p[1] == "list")
        assert list_pattern[2] == {"items": ["a", "b"]}

        # Check numeric pattern
        numeric_pattern = next(p for p in patterns if p[1] == "numeric_range")
        assert numeric_pattern[2] == {"start": 1, "end": 3, "step": 1, "zero_pad": 1}


class TestURLExpander:
    """Test the URL expander functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.expander = URLExpander()

    def test_is_expandable_url(self):
        """Test expandable URL detection."""
        assert self.expander.is_expandable_url("http://example.com/[1-3].html")
        assert self.expander.is_expandable_url("http://example.com/{a,b}.html")
        assert not self.expander.is_expandable_url("http://example.com/page.html")

    def test_expand_numeric_range_basic(self):
        """Test expanding basic numeric ranges."""
        url = "http://example.com/[1-3].html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/1.html",
            "http://example.com/2.html",
            "http://example.com/3.html",
        ]
        assert expanded == expected

    def test_expand_numeric_range_zero_pad(self):
        """Test expanding zero-padded numeric ranges."""
        url = "http://example.com/[01-03].html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/01.html",
            "http://example.com/02.html",
            "http://example.com/03.html",
        ]
        assert expanded == expected

    def test_expand_numeric_range_with_step(self):
        """Test expanding numeric ranges with step."""
        url = "http://example.com/[0-6:2].html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/0.html",
            "http://example.com/2.html",
            "http://example.com/4.html",
            "http://example.com/6.html",
        ]
        assert expanded == expected

    def test_expand_alpha_range_lowercase(self):
        """Test expanding lowercase alphabetic ranges."""
        url = "http://example.com/[a-c].html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/a.html",
            "http://example.com/b.html",
            "http://example.com/c.html",
        ]
        assert expanded == expected

    def test_expand_alpha_range_uppercase(self):
        """Test expanding uppercase alphabetic ranges."""
        url = "http://example.com/[A-C].html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/A.html",
            "http://example.com/B.html",
            "http://example.com/C.html",
        ]
        assert expanded == expected

    def test_expand_list_pattern(self):
        """Test expanding list patterns."""
        url = "http://example.com/{one,two,three}.html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/one.html",
            "http://example.com/two.html",
            "http://example.com/three.html",
        ]
        assert expanded == expected

    def test_expand_multiple_patterns(self):
        """Test expanding multiple patterns in one URL."""
        url = "http://example.com/{a,b}/[1-2].html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/a/1.html",
            "http://example.com/b/1.html",
            "http://example.com/a/2.html",
            "http://example.com/b/2.html",
        ]
        assert expanded == expected

    def test_expand_no_patterns(self):
        """Test expanding URL with no patterns."""
        url = "http://example.com/page.html"
        expanded = self.expander.expand_url(url)
        assert expanded == [url]

    def test_validate_expanded_urls(self):
        """Test URL validation."""
        urls = [
            "http://example.com/page1.html",
            "https://example.com/page2.html",
            "invalid-url",
            "http://example.com/page3.html",
        ]
        valid_urls = self.expander.validate_expanded_urls(urls)
        expected = [
            "http://example.com/page1.html",
            "https://example.com/page2.html",
            "http://example.com/page3.html",
        ]
        assert valid_urls == expected

    def test_remove_duplicates(self):
        """Test that duplicate URLs are removed."""
        # Create a URL that would generate duplicates
        url = "http://example.com/{a,a,b}.html"
        expanded = self.expander.expand_url(url)
        expected = ["http://example.com/a.html", "http://example.com/b.html"]
        assert expanded == expected


class TestExpandUrlsFunction:
    """Test the convenience function."""

    def test_expand_urls_normal(self):
        """Test normal URL expansion."""
        url = "http://example.com/[1-3].html"
        expanded = expand_urls(url)
        expected = [
            "http://example.com/1.html",
            "http://example.com/2.html",
            "http://example.com/3.html",
        ]
        assert expanded == expected

    def test_expand_urls_ignore_glob(self):
        """Test URL expansion with globbing disabled."""
        url = "http://example.com/[1-3].html"
        expanded = expand_urls(url, ignore_glob=True)
        assert expanded == [url]

    def test_expand_urls_no_patterns(self):
        """Test URL expansion with no patterns."""
        url = "http://example.com/page.html"
        expanded = expand_urls(url)
        assert expanded == [url]


class TestComplexPatterns:
    """Test complex globbing patterns and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.expander = URLExpander()

    def test_complex_multi_pattern_url(self):
        """Test URL with multiple different pattern types."""
        url = "http://example.com/{web,api}/v[1-2]/[a-b].{json,xml}"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/web/v1/a.json",
            "http://example.com/web/v1/a.xml",
            "http://example.com/web/v1/b.json",
            "http://example.com/web/v1/b.xml",
            "http://example.com/web/v2/a.json",
            "http://example.com/web/v2/a.xml",
            "http://example.com/web/v2/b.json",
            "http://example.com/web/v2/b.xml",
            "http://example.com/api/v1/a.json",
            "http://example.com/api/v1/a.xml",
            "http://example.com/api/v1/b.json",
            "http://example.com/api/v1/b.xml",
            "http://example.com/api/v2/a.json",
            "http://example.com/api/v2/a.xml",
            "http://example.com/api/v2/b.json",
            "http://example.com/api/v2/b.xml",
        ]
        assert len(expanded) == 16
        for expected_url in expected:
            assert expected_url in expanded

    def test_large_numeric_range(self):
        """Test that large ranges work correctly."""
        url = "http://example.com/[95-100].html"
        expanded = self.expander.expand_url(url)
        expected = [
            "http://example.com/95.html",
            "http://example.com/96.html",
            "http://example.com/97.html",
            "http://example.com/98.html",
            "http://example.com/99.html",
            "http://example.com/100.html",
        ]
        assert expanded == expected

    def test_single_item_patterns(self):
        """Test patterns with single items."""
        url = "http://example.com/[5-5].html"
        expanded = self.expander.expand_url(url)
        assert expanded == ["http://example.com/5.html"]

        url = "http://example.com/{single}.html"
        expanded = self.expander.expand_url(url)
        assert expanded == ["http://example.com/single.html"]


if __name__ == "__main__":
    pytest.main([__file__])
