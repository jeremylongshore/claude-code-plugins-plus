import { test, expect } from '@playwright/test';

test('Debug horizontal overflow', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  // Find all elements that extend beyond viewport
  const overflowingElements = await page.evaluate(() => {
    const viewport = window.innerWidth; // 390px
    const results: any[] = [];

    document.querySelectorAll('*').forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.right > viewport) {
        results.push({
          tag: el.tagName,
          id: el.id || '',
          class: el.className || '',
          right: Math.round(rect.right),
          width: Math.round(rect.width),
          overflow: Math.round(rect.right - viewport)
        });
      }
    });

    // Sort by overflow amount (descending)
    return results.sort((a, b) => b.overflow - a.overflow).slice(0, 20);
  });

  console.log('Overflowing elements:', JSON.stringify(overflowingElements, null, 2));

  // Also check body scrollWidth
  const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  console.log(`Body scrollWidth: ${bodyWidth}px, Viewport: ${viewportWidth}px, Overflow: ${bodyWidth - viewportWidth}px`);
});
