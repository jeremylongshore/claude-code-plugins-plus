import assert from 'node:assert/strict';
import test from 'node:test';

import { extractInternalLinks } from './internal-link-utils.mjs';

test('extractInternalLinks excludes every absolute URI scheme case-insensitively', () => {
  const html = [
    '<a href="https://example.com">web</a>',
    '<a href="JAVASCRIPT:alert(1)">script</a>',
    '<a href="vbscript:msgbox(1)">legacy script</a>',
    '<a href="  VBScript:msgbox(2)">mixed legacy script</a>',
    '<a href="data:text/plain,x">data</a>',
    '<a href="ftp://example.com/file">ftp</a>',
    '<a href="file:///etc/passwd">file</a>',
    '<a href="blob:https://example.com/id">blob</a>',
    '<a href="custom+app:open">custom</a>',
    '<a href="//cdn.example.com/file.js">scheme relative</a>',
    '<a href="/docs/start?view=all#top">internal</a>',
  ].join('');

  assert.deepEqual(extractInternalLinks(html, 'index.html'), [
    { href: '/docs/start', source: 'index.html' },
  ]);
});
