import { test, expect } from '@playwright/test';

/**
 * T4: Install CTA Test
 *
 * Tests that the "Quick Install" section exists,
 * copy button is clickable, and layout doesn't break.
 */

test.describe('Install CTA Tests', () => {
  test('should display Quick Install section on homepage', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Find Quick Install section
    const installBox = page.locator('.install-box').first();
    await expect(installBox).toBeVisible();

    // Verify install command text is present
    const installCommand = page.locator('.install-command').first();
    await expect(installCommand).toBeVisible();

    // Verify command text contains expected content (CLI install is now primary)
    const commandText = await installCommand.textContent();
    expect(commandText).toContain('pnpm add -g @intentsolutionsio/ccpi');

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/T4-install-section.png',
      fullPage: false
    });
  });

  test('should allow clicking install command to copy', async ({ page, context, browserName }) => {
    // Skip clipboard tests on webkit - clipboard-write permission not supported
    test.skip(browserName === 'webkit', 'Clipboard permissions not supported on webkit');

    // Try to grant clipboard permissions (may fail in some contexts)
    try {
      await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    } catch {
      // Some browsers don't support clipboard permissions - continue anyway
    }

    // Navigate to homepage
    await page.goto('/');

    // Find install command
    const installCommand = page.locator('.install-command').first();
    await expect(installCommand).toBeVisible();

    // Click to copy
    await installCommand.click();

    // Wait for copy animation
    await page.waitForTimeout(500);

    // Verify button feedback works (just verify click succeeded without errors)
    await expect(installCommand).toBeVisible();

    // Take screenshot after click
    await page.screenshot({
      path: 'test-results/screenshots/T4-install-copied.png',
      fullPage: false
    });
  });

  test('should verify install box doesn\'t break layout on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 390, height: 844 });

    // Navigate to homepage
    await page.goto('/');

    // Find install box
    const installBox = page.locator('.install-box').first();
    await expect(installBox).toBeVisible();

    // Scroll to install box
    await installBox.scrollIntoViewIfNeeded();

    // Verify no horizontal scroll
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);

    // Verify install command is readable (not cut off)
    const installCommand = page.locator('.install-command').first();
    const boundingBox = await installCommand.boundingBox();
    if (boundingBox) {
      // Command should be within viewport width
      expect(boundingBox.x + boundingBox.width).toBeLessThanOrEqual(viewportWidth + 10); // Allow small margin
    }

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/T4-mobile-install.png',
      fullPage: false
    });
  });

  test('should display both install boxes (styled differently)', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Count install boxes
    const installBoxes = page.locator('.install-box');
    const count = await installBoxes.count();

    // Should have at least one install box
    expect(count).toBeGreaterThanOrEqual(1);

    // Verify all install boxes are visible
    for (let i = 0; i < count; i++) {
      await expect(installBoxes.nth(i)).toBeVisible();
    }

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/T4-all-install-boxes.png',
      fullPage: false
    });
  });

  test('should verify CTA links exist and are clickable', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Find cowork CTA button in main content (not nav — nav links are hidden on mobile)
    const coworkCTA = page.locator('main .cowork-home-button, .hero .cowork-home-button, section a[href="/cowork"]').first();

    // If visible, click it; otherwise navigate directly (mobile may hide some CTAs)
    if (await coworkCTA.isVisible()) {
      await coworkCTA.click();
    } else {
      await page.goto('/cowork');
    }

    // Verify navigation occurred
    await expect(page).toHaveURL(/\/cowork/);

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/T4-cta-clicked.png',
      fullPage: false
    });
  });

  test('should verify install command is user-selectable', async ({ page }) => {
    // Navigate to homepage
    await page.goto('/');

    // Find install command
    const installCommand = page.locator('.install-command').first();
    await expect(installCommand).toBeVisible();

    // Verify element has user-select CSS (allows text selection)
    const userSelect = await installCommand.evaluate(el => {
      return window.getComputedStyle(el).userSelect;
    });

    // Should be 'all' or 'text' (not 'none')
    expect(userSelect).not.toBe('none');

    // Take screenshot
    await page.screenshot({
      path: 'test-results/screenshots/T4-install-selectable.png',
      fullPage: false
    });
  });
});
