"""Math equation processing module for Strongbird."""

import re
from typing import Optional, Dict, Any
from playwright.async_api import Page


class MathProcessor:
    """Process mathematical equations from various rendering engines."""
    
    # Unified JavaScript for math equation normalization
    # Based on external reviewer's recommendations
    UNIFIED_MATH_JS = r"""
(() => {
  const wrap = (tex, display) => display ? `\n$$${tex}$$\n` : `$${tex}$`;
  const replaced = new WeakSet();
  let processedCount = 0;

  // Helper to clean TeX content
  const cleanTex = (tex) => {
    return tex.trim()
      .replace(/^\s*\\begin\{equation\*?\}/, '')
      .replace(/\\end\{equation\*?\}\s*$/, '')
      .replace(/^\s*\\begin\{align\*?\}/, '')
      .replace(/\\end\{align\*?\}\s*$/, '')
      .trim();
  };

  // KaTeX - look for annotation elements with TeX content
  document.querySelectorAll('.katex-mathml semantics > annotation[encoding="application/x-tex"]').forEach(a => {
    const root = a.closest('.katex'); 
    if (!root || replaced.has(root)) return;
    
    const display = !!root.closest('.katex-display');
    const tex = cleanTex(a.textContent || '');
    if (!tex) return;
    
    // Try to preserve the original context by inserting into parent
    const parentP = root.closest('p');
    if (parentP && !display) {
      // For inline math, create a simple text node
      const textNode = document.createTextNode(wrap(tex, display));
      root.replaceWith(textNode);
    } else {
      // For display math or when no paragraph parent, create element
      const r = document.createElement(display ? 'p' : 'span'); 
      r.textContent = wrap(tex, display);
      r.className = 'math-converted';
      r.setAttribute('data-math', 'true');
      // Make it look like regular content
      if (display) {
        r.style.textAlign = 'center';
        r.style.margin = '1em 0';
      }
      root.replaceWith(r);
      replaced.add(r);
    }
    processedCount++;
  });

  // Wikipedia MediaWiki Math Extension - handle .mwe-math-element containers
  document.querySelectorAll('.mwe-math-element').forEach(container => {
    if (replaced.has(container)) return;
    
    const annotation = container.querySelector('annotation[encoding="application/x-tex"]');
    if (!annotation) return;
    
    const tex = cleanTex(annotation.textContent || '');
    if (!tex) return;
    
    const display = container.classList.contains('mwe-math-element-block');
    
    // Try to preserve the original context by inserting into parent
    const parentP = container.closest('p');
    if (parentP && !display) {
      // For inline math, create a simple text node within the paragraph
      const textNode = document.createTextNode(wrap(tex, display));
      container.replaceWith(textNode);
    } else {
      // For display math or when no paragraph parent, create element
      const r = document.createElement(display ? 'p' : 'span');
      r.textContent = wrap(tex, display);
      r.className = 'math-converted';
      r.setAttribute('data-math', 'true');
      // Make it look like regular content
      if (display) {
        r.style.textAlign = 'center';
        r.style.margin = '1em 0';
      }
      container.replaceWith(r);
      replaced.add(r);
    }
    processedCount++;
  });

  // Raw MathML / LaTeXML - extract TeX from annotations
  document.querySelectorAll('math > semantics > annotation[encoding="application/x-tex"]').forEach(a => {
    const math = a.closest('math'); 
    if (!math || replaced.has(math)) return;
    
    const display = (math.getAttribute('display') || '').toLowerCase() === 'block';
    const tex = cleanTex(a.textContent || '');
    if (!tex) return;
    
    const r = document.createElement(display ? 'div' : 'span'); 
    r.textContent = wrap(tex, display);
    r.className = 'math-converted';
    r.setAttribute('data-math', 'true');
    // Add content indicators for better Trafilatura recognition
    if (display) {
      r.setAttribute('role', 'math');
      r.style.display = 'block';
      r.style.margin = '0.5em 0';
    } else {
      r.style.display = 'inline';
    }
    math.replaceWith(r); 
    replaced.add(r);
    processedCount++;
  });

  // MathJax v3/v4 - use the MathJax API if available
  if (window.MathJax?.startup?.document?.math) {
    for (const m of MathJax.startup.document.math) {
      const root = m.typesetRoot; 
      if (!root || replaced.has(root)) continue;
      
      let tex = m.math || '';
      tex = cleanTex(tex);
      if (!tex) continue;
      
      const r = document.createElement(m.display ? 'div' : 'span'); 
      r.textContent = wrap(tex, m.display);
      r.className = 'math-converted';
      r.setAttribute('data-math', 'true');
      // Add content indicators for better Trafilatura recognition
      if (m.display) {
        r.setAttribute('role', 'math');
        r.style.display = 'block';
        r.style.margin = '0.5em 0';
      } else {
        r.style.display = 'inline';
      }
      root.replaceWith(r); 
      replaced.add(r);
      processedCount++;
    }
  }

  // MathJax v2 - look for script tags with math/tex content
  document.querySelectorAll('script[type^="math/tex"]').forEach(s => {
    if (replaced.has(s)) return;
    
    const tex = cleanTex(s.textContent || ''); 
    if (!tex) return;
    
    const display = s.type.includes('mode=display');
    const r = document.createElement(display ? 'div' : 'span'); 
    r.textContent = wrap(tex, display);
    r.className = 'math-converted';
    r.setAttribute('data-math', 'true');
    // Add content indicators for better Trafilatura recognition
    if (display) {
      r.setAttribute('role', 'math');
      r.style.display = 'block';
      r.style.margin = '0.5em 0';
    } else {
      r.style.display = 'inline';
    }
    s.replaceWith(r);
    replaced.add(r);
    processedCount++;
  });

  // Alternative KaTeX selectors for different versions
  document.querySelectorAll('.katex .katex-html').forEach(element => {
    const root = element.closest('.katex');
    if (!root || replaced.has(root)) return;
    
    // Try to find adjacent MathML with TeX annotation
    const mathml = root.querySelector('.katex-mathml annotation[encoding="application/x-tex"]');
    if (mathml) {
      const display = !!root.closest('.katex-display');
      const tex = cleanTex(mathml.textContent || '');
      if (!tex) return;
      
      const r = document.createElement(display ? 'div' : 'span');
      r.textContent = wrap(tex, display);
      r.className = 'math-converted';
      r.setAttribute('data-math', 'true');
      // Add content indicators for better Trafilatura recognition
      if (display) {
        r.setAttribute('role', 'math');
        r.style.display = 'block';
        r.style.margin = '0.5em 0';
      } else {
        r.style.display = 'inline';
      }
      root.replaceWith(r);
      replaced.add(r);
      processedCount++;
    }
  });

  // Return statistics for debugging
  return {
    processedCount,
    remainingMath: document.querySelectorAll('math:not(.math-converted)').length,
    remainingKatex: document.querySelectorAll('.katex:not(.math-converted)').length,
    remainingMathJax: document.querySelectorAll('mjx-container:not(.math-converted), .MathJax:not(.math-converted)').length
  };
})();
"""

    # Fallback MathML to TeX converter for remaining math elements
    MATHML_TO_TEX_JS = r"""
(() => {
  const mathmlToTex = (mathElement) => {
    // Simple MathML to TeX conversion for common elements
    // This is a basic fallback - not comprehensive
    
    const nodeName = mathElement.nodeName.toLowerCase();
    const children = Array.from(mathElement.children);
    
    switch (nodeName) {
      case 'mi': // identifier
        return mathElement.textContent || '';
      case 'mn': // number
        return mathElement.textContent || '';
      case 'mo': // operator
        const op = mathElement.textContent || '';
        // Map common operators
        const opMap = {
          '×': '\\times',
          '÷': '\\div',
          '±': '\\pm',
          '∓': '\\mp',
          '≤': '\\leq',
          '≥': '\\geq',
          '≠': '\\neq',
          '≈': '\\approx',
          '∞': '\\infty',
          '∑': '\\sum',
          '∏': '\\prod',
          '∫': '\\int',
          '√': '\\sqrt',
          'α': '\\alpha',
          'β': '\\beta',
          'γ': '\\gamma',
          'δ': '\\delta',
          'ε': '\\epsilon',
          'π': '\\pi',
          'θ': '\\theta',
          'λ': '\\lambda',
          'μ': '\\mu',
          'σ': '\\sigma',
          'φ': '\\phi',
          'ψ': '\\psi',
          'ω': '\\omega'
        };
        return opMap[op] || op;
      case 'mrow': // row of elements
        return children.map(child => mathmlToTex(child)).join(' ');
      case 'msup': // superscript
        if (children.length >= 2) {
          const base = mathmlToTex(children[0]);
          const sup = mathmlToTex(children[1]);
          return `${base}^{${sup}}`;
        }
        return '';
      case 'msub': // subscript
        if (children.length >= 2) {
          const base = mathmlToTex(children[0]);
          const sub = mathmlToTex(children[1]);
          return `${base}_{${sub}}`;
        }
        return '';
      case 'msubsup': // both subscript and superscript
        if (children.length >= 3) {
          const base = mathmlToTex(children[0]);
          const sub = mathmlToTex(children[1]);
          const sup = mathmlToTex(children[2]);
          return `${base}_{${sub}}^{${sup}}`;
        }
        return '';
      case 'mfrac': // fraction
        if (children.length >= 2) {
          const num = mathmlToTex(children[0]);
          const den = mathmlToTex(children[1]);
          return `\\frac{${num}}{${den}}`;
        }
        return '';
      case 'msqrt': // square root
        if (children.length >= 1) {
          const content = mathmlToTex(children[0]);
          return `\\sqrt{${content}}`;
        }
        return '';
      case 'mroot': // nth root
        if (children.length >= 2) {
          const content = mathmlToTex(children[0]);
          const index = mathmlToTex(children[1]);
          return `\\sqrt[${index}]{${content}}`;
        }
        return '';
      case 'munder': // underscript
        if (children.length >= 2) {
          const base = mathmlToTex(children[0]);
          const under = mathmlToTex(children[1]);
          return `\\underset{${under}}{${base}}`;
        }
        return '';
      case 'mover': // overscript
        if (children.length >= 2) {
          const base = mathmlToTex(children[0]);
          const over = mathmlToTex(children[1]);
          return `\\overset{${over}}{${base}}`;
        }
        return '';
      case 'munderover': // both under and over
        if (children.length >= 3) {
          const base = mathmlToTex(children[0]);
          const under = mathmlToTex(children[1]);
          const over = mathmlToTex(children[2]);
          return `\\overset{${over}}{\\underset{${under}}{${base}}}`;
        }
        return '';
      case 'mtable': // table/matrix
        const rows = children.filter(child => child.nodeName.toLowerCase() === 'mtr');
        if (rows.length > 0) {
          const texRows = rows.map(row => {
            const cells = Array.from(row.children).filter(cell => 
              cell.nodeName.toLowerCase() === 'mtd'
            );
            return cells.map(cell => mathmlToTex(cell)).join(' & ');
          });
          return `\\begin{matrix} ${texRows.join(' \\\\ ')} \\end{matrix}`;
        }
        return '';
      default:
        // For unknown elements, try to process children
        if (children.length > 0) {
          return children.map(child => mathmlToTex(child)).join(' ');
        }
        return mathElement.textContent || '';
    }
  };

  let processedCount = 0;
  const wrap = (tex, display) => display ? `\n$$${tex}$$\n` : `$${tex}$`;

  // Process remaining math elements that weren't converted by the main pass
  document.querySelectorAll('math:not(.math-converted)').forEach(math => {
    try {
      const display = (math.getAttribute('display') || '').toLowerCase() === 'block';
      const tex = mathmlToTex(math);
      
      if (tex && tex.trim()) {
        const r = document.createElement(display ? 'div' : 'span');
        r.textContent = wrap(tex.trim(), display);
        r.className = 'math-converted mathml-fallback';
        r.setAttribute('data-math', 'true');
        // Add content indicators for better Trafilatura recognition
        if (display) {
          r.setAttribute('role', 'math');
          r.style.display = 'block';
          r.style.margin = '0.5em 0';
        } else {
          r.style.display = 'inline';
        }
        math.replaceWith(r);
        processedCount++;
      }
    } catch (e) {
      console.warn('Failed to convert MathML element:', e);
    }
  });

  return { fallbackProcessedCount: processedCount };
})();
"""

    def __init__(self, enable_fallback: bool = True):
        """
        Initialize math processor.
        
        Args:
            enable_fallback: Enable MathML to TeX fallback conversion
        """
        self.enable_fallback = enable_fallback
    
    async def normalize_math_equations(self, page: Page, wait_for_math: bool = True) -> Dict[str, Any]:
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
                    timeout=5000
                )
            except:
                # Continue if no math elements found
                pass
        
        # Run the unified math processing script
        result = await page.evaluate(self.UNIFIED_MATH_JS)
        
        # Run fallback MathML converter if enabled and there are remaining elements
        if self.enable_fallback and result.get('remainingMath', 0) > 0:
            fallback_result = await page.evaluate(self.MATHML_TO_TEX_JS)
            result.update(fallback_result)
        
        return result
    
    def is_math_content_present(self, html: str) -> bool:
        """
        Check if HTML content likely contains mathematical equations.
        
        Args:
            html: HTML content to check
            
        Returns:
            True if math content is detected
        """
        # Check for common math rendering indicators
        math_indicators = [
            r'class="katex',
            r'class="MathJax',
            r'<math[>\s]',
            r'<mjx-container',
            r'type="math/tex',
            r'MathJax\.startup',
            r'katex\.render',
            r'\\begin\{equation',
            r'\\begin\{align',
            r'\$\$.*\$\$',  # Display math
            r'\$[^$]+\$',   # Inline math (basic check)
        ]
        
        for pattern in math_indicators:
            if re.search(pattern, html, re.IGNORECASE | re.DOTALL):
                return True
        
        return False
    
    def clean_converted_markup(self, html: str) -> str:
        """
        Clean up any remaining math markup after conversion.
        
        Args:
            html: HTML content to clean
            
        Returns:
            Cleaned HTML content
        """
        # Remove empty math containers that might remain
        patterns = [
            r'<span class="katex[^"]*">\s*</span>',
            r'<div class="katex[^"]*">\s*</div>',
            r'<mjx-container[^>]*>\s*</mjx-container>',
            r'<script type="math/tex[^"]*">\s*</script>',
        ]
        
        cleaned = html
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.DOTALL)
        
        return cleaned