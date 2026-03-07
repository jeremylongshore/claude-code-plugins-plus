import { test, expect } from '@playwright/test';

/**
 * P7: Performance — Basic performance checks on production
 */

test.describe('P7: Performance', () => {
  const criticalPages = ['/', '/explore', '/cowork', '/skills/', '/plugins/'];

  for (const path of criticalPages) {
    test(`${path} loads within 5 seconds`, async ({ page }) => {
      const start = Date.now();
      const response = await page.goto(path, { waitUntil: 'domcontentloaded' });
      const duration = Date.now() - start;

      expect(response?.status()).toBe(200);
      expect(duration).toBeLessThan(5000);
    });
  }

  test('Homepage does not have excessively long HTML lines (iOS Safari compat)', async ({ request }) => {
    const response = await request.get('https://tonsofskills.com');
    const html = await response.text();
    const lines = html.split('\n');

    // iOS Safari fails on lines > 5000 chars
    const longLines = lines.filter(line => line.length > 5000);
    expect(longLines.length).toBe(0);
  });

  test('No broken images on homepage', async ({ page }) => {
    await page.goto('/');

    const images = page.locator('img');
    const count = await images.count();

    for (let i = 0; i < count; i++) {
      const img = images.nth(i);
      const naturalWidth = await img.evaluate((el: HTMLImageElement) => el.naturalWidth);
      const src = await img.getAttribute('src');

      // naturalWidth === 0 means broken image
      if (src && !src.startsWith('data:')) {
        expect(naturalWidth, `Broken image: ${src}`).toBeGreaterThan(0);
      }
    }
  });

  test('No console errors on homepage', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out common third-party noise
    const realErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('third-party') &&
      !e.includes('Failed to load resource: net::ERR_BLOCKED_BY_CLIENT') &&
      !e.includes('X-Frame-Options')
    );

    expect(realErrors).toEqual([]);
  });

  test('No console errors on explore page', async ({ page }) => {
    const errors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });

    await page.goto('/explore');
    await page.waitForLoadState('networkidle');

    const realErrors = errors.filter(e =>
      !e.includes('favicon') &&
      !e.includes('third-party') &&
      !e.includes('Failed to load resource: net::ERR_BLOCKED_BY_CLIENT') &&
      !e.includes('X-Frame-Options')
    );

    expect(realErrors).toEqual([]);
  });
});
