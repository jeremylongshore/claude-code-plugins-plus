import { test, expect } from '@playwright/test';

/**
 * P4: Navigation — Tests nav links, internal routing, and cross-page navigation
 */

test.describe('P4: Navigation', () => {
  test('Nav logo links to homepage', async ({ page }) => {
    await page.goto('/explore');
    const logo = page.locator('a[href="/"]').first();
    await expect(logo).toBeVisible();
    await logo.click();
    await expect(page).toHaveURL(/\/$/);
  });

  test('Nav contains links to key sections', async ({ page }) => {
    await page.goto('/');

    // Check for nav links to main sections
    const navLinks = page.locator('nav a, header a');
    const hrefs: string[] = [];
    const count = await navLinks.count();
    for (let i = 0; i < count; i++) {
      const href = await navLinks.nth(i).getAttribute('href');
      if (href) hrefs.push(href);
    }

    // At minimum, we expect links to explore, cowork
    const hasExplore = hrefs.some(h => h.includes('/explore'));
    const hasCowork = hrefs.some(h => h.includes('/cowork'));
    expect(hasExplore || hasCowork).toBe(true);
  });

  test('Skills Directory links to individual skill or cowork', async ({ page }) => {
    await page.goto('/skills/');

    // Scope to the skills grid to avoid nav links
    const skillCards = page.locator('.skill-card, #skills-grid a');
    const count = await skillCards.count();
    expect(count).toBeGreaterThan(0);

    // Navigate via href instead of clicking (avoids mobile visibility issues)
    const firstCard = skillCards.first();
    const href = await firstCard.getAttribute('href');
    expect(href).toBeTruthy();

    await page.goto(href!);
    const title = await page.title();
    expect(title).not.toContain('404');
  });

  test('Plugins page lists plugin cards with links', async ({ page }) => {
    await page.goto('/plugins/');

    const pluginLinks = page.locator('a[href*="/plugins/"]');
    const count = await pluginLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Plugin detail page loads from plugins listing', async ({ page }) => {
    await page.goto('/plugins/');

    const pluginLink = page.locator('a[href*="/plugins/"]').first();
    const isVisible = await pluginLink.isVisible().catch(() => false);

    if (isVisible) {
      await pluginLink.click();
      await page.waitForLoadState('networkidle');

      const title = await page.title();
      expect(title).not.toContain('404');
      expect(title.length).toBeGreaterThan(0);
    }
  });

  test('Cowork page links back to explore or skills', async ({ page }) => {
    await page.goto('/cowork');

    const links = page.locator('a[href*="/explore"], a[href*="/skills"], a[href*="/learning"]');
    const count = await links.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Playbooks page lists playbook links', async ({ page }) => {
    await page.goto('/playbooks/');

    const playbookLinks = page.locator('a[href*="/playbooks/"]');
    const count = await playbookLinks.count();
    expect(count).toBeGreaterThan(0);
  });

  test('Learning page has navigation to sub-pages', async ({ page }) => {
    await page.goto('/learning/');

    const learningLinks = page.locator('a[href*="/learning/"]');
    const count = await learningLinks.count();
    expect(count).toBeGreaterThan(0);
  });
});
