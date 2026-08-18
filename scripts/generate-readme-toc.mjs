#!/usr/bin/env node
/**
 * generate-readme-toc.mjs
 *
 * Reads .claude-plugin/marketplace.extended.json and maintains the generated
 * blocks of the root README — the governed landing contract of blueprint 727
 * § 6A. CI fails if any bounded block is out of sync with the catalog.
 *
 * Blocks owned by this writer (the README's ONLY metrics writer — E1.9):
 *   - AUTO-TOC:  the category navigation table ONLY. Per-plugin rows are the
 *     drift engine every benchmarked repo fell into (728 § 4 C6) and are
 *     asserted absent — the catalog lives on the website and in the machine
 *     indexes, never here (§ 6A R1).
 *   - SCALE:     every published count with its cohort name and the command
 *     that reproduces it (§ 6A R4).
 *   - CERTIFICATION: rendered from certification-report.json when it exists;
 *     until Epic 10 produces one, renders the honest "not yet certified"
 *     state — never blank (§ 6A R10).
 *
 * Hard budgets enforced at emit time AND in --check (§ 6A R2): README ≤ 25 KB,
 * AUTO-TOC block ≤ 8 KB. The benchmark failure mode is a 50,315-byte README.
 *
 * Usage:
 *   node scripts/generate-readme-toc.mjs           # write README
 *   node scripts/generate-readme-toc.mjs --check   # CI: exit 1 if out of sync
 */

import { readFileSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join, resolve } from 'node:path';
import prettier from 'prettier';
import { resolveCorpus } from './corpus-resolver.mjs';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const EXTENDED = join(ROOT, '.claude-plugin', 'marketplace.extended.json');
const README = join(ROOT, 'README.md');

// ── Live stat counts ─────────────────────────────────────────────────────────
// The header badges + tagline counts (plugins / skills / agents) used to be
// hand-maintained and drifted stale. We recompute them here so they refresh on
// every `sync-marketplace`. Counts come from `git ls-files` — the COMMITTED tree —
// NOT the working directory, so a local-only/untracked SKILL.md can't skew the
// number and the result is byte-identical between a dev machine and CI's clean
// checkout (which is what `--check` compares against):
//   - plugins: catalog length (marketplace.extended.json)
//   - skills:  every tracked SKILL.md under plugins/ or skills/
//   - agents:  every tracked *.md inside an agents/ dir under plugins/
function trackedFiles() {
  const out = execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 128 * 1024 * 1024,
  });
  return out.split('\n').filter(Boolean);
}

function computeStats(catalog) {
  const plugins = (catalog.plugins || []).length;
  const files = trackedFiles();
  // The skills badge links to https://tonsofskills.com/skills, so it uses the
  // canonical marketplace-visible cohort rather than a second local walker:
  //   - skills/.curated/ is a GENERATED mirror of the best plugin skills
  //     (freshie/scripts/promote-to-curated.py) — already counted via its
  //     plugins/** source.
  //   - skills/NN-*/ is a root curriculum tree (01-devops-basics … 20 dirs,
  //     500 SKILL.md) the marketplace does NOT index. Verified live:
  //     /skills/01-devops-basics/ returns 404. Including it overstated the
  //     badge by 500 against its own link target.
  //
  // Deliberately a git-tracked-file count, NOT a read of
  // marketplace/src/data/unified-search-index.json. That artifact is committed
  // but regenerated per build, so a --check gate reading it compares a stale
  // committed value (3,008) against a fresh local one (3,069) and CI disagrees
  // with the developer — which is exactly how this change first failed CI.
  // git ls-files is byte-identical in CI and locally.
  //
  const skills = resolveCorpus('marketplace-visible', { root: ROOT }).length;
  const agents = files.filter(
    (f) => f.startsWith('plugins/') && f.includes('/agents/') && f.endsWith('.md'),
  ).length;
  return { plugins, skills, agents };
}

