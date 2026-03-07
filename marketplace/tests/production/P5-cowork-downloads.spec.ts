import { test, expect } from '@playwright/test';

/**
 * P5: Cowork Downloads — Tests download buttons, mega-zip, and plugin search on /cowork
 */

test.describe('P5: Cowork Downloads', () => {
  test('Cowork page renders hero with stats', async ({ page }) => {
    await page.goto('/cowork');

    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();

    const stats = page.locator('.cowork-hero-stat');
    const count = await stats.count();
    expect(count).toBeGreaterThanOrEqual(2);
  });

  test('Mega-download button has valid href', async ({ page }) => {
    await page.goto('/cowork');

    const megaBtn = page.locator('.mega-download-btn');
    await expect(megaBtn).toBeVisible();

    const href = await megaBtn.getAttribute('href');
    expect(href).toBeTruthy();
    expect(href).toContain('/downloads/');

    const hasDownload = await megaBtn.getAttribute('download');
    expect(hasDownload).not.toBeNull();
  });

  test('Mega-zip download URL returns 200', async ({ page, request }) => {
    await page.goto('/cowork');

    const megaBtn = page.locator('.mega-download-btn');
    const href = await megaBtn.getAttribute('href');

    if (href) {
      const url = href.startsWith('http') ? href : `https://tonsofskills.com${href}`;
      const response = await request.head(url, { failOnStatusCode: false });
      expect(response.status()).toBe(200);
    }
  });

  test('Plugin search filter works', async ({ page }) => {
    await page.goto('/cowork');

    const searchInput = page.locator('#plugin-search');
    if (!(await searchInput.isVisible().catch(() => false))) {
      test.skip();
      return;
    }

    await searchInput.fill('security');
    await page.waitForTimeout(400);

    const countLabel = page.locator('#plugin-count');
    const text = await countLabel.textContent();
    expect(text).toContain('Showing');
  });

  test('Setup guide has 3 steps', async ({ page }) => {
    await page.goto('/cowork');

    const steps = page.locator('.setup-step');
    await expect(steps).toHaveCount(3);
  });

  test('Category pack cards are present', async ({ page }) => {
    await page.goto('/cowork');

    const cards = page.locator('.cowork-card, .category-card, [class*="pack"]');
    const count = await cards.count();
    expect(count).toBeGreaterThan(0);
  });
});
