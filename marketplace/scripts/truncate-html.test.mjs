import assert from 'node:assert/strict';
import test from 'node:test';

import { truncateHtml } from './truncate-html.mjs';

const length = (value) => Array.from(value).length;

function assertBalanced(html) {
  const voidElements = new Set(['br', 'hr', 'img', 'input', 'meta', 'link', 'source', 'wbr']);
  const stack = [];
  for (const match of html.matchAll(/<\/?([A-Za-z][\w:-]*)\b[^>]*>/g)) {
    const token = match[0];
    const name = match[1].toLowerCase();
    if (token.startsWith('</')) {
      assert.equal(stack.pop(), name, `unexpected closing tag in ${html}`);
    } else if (!token.endsWith('/>') && !voidElements.has(name)) {
      stack.push(name);
    }
  }
  assert.deepEqual(stack, [], `unclosed tags in ${html}`);
}

test('returns full HTML byte-for-byte before and at the limit', () => {
  const html = '<article><p>Complete page.</p><hr></article>';
  assert.equal(truncateHtml(html, length(html) + 1), html);
  assert.equal(truncateHtml(html, length(html)), html);
});

test('truncates one character after the boundary and keeps nested markup balanced', () => {
  const html = '<article><p>Hello <strong>nested world</strong>.</p></article>';
  const result = truncateHtml(html, length(html) - 1);

  assert.notEqual(result, html);
  assert.ok(result.endsWith('</article>'));
  assert.ok(result.includes('…'));
  assert.ok(length(result) <= length(html) - 1);
  assertBalanced(result);
});

test('never splits Unicode scalar values or serialized character references', () => {
  const html = '<p>A😀B &amp; C &#128640; D</p>';
  for (let limit = 1; limit < length(html); limit++) {
    const result = truncateHtml(html, limit);
    assert.equal(
      [...result].some((character) => {
        const codePoint = character.codePointAt(0);
        return codePoint >= 0xd800 && codePoint <= 0xdfff;
      }),
      false,
    );
    assert.doesNotMatch(result, /&(?:#(?:x[\da-f]*)?|[a-z][a-z0-9]*)?$/i);
    assert.doesNotMatch(result, /&(?:#(?:x[\da-f]*)?|[a-z][a-z0-9]*)?…/i);
    assert.ok(length(result) <= limit);
    assertBalanced(result);
  }
});

test('closes nested code blocks when the limit falls inside escaped code', () => {
  const html =
    '<section><pre data-lang="html"><code>const rocket = "🚀"; &lt;tag attr=&quot;x&quot;&gt;;\nnext line</code></pre></section>';
  const result = truncateHtml(html, 78);

  assert.match(result, /^<section><pre data-lang="html"><code>/);
  assert.match(result, /…<\/code><\/pre><\/section>$/);
  assert.doesNotMatch(result, /&(?:lt|quot|gt)?…/);
  assert.ok(length(result) <= 78);
  assertBalanced(result);
});

test('handles void elements and quoted greater-than signs in attributes', () => {
  const html = '<p data-label="a > b">left<br>right after the boundary</p>';
  const result = truncateHtml(html, 42);

  assert.match(result, /^<p data-label="a > b">/);
  assertBalanced(result);
  assert.ok(length(result) <= 42);
});

test('uses only valid bounded inputs', () => {
  assert.equal(truncateHtml('<p>x</p>', 0), '');
  assert.throws(() => truncateHtml('<p>x</p>', -1), RangeError);
  assert.throws(() => truncateHtml('<p>x</p>', 1.5), RangeError);
  assert.throws(() => truncateHtml(null, 10), TypeError);
});
