import type { APIRoute } from 'astro';
import { readFileSync } from 'fs';
import { join } from 'path';

// Generate sitemap.xml from marketplace catalog
export const GET: APIRoute = async () => {
  const siteUrl = 'https://tonsofskills.com';

  // Load marketplace catalog
  const catalogPath = join(process.cwd(), '../.claude-plugin/marketplace.json');
  const catalog = JSON.parse(readFileSync(catalogPath, 'utf-8'));

  // Load skills catalog
  const skillsCatalogPath = join(process.cwd(), 'src/data/skills-catalog.json');
  const skillsCatalog = JSON.parse(readFileSync(skillsCatalogPath, 'utf-8'));

  // Static pages
  const staticPages = [
    { url: '/', priority: '1.0', changefreq: 'daily' },
    { url: '/explore', priority: '0.9', changefreq: 'daily' },
    { url: '/skills', priority: '0.9', changefreq: 'daily' },
    { url: '/cowork', priority: '0.8', changefreq: 'weekly' },
    { url: '/collections', priority: '0.8', changefreq: 'weekly' },
    { url: '/compare', priority: '0.8', changefreq: 'weekly' },
    { url: '/getting-started', priority: '0.9', changefreq: 'weekly' },
    { url: '/tools', priority: '0.9', changefreq: 'weekly' },
    { url: '/sponsor', priority: '0.7', changefreq: 'weekly' },
    { url: '/privacy', priority: '0.5', changefreq: 'monthly' },
    { url: '/terms', priority: '0.5', changefreq: 'monthly' },
    { url: '/acceptable-use', priority: '0.5', changefreq: 'monthly' },
    { url: '/skill-enhancers', priority: '0.8', changefreq: 'weekly' },
    { url: '/spotlight', priority: '0.8', changefreq: 'weekly' },
  ];

  // Generate XML
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${staticPages.map(page => `  <url>
    <loc>${siteUrl}${page.url}</loc>
    <changefreq>${page.changefreq}</changefreq>
    <priority>${page.priority}</priority>
  </url>`).join('\n')}
${catalog.plugins.map((plugin: any) => `  <url>
    <loc>${siteUrl}/plugins/${encodeURIComponent(plugin.name)}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.6</priority>
  </url>`).join('\n')}
${skillsCatalog.skills.map((skill: any) => `  <url>
    <loc>${siteUrl}/skills/${encodeURIComponent(skill.slug)}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.5</priority>
  </url>`).join('\n')}
</urlset>`;

  return new Response(sitemap, {
    headers: {
      'Content-Type': 'application/xml',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
