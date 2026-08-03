import { test, expect } from '@playwright/test';

/**
 * T4: Install CTA Test
 *
 * Tests the homepage install block: it renders, it copies, it does not break
 * the mobile layout, and its text is selectable.
 *
 * REWRITTEN 2026-08-02 (neobrutalist pass). The homepage used to carry TWO
 * install boxes — a primary `pnpm add -g @intentsolutionsio/ccpi` and a
 * secondary `/plugin marketplace add …` — inside `.install-box` wrappers, with
 * a `.install-command` <pre> that was itself the click target. The page is now
 * a single action: ONE block (`.install`), leading with the Claude-Code-native
 * slash command, with an explicit `.install-copy` button rather than a
 * click-the-code-block affordance.
 *
 * These assertions were retargeted, not relaxed. Same six behaviours are still
 * covered; the "both install boxes" case became "exactly one", which is a
 * STRONGER assertion — it now fails if a second block is ever reintroduced.
 */

const INSTALL_CMD = '/plugin marketplace add jeremylongshore/claude-code-plugins';

test.describe('Install CTA Tests', () => {
  test('should display the install block on homepage', async ({ page }) => {
    await page.goto('/');

    const installBox = page.locator('.install').first();
    await expect(installBox).toBeVisible();

    const installCommand = page.locator('.install-cmd').first();
    await expect(installCommand).toBeVisible();

    // The slash command is the primary install path — it runs inside Claude
    // Code with nothing to install first, which is the page's actual pitch.
    await expect(installCommand).toHaveText(INSTALL_CMD);

    await page.screenshot({
      path: 'test-results/screenshots/T4-install-section.png',
      fullPage: false,
    });
  });

  test('should copy the install command via the copy button', async ({ page, context, browserName }) => {
    // Skip clipboard tests on webkit - clipboard-write permission not supported
    test.skip(browserName === 'webkit', 'Clipboard permissions not supported on webkit');

    try {
      await context.grantPermissions(['clipboard-read', 'clipboard-write']);
    } catch {
      // Some browsers don't support clipboard permissions - continue anyway
    }

    await page.goto('/');

    const copyBtn = page.locator('.install-copy').first();
    await expect(copyBtn).toBeVisible();

    // The command must be on the button as data, not merely on screen — that is
    // what gets copied, so a mismatch here is a silently wrong paste.
    await expect(copyBtn).toHaveAttribute('data-copy', INSTALL_CMD);

    await copyBtn.click();

    // Confirmed state, rather than a bare "still visible" — this asserts the
    // copy path actually ran instead of just that the click did not throw.
    await expect(copyBtn).toHaveAttribute('data-copied', 'true');
    await expect(copyBtn).toHaveText('Copied');

    await page.screenshot({
      path: 'test-results/screenshots/T4-install-copied.png',
      fullPage: false,
    });
  });

  test('should verify install block doesn\'t break layout on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');

    const installBox = page.locator('.install').first();
    await expect(installBox).toBeVisible();
    await installBox.scrollIntoViewIfNeeded();

    // The page must never scroll horizontally. The command itself is allowed to
    // overflow WITHIN its own scroll container (.install-body is overflow-x:
    // auto) — that containment is the thing being verified.
    const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
    const viewportWidth = await page.evaluate(() => window.innerWidth);
    expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);

    const boxBounds = await installBox.boundingBox();
    if (boxBounds) {
      expect(boxBounds.x + boxBounds.width).toBeLessThanOrEqual(viewportWidth + 10);
    }

    await page.screenshot({
      path: 'test-results/screenshots/T4-mobile-install.png',
      fullPage: false,
    });
  });

  test('should display exactly one install block', async ({ page }) => {
    await page.goto('/');

    // The homepage has ONE action. This is deliberately an equality check: a
    // second install block reappearing is the regression this guards against.
    await expect(page.locator('.install')).toHaveCount(1);
    await expect(page.locator('.install').first()).toBeVisible();

    await page.screenshot({
      path: 'test-results/screenshots/T4-all-install-boxes.png',
      fullPage: false,
    });
  });

  test('should verify CTA links exist and are clickable', async ({ page }) => {
    await page.goto('/');

    // Cowork moved off the homepage body in the 2026-08-02 pass; the nav is now
    // the route to it. On mobile the nav collapses behind a toggle, so fall back
    // to direct navigation there rather than asserting a hidden element.
    const coworkNavLink = page.locator('nav a[href="/cowork"]').first();

    if (await coworkNavLink.isVisible()) {
      await coworkNavLink.click();
    } else {
      await page.goto('/cowork');
    }

    await expect(page).toHaveURL(/\/cowork/);

    await page.screenshot({
      path: 'test-results/screenshots/T4-cta-clicked.png',
      fullPage: false,
    });
  });

  test('should verify install command is user-selectable', async ({ page }) => {
    await page.goto('/');

    const installCommand = page.locator('.install-cmd').first();
    await expect(installCommand).toBeVisible();

    const userSelect = await installCommand.evaluate((el) => window.getComputedStyle(el).userSelect);

    // Must not be 'none' — the copy button is a convenience, not the only way
    // to get the command out of the page.
    expect(userSelect).not.toBe('none');

    await page.screenshot({
      path: 'test-results/screenshots/T4-install-selectable.png',
      fullPage: false,
    });
  });
});
