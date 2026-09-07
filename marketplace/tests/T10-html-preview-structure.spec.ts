import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { test, expect } from '@playwright/test';

// @ts-expect-error JavaScript utility has no separate declaration file.
import { truncateHtml } from '../scripts/truncate-html.mjs';

type CatalogSkill = {
  slug: string;
  content: string;
  parentPlugin?: { name?: string };
};

const catalog = JSON.parse(
  readFileSync(join(process.cwd(), 'src/data/skills-catalog.json'), 'utf8'),
) as { skills: CatalogSkill[] };
const installCatalog = JSON.parse(
  readFileSync(join(process.cwd(), '../.claude-plugin/marketplace.json'), 'utf8'),
) as { plugins: Array<{ name: string }> };
const installablePlugins = new Set(installCatalog.plugins.map((plugin) => plugin.name));

const candidate = catalog.skills.find(
  (skill) =>
    skill.content.length > 3000 &&
    skill.parentPlugin?.name &&
    installablePlugins.has(skill.parentPlugin.name),
);

test.describe('HTML preview structure', () => {
  test('plugin preview is truncated while the dedicated skill page stays complete', async ({ page }) => {
    expect(candidate, 'catalog must contain an installable skill above the preview limit').toBeDefined();
    const expectedPreview = truncateHtml(candidate!.content, 3000);

    const response = await page.goto(`/plugins/${candidate!.parentPlugin!.name}/`);
    expect(response?.status()).toBe(200);
    expect(await response!.text()).toContain(expectedPreview);
    const preview = page.locator(
      `[data-skill-slug="${candidate!.slug}"] .gist-content-inner`,
    );
    await expect(preview).toHaveCount(1);

    const previewHtml = await preview.innerHTML();
    expect(previewHtml).toContain('…');
    expect(previewHtml).not.toBe(candidate!.content.slice(0, 3000));
    expect(Array.from(previewHtml).length).toBeLessThanOrEqual(3000);

    const normalizedExpected = await page.evaluate((html) => {
      const template = document.createElement('template');
      template.innerHTML = html;
      return template.innerHTML;
    }, expectedPreview);
    expect(previewHtml).toBe(normalizedExpected);

    await page.goto(`/skills/${candidate!.slug}/`);
    const fullHtml = await page.locator('.skill-content > div').innerHTML();
    const normalizedSource = await page.evaluate((html) => {
      const template = document.createElement('template');
      template.innerHTML = html;
      return template.innerHTML;
    }, candidate!.content);
    expect(fullHtml).toBe(normalizedSource);
    expect(Array.from(fullHtml).length).toBeGreaterThan(3000);
  });
});
