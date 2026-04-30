import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

/**
 * A11y smoke tests — Phase 5 PR3 (issue #588)
 *
 * Wires axe-core/playwright into the marketplace so accessibility regressions
 * are caught at the gate. The goal of this PR is gate-wired-but-non-blocking:
 * we baseline the current violation count per page so the suite runs green
 * on day one. The cleanup pass is tracked separately under the
 * a11y-cleanup-followup workstream.
 *
 * Tags: WCAG 2.0 / 2.1 Level A and AA. Adjust per-page tag scope only when
 * a known-good rule needs to be excluded for a documented reason — never to
 * paper over fresh regressions.
 *
 * When tightening these baselines:
 *   1. Run `npm run test:a11y` locally
 *   2. Drive the count down by fixing real violations (not by relaxing tags)
 *   3. Lower the `<= N` ceiling on this page in lockstep
 *   4. When N reaches 0 for a page, switch to `toEqual([])` and remove the TODO
 */

const A11Y_TAGS = ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'];

// Stable plugin / skill slugs picked from .claude-plugin/marketplace.extended.json
// and marketplace/src/data/skills-catalog.json. Documented in CONTRIBUTING /
// installation docs as canonical examples — unlikely to be removed.
const SAMPLE_PLUGIN_SLUG = 'git-commit-smart';
const SAMPLE_SKILL_SLUG = 'cursor-advanced-composer';

interface A11yPage {
  name: string;
  path: string;
  // Day-one baseline ceiling. Lower over time. 0 means clean.
  // TODO(a11y-cleanup-followup): drive every entry below to 0
  baseline: number;
  // CSS selectors to exclude from the scan. Only used for pages where the
  // full DOM is too large for axe to walk in a sensible time budget AND the
  // excluded element is the same template repeated thousands of times — so
  // it's already covered by the detail/index pages. /explore/ and /skills/
  // both render the entire catalog (~3k cards) and time out at 120s+; we
  // scan the page chrome (nav, hero, search/filter UI, footer) and let the
  // detail pages cover the card template.
  exclude?: string[];
}

const PAGES: A11yPage[] = [
  { name: 'homepage', path: '/', baseline: 5 },
  { name: 'plugins index', path: '/plugins/', baseline: 5 },
  {
    name: 'skills index',
    path: '/skills/',
    baseline: 5,
    exclude: ['#skills-grid'],
  },
  {
    name: 'explore',
    path: '/explore/',
    baseline: 5,
    exclude: ['#results-grid'],
  },
  { name: 'cowork', path: '/cowork/', baseline: 5 },
  {
    name: `plugin detail (${SAMPLE_PLUGIN_SLUG})`,
    path: `/plugins/${SAMPLE_PLUGIN_SLUG}/`,
    baseline: 5,
  },
  {
    name: `skill detail (${SAMPLE_SKILL_SLUG})`,
    path: `/skills/${SAMPLE_SKILL_SLUG}/`,
    baseline: 5,
  },
  { name: 'docs hub', path: '/docs/', baseline: 5 },
];

test.describe('A11y baseline (axe-core, WCAG 2.0/2.1 A+AA)', () => {
  // /explore/ (~860KB) and /skills/ (~300KB) render thousands of cards;
  // axe needs more than the default 30s to walk the DOM.
  test.setTimeout(120_000);

  for (const { name, path, baseline, exclude } of PAGES) {
    test(`${name} stays at or below baseline`, async ({ page }) => {
      const response = await page.goto(path, { waitUntil: 'domcontentloaded' });
      // Make sure the page actually rendered before we audit it — a 404
      // would give a misleadingly clean axe report.
      expect(response?.status(), `${name} returned ${response?.status()}`).toBeLessThan(400);

      let builder = new AxeBuilder({ page }).withTags(A11Y_TAGS);
      if (exclude?.length) {
        for (const sel of exclude) builder = builder.exclude(sel);
      }
      const results = await builder.analyze();

      // Print a concise summary so CI logs surface the actual violation set
      // when the baseline tightens or a new rule fires.
      if (results.violations.length > 0) {
        console.log(
          `[a11y] ${name} (${path}): ${results.violations.length} violations`,
        );
        for (const v of results.violations) {
          console.log(
            `  - ${v.id} (${v.impact ?? 'unknown'}): ${v.nodes.length} node(s)`,
          );
        }
      }

      expect(
        results.violations.length,
        `${name} (${path}) exceeded a11y baseline (${baseline}). ` +
          `Run \`npm run test:a11y\` and fix the regression — do not raise the baseline.`,
      ).toBeLessThanOrEqual(baseline);
    });
  }
});
