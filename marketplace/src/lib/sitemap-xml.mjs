const XML_ENTITIES = Object.freeze({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&apos;',
});

export function escapeXml(value) {
  const text = String(value);
  for (const character of text) {
    const codePoint = character.codePointAt(0);
    const valid =
      codePoint === 0x09 ||
      codePoint === 0x0a ||
      codePoint === 0x0d ||
      (codePoint >= 0x20 && codePoint <= 0xd7ff) ||
      (codePoint >= 0xe000 && codePoint <= 0xfffd) ||
      (codePoint >= 0x10000 && codePoint <= 0x10ffff);
    if (!valid) throw new TypeError(`XML value contains forbidden code point U+${codePoint.toString(16)}`);
  }
  return text.replace(/[&<>"']/g, (character) => XML_ENTITIES[character]);
}

export function buildSitemap({ siteUrl, staticPages, docsPages, pluginNames, skillSlugs }) {
  const pages = [
    ...staticPages.map((page) => ({ ...page, location: `${siteUrl}${page.url}` })),
    ...docsPages.map((page) => ({ ...page, location: `${siteUrl}${page.url}` })),
    ...pluginNames.map((name) => ({
      location: `${siteUrl}/plugins/${encodeURIComponent(name)}`,
      changefreq: 'weekly',
      priority: '0.6',
    })),
    ...skillSlugs.map((slug) => ({
      location: `${siteUrl}/skills/${encodeURIComponent(slug)}`,
      changefreq: 'weekly',
      priority: '0.5',
    })),
  ];

  const entries = pages
    .map(
      (page) => `  <url>
    <loc>${escapeXml(page.location)}</loc>
    <changefreq>${escapeXml(page.changefreq)}</changefreq>
    <priority>${escapeXml(page.priority)}</priority>
  </url>`,
    )
    .join('\n');

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${entries}
</urlset>`;
}
