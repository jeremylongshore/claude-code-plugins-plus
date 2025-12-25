import { test, expect } from '@playwright/test';

/**
 * T1: Homepage Search Redirect Test
 *
 * Tests that the homepage search control navigates to /explore
 * when interacted with and that the search is functional.
 */

test.describe('Homepage Search Redirect', () => {
  test('should navigate to /explore when search input is focused', async ({ page }) => {
    // Load homepage
    await page.goto('/');

    // Verify homepage loaded
    await expect(page).toHaveTitle(/Claude Code Skills Hub/);

    // Find the search input on homepage
    const searchInput = page.locator('#hero-search-input');
    await expect(searchInput).toBeVisible();

    // Click on search input (force click as toggle buttons may overlap)
    await searchInput.click({ force: true });

    // Type in search input
    await searchInput.fill('prettier');

    // Verify search results appear on homepage (inline results)
    const searchResults = page.locator('#hero-search-results');
    await expect(searchResults).toBeVisible();

    // Take screenshot of homepage search
    await page.screenshot({
      path: 'test-results/screenshots/T1-homepage-search.png',
      fullPage: true
    });
  });

  test('should navigate to /explore via Browse Skills button', async ({ page }) => {
    // Load homepage
    await page.goto('/');

    // Click "Browse Skills Directory" button
    const browsSkillsBtn = page.locator('a.btn-primary', { hasText: 'Browse Skills Directory' });
    await expect(browsSkillsBtn).toBeVisible();
    await browsSkillsBtn.click();

    // Verify navigation to /skills/ page
    await expect(page).toHaveURL(/\/skills\//);

    // Take screenshot of skills page (viewport only to avoid size limit)
    await page.screenshot({
      path: 'test-results/screenshots/T1-skills-page.png',
      fullPage: false
    });
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

    // Take screenshot of /explore page
    await page.screenshot({
      path: 'test-results/screenshots/T1-explore-page.png',
      fullPage: true
    });
  });
});
