#!/usr/bin/env python3
"""
Unified test suite for Strongbird web content extractor.

This script combines:
- CLI functionality tests
- Math extraction tests
- Integration tests with Wikipedia
"""

import asyncio
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strongbird.browser import BrowserManager  # noqa: E402
from strongbird.extractor import StrongbirdExtractor  # noqa: E402


class StrongbirdTestSuite:
    """Comprehensive test suite for Strongbird."""

    def __init__(self, verbose: bool = False):
        """Initialize test suite."""
        self.test_dir = Path(__file__).parent
        self.fixtures_dir = self.test_dir / "fixtures"
        self.project_root = self.test_dir.parent
        self.verbose = verbose
        self.results = {
            "cli": [],
            "math": [],
            "integration": [],
        }
        self.stats = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "skipped": 0,
        }

    def run_command(self, cmd: str) -> Tuple[int, str, str]:
        """Run a CLI command and return output."""
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )
        return result.returncode, result.stdout, result.stderr

    def log(self, message: str, level: str = "info"):
        """Log message with appropriate formatting."""
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "skip": "⏭️",
            "test": "🧪",
        }
        icon = icons.get(level, "•")
        print(f"{icon} {message}")

    def log_verbose(self, message: str):
        """Log verbose message if verbose mode is enabled."""
        if self.verbose:
            print(f"   {message}")

    # ============================================================================
    # CLI Functionality Tests
    # ============================================================================

    def test_cli_help(self) -> Dict[str, Any]:
        """Test help command."""
        self.log("Testing help command...", "test")
        code, stdout, stderr = self.run_command("uv run strongbird --help")

        result = {
            "name": "CLI Help",
            "status": (
                "PASS"
                if code == 0 and "Extract content from web pages" in stdout
                else "FAIL"
            ),
            "details": (
                "Help command displays correctly" if code == 0 else f"Exit code: {code}"
            ),
        }

        if result["status"] == "PASS":
            self.log_verbose("Help text contains expected content")
        else:
            self.log_verbose(f"Error: {stderr[:100]}")

        return result

    def test_cli_local_extraction(self) -> Dict[str, Any]:
        """Test extraction from local HTML files."""
        self.log("Testing local file extraction...", "test")
        test_file = self.fixtures_dir / "test-mathjax.html"

        if not test_file.exists():
            return {
                "name": "CLI Local Extraction",
                "status": "SKIP",
                "details": "Test file not found",
            }

        # Test different formats
        formats_tested = []
        all_passed = True

        for format_type in ["text", "markdown", "json"]:
            code, stdout, stderr = self.run_command(
                f"uv run strongbird {test_file} --quiet --format {format_type} --no-metadata"
            )
            format_passed = code == 0 and ("MathJax" in stdout or "title" in stdout)
            formats_tested.append((format_type, format_passed))
            all_passed = all_passed and format_passed

            if format_passed:
                self.log_verbose(f"  {format_type} format: ✓")
            else:
                self.log_verbose(f"  {format_type} format: ✗")

        return {
            "name": "CLI Local Extraction",
            "status": "PASS" if all_passed else "FAIL",
            "details": f"Tested formats: {', '.join(f[0] for f in formats_tested)}",
        }

    def test_cli_output_to_file(self) -> Dict[str, Any]:
        """Test output to file functionality."""
        self.log("Testing output to file...", "test")
        test_file = self.fixtures_dir / "test-mathjax.html"
        output_file = self.test_dir / "test_output.md"

        try:
            code, stdout, stderr = self.run_command(
                f"uv run strongbird {test_file} --quiet --format markdown -o {output_file}"
            )

            if code == 0 and output_file.exists():
                content = output_file.read_text()
                success = "MathJax" in content
                result = {
                    "name": "CLI Output to File",
                    "status": "PASS" if success else "FAIL",
                    "details": f"Output file created with {len(content)} bytes",
                }
            else:
                result = {
                    "name": "CLI Output to File",
                    "status": "FAIL",
                    "details": f"Failed to create output file (exit code: {code})",
                }
        finally:
            # Clean up
            if output_file.exists():
                output_file.unlink()

        return result

    def test_cli_math_processing(self) -> Dict[str, Any]:
        """Test math processing via CLI."""
        self.log("Testing CLI math processing...", "test")
        test_file = self.fixtures_dir / "test-mathjax.html"

        code, stdout, stderr = self.run_command(
            f"uv run strongbird {test_file} --quiet --format markdown --process-math --no-metadata"
        )

        # Check for math expressions in output
        has_inline = "$" in stdout and "e^{" in stdout
        has_display = "$$" in stdout

        return {
            "name": "CLI Math Processing",
            "status": "PASS" if code == 0 and (has_inline or has_display) else "FAIL",
            "details": f"Inline: {has_inline}, Display: {has_display}",
        }

    def test_cli_metadata_handling(self) -> Dict[str, Any]:
        """Test metadata inclusion/exclusion."""
        self.log("Testing metadata handling...", "test")
        test_file = self.fixtures_dir / "comprehensive-math-test.html"

        # Test with metadata
        code1, stdout1, _ = self.run_command(
            f"uv run strongbird {test_file} --quiet --format markdown --with-metadata"
        )
        has_metadata = "---" in stdout1 and "title:" in stdout1

        # Test without metadata
        code2, stdout2, _ = self.run_command(
            f"uv run strongbird {test_file} --quiet --format markdown --no-metadata"
        )
        no_metadata = "---" not in stdout2 or "title:" not in stdout2

        return {
            "name": "CLI Metadata Handling",
            "status": (
                "PASS"
                if code1 == 0 and code2 == 0 and has_metadata and no_metadata
                else "FAIL"
            ),
            "details": f"With metadata: {has_metadata}, Without: {no_metadata}",
        }

    # ============================================================================
    # Math Extraction Tests
    # ============================================================================

    async def extract_content(
        self,
        source: str,
        process_math: bool = False,
        format_type: str = "markdown",
        include_metadata: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Helper function to extract content using strongbird."""
        is_url = source.startswith(("http://", "https://", "file://"))

        browser_manager = BrowserManager(
            headless=True,
            browser_type="chromium",
            viewport_width=1920,
            viewport_height=1080,
        )

        extractor = StrongbirdExtractor(
            browser_manager=browser_manager,
            use_playwright=is_url,
            favor_precision=False,
        )

        try:
            if is_url:
                result = await extractor.extract_async(
                    url=source,
                    output_format=format_type,
                    process_math=process_math,
                    with_metadata=include_metadata,
                )
            else:
                result = await extractor.extract_from_file_async(
                    file_path=source,
                    output_format=format_type,
                    process_math=process_math,
                    with_metadata=include_metadata,
                )
            return result
        except Exception as e:
            self.log_verbose(f"Extraction error: {e}")
            return None

    def count_math_expressions(self, content: str) -> Dict[str, int]:
        """Count different types of math expressions in extracted content."""
        counts = {
            "inline_math": len(re.findall(r"\$[^$\n]+\$", content)),
            "display_math": len(re.findall(r"\$\$[^$]+\$\$", content, re.DOTALL)),
            "total_expressions": 0,
        }
        counts["total_expressions"] = counts["inline_math"] + counts["display_math"]
        return counts

    async def test_math_local_file(
        self, filename: str, min_expressions: int = 0
    ) -> Dict[str, Any]:
        """Test math extraction for a local file."""
        self.log(f"Testing math extraction: {filename}", "test")
        filepath = self.fixtures_dir / filename

        if not filepath.exists():
            return {
                "name": f"Math: {filename}",
                "status": "SKIP",
                "details": "File not found",
            }

        try:
            result = await self.extract_content(
                source=f"file://{filepath.absolute()}",
                process_math=True,
                format_type="markdown",
                include_metadata=False,
            )

            if result is None:
                return {
                    "name": f"Math: {filename}",
                    "status": "ERROR",
                    "details": "Extraction returned None",
                }

            math_count = self.count_math_expressions(result["content"])

            return {
                "name": f"Math: {filename}",
                "status": (
                    "PASS"
                    if math_count["total_expressions"] >= min_expressions
                    else "FAIL"
                ),
                "details": f"Found {math_count['total_expressions']} expressions (expected ≥{min_expressions})",
            }

        except Exception as e:
            return {
                "name": f"Math: {filename}",
                "status": "ERROR",
                "details": str(e)[:100],
            }

    async def test_math_wikipedia(self) -> List[Dict[str, Any]]:
        """Test math extraction on Wikipedia pages."""
        self.log("Testing Wikipedia math extraction...", "test")

        wikipedia_tests = [
            {
                "url": "https://en.wikipedia.org/wiki/Quadratic_formula",
                "name": "Wikipedia: Quadratic Formula",
                "min_expressions": 3,
            },
            {
                "url": "https://en.wikipedia.org/wiki/Euler%27s_identity",
                "name": "Wikipedia: Euler's Identity",
                "min_expressions": 2,
            },
        ]

        results = []
        for test in wikipedia_tests:
            try:
                result = await self.extract_content(
                    source=test["url"],
                    process_math=True,
                    format_type="markdown",
                    include_metadata=False,
                )

                if result:
                    math_count = self.count_math_expressions(result["content"])
                    status = (
                        "PASS"
                        if math_count["total_expressions"] >= test["min_expressions"]
                        else "FAIL"
                    )
                    details = f"Found {math_count['total_expressions']} expressions"
                else:
                    status = "ERROR"
                    details = "Extraction failed"

                results.append(
                    {
                        "name": test["name"],
                        "status": status,
                        "details": details,
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "name": test["name"],
                        "status": "ERROR",
                        "details": f"Error: {str(e)[:50]}",
                    }
                )

        return results

    # ============================================================================
    # Test Execution
    # ============================================================================

    def run_cli_tests(self):
        """Run all CLI tests."""
        self.log("\n📋 CLI Functionality Tests", "info")
        self.log("=" * 50)

        tests = [
            self.test_cli_help(),
            self.test_cli_local_extraction(),
            self.test_cli_output_to_file(),
            self.test_cli_math_processing(),
            self.test_cli_metadata_handling(),
        ]

        for test_result in tests:
            self.results["cli"].append(test_result)
            self.print_test_result(test_result)
            self.update_stats(test_result)

    async def run_math_tests(self):
        """Run all math extraction tests."""
        self.log("\n🧮 Math Extraction Tests", "info")
        self.log("=" * 50)

        # Test local fixtures
        local_tests = [
            ("comprehensive-math-test.html", 6),
            ("test-mathjax.html", 4),
        ]

        for filename, min_expressions in local_tests:
            test_result = await self.test_math_local_file(filename, min_expressions)
            self.results["math"].append(test_result)
            self.print_test_result(test_result)
            self.update_stats(test_result)

    async def run_integration_tests(self):
        """Run integration tests."""
        self.log("\n🌐 Integration Tests", "info")
        self.log("=" * 50)

        try:
            wikipedia_results = await self.test_math_wikipedia()
            for test_result in wikipedia_results:
                self.results["integration"].append(test_result)
                self.print_test_result(test_result)
                self.update_stats(test_result)
        except Exception as e:
            self.log(f"Integration tests skipped: {e}", "warning")

    def print_test_result(self, result: Dict[str, Any]):
        """Print individual test result."""
        status_map = {
            "PASS": "success",
            "FAIL": "error",
            "ERROR": "error",
            "SKIP": "skip",
        }
        level = status_map.get(result["status"], "info")
        self.log(f"{result['name']}: {result['status']}", level)
        self.log_verbose(f"Details: {result['details']}")

    def update_stats(self, result: Dict[str, Any]):
        """Update test statistics."""
        self.stats["total"] += 1
        if result["status"] == "PASS":
            self.stats["passed"] += 1
        elif result["status"] == "FAIL":
            self.stats["failed"] += 1
        elif result["status"] == "ERROR":
            self.stats["errors"] += 1
        elif result["status"] == "SKIP":
            self.stats["skipped"] += 1

    def print_summary(self):
        """Print test summary."""
        self.log("\n" + "=" * 60)
        self.log("📊 Test Summary", "info")
        self.log("=" * 60)

        # Overall stats
        self.log(f"Total Tests: {self.stats['total']}")
        self.log(f"Passed: {self.stats['passed']}", "success")

        if self.stats["failed"] > 0:
            self.log(f"Failed: {self.stats['failed']}", "error")

        if self.stats["errors"] > 0:
            self.log(f"Errors: {self.stats['errors']}", "error")

        if self.stats["skipped"] > 0:
            self.log(f"Skipped: {self.stats['skipped']}", "skip")

        # Category breakdown
        self.log("\nBreakdown by Category:")
        self.log(f"  CLI Tests: {len(self.results['cli'])} tests")
        self.log(f"  Math Tests: {len(self.results['math'])} tests")
        self.log(f"  Integration Tests: {len(self.results['integration'])} tests")

        # Success rate
        if self.stats["total"] > 0:
            success_rate = (self.stats["passed"] / self.stats["total"]) * 100
            self.log(f"\nSuccess Rate: {success_rate:.1f}%")

        # Final verdict
        self.log("\n" + "=" * 60)
        if self.stats["failed"] == 0 and self.stats["errors"] == 0:
            self.log("🎉 All tests passed successfully!", "success")
            return 0
        else:
            self.log("❌ Some tests failed or had errors!", "error")
            return 1

    async def run_all_tests(self) -> int:
        """Run all test suites."""
        self.log("🚀 Strongbird Unified Test Suite", "info")
        self.log("=" * 60)

        # Quick CLI validation
        self.log("\n🔧 Quick CLI Validation", "info")
        code, stdout, _ = self.run_command("uv run strongbird --help")
        if code != 0:
            self.log("CLI is not working properly!", "error")
            return 1
        self.log("CLI is operational", "success")

        # Run test suites
        self.run_cli_tests()
        await self.run_math_tests()
        await self.run_integration_tests()

        # Print summary and return exit code
        return self.print_summary()


async def main():
    """Main entry point for test suite."""
    # Parse command line arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    skip_integration = "--skip-integration" in sys.argv

    # Create and run test suite
    suite = StrongbirdTestSuite(verbose=verbose)

    if skip_integration:
        suite.log("Skipping integration tests", "warning")

        # Override integration test method to do nothing
        async def skip_integration():
            pass

        suite.run_integration_tests = skip_integration

    exit_code = await suite.run_all_tests()
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