// Rewrite the hardcoded count occurrences (header badges + the two prose taglines)
// to the freshly computed values. Badges use plain integers; prose uses grouped.
function applyStats(readme, { plugins, skills, agents }) {
  const grouped = (n) => n.toLocaleString('en-US');
  return readme
    .replace(/badge\/plugins-[\d,%C]+-blue/g, `badge/plugins-${plugins}-blue`)
    .replace(/badge\/skills-[\d,%C]+-green/g, `badge/skills-${skills}-green`)
    .replace(
      /\d[\d,]* plugins, \d[\d,]* skills, \d[\d,]* agents/g,
      `${grouped(plugins)} plugins, ${grouped(skills)} skills, ${grouped(agents)} agents`,
    );
}

const TOC_START =
  '<!-- AUTO-TOC:START — do not edit; run `node scripts/generate-readme-toc.mjs` -->';
const TOC_END = '<!-- AUTO-TOC:END -->';
const SCALE_START =
  '<!-- SCALE:START — do not edit; run `node scripts/generate-readme-toc.mjs` -->';
const SCALE_END = '<!-- SCALE:END -->';
const CERT_START =
  '<!-- CERTIFICATION:START — do not edit; run `node scripts/generate-readme-toc.mjs` -->';
const CERT_END = '<!-- CERTIFICATION:END -->';

// § 6A R2 — byte budgets. The README is a landing contract, not a catalog.
const README_BYTE_BUDGET = 25 * 1024;
const TOC_BYTE_BUDGET = 8 * 1024;

// Display metadata for each category: emoji + human-friendly label.
// Categories not listed fall back to auto-title and a default emoji.
const CATEGORIES = {
  'ai-ml': { emoji: '🤖', label: 'AI & Machine Learning' },
  'ai-agency': { emoji: '🎭', label: 'AI Agents & Agency' },
  'api-development': { emoji: '🔌', label: 'API Development' },
  'business-tools': { emoji: '💼', label: 'Business Tools' },
  community: { emoji: '👥', label: 'Community' },
  crypto: { emoji: '₿', label: 'Crypto & Web3' },
  database: { emoji: '💾', label: 'Database' },
  design: { emoji: '🎨', label: 'Design' },
  devops: { emoji: '🔧', label: 'DevOps & Infrastructure' },
  examples: { emoji: '📚', label: 'Examples & Templates' },
  mcp: { emoji: '🧩', label: 'MCP Servers' },
  packages: { emoji: '📦', label: 'Packages' },
  performance: { emoji: '⚡', label: 'Performance' },
  productivity: { emoji: '✅', label: 'Productivity' },
  'saas-packs': { emoji: '🎁', label: 'SaaS Skill Packs' },
  security: { emoji: '🔐', label: 'Security' },
  'skill-enhancers': { emoji: '✨', label: 'Skill Enhancers' },
  testing: { emoji: '🧪', label: 'Testing' },
};

function metaFor(slug) {
  if (CATEGORIES[slug]) return CATEGORIES[slug];
  const label = slug
    .split(/[-_]/)
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : ''))
    .join(' ');
  return { emoji: '📁', label };
}

// GitHub auto-slug algorithm (matches @primer/slug / GFM TableOfContentsFilter):
//   1. lowercase
//   2. strip characters that aren't word-chars, hyphens, or plain spaces
//      (so "&" becomes nothing, "AI & ML" becomes "ai  ml" with two spaces)
//   3. replace each space with a hyphen (DO NOT collapse — "ai  ml" → "ai--ml")
// Unicode emojis fall into the "stripped" bucket, so leading emojis produce a
// leading hyphen; avoid by keeping display emojis out of the actual header text.
function githubSlug(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\- ]/g, '')
    .replace(/ /g, '-');
}

function escapeTable(text) {
  if (!text) return '';
  return text.replace(/\|/g, '\\|').replace(/\r?\n/g, ' ').replace(/\s+/g, ' ').trim();
}

function truncate(text, max = 120) {
  if (!text) return '';
  const clean = text.trim();
  if (clean.length <= max) return clean;
  return clean.slice(0, max - 1).replace(/\s+\S*$/, '') + '…';
}

