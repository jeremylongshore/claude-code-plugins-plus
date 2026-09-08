import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import { extractInternalLinks, pathExistsInDist } from './internal-link-utils.mjs';

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
    '<a href="javascript&#58;alert(1)">numeric colon</a>',
    '<a href="jav&#x61;script&colon;alert(1)">encoded scheme</a>',
    '<a href="java&Tab;script&colon;alert(1)">control-obfuscated scheme</a>',
    '<a href="//cdn.example.com/file.js">scheme relative</a>',
    '<a data-href="/not-a-link">metadata</a>',
    '<a href = "/docs/spaced">spaced attribute</a>',
    '<a href=/docs/unquoted>unquoted attribute</a>',
    '<a href="/docs/start?view=all#top">internal</a>',
  ].join('');

  assert.deepEqual(extractInternalLinks(html, 'index.html'), [
    { href: '/docs/spaced', source: 'index.html' },
    { href: '/docs/unquoted', source: 'index.html' },
    { href: '/docs/start', source: 'index.html' },
  ]);
});

test('pathExistsInDist rejects lexical, encoded, and symlink traversal', () => {
  const root = mkdtempSync(join(tmpdir(), 'internal-links-'));
  const dist = join(root, 'dist');
  mkdirSync(join(dist, 'docs'), { recursive: true });
  writeFileSync(join(dist, 'index.html'), 'root');
  writeFileSync(join(dist, 'docs/index.html'), 'docs');
  writeFileSync(join(root, 'package.json'), '{}');
  symlinkSync(join(root, 'package.json'), join(dist, 'outside-link'));

  assert.equal(pathExistsInDist(dist, '/'), true);
  assert.equal(pathExistsInDist(dist, '/docs'), true);
  assert.equal(pathExistsInDist(dist, '/../../package.json'), false);
  assert.equal(pathExistsInDist(dist, '/%2e%2e/%2e%2e/package.json'), false);
  assert.equal(pathExistsInDist(dist, '/%252e%252e/%252e%252e/package.json'), false);
  assert.equal(pathExistsInDist(dist, '/outside-link'), false);
  assert.equal(pathExistsInDist(dist, '/bad%2'), false);
});
