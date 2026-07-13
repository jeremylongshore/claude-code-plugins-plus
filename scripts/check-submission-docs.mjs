#!/usr/bin/env node
/**
 * check-submission-docs.mjs — CI intake gate for the tiered submission-documents
 * standard (000-docs/700-DR-GUID-skill-submission-standard.md).
 *
 * WHY THIS EXISTS
 *   Every plugin submission — external and Intent Solutions' own — must ship the
 *   written proof its tier requires (templates/skill-docs/README.md). The
 *   standard existed but nothing deterministic enforced it, so a new plugin
 *   could land docs-less and the debt piled onto human review. This gate reads
 *   the PR diff, finds NEW plugin directories, classifies each one's tier from
 *   its contents, and fails the PR listing exactly which required documents are
 *   missing.
 *
 * WHAT COUNTS AS A "NEW PLUGIN"
 *   A plugin dir is a directory containing `.claude-plugin/plugin.json`. It is
 *   NEW when that plugin.json is an ADDED file in the diff vs the base ref
 *   (`--diff-filter=A`), staged, or untracked. Edits to existing plugins are
 *   out of scope — this is an intake gate, not a retroactive sweep of the
 *   existing corpus.
 *
 * TIER → REQUIRED DOCS (the matrix in templates/skill-docs/README.md; the doc
 * files live in the plugin dir as docs/PRD.md etc — a root-level PRD.md is also
 * accepted, matching the templates/skill-docs/examples/mnemos worked example):
 *   micro     a single command/skill/agent, no scripts   → PRD.md
 *   standard  scripts, or more than one component        → PRD.md + ADR.md
 *   pack      two or more skills (multi-skill pack)      → PRD.md + ADR.md + ONE-PAGER.md
 *   CFO-ONE-PAGER.md ("where money is the pitch") is an editorial judgment the
 *   gate cannot make deterministically — it stays review-enforced, not
 *   gate-enforced.
 *
 * EXEMPTION
 *   A dir containing `.source.json` is an externally-synced mirror
 *   (scripts/sync-external.mjs writes that marker). Mirrors are exempt: the
 *   contributor's own repo is the source of truth and their docs live upstream
 *   (see CLAUDE.md § External Plugin Sync). The exemption is logged, never
 *   silent.
 *
 * DESIGNED CLEAN PASS
 *   A PR that adds no new plugin exits 0 with a log line. The skip lives INSIDE
 *   the script — the CI job always runs and always reports, so the ci-required
 *   aggregate never sees an undesigned `skipped` result (CLAUDE.md § CI gate
 *   architecture, rule 3).
 *
 * USAGE
 *   node scripts/check-submission-docs.mjs --changed-only --base origin/main   # CI mode
 *   node scripts/check-submission-docs.mjs plugins/devops/my-plugin            # check a dir directly
 *   node scripts/check-submission-docs.mjs --root /path/to/repo --changed-only --base <ref>
 *
 * EXIT CODES
 *   0  no new plugins, all required docs present, or only exempt mirrors
 *   1  at least one new plugin is missing required documents
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { execFileSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_ROOT = path.resolve(__dirname, '..');
const TEMPLATES_HINT = 'templates/skill-docs/';
const STANDARD_HINT = '000-docs/700-DR-GUID-skill-submission-standard.md';

const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

export const TIER = { MICRO: 'micro', STANDARD: 'standard', PACK: 'pack' };

/** Required document basenames per tier (the templates/skill-docs matrix). */
export function requiredDocsForTier(tier) {
  switch (tier) {
    case TIER.MICRO:
      return ['PRD.md'];
    case TIER.STANDARD:
      return ['PRD.md', 'ADR.md'];
    case TIER.PACK:
      return ['PRD.md', 'ADR.md', 'ONE-PAGER.md'];
    default:
      throw new Error(`unknown tier: ${tier}`);
  }
}

// File extensions that make a plugin "has scripts" for tier purposes. Markdown
// and JSON manifests are not scripts; executable/interpreted code is.
const SCRIPT_EXT = new Set([
  '.sh',
  '.bash',
  '.zsh',
  '.py',
  '.js',
  '.mjs',
  '.cjs',
  '.ts',
  '.tsx',
  '.jsx',
]);

