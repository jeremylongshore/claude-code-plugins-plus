#!/usr/bin/env node
/**
 * Update Metrics — Surgically updates plugin/skill/agent counts everywhere they
 * appear in README.md, plus the GitHub repo description.
 *
 * Source of truth (in priority order):
 *   - .claude-plugin/marketplace.extended.json      → pluginCount, categories, mcp/saas/instruction split
 *   - marketplace/src/data/unified-search-index.json → skillCount, agentCount
 *   - README contributor list (literal count of `- **[@user]` entries)
 *
 * What gets updated in README.md:
 *   1. shields.io badges (top of file): plugins-NNN-blue and skills-N,NNN-green
 *   2. Top-of-file tagline: "NNN plugins, X,XXX skills, NNN agents, N community contributors"
 *   3. "The Numbers" table mid-doc (Total skills / Plugins / Agents / Categories / Contributors)
 *   4. "Plugin Types" section: AI Instruction (NNN plugins), MCP Server (N), SaaS Skill Packs (NNN)
 *   5. Footer version stamp: "Skills: X,XXX | Plugins: NNN"
 *
 * GitHub repo description is also synced (best-effort; needs `gh` auth).
 *
 * Usage:
 *   node scripts/update-metrics.mjs [--dry-run]
 *
 * Runs weekly via .github/workflows/update-metrics.yml
 */

import { readFileSync, writeFileSync, existsSync } from 'fs';
import { resolve, dirname, join } from 'path';
import { fileURLToPath } from 'url';
import { execSync } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const REPO_ROOT = resolve(__dirname, '..');
const DRY_RUN = process.argv.includes('--dry-run');

console.log(`\nMetrics Update${DRY_RUN ? ' (DRY RUN)' : ''}\n${'='.repeat(48)}\n`);

// ── 1. Load source-of-truth catalogs ─────────────────────────────
const catalogPath = join(REPO_ROOT, '.claude-plugin/marketplace.extended.json');
const searchIndexPath = join(REPO_ROOT, 'marketplace/src/data/unified-search-index.json');
const skillsCatalogPath = join(REPO_ROOT, 'marketplace/src/data/skills-catalog.json');
const readmePath = join(REPO_ROOT, 'README.md');

const catalog = JSON.parse(readFileSync(catalogPath, 'utf-8'));
const pluginCount = catalog.plugins.length;
const categorySet = new Set(catalog.plugins.map((p) => p.category));
const categoryCount = categorySet.size;
const mcpCount = catalog.plugins.filter((p) => p.category === 'mcp').length;
const saasPackCount = catalog.plugins.filter((p) => p.category === 'saas-packs').length;
const aiInstructionCount = pluginCount - mcpCount - saasPackCount;

let skillCount;
let agentCount;
if (existsSync(searchIndexPath)) {
  const searchIndex = JSON.parse(readFileSync(searchIndexPath, 'utf-8'));
  skillCount = searchIndex.stats.totalSkills;
  agentCount = searchIndex.stats.totalAgents ?? 0;
} else if (existsSync(skillsCatalogPath)) {
  const skillsCatalog = JSON.parse(readFileSync(skillsCatalogPath, 'utf-8'));
  skillCount = skillsCatalog.count;
  agentCount = 0; // unknown without unified index
  console.warn('⚠ unified-search-index.json missing; agentCount unknown (using 0).');
} else {
  console.error('ERROR: No skills data found. Run marketplace build first.');
  process.exit(1);
}

// ── 2. Read README + count contributors literally ────────────────
let readme = readFileSync(readmePath, 'utf-8');
const original = readme;
const contributorCount = countContributors(readme);

console.log(`Plugins:        ${pluginCount}  (mcp=${mcpCount}, saas=${saasPackCount}, ai-instruction=${aiInstructionCount})`);
console.log(`Skills:         ${skillCount}`);
console.log(`Agents:         ${agentCount}`);
console.log(`Categories:     ${categoryCount}`);
console.log(`Contributors:   ${contributorCount}\n`);

const fmt = (n) => Number(n).toLocaleString('en-US');

