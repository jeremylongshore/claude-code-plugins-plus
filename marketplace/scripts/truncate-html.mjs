/**
 * Return a deterministic, structurally valid HTML prefix.
 *
 * The limit is measured in Unicode code points in the serialized output. The
 * truncator reserves space for every closing tag and the ellipsis before it
 * accepts another token, so a truncated result never exceeds `maxLength`.
 * Character references and Unicode code points are indivisible text atoms.
 * Input that already fits is returned byte-for-byte unchanged.
 */

const VOID_ELEMENTS = new Set([
  'area',
  'base',
  'br',
  'col',
  'embed',
  'hr',
  'img',
  'input',
  'link',
  'meta',
  'param',
  'source',
  'track',
  'wbr',
]);

const ELLIPSIS = '…';

function serializedLength(value) {
  return Array.from(value).length;
}

function findTagEnd(html, start) {
  if (html.startsWith('<!--', start)) {
    const commentEnd = html.indexOf('-->', start + 4);
    return commentEnd === -1 ? -1 : commentEnd + 2;
  }

  let quote = null;
  for (let cursor = start + 1; cursor < html.length; cursor++) {
    const character = html[cursor];
    if (quote) {
      if (character === quote) quote = null;
      continue;
    }
    if (character === '"' || character === "'") {
      quote = character;
      continue;
    }
    if (character === '>') return cursor;
  }
  return -1;
}

function readTextAtom(html, start) {
  if (html[start] === '&') {
    const reference = /^&(?:#[0-9]+|#[xX][0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]+);/.exec(
      html.slice(start),
    );
    if (reference) return reference[0];
  }

  const codePoint = html.codePointAt(start);
  return String.fromCodePoint(codePoint);
}

function tagName(token, closing = false) {
  const expression = closing
    ? /^<\s*\/\s*([A-Za-z][\w:-]*)/
    : /^<\s*([A-Za-z][\w:-]*)/;
  return expression.exec(token)?.[1]?.toLowerCase() ?? null;
}

function closingLength(stack) {
  return stack.reduce((total, tag) => total + serializedLength(`</${tag}>`), 0);
}

export function truncateHtml(html, maxLength) {
  if (typeof html !== 'string') throw new TypeError('html must be a string');
  if (!Number.isSafeInteger(maxLength) || maxLength < 0) {
    throw new RangeError('maxLength must be a non-negative safe integer');
  }

  if (serializedLength(html) <= maxLength) return html;
  if (maxLength < serializedLength(ELLIPSIS)) return '';

  const output = [];
  const stack = [];
  let used = 0;
  let cursor = 0;
  let truncated = false;

  const canAppend = (value, nextStack = stack) =>
    used +
      serializedLength(value) +
      serializedLength(ELLIPSIS) +
      closingLength(nextStack) <=
    maxLength;

  while (cursor < html.length) {
    if (html[cursor] !== '<') {
      const atom = readTextAtom(html, cursor);
      if (!canAppend(atom)) {
        truncated = true;
        break;
      }
      output.push(atom);
      used += serializedLength(atom);
      cursor += atom.length;
      continue;
    }

    const end = findTagEnd(html, cursor);
    if (end === -1) {
      truncated = true;
      break;
    }

    const token = html.slice(cursor, end + 1);
    const closingName = tagName(token, true);
    if (closingName) {
      if (stack.at(-1) !== closingName) {
        truncated = true;
        break;
      }

      const canonicalClose = `</${closingName}>`;
      output.push(canonicalClose);
      used += serializedLength(canonicalClose);
      stack.pop();
      cursor = end + 1;
      continue;
    }

    const openingName = tagName(token);
    const isSelfClosing = /\/\s*>$/.test(token);
    const opensElement = openingName && !isSelfClosing && !VOID_ELEMENTS.has(openingName);
    const nextStack = opensElement ? [...stack, openingName] : stack;

    if (!canAppend(token, nextStack)) {
      truncated = true;
      break;
    }

    output.push(token);
    used += serializedLength(token);
    if (opensElement) stack.push(openingName);
    cursor = end + 1;
  }

  if (!truncated && cursor === html.length) return output.join('');

  output.push(ELLIPSIS);
  for (let index = stack.length - 1; index >= 0; index--) {
    output.push(`</${stack[index]}>`);
  }
  return output.join('');
}
