#!/usr/bin/env node
/**
 * generate-plugin-package-jsons.mjs
 *
 * For every plugin in `plugins/**` that has a `.claude-plugin/plugin.json` but
 * no sibling `package.json`, generate one following the @intentsolutionsio
 * scope + <slug> naming convention.
 *
 * npm packages are a TRACKING/PROOF layer only (D1=B). Installation remains
 * via the marketplace (`ccpi install <slug>` or `/plugin install <slug>`).
 *
 * Usage:
 *   node scripts/generate-plugin-package-jsons.mjs            # write files
 *   node scripts/generate-plugin-package-jsons.mjs --dry-run  # show plan only
 *   node scripts/generate-plugin-package-jsons.mjs --probe    # dry-run + npm registry collision check
 */

import { existsSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const PLUGINS_DIR = join(ROOT, 'plugins');
const REPO_URL = 'https://github.com/jeremylongshore/claude-code-plugins';
const SCOPE = '@intentsolutionsio';

// FS-only / personal-prefix dirs and known duplicates — skip entirely.
const EXCLUDE_PREFIXES = [
  join(PLUGINS_DIR, 'jeremy-google-adk'),
  join(PLUGINS_DIR, 'jeremy-vertex-ai'),
  join(PLUGINS_DIR, 'saas-packs', 'skill-databases'),
];

function isExcluded(pluginDir) {
  return EXCLUDE_PREFIXES.some((p) => pluginDir === p || pluginDir.startsWith(p + '/'));
}

function walkPluginDirs(root) {
  // Plugin root = any directory containing plugin.json (either at the
  // canonical .claude-plugin/plugin.json location or at the plugin root —
  // some 3rd-party contributions use the old root layout).
  const found = [];
  function walk(dir) {
    let entries;
    try {
      entries = readdirSync(dir, { withFileTypes: true });
    } catch {
      return;
    }
    const hasPluginJson =
      existsSync(join(dir, '.claude-plugin', 'plugin.json')) ||
      existsSync(join(dir, 'plugin.json'));
    if (hasPluginJson) {
      found.push(dir);
      // Still descend — rare nested plugins exist (e.g. the historical
      // saas-packs/skill-databases/windsurf duplicate). Exclusion list handles them.
    }
    for (const ent of entries) {
      if (!ent.isDirectory()) continue;
      // Skip internals that can't themselves be plugin roots.
      if (ent.name === 'node_modules' || ent.name === '.git' || ent.name === 'dist') continue;
      if (ent.name === '.claude-plugin') continue;
      if (ent.name === 'skills' || ent.name === 'commands' || ent.name === 'agents') continue;
      if (ent.name === 'hooks' || ent.name === 'scripts' || ent.name === 'references') continue;
      walk(join(dir, ent.name));
    }
  }
  walk(root);
  return found;
}

function readPluginJson(pluginDir) {
  const canonical = join(pluginDir, '.claude-plugin', 'plugin.json');
  const fallback = join(pluginDir, 'plugin.json');
  if (existsSync(canonical)) return readJson(canonical);
  if (existsSync(fallback)) return readJson(fallback);
  throw new Error(`no plugin.json at ${pluginDir}`);
}

function readJson(path) {
  return JSON.parse(readFileSync(path, 'utf-8'));
}

function slugFromPath(pluginDir) {
  return pluginDir.split('/').pop();
}

function scopedName(slug) {
  return `${SCOPE}/${slug}`;
}

// npm package names: lowercase, URL-safe, no spaces, max 214 chars. Our slugs
// are already kebab-case from plugin directory names, so pass-through.
function isValidNpmName(name) {
  if (name.length > 214) return false;
  const body = name.startsWith('@') ? name.slice(name.indexOf('/') + 1) : name;
  return /^[a-z0-9][a-z0-9._-]*$/.test(body);
}

function buildPackageJson(pluginDir, pluginJson) {
  const slug = slugFromPath(pluginDir);
  const relDir = relative(ROOT, pluginDir);
  const name = scopedName(slug);
  const description = (pluginJson.description || `Claude Code plugin: ${slug}`)
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 200);

  // Pull keywords from plugin.json, normalize, add standard tags.
  const baseKeywords = Array.isArray(pluginJson.keywords) ? pluginJson.keywords : [];
  const keywords = Array.from(
    new Set(
      [...baseKeywords, 'claude-code', 'claude-plugin', 'tonsofskills'].map((k) =>
        String(k).toLowerCase().trim()
      )
    )
  ).slice(0, 20); // npm soft-limits keywords; keep it reasonable

  // Only include files that actually exist in the plugin directory.
  const candidateFiles = [
    'README.md',
    '.claude-plugin',
    'skills',
    'commands',
    'agents',
    'hooks',
    'scripts',
  ];
  const files = candidateFiles.filter((f) => existsSync(join(pluginDir, f)));
  // Always ship README if present; if not, fall back to whatever exists.
  if (!files.includes('README.md') && existsSync(join(pluginDir, 'README.md'))) {
    files.unshift('README.md');
  }

  const pkg = {
    name,
    version: pluginJson.version && /^\d+\.\d+\.\d+/.test(pluginJson.version)
      ? pluginJson.version
      : '1.0.0',
    description,
    keywords,
    repository: {
      type: 'git',
      url: `git+${REPO_URL}.git`,
      directory: relDir,
    },
    homepage: `https://tonsofskills.com/plugins/${slug}`,
    bugs: `${REPO_URL}/issues`,
    license: pluginJson.license || 'MIT',
    author: pluginJson.author || {
      name: 'Jeremy Longshore',
      email: 'jeremy@intentsolutions.io',
      url: 'https://github.com/jeremylongshore',
    },
    publishConfig: { access: 'public' },
    files,
    scripts: {
      postinstall:
        'node -e "console.log(\\"\\\\n→ This npm package is a tracking/proof artifact. Install the plugin via:\\\\n  ccpi install ' +
        slug +
        '\\\\n  or /plugin install ' +
        slug +
        '@claude-code-plugins-plus in Claude Code\\\\n\\")"',
    },
  };

  return pkg;
}

