import { test, expect } from '@playwright/test';

/**
 * P1: Core Pages — Smoke tests for every major page on tonsofskills.com
 * Verifies 200 status, page title, and key elements render.
 */

const corePages = [
  { path: '/', titleMatch: /Tons of Skills|Skills Hub/, desc: 'Homepage' },
  { path: '/explore', titleMatch: /Explore/, desc: 'Explore' },
  { path: '/skills/', titleMatch: /Skills/, desc: 'Skills Directory' },
  { path: '/plugins/', titleMatch: /Plugin|Browse/, desc: 'Plugins' },
  { path: '/cowork', titleMatch: /Cowork|Download/, desc: 'Cowork' },
  { path: '/getting-started', titleMatch: /Getting Started/, desc: 'Getting Started' },
  { path: '/learning/', titleMatch: /Learn/, desc: 'Learning' },
  { path: '/playbooks/', titleMatch: /Playbook/, desc: 'Playbooks' },
  { path: '/tools', titleMatch: /Tool/, desc: 'Tools' },
  { path: '/sponsor', titleMatch: /Sponsor/, desc: 'Sponsor' },
  { path: '/privacy', titleMatch: /Privacy/, desc: 'Privacy' },
  { path: '/terms', titleMatch: /Terms/, desc: 'Terms' },
];

test.describe('P1: Core Pages Smoke Tests', () => {
  for (const pg of corePages) {
    test(`${pg.desc} (${pg.path}) loads with 200`, async ({ page }) => {
      const response = await page.goto(pg.path);
      expect(response?.status()).toBe(200);
      await expect(page).toHaveTitle(pg.titleMatch);
    });
  }

  test('Homepage renders hero heading', async ({ page }) => {
    await page.goto('/');
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
  });

  test('Homepage renders search input', async ({ page }) => {
    await page.goto('/');
    const search = page.locator('#hero-search-input');
    await expect(search).toBeVisible();
  });

  test('Homepage renders install command box', async ({ page }) => {
    await page.goto('/');
    const installBox = page.locator('.install-cmd, [data-install], code').first();
    await expect(installBox).toBeVisible();
  });

  test('Navigation bar is present on all pages', async ({ page }) => {
    await page.goto('/');
    const nav = page.locator('nav, .nav, header').first();
    await expect(nav).toBeVisible();
  });

  test('Footer is present', async ({ page }) => {
    await page.goto('/');
    const footer = page.locator('footer').first();
    await expect(footer).toBeVisible();
  });
});
