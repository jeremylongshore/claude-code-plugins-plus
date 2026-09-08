import { existsSync, realpathSync } from 'node:fs';
import { isAbsolute, relative, resolve, sep } from 'node:path';

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

function hrefAttribute(attributes) {
  let offset = 0;
  while (offset < attributes.length) {
    while (/\s/.test(attributes[offset] ?? '')) offset += 1;
    if (offset >= attributes.length || attributes[offset] === '/') break;

    const nameStart = offset;
    while (offset < attributes.length && !/[\s=/>]/.test(attributes[offset])) offset += 1;
    const name = attributes.slice(nameStart, offset).toLowerCase();
    while (/\s/.test(attributes[offset] ?? '')) offset += 1;
    if (attributes[offset] !== '=') continue;
    offset += 1;
    while (/\s/.test(attributes[offset] ?? '')) offset += 1;

    let value;
    const quote = attributes[offset];
    if (quote === '"' || quote === "'") {
      offset += 1;
      const valueStart = offset;
      while (offset < attributes.length && attributes[offset] !== quote) offset += 1;
      value = attributes.slice(valueStart, offset);
      if (offset < attributes.length) offset += 1;
    } else {
      const valueStart = offset;
      while (offset < attributes.length && !/[\s>]/.test(attributes[offset])) offset += 1;
      value = attributes.slice(valueStart, offset);
    }
    if (name === 'href') return value;
  }
  return null;
}

function isInside(root, candidate) {
  const child = relative(root, candidate);
  return child === '' || (!isAbsolute(child) && child !== '..' && !child.startsWith(`..${sep}`));
}

function decodeUrlPath(value) {
  let decoded = value;
  for (let count = 0; count < 3; count += 1) {
    let next;
    try {
      next = decodeURIComponent(decoded);
    } catch {
      return null;
    }
    if (next === decoded) break;
    decoded = next;
  }
  if (/[\u0000-\u001F\u007F]/.test(decoded)) return null;
  return decoded.replaceAll('\\', '/');
}

export function pathExistsInDist(distDirectory, href) {
  const decoded = decodeUrlPath(href);
  if (decoded === null) return false;
  let normalizedPath = decoded === '/' ? '' : decoded.replace(/^\/+/, '').replace(/\/$/, '');
  const distRoot = resolve(distDirectory);
  if (normalizedPath === '') normalizedPath = 'index.html';
  const candidates = [
    resolve(distRoot, normalizedPath, 'index.html'),
    resolve(distRoot, `${normalizedPath}.html`),
    resolve(distRoot, normalizedPath),
  ];
  let realRoot;
  try {
    realRoot = realpathSync(distRoot);
  } catch {
    return false;
  }
  return candidates.some((candidate) => {
    if (!isInside(distRoot, candidate) || !existsSync(candidate)) return false;
    try {
      return isInside(realRoot, realpathSync(candidate));
    } catch {
      return false;
    }
  });
}

/**
 * Extract navigable same-site links from rendered anchor elements.
 * Absolute URI schemes are outside this validator's filesystem scope.
 */
export function extractInternalLinks(html, sourcePath) {
  const links = [];
  const anchorRegex = /<a\b((?:[^>"']|"[^"]*"|'[^']*')*)>/gi;
  let match;

  while ((match = anchorRegex.exec(html)) !== null) {
    const rawHref = hrefAttribute(match[1]);
    if (rawHref === null) continue;
    const href = decodeHtmlReferences(rawHref).trim();

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