async function probeNpmRegistry(name) {
  try {
    const res = await fetch(`https://registry.npmjs.org/${encodeURIComponent(name)}`, {
      method: 'HEAD',
    });
    // 200 = exists (could be ours or a collision)
    // 404 = free
    return res.status;
  } catch {
    return -1;
  }
}

async function collisionCheck(names, { concurrency = 10 } = {}) {
  const hits = new Map(); // name -> status
  let i = 0;
  async function worker() {
    while (i < names.length) {
      const idx = i++;
      const name = names[idx];
      const status = await probeNpmRegistry(name);
      hits.set(name, status);
    }
  }
  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);
  return hits;
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run') || args.includes('--probe');
  const probe = args.includes('--probe');

  const pluginDirs = walkPluginDirs(PLUGINS_DIR);
  const needsScaffold = [];
  const skipped = [];
  const existing = [];

  for (const pluginDir of pluginDirs) {
    if (isExcluded(pluginDir)) {
      skipped.push({ pluginDir, reason: 'excluded (personal-prefix or known duplicate)' });
      continue;
    }
    if (existsSync(join(pluginDir, 'package.json'))) {
      existing.push(pluginDir);
      continue;
    }
    const pluginJson = readPluginJson(pluginDir);
    const slug = slugFromPath(pluginDir);
    const candidateName = scopedName(slug);
    if (!isValidNpmName(candidateName)) {
      skipped.push({ pluginDir, reason: `invalid npm name: ${candidateName}` });
      continue;
    }
    needsScaffold.push({ pluginDir, slug, candidateName, pluginJson });
  }

  console.log(`Plugins with package.json already: ${existing.length}`);
  console.log(`Plugins to scaffold:                ${needsScaffold.length}`);
  console.log(`Skipped (excluded/invalid):         ${skipped.length}`);
  if (skipped.length) {
    for (const s of skipped) {
      console.log(`  - ${relative(ROOT, s.pluginDir)}: ${s.reason}`);
    }
  }

  if (probe) {
    console.log(`\nProbing npm registry for ${needsScaffold.length} candidate names...`);
    const names = needsScaffold.map((n) => n.candidateName);
    const statuses = await collisionCheck(names);
    const collisions = [];
    const free = [];
    const errors = [];
    for (const [name, status] of statuses) {
      if (status === 404) free.push(name);
      else if (status === 200) collisions.push(name);
      else errors.push(`${name} (HTTP ${status})`);
    }
    console.log(`  free (404):        ${free.length}`);
    console.log(`  already on npm:    ${collisions.length}`);
    console.log(`  unresolved:        ${errors.length}`);
    if (collisions.length) {
      console.log('\n  ⚠ Collisions — these names already exist on npm:');
      for (const c of collisions.slice(0, 30)) console.log(`    - ${c}`);
      if (collisions.length > 30) console.log(`    ... and ${collisions.length - 30} more`);
    }
    if (errors.length) {
      console.log('\n  ⚠ Unresolved (transient registry errors):');
      for (const e of errors.slice(0, 10)) console.log(`    - ${e}`);
    }
  }

  if (dryRun) {
    console.log('\nDry-run mode. No files written.');
    return;
  }

  let written = 0;
  for (const { pluginDir, pluginJson } of needsScaffold) {
    const pkg = buildPackageJson(pluginDir, pluginJson);
    const out = JSON.stringify(pkg, null, 2) + '\n';
    writeFileSync(join(pluginDir, 'package.json'), out);
    written++;
  }
  console.log(`\nWrote ${written} package.json files.`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
