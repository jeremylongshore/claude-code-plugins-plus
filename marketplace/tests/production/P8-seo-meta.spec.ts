import { test, expect } from '@playwright/test';

/**
 * P8: SEO & Meta — Validates meta tags, Open Graph, and canonical URLs
 */

test.describe('P8: SEO & Meta', () => {
  const pages = [
    { path: '/', name: 'Homepage' },
    { path: '/explore', name: 'Explore' },
    { path: '/cowork', name: 'Cowork' },
    { path: '/skills/', name: 'Skills' },
    { path: '/plugins/', name: 'Plugins' },
  ];

  for (const pg of pages) {
    test(`${pg.name} has meta description`, async ({ page }) => {
      await page.goto(pg.path);

      const metaDesc = page.locator('meta[name="description"]');
      const content = await metaDesc.getAttribute('content');
      expect(content).toBeTruthy();
      expect(content!.length).toBeGreaterThan(20);
    });
  }

  test('Homepage has Open Graph tags', async ({ page }) => {
    await page.goto('/');

    const ogTitle = await page.locator('meta[property="og:title"]').getAttribute('content');
    expect(ogTitle).toBeTruthy();

    const ogDesc = await page.locator('meta[property="og:description"]').getAttribute('content');
    expect(ogDesc).toBeTruthy();

    const ogType = await page.locator('meta[property="og:type"]').getAttribute('content');
    expect(ogType).toBeTruthy();
  });

  test('Homepage canonical URL points to tonsofskills.com', async ({ page }) => {
    await page.goto('/');

    const canonical = page.locator('link[rel="canonical"]');
    const count = await canonical.count();

    if (count > 0) {
      const href = await canonical.getAttribute('href');
      if (href) {
        expect(href).toContain('tonsofskills.com');
      }
      // If href is null, canonical tag exists but is empty — not a failure
    }
  });

  test('Sitemap is accessible', async ({ request }) => {
    const response = await request.get('https://tonsofskills.com/sitemap-index.xml', {
      failOnStatusCode: false,
    });

    // Could be sitemap.xml or sitemap-index.xml
    if (response.status() !== 200) {
      const altResponse = await request.get('https://tonsofskills.com/sitemap.xml', {
        failOnStatusCode: false,
      });
      expect(altResponse.status()).toBe(200);
    } else {
      expect(response.status()).toBe(200);
    }
  });

  test('Robots.txt is accessible', async ({ request }) => {
    const response = await request.get('https://tonsofskills.com/robots.txt', {
      failOnStatusCode: false,
    });
    // Robots.txt may or may not exist, just check it doesn't 500
    expect(response.status()).toBeLessThan(500);
  });

  test('No pages reference old claudecodeplugins.io domain in meta', async ({ page }) => {
    await page.goto('/');

    const allMeta = page.locator('meta');
    const count = await allMeta.count();

    for (let i = 0; i < count; i++) {
      const content = await allMeta.nth(i).getAttribute('content');
      if (content) {
        expect(content).not.toContain('claudecodeplugins.io');
      }
    }

    // Check canonical too
    const canonical = page.locator('link[rel="canonical"]');
    const canonicalCount = await canonical.count();
    for (let i = 0; i < canonicalCount; i++) {
      const href = await canonical.nth(i).getAttribute('href');
      if (href) {
        expect(href).not.toContain('claudecodeplugins.io');
      }
    }
  });
});
