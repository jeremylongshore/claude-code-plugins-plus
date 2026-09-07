const ABSOLUTE_URI = /^[a-z][a-z\d+.-]*:/i;

/**
 * Extract navigable same-site links from rendered anchor elements.
 * Absolute URI schemes are outside this validator's filesystem scope.
 */
export function extractInternalLinks(html, sourcePath) {
  const links = [];
  const hrefRegex = /<a[^>]+href=["']([^"']+)["']/gi;
  let match;

  while ((match = hrefRegex.exec(html)) !== null) {
    const href = match[1].trim();

    if (ABSOLUTE_URI.test(href) || href.startsWith('//') || href.startsWith('#')) continue;
    if (href.includes('${')) continue;

    const path = href.split('?')[0].split('#')[0];
    if (!path) continue;

    links.push({ href: path, source: sourcePath });
  }

  return links;
}
