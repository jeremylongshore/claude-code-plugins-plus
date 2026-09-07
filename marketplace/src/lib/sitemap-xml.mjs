const XML_ENTITIES = Object.freeze({
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&apos;',
});

export function escapeXml(value) {
  return String(value).replace(/[&<>"']/g, (character) => XML_ENTITIES[character]);
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