function buildBlock(catalog) {
  const plugins = catalog.plugins || [];
  const byCategory = new Map();
  for (const p of plugins) {
    const cat = p.category || 'uncategorized';
    if (!byCategory.has(cat)) byCategory.set(cat, []);
    byCategory.get(cat).push(p);
  }

  // Stable ordering: CATEGORIES definition order first, then unknowns alpha.
  const known = Object.keys(CATEGORIES).filter((k) => byCategory.has(k));
  const unknown = Array.from(byCategory.keys())
    .filter((k) => !(k in CATEGORIES))
    .sort();
  const ordered = [...known, ...unknown];

  const lines = [];
  lines.push(TOC_START);
  lines.push('');
  lines.push('## Browse by category');
  lines.push('');
  lines.push(
    `The ${ordered.length} categories below link into the live marketplace. Plugin counts are the catalog-entry cohort — regenerated from \`marketplace.extended.json\` by this generator; the catalog itself lives on [tonsofskills.com](https://tonsofskills.com), never in this file (§ 6A of the platform blueprint).`,
  );
  lines.push('');

  // Category navigation table — the ONLY table this block may contain (R1).
  lines.push('|     | Category | Plugins |');
  lines.push('| --- | -------- | ------: |');
  for (const slug of ordered) {
    const meta = metaFor(slug);
    const count = byCategory.get(slug).length;
    lines.push(
      `| ${meta.emoji} | [${meta.label}](https://tonsofskills.com/plugins?category=${encodeURIComponent(slug)}) | ${count} |`,
    );
  }
  lines.push('');
  lines.push(TOC_END);
  return lines.join('\n');
}

// § 6A R4 — every published count with its cohort name and reproducing command.
function buildScaleBlock({ plugins, skills, agents }, categoryCount) {
  const grouped = (n) => n.toLocaleString('en-US');
  return [
    SCALE_START,
    '',
    '## Scale, labeled',
    '',
    'Every number below names the cohort it counts and the command that reproduces it — an unlabeled count is how a corpus ends up with five contradictory answers to "how many skills."',
    '',
    '| Count | Cohort | Reproduce with |',
    '| ----: | ------ | -------------- |',
    `| ${grouped(plugins)} | catalog plugins (catalog-entry cohort) | \`node scripts/generate-readme-toc.mjs\` over \`marketplace.extended.json\` |`,
    `| ${grouped(skills)} | marketplace-visible skills (distinct) | \`resolveCorpus('marketplace-visible')\` via \`pnpm run measure:e1\` |`,
    `| ${grouped(agents)} | agent definitions in plugins | \`git ls-files 'plugins/**' \\| grep '/agents/.*\\.md'\` |`,
    `| ${categoryCount} | plugin categories | \`ls -d plugins/*/\` |`,
    '',
    SCALE_END,
  ].join('\n');
}

// § 6A R10 — the certified/pending split renders from the certification report;
// an absent report renders the honest zero state, never a blank.
function buildCertBlock() {
  const reportPath = join(ROOT, 'certification-report.json');
  let body;
  try {
    const report = JSON.parse(readFileSync(reportPath, 'utf-8'));
    const certified = Number(report?.certified ?? 0);
    const pending = Number(report?.pending ?? 0);
    body =
      `Certification status from \`certification-report.json\`: ` +
      `**${certified} certified** · **${pending} pending**. A tier is a computed, expiring ` +
      `claim with retained evidence — never a self-approved badge.`;
  } catch {
    body =
      '**Not yet certified.** The certification program (tiers T0–T4 with retained, ' +
      'hash-matched evidence) is a later epic of the platform blueprint; until its report ' +
      'exists, no artifact on this surface claims a tier. This line is rendered from the ' +
      'absence of `certification-report.json` — honestly, not cosmetically.';
  }
  return [CERT_START, '', body, '', CERT_END].join('\n');
}

