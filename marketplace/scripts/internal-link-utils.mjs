const ABSOLUTE_URI = /^[a-z][a-z\d+.-]*:/i;
const NAMED_REFERENCES = Object.freeze({
  amp: '&',
  colon: ':',
  period: '.',
  plus: '+',
  Tab: '\t',
  NewLine: '\n',
});

function decodeHtmlReferences(value) {
  return value.replace(
    /&#(?:x([\da-f]+)|([\d]+));?|&([A-Za-z]+);/gi,
    (reference, hexadecimal, decimal, named) => {
      if (named) return NAMED_REFERENCES[named] ?? reference;
      const codePoint = Number.parseInt(hexadecimal ?? decimal, hexadecimal ? 16 : 10);
      if (!Number.isSafeInteger(codePoint) || codePoint < 0 || codePoint > 0x10ffff) {
        return '\uFFFD';
      }
      return String.fromCodePoint(codePoint);
    },
  );
}

/**
 * Extract navigable same-site links from rendered anchor elements.
 * Absolute URI schemes are outside this validator's filesystem scope.
 */
export function extractInternalLinks(html, sourcePath) {
  const links = [];
  const hrefRegex = /<a[^>]+href=["']([^"']+)["']/gi;
  let match;

  while ((match = hrefRegex.exec(html)) !== null) {
    const href = decodeHtmlReferences(match[1]).trim();

    const schemeCandidate = href.replace(/[\u0000-\u0020]/g, '');
    if (
      ABSOLUTE_URI.test(schemeCandidate) ||
      href.startsWith('//') ||
      href.startsWith('#')
    ) {
      continue;
    }
    if (href.includes('${')) continue;

    const path = href.split('?')[0].split('#')[0];
    if (!path) continue;

    links.push({ href: path, source: sourcePath });
  }

  return links;
}
