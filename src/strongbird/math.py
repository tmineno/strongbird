"""Math equation processing module for Strongbird."""

import re
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import Page


class MathProcessor:
    """Process mathematical equations from various rendering engines."""

    def __init__(self, enable_fallback: bool = True):
        """
        Initialize math processor.

        Args:
            enable_fallback: Enable MathML to TeX fallback conversion
        """
        self.enable_fallback = enable_fallback
        self.js_scripts = self._load_js_scripts()

    def _load_js_scripts(self) -> Dict[str, str]:
        """
        Load JavaScript files from js/ directory.

        Returns:
            Dictionary with script names and their content
        """
        js_dir = Path(__file__).parent / "js"
        scripts = {}

        # Load unified math processing script
        unified_math_file = js_dir / "unified_math.js"
        if unified_math_file.exists():
            scripts["unified_math"] = unified_math_file.read_text(encoding="utf-8")

        # Load MathML fallback script
        mathml_fallback_file = js_dir / "mathml_fallback.js"
        if mathml_fallback_file.exists():
            scripts["mathml_fallback"] = mathml_fallback_file.read_text(
                encoding="utf-8"
            )

        return scripts

    async def normalize_math_equations(
        self, page: Page, wait_for_math: bool = True
    ) -> Dict[str, Any]:
        """
        Normalize math equations in the page to TeX format.

        Args:
            page: Playwright page instance
            wait_for_math: Wait for math elements to appear before processing

        Returns:
            Dictionary with processing statistics
        """
        if wait_for_math:
            # Wait for math elements to appear (with timeout)
            try:
                await page.wait_for_selector(
                    "mjx-container, .katex, math, script[type^='math/tex'], .MathJax",
                    timeout=5000,
                )
            except Exception:
                # Continue if no math elements found
                pass

        # Run the unified math processing script
        if "unified_math" in self.js_scripts:
            result = await page.evaluate(self.js_scripts["unified_math"])
        else:
            result = {"processedCount": 0, "remainingMath": 0}

        # Run fallback MathML converter if enabled and there are remaining elements
        if self.enable_fallback and result.get("remainingMath", 0) > 0:
            if "mathml_fallback" in self.js_scripts:
                fallback_result = await page.evaluate(
                    self.js_scripts["mathml_fallback"]
                )
                result.update(fallback_result)

        return result

    def is_math_content_present(self, html: str) -> bool:
        """
        Check if HTML content likely contains mathematical equations.

        Args:
            html: HTML content to check

        Returns:
            True if math content is likely present
        """
        # Math-related selectors and patterns
        math_indicators = [
            # KaTeX
            r'class="katex"',
            r"katex\.min\.(css|js)",
            # MathJax
            r"MathJax",
            r"mathjax",
            r"script.*math/tex",
            r'type="math/tex"',
            # MathML
            r"<math[>\s]",
            r'xmlns="http://www\.w3\.org/1998/Math/MathML"',
            # Wikipedia math
            r'class="mwe-math',
            # General LaTeX-like patterns
            r"\$\$.*\$\$",
            r"\\\(.*\\\)",
            r"\\\[.*\\\]",
            r"\\begin\{equation",
            r"\\frac\{",
            r"\\sqrt\{",
            r"\\sum_",
            r"\\int_",
        ]

        for pattern in math_indicators:
            if re.search(pattern, html, re.IGNORECASE | re.DOTALL):
                return True

        return False

    def extract_math_from_text(self, text: str) -> Optional[str]:
        """
        Extract and clean mathematical notation from text.

        Args:
            text: Text content that may contain math

        Returns:
            Cleaned mathematical notation or None
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text.strip())

        # Look for LaTeX-style math delimiters
        inline_patterns = [
            r"\$([^$\n]+)\$",
            r"\\\(([^)]+)\\\)",
        ]

        display_patterns = [
            r"\$\$([^$]+)\$\$",
            r"\\\[([^\]]+)\\\]",
            r"\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}",
            r"\\begin\{align\*?\}(.*?)\\end\{align\*?\}",
        ]

        # Check for display math first (longer matches)
        for pattern in display_patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                math_content = match.group(1).strip()
                if math_content:
                    return f"$${math_content}$$"

        # Check for inline math
        for pattern in inline_patterns:
            match = re.search(pattern, text)
            if match:
                math_content = match.group(1).strip()
                if math_content:
                    return f"${math_content}$"

        return None