// Splice one sentinel-bounded block; the sentinels must already exist.
function spliceBlock(readme, start, end, block) {
  const startIdx = readme.indexOf(start);
  const endIdx = readme.indexOf(end);
  if (startIdx === -1 || endIdx === -1) {
    throw new Error(`README.md is missing the ${start.slice(5, 20)}… sentinels.`);
  }
  if (endIdx < startIdx) throw new Error(`README sentinels out of order for ${start}`);
  return readme.slice(0, startIdx) + block + readme.slice(endIdx + end.length);
}

// § 6A R1 + R2 — fail loudly at emit time, not just in a separate gate.
function assertLandingContract(finalText, tocBlock) {
  const readmeBytes = Buffer.byteLength(finalText, 'utf-8');
  if (readmeBytes > README_BYTE_BUDGET) {
    throw new Error(
      `README byte budget exceeded: ${readmeBytes} > ${README_BYTE_BUDGET} (§ 6A R2). ` +
        'The README is a landing contract — move content to the website or docs.',
    );
  }
  const tocBytes = Buffer.byteLength(tocBlock, 'utf-8');
  if (tocBytes > TOC_BYTE_BUDGET) {
    throw new Error(`AUTO-TOC byte budget exceeded: ${tocBytes} > ${TOC_BYTE_BUDGET} (§ 6A R2).`);
  }
  // R1: the block may contain exactly one table — the category table. A
  // planted per-plugin/per-skill row (backticked name cell) is a red run.
  const tableRows = tocBlock.split('\n').filter((l) => l.startsWith('|'));
  const backtickRows = tableRows.filter((l) => /^\|\s*`/.test(l));
  if (backtickRows.length > 0) {
    throw new Error(
      `AUTO-TOC contains ${backtickRows.length} per-plugin row(s) — forbidden (§ 6A R1 / 728 § 4 C6).`,
    );
  }
}

function replaceBlock(readme, newBlock) {
  const startIdx = readme.indexOf(TOC_START);
  const endIdx = readme.indexOf(TOC_END);

  if (startIdx === -1 || endIdx === -1) {
    throw new Error(
      `README.md is missing the TOC sentinels. Add:\n${TOC_START}\n${TOC_END}\nwhere the TOC should live.`,
    );
  }
  if (endIdx < startIdx) {
    throw new Error('README TOC sentinels are in the wrong order.');
  }

  const before = readme.slice(0, startIdx);
  const after = readme.slice(endIdx + TOC_END.length);
  return before + newBlock + after;
}

// Pipe the entire updated README through Prettier so the generator owns both
// the bounded block AND the surrounding-whitespace expectations Prettier has.
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
  const args = process.argv.slice(2);
  const checkMode = args.includes('--check');

  const catalog = JSON.parse(readFileSync(EXTENDED, 'utf-8'));
  const block = buildBlock(catalog);
  const stats = computeStats(catalog);
  const categoryCount = new Set((catalog.plugins || []).map((p) => p.category || 'uncategorized'))
    .size;
  const current = readFileSync(README, 'utf-8');
  let spliced = replaceBlock(current, block);
  spliced = spliceBlock(spliced, SCALE_START, SCALE_END, buildScaleBlock(stats, categoryCount));
  spliced = spliceBlock(spliced, CERT_START, CERT_END, buildCertBlock());
  spliced = applyStats(spliced, stats);
  const updated = await formatReadme(spliced);
  assertLandingContract(updated, block);

  if (checkMode) {
    if (current !== updated) {
      console.error(
        'README.md TOC is out of sync with marketplace.extended.json.\n' +
          'Run: node scripts/generate-readme-toc.mjs',
      );
      process.exit(1);
    }
    console.log('README TOC in sync.');
    return;
  }

  if (current === updated) {
    console.log('README TOC already up to date.');
    return;
  }

  writeFileSync(README, updated);
  const newBytes = Buffer.byteLength(updated, 'utf-8');
  console.log(`README updated (${(newBytes / 1024).toFixed(1)} KB).`);
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
