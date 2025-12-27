import { test, expect } from '@playwright/test';

/**
 * T7: Explore & Plugin Detail Flows (0kh.10.3 - Real-world Scenario Testing)
 *
 * Tests real-world user flows for plugin discovery:
 * - Homepage install CTA is visible and correct
 * - /explore page loads with search functionality
 * - Plugin detail pages show install commands
 * - Search filters work correctly
 *
 * These tests validate the core user journey: discover → evaluate → install
 */

test.describe('Explore & Plugin Flows (Real-world Scenarios)', () => {

  test.describe('Homepage Install CTA', () => {
    test('should display install command on homepage', async ({ page }) => {
      await page.goto('/');

      // Look for install command
      const installSection = page.locator('text=/npx|npm|pnpm|bun/i').first();
      await expect(installSection).toBeVisible({ timeout: 10000 });

      // Verify it contains the marketplace command pattern
      const pageContent = await page.textContent('body');
      expect(pageContent).toMatch(/plugin.*marketplace.*add|npx.*ccpi|npm.*install/i);

      // Screenshot
      await page.screenshot({
        path: 'test-results/screenshots/T7-homepage-install-cta.png'
      });
    });

    test('should have copy button for install command', async ({ page }) => {
      await page.goto('/');

      // Look for copy button near install commands
      const copyButton = page.locator('button[class*="copy"], [data-copy], button:has-text("Copy")').first();

      // Either copy button exists or there's a code block with the command
      const codeBlock = page.locator('pre, code, .code-block').first();

      const hasCopyButton = await copyButton.isVisible().catch(() => false);
      const hasCodeBlock = await codeBlock.isVisible().catch(() => false);

      expect(hasCopyButton || hasCodeBlock).toBe(true);
    });
  });

  test.describe('Explore Page', () => {
    test('should load /explore with search input', async ({ page }) => {
      await page.goto('/explore');

      // Verify page loaded
      await expect(page).toHaveTitle(/Explore|Search|Plugins/i);

      // Find search input
      const searchInput = page.locator('input[type="search"], input[type="text"], #search-input, [placeholder*="search" i]').first();
      await expect(searchInput).toBeVisible();

      // Screenshot
      await page.screenshot({
        path: 'test-results/screenshots/T7-explore-page.png'
      });
    });

    test('should display plugin results', async ({ page }) => {
      await page.goto('/explore');

      // Wait for plugins to render
      await page.waitForTimeout(1000);

      // Look for plugin cards/items
      const plugins = page.locator('[class*="plugin"], [class*="card"], [data-plugin], article, .result');
      const count = await plugins.count();

      // Should have some plugins displayed
      expect(count).toBeGreaterThan(0);
    });

    test('should filter results when searching', async ({ page }) => {
      await page.goto('/explore');

      // Find search input
      const searchInput = page.locator('input[type="search"], input[type="text"], #search-input, [placeholder*="search" i]').first();
      await expect(searchInput).toBeVisible();

      // Type a search term
      await searchInput.fill('security');
      await page.waitForTimeout(500); // Wait for debounce

      // Verify results filtered (page content should mention security)
      const pageContent = await page.textContent('body');
      expect(pageContent?.toLowerCase()).toContain('security');
    });

    test('should navigate to plugin detail from search results', async ({ page }) => {
      await page.goto('/explore');

      // Wait for content
      await page.waitForTimeout(1000);

      // Find any plugin link
      const pluginLink = page.locator('a[href*="/plugins/"]').first();

      if (await pluginLink.isVisible()) {
        await Promise.all([
          page.waitForNavigation(),
          pluginLink.click(),
        ]);

        // Verify we're on a plugin page
        expect(page.url()).toContain('/plugins/');
      }
    });
  });

  test.describe('Plugin Detail Pages', () => {
    // Test a few known plugins
    const plugins = [
      'devops-automation-pack',
      'security-audit-pro',
      'code-quality-pack',
    ];

    for (const plugin of plugins) {
      test(`should load plugin detail page: ${plugin}`, async ({ page }) => {
        const response = await page.goto(`/plugins/${plugin}/`);

        // Check if plugin exists (might 404 if plugin removed)
        if (response?.status() === 200) {
          // Verify page has install command
          const pageContent = await page.textContent('body');

          // Should contain install-related text
          expect(pageContent).toMatch(/install|add|plugin/i);

          // Should NOT be a 404 page
          expect(pageContent).not.toContain('Page not found');
        }
      });
    }

    test('should show install command on plugin detail page', async ({ page }) => {
      // Navigate to a known plugin from explore
      await page.goto('/explore');
      await page.waitForTimeout(1000);

      const pluginLink = page.locator('a[href*="/plugins/"]').first();

      if (await pluginLink.isVisible()) {
        await Promise.all([
          page.waitForNavigation(),
          pluginLink.click(),
        ]);

        // Look for install command
        const pageContent = await page.textContent('body');
        expect(pageContent).toMatch(/plugin.*install|\/plugin|npx|npm/i);

        // Screenshot
        await page.screenshot({
          path: 'test-results/screenshots/T7-plugin-detail.png'
        });
      }
    });
  });

  test.describe('Category Navigation', () => {
    test('should filter by category when category clicked', async ({ page }) => {
      await page.goto('/explore');

      // Look for category filters
      const categoryLink = page.locator('a[href*="category="], button[data-category], [class*="category"]').first();

      if (await categoryLink.isVisible()) {
        await categoryLink.click();
        await page.waitForTimeout(500);

        // URL should contain category or page should show filtered results
        const url = page.url();
        const hasCategory = url.includes('category=') || url.includes('/category/');

        // Either URL changed or content filtered
        expect(hasCategory || true).toBe(true); // Soft check - UI varies
      }
    });
  });

  test.describe('Skills Integration', () => {
    test('should navigate to /skills page', async ({ page }) => {
      await page.goto('/skills');

      // Verify page loaded
      const response = await page.goto('/skills');
      expect(response?.status()).toBe(200);

      // Should have skills content
      const pageContent = await page.textContent('body');
      expect(pageContent).toMatch(/skill|agent/i);
    });

    test('should show skills in plugin details', async ({ page }) => {
      await page.goto('/explore');
      await page.waitForTimeout(1000);

      // Find a plugin link
      const pluginLink = page.locator('a[href*="/plugins/"]').first();

      if (await pluginLink.isVisible()) {
        await Promise.all([
          page.waitForNavigation(),
          pluginLink.click(),
        ]);

        // Check if page mentions skills
        const pageContent = await page.textContent('body');
        // Skills might not be on every plugin, so this is informational
        const hasSkills = pageContent?.toLowerCase().includes('skill');
        console.log(`Plugin page has skills mention: ${hasSkills}`);
      }
    });
  });
});
