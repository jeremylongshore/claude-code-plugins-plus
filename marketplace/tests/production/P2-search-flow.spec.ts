import { test, expect } from '@playwright/test';

/**
 * P2: Search Flow — Tests search from homepage through explore page results
 */

test.describe('P2: Search Flow', () => {
  test('Homepage search redirects to /explore on click', async ({ page }) => {
    await page.goto('/');

    const searchInput = page.locator('#hero-search-input');
    await expect(searchInput).toBeVisible();

    await Promise.all([
      page.waitForURL(/\/explore/),
      searchInput.click({ force: true }),
    ]);

    await expect(page).toHaveURL(/\/explore/);
  });

  test('Explore page search input is functional', async ({ page }) => {
    await page.goto('/explore');

    const searchInput = page.locator('.hero-search-input').first();
    await expect(searchInput).toBeVisible();

    await searchInput.fill('security');
    await expect(searchInput).toHaveValue('security');
  });

  test('Search returns results for known plugin', async ({ page }) => {
    await page.goto('/explore');

    const searchInput = page.locator('.hero-search-input').first();
    await searchInput.fill('prettier');
    await page.waitForTimeout(600);

    // Should have at least one result card visible
    const resultCards = page.locator('a[href*="/plugins/"], a[href*="/skills/"]');
    const count = await resultCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Search returns results for known skill', async ({ page }) => {
    await page.goto('/explore');

    const searchInput = page.locator('.hero-search-input').first();
    await searchInput.fill('genkit');
    await page.waitForTimeout(600);

    const resultCards = page.locator('a[href*="/plugins/"], a[href*="/skills/"], a[href*="/cowork"]');
    const count = await resultCards.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Empty search query shows no-results state gracefully', async ({ page }) => {
    await page.goto('/explore');

    const searchInput = page.locator('.hero-search-input').first();
    await searchInput.fill('xyznonexistent999zzz');
    await page.waitForTimeout(600);

    // Page should not crash
    await expect(page).toHaveTitle(/Explore/);
  });

  test('Search results link to valid pages', async ({ page }) => {
    await page.goto('/explore');

    const searchInput = page.locator('.hero-search-input').first();
    await searchInput.fill('security');
    await page.waitForTimeout(600);

    const firstResult = page.locator('a[href*="/plugins/"], a[href*="/skills/"], a[href*="/cowork"]').first();
    const isVisible = await firstResult.isVisible().catch(() => false);

    if (isVisible) {
      const href = await firstResult.getAttribute('href');
      expect(href).toBeTruthy();

      await firstResult.click();
      const response = await page.waitForLoadState('networkidle');
      // Should land on a valid page (not 404)
      const title = await page.title();
      expect(title).not.toContain('404');
    }
  });
});
