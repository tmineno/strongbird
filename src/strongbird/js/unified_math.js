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
