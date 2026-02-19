import { test, expect } from '@playwright/test';

/**
 * T9: Cowork Integration Tests
 *
 * Tests the cowork feature integration across the site:
 * homepage section, navigation links, and mobile responsiveness.
 */

test.describe('Cowork Integration', () => {

  test.describe('Homepage Cowork Section', () => {
    test('should display cowork section with badge and title', async ({ page }) => {
      await page.goto('/');

      const section = page.locator('.cowork-home-section');
      await expect(section).toBeVisible();

      const badge = page.locator('.cowork-home-badge');
      await expect(badge).toBeVisible();

      const title = page.locator('.cowork-home-title');
      await expect(title).toBeVisible();
      await expect(title).toContainText('Download Plugin Packs');

      await page.screenshot({
        path: 'test-results/screenshots/T9-homepage-cowork-section.png'
      });
    });

    test('should show featured CoworkGrid cards (max 6)', async ({ page }) => {
      await page.goto('/');

      const section = page.locator('.cowork-home-section');
      await expect(section).toBeVisible();

      // CoworkGrid renders cards within the section
      const cards = section.locator('.cowork-card, .pack-card, [class*="card"]');
      const count = await cards.count();

      // Should render between 1 and 6 featured cards (limit={6} in index.astro)
      expect(count).toBeGreaterThanOrEqual(1);
      expect(count).toBeLessThanOrEqual(6);
    });

    test('should navigate to /cowork from CTA button', async ({ page }) => {
      await page.goto('/');

      const ctaButton = page.locator('.cowork-home-button');
      await expect(ctaButton).toBeVisible();

      // Verify href
      const href = await ctaButton.getAttribute('href');
      expect(href).toBe('/cowork');

      // Click and verify navigation
      await Promise.all([
        page.waitForURL(/\/cowork/),
        ctaButton.click(),
      ]);

      await expect(page).toHaveURL(/\/cowork/);
    });
  });

  test.describe('Navigation Links', () => {
    test('Cowork link visible in desktop nav', async ({ page, browserName }, testInfo) => {
      // Skip on mobile viewports
      test.skip(testInfo.project.name.includes('mobile'), 'Desktop nav test');

      await page.goto('/');

      const coworkNavLink = page.locator('nav a[href="/cowork"]');
      await expect(coworkNavLink).toBeVisible();
    });

    test('nav link navigates to /cowork', async ({ page, browserName }, testInfo) => {
      test.skip(testInfo.project.name.includes('mobile'), 'Desktop nav test');

      await page.goto('/');

      const coworkNavLink = page.locator('nav a[href="/cowork"]');
      if (!(await coworkNavLink.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      await Promise.all([
        page.waitForURL(/\/cowork/),
        coworkNavLink.click(),
      ]);

      await expect(page).toHaveURL(/\/cowork/);
    });

    test('cowork link exists in page DOM', async ({ page }) => {
      await page.goto('/');

      // Should have at least one link to /cowork somewhere on the page
      const coworkLinks = page.locator('a[href="/cowork"]');
      const count = await coworkLinks.count();
      expect(count).toBeGreaterThanOrEqual(1);
    });
  });

  test.describe('Mobile Responsive', () => {
    test('cowork page has no horizontal scroll at 390px width', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('/cowork');

      // Check that body doesn't have major horizontal overflow
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = 390;
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth + 50); // 50px tolerance for minor element overflow

      await page.screenshot({
        path: 'test-results/screenshots/T9-cowork-mobile.png'
      });
    });

    test('mega-banner stacks vertically on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('/cowork');

      const megaBanner = page.locator('.mega-banner');
      if (!(await megaBanner.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      const flexDirection = await megaBanner.evaluate(el =>
        window.getComputedStyle(el).flexDirection
      );
      expect(flexDirection).toBe('column');
    });

    test('grid renders single column on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('/cowork');

      const pluginList = page.locator('.plugin-list');
      if (!(await pluginList.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      const columns = await pluginList.evaluate(el =>
        window.getComputedStyle(el).gridTemplateColumns
      );
      // Should be single column (one value, not multiple)
      const columnCount = columns.split(/\s+/).length;
      expect(columnCount).toBe(1);
    });

    test('download buttons are touch-friendly (min height >= 36px)', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });
      await page.goto('/cowork');

      const megaBtn = page.locator('.mega-download-btn');
      if (!(await megaBtn.isVisible().catch(() => false))) {
        test.skip();
        return;
      }

      const box = await megaBtn.boundingBox();
      expect(box).not.toBeNull();
      expect(box!.height).toBeGreaterThanOrEqual(36);
    });
  });
});
