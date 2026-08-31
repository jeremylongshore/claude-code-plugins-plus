import assert from 'node:assert/strict';
import test from 'node:test';

import { inlineFormat, isSafeLinkTarget, mdToHtml } from './md-to-html.mjs';

test('keeps inline code opaque and escapes its contents', () => {
  for (const identifier of [
    'QUERY_ATTRIBUTION_HISTORY',
    'VALIDATION_MODE',
    'MATCH_BY_COLUMN_NAME',
  ]) {
    assert.equal(inlineFormat(`Use \`${identifier}\`.`), `Use <code>${identifier}</code>.`);
  }

  assert.equal(
    inlineFormat('`<img src=x onerror=alert(1)> **not bold** [not a link](javascript:x)`'),
    '<code>&lt;img src=x onerror=alert(1)&gt; **not bold** [not a link](javascript:x)</code>',
  );
  assert.equal(inlineFormat('``a`b``'), '<code>a`b</code>');
});

test('handles unmatched and multiline backticks deterministically', () => {
  assert.equal(
    inlineFormat('before `QUERY_ATTRIBUTION_HISTORY after'),
    'before `QUERY_ATTRIBUTION_HISTORY after',
  );
  assert.equal(inlineFormat('`line 1\nline_2`'), '<code>line 1\nline_2</code>');
  assert.equal(inlineFormat('before ``code` after'), 'before ``code` after');
});

test('joins soft-wrapped paragraphs before resolving multiline inline code', () => {
  const markdown = [
    'The warehouse query does not prove the absence of an account-level monitor. Inspect both',
    'levels and report serverless coverage separately. Do not use `CREATE OR REPLACE RESOURCE',
    'MONITOR` as an audit shortcut because replacing an existing guardrail changes live state.',
  ].join('\n');

  assert.equal(
    mdToHtml(markdown),
    '<p>The warehouse query does not prove the absence of an account-level monitor. Inspect both levels and report serverless coverage separately. Do not use <code>CREATE OR REPLACE RESOURCE MONITOR</code> as an audit shortcut because replacing an existing guardrail changes live state.</p>',
  );
});

test('preserves nested formatting without crossing code or word boundaries', () => {
  assert.equal(
    inlineFormat('**bold *italic* and `VALIDATION_MODE`**'),
    '<strong>bold <em>italic</em> and <code>VALIDATION_MODE</code></strong>',
  );
  assert.equal(inlineFormat('***nested***'), '<strong><em>nested</em></strong>');
  assert.equal(inlineFormat('QUERY_ATTRIBUTION_HISTORY'), 'QUERY_ATTRIBUTION_HISTORY');
  assert.equal(
    inlineFormat('[**Safe** `MATCH_BY_COLUMN_NAME`](https://docs.example.test/path)'),
    '<a href="https://docs.example.test/path"><strong>Safe</strong> <code>MATCH_BY_COLUMN_NAME</code></a>',
  );
});