// Dirs whose contents never count toward the inventory: the docs being graded,
// the manifest dir, and the forge build-time audit trail.
const INVENTORY_EXCLUDED_DIRS = new Set([
  'docs',
  '.claude-plugin',
  '.forge',
  '.git',
  'node_modules',
]);

/**
 * Classify a plugin's tier from its component inventory. Pure, so tests drive
 * it directly.
 *
 * @param {{skills:number, commands:number, agents:number, hasScripts:boolean}} inv
 * @returns {string} one of TIER.*
 */
export function classifyTier(inv) {
  if (inv.skills >= 2) return TIER.PACK; // multi-skill pack
  const components = inv.skills + inv.commands + inv.agents;
  if (inv.hasScripts || components >= 2) return TIER.STANDARD; // skills plus scripts/commands
  return TIER.MICRO; // a single command or skill, no scripts
}

/**
 * Walk a plugin directory and count its components.
 *
 * @param {string} absPluginDir
 * @returns {{skills:number, commands:number, agents:number, hasScripts:boolean}}
 */
export function inventoryPluginDir(absPluginDir) {
  const inv = { skills: 0, commands: 0, agents: 0, hasScripts: false };
  const walk = (absDir, relSegments) => {
    let entries;
    try {
      entries = fs.readdirSync(absDir, { withFileTypes: true });
    } catch {
      return;
    }
    for (const ent of entries) {
      if (ent.isDirectory()) {
        if (relSegments.length === 0 && INVENTORY_EXCLUDED_DIRS.has(ent.name)) continue;
        if (ent.name === '.git' || ent.name === 'node_modules') continue;
        walk(path.join(absDir, ent.name), [...relSegments, ent.name]);
        continue;
      }
      if (!ent.isFile()) continue;
      const top = relSegments[0] ?? '';
      const ext = path.extname(ent.name).toLowerCase();
      if (ent.name === 'SKILL.md' && (top === 'skills' || relSegments.length === 0)) {
        inv.skills++;
      } else if (top === 'commands' && ext === '.md') {
        inv.commands++;
      } else if (top === 'agents' && ext === '.md') {
        inv.agents++;
      } else if (SCRIPT_EXT.has(ext)) {
        inv.hasScripts = true;
      } else if (top === 'hooks') {
        // Hook configs auto-execute commands — a hooks/ dir is beyond micro
        // even when the payload lives in a JSON/YAML file, not a script file.
        inv.hasScripts = true;
      }
    }
  };
  walk(absPluginDir, []);
  return inv;
}

/**
 * Resolve where a required doc actually is: `docs/<name>` (the canonical
 * location per the 700 standard) or `<name>` at the plugin root (the shape of
 * the mnemos worked example). Empty files do not count.
 *
 * @returns {string|null} repo-relative-ish path found, or null when missing
 */
export function findDoc(absPluginDir, docName) {
  for (const candidate of [path.join('docs', docName), docName]) {
    const abs = path.join(absPluginDir, candidate);
    try {
      const st = fs.statSync(abs);
      if (st.isFile() && st.size > 0) return candidate;
    } catch {
      /* keep looking */
    }
  }
  return null;
}

/**
 * Check one plugin dir against the standard.
 *
 * @param {string} rootDir  repo root
 * @param {string} pluginDir  repo-relative plugin dir
 * @returns {{pluginDir:string, exempt:boolean, tier?:string, inventory?:object,
 *            missing?:string[], found?:string[]}}
 */
export function checkPlugin(rootDir, pluginDir) {
  const abs = path.resolve(rootDir, pluginDir);
  if (fs.existsSync(path.join(abs, '.source.json'))) {
    return { pluginDir, exempt: true };
  }
  const inventory = inventoryPluginDir(abs);
  const tier = classifyTier(inventory);
  const missing = [];
  const found = [];
  for (const doc of requiredDocsForTier(tier)) {
    const where = findDoc(abs, doc);
    if (where) found.push(where);
    else missing.push(doc);
  }
  return { pluginDir, exempt: false, tier, inventory, missing, found };
}

/**
 * Plugin dirs whose `.claude-plugin/plugin.json` is ADDED in the diff vs
 * `base` (committed, staged, or untracked — same collection mechanism as
 * scan-synced-content.mjs, narrowed to added manifests under plugins/).
 *
 * @returns {string[]} repo-relative plugin dirs, deduped + sorted
 */