// ── 3. Apply replacements ────────────────────────────────────────
readme = applySubstitution(readme, {
  // 3a. shields.io badges (URL-encoded: comma → %2C)
  // Plugins badge: ![Plugins](https://img.shields.io/badge/plugins-NNN-blue)
  pluginsBadge: {
    re: /(badge\/plugins-)\d+(-blue)/g,
    to: `$1${pluginCount}$2`,
    label: `plugins badge → ${pluginCount}`,
  },
  // Skills badge: ![Skills](https://img.shields.io/badge/skills-N%2CNNN-green)
  skillsBadge: {
    re: /(badge\/skills-)[\d,%C]+(-green)/g,
    to: `$1${encodeURIComponent(fmt(skillCount))}$2`,
    label: `skills badge → ${fmt(skillCount)}`,
  },

  // 3b. Top-of-file tagline (line ~10):
  //     "NNN plugins, X,XXX skills, NNN agents, N community contributors — validated and ready to install."
  tagline: {
    re: /^\d[\d,]*\s+plugins,\s+[\d,]+\s+skills,\s+\d+\s+agents,\s+\d+\s+community contributors\b/m,
    to: `${pluginCount} plugins, ${fmt(skillCount)} skills, ${agentCount} agents, ${contributorCount} community contributors`,
    label: 'top-of-file tagline',
  },

  // 3c. "The Numbers" table cells. Each row is matched by its label column.
  numbersTotalSkills: {
    re: /(\|\s*Total skills\s*\|\s*)[\d,]+(\s*\|)/,
    to: `$1${fmt(skillCount)}$2`,
    label: 'Numbers table: Total skills',
  },
  numbersPlugins: {
    re: /(\|\s*Plugins \(marketplace\)\s*\|\s*)[\d,]+(\s*\|)/,
    to: `$1${pluginCount}$2`,
    label: 'Numbers table: Plugins',
  },
  numbersAgents: {
    re: /(\|\s*Agents\s*\|\s*)[\d,]+(\s*\|)/,
    to: `$1${agentCount}$2`,
    label: 'Numbers table: Agents',
  },
  numbersCategories: {
    re: /(\|\s*Plugin categories\s*\|\s*)[\d,]+(\s*\|)/,
    to: `$1${categoryCount}$2`,
    label: 'Numbers table: Categories',
  },
  numbersContributors: {
    re: /(\|\s*Contributors\s*\|\s*)[\d,]+(\s*\|)/,
    to: `$1${contributorCount}$2`,
    label: 'Numbers table: Contributors',
  },

  // 3d. "Plugin Types" subtotals — three lines:
  //     ### AI Instruction Plugins (NNN plugins)
  //     ### MCP Server Plugins (N plugins)
  //     ### SaaS Skill Packs (NNN plugins ...)
  pluginTypesAi: {
    re: /(### AI Instruction Plugins \()\d+( plugins?\))/,
    to: `$1${aiInstructionCount}$2`,
    label: 'Plugin Types: AI Instruction',
  },
  pluginTypesMcp: {
    re: /(### MCP Server Plugins \()\d+( plugins?\))/,
    to: `$1${mcpCount}$2`,
    label: 'Plugin Types: MCP',
  },
  // SaaS line currently reads "(NNN plugins across NN pack collections)".
  // We rewrite the leading plugin count and leave the trailing prose alone, since
  // pack collection count is editorial, not catalog-derived.
  pluginTypesSaas: {
    re: /(### SaaS Skill Packs \()\d+( plugins\b)/,
    to: `$1${saasPackCount}$2`,
    label: 'Plugin Types: SaaS Packs',
  },

  // 3e. Footer version stamp
  //     **Version**: X.Y.Z | **Last Updated**: ... | **Skills**: X,XXX | **Plugins**: NNN
  footerSkills: {
    re: /(\*\*Skills\*\*:\s+)[\d,]+/,
    to: `$1${fmt(skillCount)}`,
    label: 'Footer: Skills',
  },
  footerPlugins: {
    re: /(\*\*Plugins\*\*:\s+)\d+/,
    to: `$1${pluginCount}`,
    label: 'Footer: Plugins',
  },
});

// ── 4. Write README ──────────────────────────────────────────────
if (readme !== original) {
  if (!DRY_RUN) {
    writeFileSync(readmePath, readme, 'utf-8');
    console.log(`\n✔ Wrote updated README.md`);
  } else {
    console.log(`\n(DRY RUN) Would update README.md`);
  }
} else {
  console.log(`\nREADME.md: already in sync`);
}

// ── 5. GitHub repo description ───────────────────────────────────
// Wording mirrors the existing description; only the three numbers change.
const newDescription = `${pluginCount} plugins, ${fmt(skillCount)} skills, ${agentCount} agents for Claude Code. Open-source marketplace at tonsofskills.com with the ccpi CLI package manager.`;
let currentDescription = '';
try {
  currentDescription = execSync('gh repo view --json description -q .description', {
    cwd: REPO_ROOT,
    encoding: 'utf-8',
    timeout: 10000,
  }).trim();
} catch {
  console.log('\nSkipping repo description sync (gh CLI not available or unauthed).');
}
if (currentDescription && currentDescription !== newDescription) {
  console.log(`\nRepo description:`);
  console.log(`  Old: ${currentDescription}`);
  console.log(`  New: ${newDescription}`);
  if (!DRY_RUN) {
    try {
      execSync(`gh repo edit --description "${newDescription.replace(/"/g, '\\"')}"`, {
        cwd: REPO_ROOT,
        encoding: 'utf-8',
        timeout: 10000,
      });
      console.log(`  ✔ Updated`);
    } catch (e) {
      console.log(`  ⚠ Failed: ${e.message}`);
    }
  } else {
    console.log(`  (DRY RUN)`);
  }
}

console.log(`\n${'='.repeat(48)}`);
console.log(`Metrics update complete${DRY_RUN ? ' (DRY RUN)' : ''}`);
console.log();

// ── helpers ──────────────────────────────────────────────────────

function countContributors(text) {
  // Count entries in the `## Contributors` section: lines starting with `- **[@…`
  const lines = text.split('\n');
  let inSection = false;
  let n = 0;
  for (const line of lines) {
    if (/^##\s+Contributors\b/.test(line)) {
      inSection = true;
      continue;
    }
    if (inSection && /^##\s+/.test(line)) break;
    if (inSection && /^- \*\*\[@/.test(line)) n++;
  }
  return n;
}

function applySubstitution(text, ops) {
  let out = text;
  for (const [, op] of Object.entries(ops)) {
    const before = out;
    // Re-clone the regex per use so /g doesn't carry stale lastIndex across .test() + .replace().
    const probe = new RegExp(op.re.source, op.re.flags);
    const matched = probe.test(out);
    out = out.replace(op.re, op.to);
    if (!matched) {
      console.log(`  ! ${op.label.padEnd(36)} (pattern not found — likely stale)`);
    } else if (out === before) {
      console.log(`  · ${op.label.padEnd(36)} (already current)`);
    } else {
      console.log(`  ✔ ${op.label}`);
    }
  }
  return out;
}
