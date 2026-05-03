#!/usr/bin/env node
/**
 * render-spotlight.mjs
 *
 * Regenerates the README "Killer Skill of the Week" block from
 * `marketplace/src/data/spotlights.json` (the same file that drives the
 * homepage `KillerSkills.astro` card). Single source of truth = the JSON;
 * the README block is a derived view bounded by HTML comment sentinels.
 *
 * Eliminates the historical drift where the README spotlight and the
 * website spotlight pointed at different plugins (web-analytics in README
 * vs code-cleanup in JSON, both claiming W16).
 *
 * Usage:
 *   node scripts/render-spotlight.mjs           # write README
 *   node scripts/render-spotlight.mjs --check   # CI: exit 1 if out of sync
 *
 * Sentinels (must already exist in README):
 *   <!-- KILLER-SKILL:START — do not edit; run `node scripts/render-spotlight.mjs` -->
 *   <!-- KILLER-SKILL:END -->
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import prettier from 'prettier';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const SPOTLIGHTS = join(ROOT, 'marketplace', 'src', 'data', 'spotlights.json');
const README = join(ROOT, 'README.md');

const START = '<!-- KILLER-SKILL:START — do not edit; run `node scripts/render-spotlight.mjs` -->';
const END = '<!-- KILLER-SKILL:END -->';

const MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

// 2026-W18 → "Week of May 2, 2026 (W18)" — derived from the ISO week so
// the human-friendly label stays in lockstep with the JSON's `week`.
function isoWeekToLabel(isoWeek, lastUpdated) {
  // Use lastUpdated when present (it's the actual edit date and matches
  // what the curator intended). Falls back to ISO-week math otherwise.
  if (lastUpdated && /^\d{4}-\d{2}-\d{2}$/.test(lastUpdated)) {
    const [y, m, d] = lastUpdated.split('-').map((n) => parseInt(n, 10));
    const wMatch = /W(\d{1,2})/.exec(isoWeek || '');
    const wkSuffix = wMatch ? ` (W${wMatch[1].padStart(2, '0')})` : '';
    return `Week of ${MONTHS[m - 1]} ${d}, ${y}${wkSuffix}`;
  }
  return `Week of ${isoWeek}`;
}

// Plugin link: external (https://...) keeps the URL; internal (/plugins/x)
// gets prefixed with the marketplace domain so the README link works
// outside the site.
function externalize(link) {
  if (!link) return null;
  if (link.startsWith('http://') || link.startsWith('https://')) return link;
  if (link.startsWith('/')) return `https://tonsofskills.com${link}`;
  return link;
}

function bestLinkLabel(s) {
  const link = s.link || '';
  if (link.startsWith('http')) return 'View on GitHub';
  return 'Browse on Marketplace';
}

function renderBlock(data) {
  const s = data.spotlight;
  if (!s) throw new Error('spotlights.json has no `spotlight` field');

  const link = externalize(s.link);
  const authorLink = s.authorGithub
    ? `[${s.author}](https://github.com/${s.authorGithub})`
    : s.author || 'Anonymous';
  const linkLabel = bestLinkLabel(s);
  const weekLabel = isoWeekToLabel(data.week, data.meta?.lastUpdated);

  // Hall-of-fame inline list. Each entry uses its own link (external vs
  // /plugins/<slug>) per the JSON. Most-recent first.
  const previous = (data.hallOfFame || [])
    .map((h) => {
      const href = externalize(h.link);
      return `[${h.pluginSlug}](${href})`;
    })
    .join(', ');

  // Optional headline + quote — fall back gracefully if absent.
  const headlineLine = s.headline ? `> **${s.headline}**\n>\n` : '';
  const whyLine = s.whyKiller ? `> ${s.whyKiller}\n>\n` : '';
  const quoteLine = s.quote ? `> *"${s.quote}"* — ${s.author || 'Anonymous'}\n>\n` : '';

  const lines = [
    START,
    `> **${data.title || 'Killer Skill of the Week'}** — [${s.pluginSlug}](${link}) by ${authorLink}`,
    '>',
    `${headlineLine}${whyLine}${quoteLine}> Grade: ${s.grade || 'A'} | ${weekLabel} | [${linkLabel}](${link})`,
    '>',
    `> Previous picks: ${previous || '_(none yet)_'}. See all at [tonsofskills.com](https://tonsofskills.com).`,
    END,
  ];
  return lines.join('\n');
}

function splice(readme, block) {
  const s = readme.indexOf(START);
  const e = readme.indexOf(END);
  if (s === -1 || e === -1) {
    throw new Error(`README.md missing KILLER-SKILL sentinels. Add:\n${START}\n${END}\n`);
  }
  return readme.slice(0, s) + block + readme.slice(e + END.length);
}

// Pipe the entire spliced README through Prettier so the generator owns both
// the bounded block AND Prettier's surrounding-whitespace expectations.
// Without this, `prettier --check README.md` and this script's `--check` mode
// fight over blank lines around the sentinels (issue #657).
//
// resolveConfig() loads the repo's Prettier settings (.prettierrc and friends)
// — without it, prettier.format() runs with library defaults and produces
// output that disagrees with what `prettier --check` from the CLI expects.
async function formatReadme(content) {
  const options = (await prettier.resolveConfig(README)) || {};
  return prettier.format(content, { ...options, filepath: README });
}

async function main() {
  const check = process.argv.includes('--check');
  const data = JSON.parse(readFileSync(SPOTLIGHTS, 'utf-8'));
  const block = renderBlock(data);
  const readme = readFileSync(README, 'utf-8');
  const spliced = splice(readme, block);
  const updated = await formatReadme(spliced);

  if (updated === readme) {
    console.log('✓ README KILLER-SKILL block already in sync with spotlights.json');
    return;
  }

  if (check) {
    console.error('✗ README KILLER-SKILL block is OUT OF SYNC with spotlights.json.');
    console.error('  Run: node scripts/render-spotlight.mjs');
    process.exit(1);
  }

  writeFileSync(README, updated);
  console.log('✓ README KILLER-SKILL block regenerated from spotlights.json');
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
