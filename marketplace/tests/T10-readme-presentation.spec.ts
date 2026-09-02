import { test, expect } from '@playwright/test';

const PLUGIN_PATH = '/plugins/databricks-workspace-mcp/';
const localChromium = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH;

test.use(
  localChromium
    ? {
        launchOptions: { executablePath: localChromium, args: ['--no-sandbox'] },
        video: 'off',
      }
    : {},
);

for (const viewport of [
  { name: 'desktop', width: 1440, height: 900 },
  { name: 'mobile', width: 390, height: 844 },
]) {
  test(`renders the first-party README presentation accessibly on ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    const response = await page.goto(PLUGIN_PATH);

    expect(response?.status()).toBe(200);

    const section = page.locator('.readme-section').filter({ hasText: 'What It Does' }).first();
    await expect(section).toBeVisible();
    await expect(section).toContainText('Databricks control plane');
    await expect(section).toContainText('License: MIT');
    await expect(section).toContainText('Transport: MCP over stdio and HTTP');
    await expect(section).toContainText('Access: Read-only');

    const rendered = section.locator('.readme-content');
    await expect(rendered.locator('strong').first()).toContainText('control plane');
    await expect(rendered.locator('code')).toContainText('system.*');
    await expect(rendered.locator('li')).toHaveCount(3);

    const text = await rendered.innerText();
    expect(text).not.toMatch(/<(?:h1|p|img|strong|br|code)\b/i);

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow).toBeLessThanOrEqual(0);
  });
}
