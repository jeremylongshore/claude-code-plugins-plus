import { test, expect } from '@playwright/test';

/**
 * Debug test: Homepage search redirects to /explore, so we test search on /explore directly
 */
test('Debug search functionality', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // Go directly to /explore where search actually works
  await page.goto('/explore');

  const searchInput = page.locator('.hero-search-input').first();
  const searchResults = page.locator('.search-results, [class*="results"]').first();

  // Check initial state
  await expect(searchInput).toBeVisible();

  // Check if JavaScript loaded
  const hasSearchData = await page.evaluate(() => {
    return typeof window !== 'undefined' && document.querySelector('.hero-search-input') !== null;
  });
  console.log('Has search input in DOM:', hasSearchData);

  // Fill search input
  await searchInput.click();
  await searchInput.fill('prettier');

  // Wait for debounce (200ms) + margin
  await page.waitForTimeout(500);

  // Verify input accepted the text
  await expect(searchInput).toHaveValue('prettier');
  console.log('Search input has value: prettier');
});
