#!/usr/bin/env python3
"""
Test suite for strongbird math extraction functionality.
"""

import asyncio
import sys
import re
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strongbird.browser import BrowserManager
from strongbird.extractor import StrongbirdExtractor


async def extract_content(source: str, process_math: bool = False, 
                         format_type: str = "markdown", include_metadata: bool = True):
    """Helper function to extract content using strongbird."""
    # Determine if source is URL or file
    is_url = source.startswith(('http://', 'https://', 'file://'))
    
    # Create browser manager
    browser_manager = BrowserManager(
        headless=True,
        browser_type="chromium",
        viewport_width=1920,
        viewport_height=1080,
    )
    
    # Create extractor
    extractor = StrongbirdExtractor(
        browser_manager=browser_manager,
        use_playwright=not is_url or is_url,  # Use playwright for URLs
        favor_precision=False,
    )
    
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


class MathExtractionTester:
    """Test math extraction functionality."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.fixtures_dir = self.test_dir / "fixtures"
        self.results = []
    
    def count_math_expressions(self, content: str) -> Dict[str, int]:
        """Count different types of math expressions in extracted content."""
        counts = {
            "inline_math": len(re.findall(r'\$[^$\n]+\$', content)),
            "display_math": len(re.findall(r'\$\$[^$]+\$\$', content, re.DOTALL)),
            "total_expressions": 0
        }
        counts["total_expressions"] = counts["inline_math"] + counts["display_math"]
        return counts
    
    def extract_math_examples(self, content: str, limit: int = 5) -> List[str]:
        """Extract examples of math expressions from content."""
        examples = []
        
        # Find inline math
        inline_matches = re.findall(r'\$[^$\n]+\$', content)
        examples.extend(inline_matches[:limit//2])
        
        # Find display math
        display_matches = re.findall(r'\$\$[^$]+\$\$', content, re.DOTALL)
        examples.extend([match.replace('\n', ' ').strip() for match in display_matches[:limit//2]])
        
        return examples[:limit]
    
    async def test_file(self, filename: str, expected_min_expressions: int = 0) -> Dict[str, Any]:
        """Test math extraction for a specific file."""
        filepath = self.fixtures_dir / filename
        
        if not filepath.exists():
            return {
                "file": filename,
                "status": "SKIP",
                "error": f"File not found: {filepath}",
                "math_count": {"total_expressions": 0}
            }
        
        try:
            # Extract content with math processing
            result = await extract_content(
                source=f"file://{filepath.absolute()}",
                process_math=True,
                format_type="markdown",
                include_metadata=False
            )
            
            if result is None:
                return {
                    "file": filename,
                    "status": "ERROR",
                    "error": "Extraction returned None",
                    "math_count": {"total_expressions": 0}
                }
            
            # Count math expressions
            math_count = self.count_math_expressions(result["content"])
            math_examples = self.extract_math_examples(result["content"])
            
            # Determine test status
            status = "PASS" if math_count["total_expressions"] >= expected_min_expressions else "FAIL"
            
            return {
                "file": filename,
                "status": status,
                "math_count": math_count,
                "math_examples": math_examples,
                "content_length": len(result["content"])
            }
            
        except Exception as e:
            return {
                "file": filename,
                "status": "ERROR",
                "error": str(e),
                "math_count": {"total_expressions": 0}
            }
    
    async def test_wikipedia_samples(self) -> List[Dict[str, Any]]:
        """Test math extraction on Wikipedia pages."""
        wikipedia_tests = [
            {
                "url": "https://en.wikipedia.org/wiki/Quadratic_formula",
                "name": "wikipedia_quadratic_formula",
                "min_expressions": 3
            },
            {
                "url": "https://en.wikipedia.org/wiki/Euler%27s_identity",
                "name": "wikipedia_eulers_identity", 
                "min_expressions": 2
            }
        ]
        
        results = []
        for test in wikipedia_tests:
            try:
                result = await extract_content(
                    source=test["url"],
                    process_math=True,
                    format_type="markdown",
                    include_metadata=False
                )
                
                if result is None:
                    results.append({
                        "file": test["name"],
                        "status": "ERROR",
                        "error": "Extraction returned None",
                        "math_count": {"total_expressions": 0}
                    })
                    continue
                
                math_count = self.count_math_expressions(result["content"])
                math_examples = self.extract_math_examples(result["content"])
                
                status = "PASS" if math_count["total_expressions"] >= test["min_expressions"] else "FAIL"
                
                results.append({
                    "file": test["name"],
                    "status": status,
                    "math_count": math_count,
                    "math_examples": math_examples,
                    "content_length": len(result["content"])
                })
                
            except Exception as e:
                results.append({
                    "file": test["name"],
                    "status": "ERROR",
                    "error": str(e),
                    "math_count": {"total_expressions": 0}
                })
        
        return results
    
    async def run_all_tests(self) -> None:
        """Run all math extraction tests."""
        print("🧮 Strongbird Math Extraction Test Suite")
        print("=" * 50)
        
        # Test local HTML fixtures
        local_tests = [
            ("comprehensive-math-test.html", 6),  # Expect at least 6 math expressions
            ("test-mathjax.html", 4)              # Expect at least 4 math expressions
        ]
        
        print("\n📁 Testing Local HTML Fixtures:")
        print("-" * 30)
        
        for filename, min_expressions in local_tests:
            result = await self.test_file(filename, min_expressions)
            self.results.append(result)
            self.print_test_result(result)
        
        # Test Wikipedia samples (with internet connection)
        print("\n🌐 Testing Wikipedia Samples:")
        print("-" * 30)
        
        try:
            wikipedia_results = await self.test_wikipedia_samples()
            self.results.extend(wikipedia_results)
            
            for result in wikipedia_results:
                self.print_test_result(result)
                
        except Exception as e:
            print(f"⚠️  Wikipedia tests skipped: {e}")
        
        # Print summary
        self.print_summary()
    
    def print_test_result(self, result: Dict[str, Any]) -> None:
        """Print individual test result."""
        status_icon = {
            "PASS": "✅",
            "FAIL": "❌", 
            "ERROR": "💥",
            "SKIP": "⏭️"
        }
        
        icon = status_icon.get(result["status"], "❓")
        filename = result["file"]
        math_count = result["math_count"]["total_expressions"]
        
        print(f"{icon} {filename}: {math_count} math expressions")
        
        if result["status"] == "ERROR":
            print(f"   Error: {result.get('error', 'Unknown error')}")
        elif result["status"] == "PASS" and result.get("math_examples"):
            print(f"   Examples: {', '.join(result['math_examples'][:2])}")
    
    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        
        total_tests = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        errors = len([r for r in self.results if r["status"] == "ERROR"])
        skipped = len([r for r in self.results if r["status"] == "SKIP"])
        
        print(f"   Total: {total_tests}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   💥 Errors: {errors}")
        print(f"   ⏭️  Skipped: {skipped}")
        
        total_math = sum(r["math_count"]["total_expressions"] for r in self.results)
        print(f"   🧮 Total math expressions found: {total_math}")
        
        # Exit with appropriate code
        if failed > 0 or errors > 0:
            print(f"\n❌ Some tests failed!")
            sys.exit(1)
        else:
            print(f"\n✅ All tests passed!")


async def main():
    """Run the math extraction test suite."""
    tester = MathExtractionTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())