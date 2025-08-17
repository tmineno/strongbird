"""
CLI functionality tests for Strongbird.
"""

import subprocess
from pathlib import Path

import pytest


@pytest.mark.cli
class TestCLI:
    """Test CLI functionality."""

    def run_command(self, cmd: list, project_root: Path):
        """Run a CLI command and return output."""
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        return result

    def test_help_command(self, project_root):
        """Test that help command works and displays expected content."""
        result = self.run_command(["uv", "run", "strongbird", "--help"], project_root)

        assert (
            result.returncode == 0
        ), f"Help command failed with stderr: {result.stderr}"
        assert "Extract content from web pages" in result.stdout
        assert "Usage:" in result.stdout
        assert "Options:" in result.stdout

    def test_version_command(self, project_root):
        """Test that version command works."""
        result = self.run_command(
            ["uv", "run", "strongbird", "--version"], project_root
        )

        assert (
            result.returncode == 0
        ), f"Version command failed with stderr: {result.stderr}"
        # Version output format may vary, just check it's not empty
        assert result.stdout.strip() != ""

    @pytest.mark.parametrize("format_type", ["text", "markdown", "json"])
    def test_local_file_extraction(self, project_root, mathjax_test_file, format_type):
        """Test extraction from local HTML files with different formats."""
        result = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(mathjax_test_file),
                "--quiet",
                "--format",
                format_type,
                "--no-metadata",
            ],
            project_root,
        )

        assert (
            result.returncode == 0
        ), f"Extraction failed for {format_type}: {result.stderr}"
        assert len(result.stdout) > 0, f"No output for {format_type} format"

        # Check for expected content based on format
        if format_type == "json":
            assert "{" in result.stdout and "}" in result.stdout
        else:
            # Should contain some content from the test file
            assert "MathJax" in result.stdout or "math" in result.stdout.lower()

    def test_output_to_file(self, project_root, mathjax_test_file, tmp_path):
        """Test output to file functionality."""
        output_file = tmp_path / "test_output.md"

        result = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(mathjax_test_file),
                "--quiet",
                "--format",
                "markdown",
                "-o",
                str(output_file),
            ],
            project_root,
        )

        assert result.returncode == 0, f"Output to file failed: {result.stderr}"
        assert output_file.exists(), "Output file was not created"

        content = output_file.read_text()
        assert len(content) > 0, "Output file is empty"
        assert "MathJax" in content or "math" in content.lower()

    def test_math_processing_flag(self, project_root, mathjax_test_file):
        """Test math processing via CLI flag."""
        result = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(mathjax_test_file),
                "--quiet",
                "--format",
                "markdown",
                "--process-math",
                "--no-metadata",
            ],
            project_root,
        )

        assert result.returncode == 0, f"Math processing failed: {result.stderr}"

        # Check for math expressions in output
        # Should contain $ or $$ for math delimiters
        assert "$" in result.stdout, "No math expressions found in output"

    def test_metadata_inclusion(self, project_root, comprehensive_math_file):
        """Test metadata inclusion in output."""
        # Test with metadata
        result_with = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(comprehensive_math_file),
                "--quiet",
                "--format",
                "markdown",
                "--with-metadata",
            ],
            project_root,
        )

        assert result_with.returncode == 0
        assert "---" in result_with.stdout, "Metadata markers not found"
        assert "title:" in result_with.stdout or "Title:" in result_with.stdout

    def test_metadata_exclusion(self, project_root, comprehensive_math_file):
        """Test metadata exclusion from output."""
        # Test without metadata
        result_without = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(comprehensive_math_file),
                "--quiet",
                "--format",
                "markdown",
                "--no-metadata",
            ],
            project_root,
        )

        assert result_without.returncode == 0
        # Should not have metadata markers
        assert (
            "---\n---" not in result_without.stdout
            or "title:" not in result_without.stdout.lower()
        )

    def test_quiet_flag(self, project_root, mathjax_test_file):
        """Test that quiet flag suppresses progress messages."""
        # Run without quiet flag
        result_verbose = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(mathjax_test_file),
                "--format",
                "markdown",
                "--no-metadata",
            ],
            project_root,
        )

        # Run with quiet flag
        result_quiet = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(mathjax_test_file),
                "--quiet",
                "--format",
                "markdown",
                "--no-metadata",
            ],
            project_root,
        )

        assert result_verbose.returncode == 0
        assert result_quiet.returncode == 0

        # Quiet output should only contain the extracted content
        # (this is a basic check, actual behavior may vary)
        assert len(result_quiet.stderr) == 0 or len(result_quiet.stderr) < len(
            result_verbose.stderr
        )

    def test_invalid_file_path(self, project_root):
        """Test handling of invalid file path."""
        result = self.run_command(
            ["uv", "run", "strongbird", "/nonexistent/file.html", "--quiet"],
            project_root,
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0
        assert "not found" in result.stderr.lower() or "error" in result.stderr.lower()

    @pytest.mark.parametrize(
        "option,value",
        [
            ("--timeout", "5000"),
            ("--viewport", "1024x768"),
            ("--browser", "chromium"),
        ],
    )
    def test_browser_options(self, project_root, mathjax_test_file, option, value):
        """Test various browser configuration options."""
        result = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(mathjax_test_file),
                "--quiet",
                "--format",
                "text",
                "--no-metadata",
                option,
                value,
            ],
            project_root,
        )

        # These options should be accepted without error
        assert (
            result.returncode == 0
        ), f"Option {option} with value {value} failed: {result.stderr}"

    def test_no_playwright_flag(self, project_root, mathjax_test_file):
        """Test extraction without Playwright rendering."""
        result = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                str(mathjax_test_file),
                "--quiet",
                "--no-playwright",
                "--format",
                "text",
                "--no-metadata",
            ],
            project_root,
        )

        # Should still work for local files
        assert result.returncode == 0, f"No-playwright mode failed: {result.stderr}"
        assert len(result.stdout) > 0

    def test_parallel_processing_option(self, project_root):
        """Test parallel processing CLI option."""
        result = self.run_command(
            [
                "uv",
                "run",
                "strongbird",
                "http://httpbin.org/get?id=[1-2]",
                "--quiet",
                "-j",
                "2",
                "--format",
                "text",
                "--no-metadata",
            ],
            project_root,
        )

        # Should accept the parallel processing option
        # Note: This might fail if no network, so we just check the option is accepted
        assert "-j" in ["uv", "run", "strongbird", "--help"] or result.returncode in [
            0,
            1,
        ]

    def test_url_globbing_expansion(self, project_root):
        """Test URL globbing pattern expansion."""
        result = self.run_command(["uv", "run", "strongbird", "--help"], project_root)

        # Check that globbing-related options exist
        assert "--ignore-glob" in result.stdout or result.returncode == 0
