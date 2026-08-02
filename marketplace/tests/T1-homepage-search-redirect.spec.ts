import { test, expect } from '@playwright/test';

/**
 * T1: Homepage → search entry point
 *
 * REWRITTEN 2026-08-02 (neobrutalist pass). The homepage used to carry a hero
 * search input (`#hero-search-input`) plus All/Plugins/Skills toggle buttons
 * whose only job was to bounce the visitor to /explore with a type filter. The
 * homepage is now a single action — the install block — and search is reached
 * through the nav.
 *
 * The redirect-on-focus behaviour is genuinely gone, so those three cases could
 * not be "fixed", only re-pointed at what replaced them. What is covered now:
 * the homepage still offers a path to search, and the search that path leads to
 * still works — which is the user-facing guarantee those tests actually existed
 * to protect. The /explore-side coverage (last case) is unchanged.
 */

test.describe('Homepage search entry point', () => {
  test('homepage exposes a route to explore', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/Tons of Skills/);

    // At least one link to /explore must exist in the document. On mobile the
    // nav is collapsed behind a toggle, so this asserts presence in the DOM
    // rather than visibility — the mobile-nav interaction is T3's job.
    const exploreLinks = page.locator('a[href*="/explore"]');
    expect(await exploreLinks.count()).toBeGreaterThan(0);

    await page.screenshot({ path: 'test-results/screenshots/T1-homepage-search.png' });
  });

  test('homepage no longer carries its own search input', async ({ page }) => {
    await page.goto('/');

    // Guards the design decision rather than merely tolerating it: if a hero
    // search is ever re-added to the homepage, this fails and forces the
    // "one action per page" call to be made deliberately, not by drift.
    await expect(page.locator('#hero-search-input')).toHaveCount(0);
    await expect(page.locator('button.toggle-btn')).toHaveCount(0);
  });

  test('should have navigation link to explore or skills', async ({ page }) => {
    await page.goto('/');

    const links = page.locator('a[href*="/explore"], a[href*="/skills"]');
    const count = await links.count();
    expect(count).toBeGreaterThan(0);

    // Find the first visible link and navigate to its href
    let href: string | null = null;
    for (let i = 0; i < count; i++) {
      if (await links.nth(i).isVisible()) {
        href = await links.nth(i).getAttribute('href');
        break;
      }
    }

    // If no visible link (mobile nav collapsed), navigate directly
    if (href) {
      await page.goto(href);
    } else {
      await page.goto('/explore');
    }

    await expect(page).toHaveURL(/\/explore|\/skills/);

    await page.screenshot({ path: 'test-results/screenshots/T1-skills-page.png' });
  });

  test('should navigate to /explore and verify search input is focusable', async ({ page }) => {
    // Navigate directly to /explore
    await page.goto('/explore');

    // Verify /explore page loaded
    await expect(page).toHaveTitle(/Explore/);

    // Find search input on explore page
    const exploreSearchInput = page.locator('.hero-search-input');
    await expect(exploreSearchInput).toBeVisible();

    // Verify search input is focusable
    await exploreSearchInput.focus();
    await expect(exploreSearchInput).toBeFocused();

    // Type in search input
    await exploreSearchInput.fill('test search');
    await expect(exploreSearchInput).toHaveValue('test search');

    // Take screenshot of /explore page (viewport only to avoid >32767px limit)
    await page.screenshot({ path: 'test-results/screenshots/T1-explore-page.png' });
  });
});
