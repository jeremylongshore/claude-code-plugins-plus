import assert from 'node:assert/strict';
import test from 'node:test';

import { buildSitemap, escapeXml } from '../src/lib/sitemap-xml.mjs';

test('escapeXml encodes all XML-significant characters', () => {
  assert.equal(escapeXml(`<tag a="x" b='y'>&`), '&lt;tag a=&quot;x&quot; b=&apos;y&apos;&gt;&amp;');
  assert.equal(escapeXml('tab\tline\nreturn\r'), 'tab\tline\nreturn\r');
  assert.throws(() => escapeXml('\u0001'), /forbidden code point U\+1/);
  assert.throws(() => escapeXml('\uFFFE'), /forbidden code point U\+fffe/);
  assert.throws(() => escapeXml('\uD800'), /forbidden code point U\+d800/);
});

test('buildSitemap cannot inject catalog or filesystem values into XML markup', () => {
  const xml = buildSitemap({
    siteUrl: 'https://tonsofskills.com',
    staticPages: [],
    docsPages: [{ url: '/docs/a?<SCRIPT>', changefreq: 'weekly', priority: '0.7' }],
    pluginNames: ['bad</loc><script>alert(1)</script>'],
    skillSlugs: ['skill&name'],
  });

  assert.doesNotMatch(xml, /<script>/i);
  assert.match(xml, /a\?&lt;SCRIPT&gt;/);
  assert.match(xml, /bad%3C%2Floc%3E%3Cscript%3Ealert\(1\)%3C%2Fscript%3E/);
  assert.match(xml, /skill%26name/);
});
