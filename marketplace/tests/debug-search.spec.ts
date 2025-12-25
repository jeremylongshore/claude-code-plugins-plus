import { test, expect } from '@playwright/test';

test('Debug search functionality', async ({ page }) => {
  // Enable console logging
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  await page.goto('/');

  const searchInput = page.locator('#hero-search-input');
  const searchResults = page.locator('#hero-search-results');

  // Check initial state
  await expect(searchInput).toBeVisible();

  // Check if JavaScript loaded
  const hasSearchData = await page.evaluate(() => {
    return typeof window !== 'undefined' && document.getElementById('hero-search-input') !== null;
  });
  console.log('Has search input in DOM:', hasSearchData);

  // Fill search input and type manually to ensure input event fires
  await searchInput.click();
  await searchInput.fill('prettier');

  // Wait for debounce (200ms) + margin
  await page.waitForTimeout(500);

  // Check state
  const isHidden = await searchResults.evaluate(el => el.classList.contains('hidden'));
  console.log('Results hidden after fill:', isHidden);

  const innerHTML = await searchResults.innerHTML();
  console.log('Results innerHTML length:', innerHTML.length);

  if (!isHidden) {
    await expect(searchResults).toBeVisible();
  } else {
    console.log('ERROR: Results still hidden after typing');
  }
});