test('escapes raw Markdown HTML instead of passing executable elements to set:html', () => {
  const raw = [
    '<script>alert(1)</script>',
    '<style>body{display:none}</style>',
    '<img src=x onerror="alert(1)">',
    '<svg><animate onbegin=alert(1) /></svg>',
  ].join(' ');
  const rendered = mdToHtml(raw);

  assert.equal(rendered.includes('<script'), false);
  assert.equal(rendered.includes('<style'), false);
  assert.equal(rendered.includes('<img'), false);
  assert.equal(rendered.includes('<svg'), false);
  assert.match(rendered, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  assert.match(rendered, /&lt;img src=x onerror=&quot;alert\(1\)&quot;&gt;/);
});

test('rejects executable, obfuscated, and attribute-injection link targets', () => {
  const dangerousTargets = [
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    'java%73cript%3Aalert(1)',
    'javascript&#58;alert(1)',
    'java%0ascript:alert(1)',
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox(1)',
    'http://example.test/insecure',
    '//evil.example/steal',
    'https://safe.example/"onmouseover="alert(1)',
    'javascript%252525252525252525253Aalert(1)',
  ];

  for (const target of dangerousTargets) {
    assert.equal(isSafeLinkTarget(target), false, target);
    const rendered = inlineFormat(`[label](${target})`);
    assert.equal(rendered, 'label', target);
    assert.equal(rendered.includes('<a '), false, target);
  }

  assert.equal(
    inlineFormat('[label](https://safe.example/" onclick="alert(1))'),
    'label',
    'quotes and whitespace cannot break out of href',
  );
});

test('retains explicitly safe web, mail, anchor, and relative links with escaped attributes', () => {
  const safeTargets = [
    'https://docs.example.test/path?a=1&b=2',
    'https://docs.example.test/Simpson%27s_paradox',
    'https://docs.example.test/%22quoted%22',
    'mailto:owner@example.test',
    '#prerequisites',
    '#',
    'references/official-sources.md',
    './neighbor.md',
    '../parent.md',
    '/docs/start/',
    '?view=compact',
  ];

  for (const target of safeTargets) {
    assert.equal(isSafeLinkTarget(target), true, target);
    assert.equal(
      inlineFormat(`[label](${target})`),
      `<a href="${target.replace(/&/g, '&amp;')}">label</a>`,
      target,
    );
  }
});

test('preserves block structure while applying safe inline rendering everywhere', () => {
  const markdown = [
    '# Heading with `VALIDATION_MODE`',
    '',
    '- **Bold** and [docs](references/guide.md)',
    '1. *Italic* and `MATCH_BY_COLUMN_NAME`',
    '',
    '| Option | Value |',
    '| --- | --- |',
    '| Mode | `QUERY_ATTRIBUTION_HISTORY` |',
    '',
    '```sql',
    'SELECT MATCH_BY_COLUMN_NAME, "<script>";',
    '```',
  ].join('\n');

  assert.equal(
    mdToHtml(markdown),
    [
      '<h1>Heading with <code>VALIDATION_MODE</code></h1>',
      '<ul>',
      '<li><strong>Bold</strong> and <a href="references/guide.md">docs</a></li>',
      '</ul>',
      '<ol>',
      '<li><em>Italic</em> and <code>MATCH_BY_COLUMN_NAME</code></li>',
      '</ol>',
      '<table><thead><tr>',
      '<th>Option</th>',
      '<th>Value</th>',
      '</tr></thead><tbody>',
      '<tr>',
      '<td>Mode</td>',
      '<td><code>QUERY_ATTRIBUTION_HISTORY</code></td>',
      '</tr>',
      '</tbody></table>',
      '<pre data-lang="sql"><code>',
      'SELECT MATCH_BY_COLUMN_NAME, &quot;&lt;script&gt;&quot;;',
      '</code></pre>',
    ].join('\n'),
  );
});

test('flushes buffered paragraphs and list items at every block boundary and EOF', () => {
  const markdown = [
    'soft paragraph',
    'at heading boundary',
    '## Heading',
    '- wrapped list item',
    '  continuation',
    '',
    'paragraph before table',
    '| A | B |',
    '| --- | --- |',
    '| one | two |',
    'paragraph before fence',
    '```txt',
    '<unsafe>',
    '```',
    'final',
    'paragraph',
  ].join('\n');

  assert.equal(
    mdToHtml(markdown),
    [
      '<p>soft paragraph at heading boundary</p>',
      '<h2>Heading</h2>',
      '<ul>',
      '<li>wrapped list item continuation</li>',
      '</ul>',
      '<p>paragraph before table</p>',
      '<table><thead><tr>',
      '<th>A</th>',
      '<th>B</th>',
      '</tr></thead><tbody>',
      '<tr>',
      '<td>one</td>',
      '<td>two</td>',
      '</tr>',
      '</tbody></table>',
      '<p>paragraph before fence</p>',
      '<pre data-lang="txt"><code>',
      '&lt;unsafe&gt;',
      '</code></pre>',
      '<p>final paragraph</p>',
    ].join('\n'),
  );
});
