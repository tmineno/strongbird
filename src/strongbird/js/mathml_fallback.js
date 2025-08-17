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
