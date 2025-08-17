"""
Comprehensive test suite for batch mode functionality in Strongbird.
"""

import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from strongbird.batch_reader import BatchFileReader
from strongbird.cli_orchestrator import CLIOrchestrator
from strongbird.config import (
    BrowserConfig,
    CrawlConfig,
    ExtractionConfig,
    OutputConfig,
    ParallelConfig,
    PlaywrightConfig,
)


@pytest.mark.cli
class TestBatchFileReader:
    """Test the BatchFileReader class."""

    def test_read_simple_urls(self, tmp_path):
        """Test reading simple URLs from batch file."""
        batch_file = tmp_path / "simple_urls.txt"
        batch_file.write_text(
            "https://example.com\n"
            "https://httpbin.org/html\n"
            "https://httpbin.org/json\n"
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 3
        assert "https://example.com" in urls
        assert "https://httpbin.org/html" in urls
        assert "https://httpbin.org/json" in urls

    def test_read_urls_with_comments_and_empty_lines(self, tmp_path):
        """Test reading URLs while filtering comments and empty lines."""
        batch_file = tmp_path / "urls_with_comments.txt"
        batch_file.write_text(
            "# This is a comment\n"
            "https://example.com\n"
            "\n"
            "# Another comment\n"
            "https://httpbin.org/html\n"
            "\n"
            "https://httpbin.org/json\n"
            "# Final comment\n"
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 3
        assert "https://example.com" in urls
        assert "https://httpbin.org/html" in urls
        assert "https://httpbin.org/json" in urls

    def test_read_urls_with_glob_patterns(self, tmp_path):
        """Test reading URLs with glob patterns."""
        batch_file = tmp_path / "glob_urls.txt"
        batch_file.write_text(
            "https://httpbin.org/status/[200-202]\n"
            "https://httpbin.org/{get,post}\n"
            "https://example.com/page[1-3].html\n"
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 3
        assert "https://httpbin.org/status/[200-202]" in urls
        assert "https://httpbin.org/{get,post}" in urls
        assert "https://example.com/page[1-3].html" in urls

    def test_read_mixed_url_types(self, tmp_path):
        """Test reading mixed URL types including file paths."""
        batch_file = tmp_path / "mixed_urls.txt"
        batch_file.write_text(
            "https://example.com\n"
            "http://httpbin.org/html\n"
            "file:///etc/hosts\n"
            "/path/to/local/file.html\n"
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 4
        assert "https://example.com" in urls
        assert "http://httpbin.org/html" in urls
        assert "file:///etc/hosts" in urls
        assert "/path/to/local/file.html" in urls

    def test_invalid_urls_with_warnings(self, tmp_path, capsys):
        """Test that invalid URLs generate warnings but don't stop processing."""
        batch_file = tmp_path / "invalid_urls.txt"
        batch_file.write_text(
            "https://example.com\n"
            "not-a-url\n"
            "invalid://test\n"
            "https://httpbin.org/html\n"
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        # Should only get valid URLs
        assert len(urls) == 2
        assert "https://example.com" in urls
        assert "https://httpbin.org/html" in urls

        # Check warnings were printed
        captured = capsys.readouterr()
        assert "Warning: Line 2 doesn't look like a URL: not-a-url" in captured.out
        assert "Warning: Line 3 doesn't look like a URL: invalid://test" in captured.out

    def test_nonexistent_file(self):
        """Test error handling for nonexistent files."""
        reader = BatchFileReader()

        with pytest.raises(FileNotFoundError, match="Batch file not found"):
            reader.read_urls_from_file("nonexistent_file.txt")

    def test_directory_instead_of_file(self, tmp_path):
        """Test error handling when path is a directory."""
        reader = BatchFileReader()

        with pytest.raises(IOError, match="Path is not a file"):
            reader.read_urls_from_file(str(tmp_path))

    def test_empty_batch_file(self, tmp_path):
        """Test handling of empty batch files."""
        batch_file = tmp_path / "empty.txt"
        batch_file.write_text("")

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 0

    def test_batch_file_only_comments(self, tmp_path):
        """Test handling of batch files with only comments."""
        batch_file = tmp_path / "only_comments.txt"
        batch_file.write_text("# Comment 1\n" "# Comment 2\n" "\n" "# Comment 3\n")

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 0

    def test_validate_batch_file_success(self, tmp_path):
        """Test successful batch file validation."""
        batch_file = tmp_path / "valid.txt"
        batch_file.write_text("https://example.com\nhttps://httpbin.org/html\n")

        reader = BatchFileReader()
        is_valid, message = reader.validate_batch_file(str(batch_file))

        assert is_valid is True
        assert "Found 2 URLs" in message

    def test_validate_batch_file_empty(self, tmp_path):
        """Test validation of empty batch file."""
        batch_file = tmp_path / "empty.txt"
        batch_file.write_text("")

        reader = BatchFileReader()
        is_valid, message = reader.validate_batch_file(str(batch_file))

        assert is_valid is False
        assert "contains no valid URLs" in message

    def test_validate_batch_file_nonexistent(self):
        """Test validation of nonexistent batch file."""
        reader = BatchFileReader()
        is_valid, message = reader.validate_batch_file("nonexistent.txt")

        assert is_valid is False
        assert "Batch file not found" in message


@pytest.mark.cli
class TestBatchModeCLI:
    """Test batch mode CLI functionality."""

    def run_cli_command(self, cmd: list, project_root: Path):
        """Run a CLI command and return result."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        return result

    def test_batch_option_in_help(self, project_root):
        """Test that --batch option appears in help output."""
        result = self.run_cli_command(
            ["uv", "run", "strongbird", "--help"], project_root
        )

        assert result.returncode == 0
        assert "--batch" in result.stdout
        assert "Read URLs from batch file" in result.stdout

    def test_batch_without_source_argument(self, project_root, tmp_path):
        """Test that batch mode works without SOURCE argument."""
        batch_file = tmp_path / "test.txt"
        batch_file.write_text("https://httpbin.org/html\n")
        output_dir = tmp_path / "output"

        result = self.run_cli_command(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--no-playwright",
            ],
            project_root,
        )

        assert result.returncode == 0

    def test_batch_with_source_argument_error(self, project_root, tmp_path):
        """Test error when both batch and source are provided."""
        batch_file = tmp_path / "test.txt"
        batch_file.write_text("https://httpbin.org/html\n")

        result = self.run_cli_command(
            [
                "uv",
                "run",
                "strongbird",
                "https://example.com",
                "--batch",
                str(batch_file),
                "--output",
                str(tmp_path / "output"),
            ],
            project_root,
        )

        assert result.returncode == 1
        assert (
            "Cannot use both SOURCE argument and --batch option together"
            in result.stderr
        )

    def test_no_source_no_batch_error(self, project_root):
        """Test error when neither source nor batch is provided."""
        result = self.run_cli_command(["uv", "run", "strongbird"], project_root)

        assert result.returncode == 1
        assert (
            "Either SOURCE argument or --batch option must be provided" in result.stderr
        )

    def test_batch_nonexistent_file_error(self, project_root):
        """Test error handling for nonexistent batch file."""
        result = self.run_cli_command(
            ["uv", "run", "strongbird", "--batch", "nonexistent.txt"], project_root
        )

        assert result.returncode != 0
        assert "does not exist" in result.stderr

    def test_batch_without_output_error(self, project_root, tmp_path):
        """Test error when batch mode is used without output option."""
        batch_file = tmp_path / "test.txt"
        batch_file.write_text("https://httpbin.org/html\n")

        result = self.run_cli_command(
            ["uv", "run", "strongbird", "--batch", str(batch_file)], project_root
        )

        assert result.returncode == 1
        assert "Batch processing requires --output" in result.stderr


@pytest.mark.integration
class TestBatchModeIntegration:
    """Integration tests for batch mode (requires network)."""

    def test_batch_simple_urls(self, project_root, tmp_path):
        """Test batch processing of simple URLs."""
        batch_file = tmp_path / "simple.txt"
        batch_file.write_text("https://httpbin.org/html\n" "https://httpbin.org/json\n")
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--no-playwright",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        assert result.returncode == 0
        assert output_dir.exists()

        # Check that files were created
        output_files = list(output_dir.glob("*.md"))
        assert len(output_files) == 2

        # Check file naming convention
        file_names = [f.name for f in output_files]
        assert any("httpbin.org_html" in name for name in file_names)
        assert any("httpbin.org_json" in name for name in file_names)

    def test_batch_with_glob_patterns(self, project_root, tmp_path):
        """Test batch processing with URL glob patterns."""
        batch_file = tmp_path / "glob.txt"
        batch_file.write_text("https://httpbin.org/{get,post}\n")
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--no-playwright",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        assert result.returncode == 0
        assert output_dir.exists()

        # Should expand to 2 URLs: get and post
        output_files = list(output_dir.glob("*.md"))
        assert len(output_files) == 2

    def test_batch_parallel_processing(self, project_root, tmp_path):
        """Test batch processing with parallel workers."""
        batch_file = tmp_path / "parallel.txt"
        batch_file.write_text(
            "https://httpbin.org/html\n"
            "https://httpbin.org/json\n"
            "https://httpbin.org/get\n"
            "https://httpbin.org/user-agent\n"
        )
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--no-playwright",
                "-j",
                "3",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        assert result.returncode == 0
        assert output_dir.exists()

        output_files = list(output_dir.glob("*.md"))
        assert len(output_files) == 4

    def test_batch_with_failures(self, project_root, tmp_path):
        """Test batch processing with some failing URLs."""
        batch_file = tmp_path / "with_failures.txt"
        batch_file.write_text(
            "https://httpbin.org/html\n"
            "https://invalid-domain-that-does-not-exist.com/test\n"
            "https://httpbin.org/json\n"
        )
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--no-playwright",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        # Should succeed overall even with some failures
        assert result.returncode == 0
        assert output_dir.exists()

        # Should only create files for successful extractions
        output_files = list(output_dir.glob("*.md"))
        assert len(output_files) == 2  # Only the valid httpbin URLs

        # Error message should appear in output
        assert (
            "Error processing" in result.stdout or "Error processing" in result.stderr
        )

    def test_batch_different_output_formats(self, project_root, tmp_path):
        """Test batch processing with different output formats."""
        batch_file = tmp_path / "formats.txt"
        batch_file.write_text("https://httpbin.org/json\n")

        # Test JSON format
        output_dir = tmp_path / "json_output"
        result = subprocess.run(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--format",
                "json",
                "--no-playwright",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        assert result.returncode == 0
        json_files = list(output_dir.glob("*.json"))
        assert len(json_files) == 1

        # Test text format
        output_dir = tmp_path / "text_output"
        result = subprocess.run(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--format",
                "text",
                "--no-playwright",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        assert result.returncode == 0
        text_files = list(output_dir.glob("*.txt"))
        assert len(text_files) == 1

    def test_batch_ignore_glob_option(self, project_root, tmp_path):
        """Test batch processing with --ignore-glob option."""
        batch_file = tmp_path / "literal.txt"
        batch_file.write_text(
            "https://httpbin.org/anything/literal[1-3]\n"  # Should be treated literally
        )
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                "uv",
                "run",
                "strongbird",
                "--batch",
                str(batch_file),
                "--output",
                str(output_dir),
                "--ignore-glob",
                "--no-playwright",
                "--quiet",
            ],
            capture_output=True,
            text=True,
            cwd=project_root,
        )

        # Should process as single URL (literal brackets)
        assert result.returncode == 0
        output_files = list(output_dir.glob("*.md"))
        assert len(output_files) <= 1  # May fail but should be treated as single URL


@pytest.mark.asyncio
class TestBatchModeOrchestrator:
    """Test batch mode functionality in CLIOrchestrator."""

    async def test_run_batch_validation(self, tmp_path):
        """Test batch file validation in orchestrator."""
        # Create mock configs
        browser_config = BrowserConfig()
        extraction_config = ExtractionConfig()
        playwright_config = PlaywrightConfig()
        crawl_config = CrawlConfig()
        output_config = OutputConfig(output_path=str(tmp_path / "output"))
        parallel_config = ParallelConfig()

        orchestrator = CLIOrchestrator(
            browser_config=browser_config,
            extraction_config=extraction_config,
            playwright_config=playwright_config,
            crawl_config=crawl_config,
            output_config=output_config,
            parallel_config=parallel_config,
        )

        # Test with nonexistent file
        with pytest.raises(SystemExit):
            await orchestrator.run_batch("nonexistent.txt")

    async def test_run_batch_no_output_path(self, tmp_path):
        """Test batch mode requires output path."""
        batch_file = tmp_path / "test.txt"
        batch_file.write_text("https://example.com\n")

        # Create configs without output path
        browser_config = BrowserConfig()
        extraction_config = ExtractionConfig()
        playwright_config = PlaywrightConfig()
        crawl_config = CrawlConfig()
        output_config = OutputConfig()  # No output path
        parallel_config = ParallelConfig()

        orchestrator = CLIOrchestrator(
            browser_config=browser_config,
            extraction_config=extraction_config,
            playwright_config=playwright_config,
            crawl_config=crawl_config,
            output_config=output_config,
            parallel_config=parallel_config,
        )

        with pytest.raises(SystemExit):
            await orchestrator.run_batch(str(batch_file))

    @patch("strongbird.cli_orchestrator.ParallelProcessor")
    async def test_run_batch_url_expansion(self, mock_parallel_processor, tmp_path):
        """Test URL expansion in batch processing."""
        batch_file = tmp_path / "test.txt"
        batch_file.write_text("https://example.com/[1-2]\n" "https://test.com/{a,b}\n")

        # Mock the parallel processor
        mock_processor = MagicMock()
        mock_processor.process_urls_parallel = AsyncMock(
            return_value=[
                {"content": "test1"},
                {"content": "test2"},
                {"content": "test3"},
                {"content": "test4"},
            ]
        )
        mock_parallel_processor.return_value = mock_processor

        # Create configs
        browser_config = BrowserConfig()
        extraction_config = ExtractionConfig()
        playwright_config = PlaywrightConfig()
        crawl_config = CrawlConfig()
        output_config = OutputConfig(output_path=str(tmp_path / "output"), quiet=True)
        parallel_config = ParallelConfig()

        orchestrator = CLIOrchestrator(
            browser_config=browser_config,
            extraction_config=extraction_config,
            playwright_config=playwright_config,
            crawl_config=crawl_config,
            output_config=output_config,
            parallel_config=parallel_config,
        )

        # Mock handle_output to avoid file operations
        orchestrator.handle_output = MagicMock()

        await orchestrator.run_batch(str(batch_file))

        # Should have expanded to 4 URLs total
        args, kwargs = mock_processor.process_urls_parallel.call_args
        urls = args[0]
        assert len(urls) == 4
        assert "https://example.com/1" in urls
        assert "https://example.com/2" in urls
        assert "https://test.com/a" in urls
        assert "https://test.com/b" in urls


@pytest.mark.cli
class TestBatchModeEdgeCases:
    """Test edge cases and error conditions for batch mode."""

    def test_batch_file_with_unicode(self, tmp_path):
        """Test batch file with unicode characters."""
        batch_file = tmp_path / "unicode.txt"
        batch_file.write_text(
            "# Test with unicode: 测试\n"
            "https://example.com/测试\n"
            "https://httpbin.org/anything/émoji\n",
            encoding="utf-8",
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 2
        assert "https://example.com/测试" in urls
        assert "https://httpbin.org/anything/émoji" in urls

    def test_batch_file_very_long_lines(self, tmp_path):
        """Test batch file with very long URLs."""
        long_url = "https://example.com/" + "a" * 1000
        batch_file = tmp_path / "long.txt"
        batch_file.write_text(f"{long_url}\n")

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 1
        assert urls[0] == long_url

    def test_batch_file_windows_line_endings(self, tmp_path):
        """Test batch file with Windows line endings."""
        batch_file = tmp_path / "windows.txt"
        batch_file.write_bytes(
            b"https://example.com\r\n" b"https://httpbin.org/html\r\n"
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 2
        assert "https://example.com" in urls
        assert "https://httpbin.org/html" in urls

    def test_batch_file_mixed_line_endings(self, tmp_path):
        """Test batch file with mixed line endings."""
        batch_file = tmp_path / "mixed.txt"
        batch_file.write_bytes(
            b"https://example.com\n"
            b"https://httpbin.org/html\r\n"
            b"https://test.com\r"
        )

        reader = BatchFileReader()
        urls = reader.read_urls_from_file(str(batch_file))

        assert len(urls) == 3
        assert "https://example.com" in urls
        assert "https://httpbin.org/html" in urls
        assert "https://test.com" in urls


# ============================================================================
# Pytest Configuration for Batch Tests
# ============================================================================


def pytest_configure(config):
    """Register custom markers for batch tests."""
    config.addinivalue_line("markers", "batch: mark test as a batch mode test")
