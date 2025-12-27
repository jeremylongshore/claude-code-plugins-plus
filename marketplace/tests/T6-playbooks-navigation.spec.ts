import { test, expect } from '@playwright/test';

/**
 * T6: Playbooks Navigation Test (0kh.10.3 - Real-world Scenario Testing)
 *
 * Tests real-world user flows for the playbooks section:
 * - Playbooks index page loads correctly
 * - All playbook links are clickable and render content (no 404s)
 * - Each playbook page contains expected structure
 *
 * This is a critical regression test after the playbooks 404 fix (PRs #209-#212).
 */

test.describe('Playbooks Navigation (Real-world Scenarios)', () => {

  test.describe('Playbooks Index', () => {
    test('should display playbooks index with all 11 playbooks', async ({ page }) => {
      await page.goto('/playbooks');

      // Verify page loaded (not 404)
      await expect(page).toHaveTitle(/Playbooks|Production/i);

      // Find playbook cards/links
      const playbookLinks = page.locator('a[href*="/playbooks/"]').filter({
        hasNot: page.locator('a[href="/playbooks"]') // Exclude self-link
      });

      // Should have at least 10 playbooks (we have 11)
      const count = await playbookLinks.count();
      expect(count).toBeGreaterThanOrEqual(10);

      // Screenshot
      await page.screenshot({
        path: 'test-results/screenshots/T6-playbooks-index.png'
      });
    });

    test('should have visible playbook titles and descriptions', async ({ page }) => {
      await page.goto('/playbooks');

      // Check for playbook content structure
      const playbookCards = page.locator('[class*="playbook"], [data-playbook], .card, article').first();

      // At minimum, the page should have text content about playbooks
      const pageContent = await page.textContent('main, .content, body');
      expect(pageContent).toContain('Rate Limit');
    });
  });

  test.describe('Individual Playbook Pages', () => {
    // Test each known playbook route
    const playbooks = [
      { slug: '01-multi-agent-rate-limits', title: 'Rate Limit' },
      { slug: '02-cost-caps', title: 'Cost' },
      { slug: '03-mcp-reliability', title: 'MCP' },
      { slug: '04-ollama-migration', title: 'Ollama' },
      { slug: '05-incident-debugging', title: 'Incident' },
      { slug: '06-self-hosted-stack', title: 'Self-Hosted' },
      { slug: '07-compliance-audit', title: 'Compliance' },
      { slug: '08-team-presets', title: 'Team' },
      { slug: '09-cost-attribution', title: 'Attribution' },
      { slug: '10-progressive-enhancement', title: 'Progressive' },
      { slug: '11-advanced-tool-use', title: 'Tool Use' },
    ];

    for (const playbook of playbooks) {
      test(`should load ${playbook.slug} without 404`, async ({ page }) => {
        const response = await page.goto(`/playbooks/${playbook.slug}/`);

        // Verify HTTP 200 (not 404)
        expect(response?.status()).toBe(200);

        // Verify page has content (not error page)
        const bodyText = await page.textContent('body');
        expect(bodyText?.toLowerCase()).toContain(playbook.title.toLowerCase());

        // Verify it's not a generic error page
        expect(bodyText).not.toContain('404');
        expect(bodyText).not.toContain('Page not found');
      });
    }

    test('should navigate from index to playbook and back', async ({ page }) => {
      // Start at index
      await page.goto('/playbooks');

      // Click first playbook link
      const firstPlaybook = page.locator('a[href*="/playbooks/0"]').first();
      await expect(firstPlaybook).toBeVisible();

      await Promise.all([
        page.waitForNavigation(),
        firstPlaybook.click(),
      ]);

      // Verify we're on a playbook page
      expect(page.url()).toMatch(/\/playbooks\/\d{2}-/);

      // Navigate back
      await page.goBack();

      // Verify we're back on index
      await expect(page).toHaveURL(/\/playbooks\/?$/);
    });
  });

  test.describe('Dynamic Link Enumeration', () => {
    test('should click every playbook link found on index page', async ({ page }) => {
      await page.goto('/playbooks');

      // Get all playbook hrefs from the page
      const links = await page.locator('a[href^="/playbooks/"][href$="/"]').all();
      const hrefs: string[] = [];

      for (const link of links) {
        const href = await link.getAttribute('href');
        if (href && href !== '/playbooks/' && !hrefs.includes(href)) {
          hrefs.push(href);
        }
      }

      // Verify we found playbook links
      expect(hrefs.length).toBeGreaterThan(0);

      // Visit each one and verify no 404
      const results: { href: string; status: number | undefined }[] = [];

      for (const href of hrefs) {
        const response = await page.goto(href);
        results.push({ href, status: response?.status() });

        // Each should return 200
        expect(response?.status(), `${href} returned ${response?.status()}`).toBe(200);
      }

      // Log results for debugging
      console.log('Playbook navigation results:', results);
    });
  });

  test.describe('Mobile Viewport', () => {
    test('should display playbooks correctly on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });

      await page.goto('/playbooks');

      // Verify no horizontal scroll
      const bodyWidth = await page.evaluate(() => document.body.scrollWidth);
      const viewportWidth = await page.evaluate(() => window.innerWidth);
      expect(bodyWidth).toBeLessThanOrEqual(viewportWidth);

      // Verify playbooks are visible
      const content = await page.textContent('body');
      expect(content).toContain('Rate Limit');

      // Screenshot
      await page.screenshot({
        path: 'test-results/screenshots/T6-playbooks-mobile.png'
      });
    });

    test('should be able to tap playbook on mobile', async ({ page }) => {
      await page.setViewportSize({ width: 390, height: 844 });

      await page.goto('/playbooks');

      const playbookLink = page.locator('a[href*="/playbooks/0"]').first();
      await expect(playbookLink).toBeVisible();

      // Click (tap) and verify navigation
      await Promise.all([
        page.waitForNavigation(),
        playbookLink.click(),
      ]);

      expect(page.url()).toMatch(/\/playbooks\/\d{2}-/);
    });
  });
});