export function newPluginDirsFromDiff(rootDir, base) {
  const run = (args) => {
    try {
      return execFileSync('git', ['-C', rootDir, ...args], {
        encoding: 'utf8',
        stdio: ['ignore', 'pipe', 'ignore'],
      })
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
    } catch {
      return [];
    }
  };
  const added = new Set([
    ...run(['diff', '--name-only', '--diff-filter=A', base]),
    ...run(['diff', '--name-only', '--diff-filter=A', '--cached', base]),
    ...run(['ls-files', '--others', '--exclude-standard']),
  ]);
  const dirs = new Set();
  const manifestRe = /^plugins\/.+\/\.claude-plugin\/plugin\.json$/;
  for (const rel of added) {
    if (!manifestRe.test(rel)) continue;
    dirs.add(path.dirname(path.dirname(rel)));
  }
  return [...dirs].sort();
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────
function parseArgs(argv) {
  const opts = { changedOnly: false, base: null, root: DEFAULT_ROOT, paths: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--changed-only') opts.changedOnly = true;
    else if (a === '--base') opts.base = argv[++i];
    else if (a.startsWith('--base=')) opts.base = a.slice('--base='.length);
    else if (a === '--root') opts.root = path.resolve(argv[++i]);
    else if (a.startsWith('--root=')) opts.root = path.resolve(a.slice('--root='.length));
    else if (a.startsWith('--')) {
      /* ignore unknown flags */
    } else opts.paths.push(a);
  }
  return opts;
}

function log(msg, color = '') {
  console.log(`${color}${msg}${colors.reset}`);
}

function main() {
  const opts = parseArgs(process.argv.slice(2));

  let pluginDirs;
  if (opts.paths.length > 0) {
    pluginDirs = opts.paths.map((p) => path.relative(opts.root, path.resolve(opts.root, p)));
  } else {
    const base = opts.base || 'origin/main';
    pluginDirs = newPluginDirsFromDiff(opts.root, base);
    log(`📋 Submission-documents intake gate (base: ${base})\n`, colors.bright + colors.cyan);
    if (pluginDirs.length === 0) {
      // Designed clean pass: the job always runs and always reports; a PR that
      // adds no new plugin has nothing for this standard to grade.
      log('✅ No new plugin directories in this diff — nothing to check.', colors.green);
      process.exitCode = 0;
      return;
    }
  }

  let failures = 0;
  for (const pluginDir of pluginDirs) {
    const result = checkPlugin(opts.root, pluginDir);
    if (result.exempt) {
      log(
        `  ✓ ${pluginDir} — external mirror (.source.json): exempt, docs live upstream`,
        colors.dim,
      );
      continue;
    }
    const inv = result.inventory;
    const shape = `${inv.skills} skill(s), ${inv.commands} command(s), ${inv.agents} agent(s), scripts: ${inv.hasScripts ? 'yes' : 'no'}`;
    if (result.missing.length === 0) {
      log(
        `  ✓ ${pluginDir} — tier: ${result.tier} (${shape}) — all required docs present`,
        colors.green,
      );
      for (const f of result.found) log(`      found: ${pluginDir}/${f}`, colors.dim);
    } else {
      failures++;
      log(`  ✗ ${pluginDir} — tier: ${result.tier} (${shape})`, colors.red);
      for (const doc of result.missing) {
        log(`      MISSING required document: ${pluginDir}/docs/${doc}`, colors.red);
      }
      for (const f of result.found) log(`      found: ${pluginDir}/${f}`, colors.dim);
    }
  }

  if (failures > 0) {
    log(
      `\n❌ ${failures} new plugin(s) missing required submission documents.`,
      colors.bright + colors.red,
    );
    log(
      `   Fix: copy the fill-in templates from ${TEMPLATES_HINT} into your plugin dir as\n` +
        `   docs/PRD.md (+ docs/ADR.md, docs/ONE-PAGER.md per your tier) and fill them in.\n` +
        `   Tier matrix: ${TEMPLATES_HINT}README.md · standard: ${STANDARD_HINT}\n` +
        `   Worked example: ${TEMPLATES_HINT}examples/mnemos/`,
      colors.yellow,
    );
    process.exitCode = 1;
    return;
  }
  log('\n✅ Submission-documents gate passed.', colors.green);
  process.exitCode = 0;
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  main();
}
