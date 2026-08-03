import { test, expect } from '@playwright/test';

/**
 * T9: Cowork Integration Tests
 *
 * Tests the cowork feature integration across the site:
 * homepage section, navigation links, and mobile responsiveness.
 */

test.describe('Cowork Integration', () => {

  // REWRITTEN 2026-08-02 (neobrutalist pass). The homepage used to embed a
  // featured CoworkGrid (`.cowork-home-section` / `.cowork-home-title` /
  // `.cowork-home-button`, limit 6). The homepage is now a single action and
  // Cowork is reached through the nav. Nothing was deleted — /cowork keeps its
  // route and its own full grid, covered in depth by T8.
  //
  // What these cases protect is unchanged in substance: a visitor landing on the
  // homepage can still get to Cowork, and the destination still works.
  test.describe('Homepage → Cowork route', () => {
    test('homepage links to /cowork', async ({ page }) => {
      await page.goto('/');

      // DOM presence, not visibility: the nav collapses behind a toggle on
      // mobile, and the visible-nav case is asserted separately below.
      const coworkLinks = page.locator('a[href="/cowork"]');
      expect(await coworkLinks.count()).toBeGreaterThan(0);

      await page.screenshot({
        path: 'test-results/screenshots/T9-homepage-cowork-section.png'
      });
    });

    test('homepage no longer embeds the cowork grid', async ({ page }) => {
      await page.goto('/');

      // Guards the decision rather than merely tolerating it: if the grid is
      // ever re-embedded, this fails and forces the "one action per page" call
      // to be made deliberately instead of by drift.
      await expect(page.locator('.cowork-home-section')).toHaveCount(0);
    });

    test('following the homepage link reaches a working /cowork grid', async ({ page }) => {
      await page.goto('/');

      const href = await page.locator('a[href="/cowork"]').first().getAttribute('href');
      expect(href).toBe('/cowork');

      await page.goto('/cowork');
      await expect(page).toHaveURL(/\/cowork/);

      // The destination must actually render packs — a link to an empty page is
      // the failure mode this replaces the old "max 6 cards" assertion with.
      const cards = page.locator('.cowork-card, .pack-card, [class*="card"]');
      expect(await cards.count()).toBeGreaterThanOrEqual(1);
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
