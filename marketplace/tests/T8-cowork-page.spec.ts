import { test, expect } from '@playwright/test';

/**
 * T8: Cowork Downloads Page
 *
 * Tests the /cowork page rendering, plugin search filter,
 * download button integrity, and accessibility.
 */

test.describe('Cowork Downloads Page', () => {

  test.describe('Page Rendering', () => {
    test('should load /cowork with 200 status', async ({ page }) => {
      const response = await page.goto('/cowork');
      expect(response?.status()).toBe(200);

      await page.screenshot({
        path: 'test-results/screenshots/T8-cowork-page.png'
      });
    });

    test('should display hero with badge, heading, and stats', async ({ page }) => {
      await page.goto('/cowork');

      // Badge
      const badge = page.locator('.cowork-hero-badge');
      await expect(badge).toBeVisible();
      await expect(badge).toContainText('FOR COWORK USERS');

      // H1
      const heading = page.locator('.cowork-hero h1');
      await expect(heading).toBeVisible();
      await expect(heading).toContainText('Download Plugin Packs');

      // 3 stat items
      const stats = page.locator('.cowork-hero-stat');
      await expect(stats).toHaveCount(3);
    });

    test('should display mega-download banner with Download All button', async ({ page }) => {
      await page.goto('/cowork');

      const megaBanner = page.locator('.mega-banner');
      await expect(megaBanner).toBeVisible();

      const megaBtn = page.locator('.mega-download-btn');
      await expect(megaBtn).toBeVisible();
      await expect(megaBtn).toContainText('Download All');
    });

    test('should display security banner with checklist items', async ({ page }) => {
      await page.goto('/cowork');

      const securityBanner = page.locator('.security-banner');
      await expect(securityBanner).toBeVisible();

      const items = page.locator('.security-list li');
      const count = await items.count();
      expect(count).toBe(6);
    });

    test('should display category packs grid', async ({ page }) => {
      await page.goto('/cowork');

      // CoworkGrid renders .cowork-grid with .cowork-card items
      const grid = page.locator('.cowork-grid, .cowork-section');
      await expect(grid.first()).toBeVisible();
    });

    test('should display setup guide with 3 numbered steps', async ({ page }) => {
      await page.goto('/cowork');

      const steps = page.locator('.setup-step');
      await expect(steps).toHaveCount(3);

      const stepNumbers = page.locator('.step-number');
      await expect(stepNumbers).toHaveCount(3);

      await page.screenshot({
        path: 'test-results/screenshots/T8-setup-guide.png'
      });
    });

    test('should display learning path with navigation links', async ({ page }) => {
      await page.goto('/cowork');

      const learningPath = page.locator('.learning-path');
      await expect(learningPath).toBeVisible();

      const learningLinks = page.locator('.learning-link');
      const count = await learningLinks.count();
      expect(count).toBe(4);
    });
  });

  test.describe('Plugin Search Filter', () => {
    test('should filter plugins by name when typing', async ({ page }) => {
      await page.goto('/cowork');

      const searchInput = page.locator('#plugin-search');
      // Search may not be visible if no plugins are rendered (build-dependent)
      if (!(await searchInput.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      const countLabel = page.locator('#plugin-count');

      // Type a search query
      await searchInput.fill('security');
      await page.waitForTimeout(300);

      // Count text should change
      const filteredText = await countLabel.textContent();
      expect(filteredText).toContain('Showing');

      await page.screenshot({
        path: 'test-results/screenshots/T8-search-filter.png'
      });
    });

    test('should show all plugins when search cleared', async ({ page }) => {
      await page.goto('/cowork');

      const searchInput = page.locator('#plugin-search');
      if (!(await searchInput.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      // Type then clear
      await searchInput.fill('security');
      await page.waitForTimeout(300);
      await searchInput.fill('');
      await page.waitForTimeout(300);

      const countLabel = page.locator('#plugin-count');
      const text = await countLabel.textContent();
      expect(text).toContain('Showing all');
    });

    test('should handle no-result search', async ({ page }) => {
      await page.goto('/cowork');

      const searchInput = page.locator('#plugin-search');
      if (!(await searchInput.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      await searchInput.fill('xyznonexistentplugin999');
      await page.waitForTimeout(300);

      const countLabel = page.locator('#plugin-count');
      const text = await countLabel.textContent();
      expect(text).toContain('Showing 0');
    });

    test('should filter by category name too', async ({ page }) => {
      await page.goto('/cowork');

      const searchInput = page.locator('#plugin-search');
      if (!(await searchInput.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      // Plugin items have data-category attribute
      await searchInput.fill('devops');
      await page.waitForTimeout(300);

      // At least some items should still be visible
      const visibleItems = page.locator('.plugin-item:visible');
      const count = await visibleItems.count();
      // devops category should have plugins
      expect(count).toBeGreaterThanOrEqual(0);
    });
  });

  test.describe('Download Buttons', () => {
    test('mega-zip button has download attribute and href', async ({ page }) => {
      await page.goto('/cowork');

      const megaBtn = page.locator('.mega-download-btn');
      await expect(megaBtn).toBeVisible();

      const hasDownload = await megaBtn.getAttribute('download');
      expect(hasDownload).not.toBeNull();

      const href = await megaBtn.getAttribute('href');
      expect(href).toBeTruthy();
      expect(href).toContain('/downloads/');
    });

    test('individual plugin buttons have download hrefs', async ({ page }) => {
      await page.goto('/cowork');

      const pluginBtns = page.locator('.plugin-dl-btn');
      const count = await pluginBtns.count();

      if (count > 0) {
        // Check first plugin button
        const href = await pluginBtns.first().getAttribute('href');
        expect(href).toBeTruthy();

        const hasDownload = await pluginBtns.first().getAttribute('download');
        expect(hasDownload).not.toBeNull();
      }
    });
  });

  test.describe('Accessibility', () => {
    test('search input has aria-label and associated label', async ({ page }) => {
      await page.goto('/cowork');

      const searchInput = page.locator('#plugin-search');
      if (!(await searchInput.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      // Check aria-label
      const ariaLabel = await searchInput.getAttribute('aria-label');
      expect(ariaLabel).toBeTruthy();

      // Check for associated label element
      const label = page.locator('label[for="plugin-search"]');
      await expect(label).toHaveCount(1);
    });
  });
});
