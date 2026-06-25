#!/usr/bin/env node
/**
 * External Plugin Sync Engine
 *
 * Syncs plugins from external repositories defined in sources.yaml.
 * Runs weekly via GitHub Actions to keep community plugins fresh.
 *
 * Usage:
 *   node scripts/sync-external.mjs [options]
 *
 * Options:
 *   --force        Force sync even if no changes detected
 *   --dry-run      Show what would be synced without making changes
 *   --source=NAME  Sync only the specified source
 *   --verbose      Show detailed output
 *
 * 2026-06-02 rewrite (claude-5h8v):
 *   Switched from per-file GitHub Contents-API calls to `git clone
 *   --depth=1 --filter=blob:none --sparse`. The previous implementation
 *   burned ~5000 API calls per run (one per file × 48 sources × references/**
 *   glob expansion) and 403'd out partway through every time. Git protocol
 *   has higher rate limits AND naturally handles the path filter via
 *   sparse-checkout, so we get all of a source's files in one operation.
 *
 *   Also added auto-catalog-entry generation: after a sync writes new
 *   files, if marketplace.extended.json has no entry for the plugin name,
 *   we generate one from sources.yaml metadata + the synced plugin.json.
 *   This closes the "filesystem synced but plugin invisible" gap that
 *   stranded 16 plugins from the v1 sync (tracked in claude-x1el).
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';
import yaml from 'js-yaml';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '..');
const SOURCES_FILE = path.join(ROOT_DIR, 'sources.yaml');
const CATALOG_FILE = path.join(ROOT_DIR, '.claude-plugin', 'marketplace.extended.json');

// Parse command line arguments
const args = process.argv.slice(2);
const options = {
  force: args.includes('--force'),
  dryRun: args.includes('--dry-run'),
  verbose: args.includes('--verbose'),
  source: args.find((a) => a.startsWith('--source='))?.split('=')[1] || null,
};

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  red: '\x1b[31m',
  cyan: '\x1b[36m',
};

function log(message, color = '') {
  console.log(`${color}${message}${colors.reset}`);
}

function logVerbose(message) {
  if (options.verbose) {
    console.log(`${colors.dim}  ${message}${colors.reset}`);
  }
}

/**
 * Sparse-clone a repo into a temp dir and return the local path.
 * The clone uses --depth=1 --filter=blob:none, then sparse-checkout
 * restricts blob materialization to the source_path subtree. Result:
 * ONE git fetch per source, zero REST API calls.
 *
 * Caller must clean up the returned tmpdir.
 */
function sparseCheckout(repo, sourcePath, branch = 'main') {
  const tmpdir = fs.mkdtempSync(path.join(os.tmpdir(), `sync-${repo.replace('/', '-')}-`));
  // Authenticated clone bumps rate limits when GITHUB_TOKEN is present.
  // Format: https://x-access-token:TOKEN@github.com/owner/repo.git
  const authUrl = process.env.GITHUB_TOKEN
    ? `https://x-access-token:${process.env.GITHUB_TOKEN}@github.com/${repo}.git`
    : `https://github.com/${repo}.git`;

  // Normalize source_path: '' or '.' means "whole repo root". Anything
  // else is treated as a path prefix. `--no-cone` mode treats patterns
  // as gitignore-style, so `/*` matches every entry at root recursively.
  const wholeRepo = !sourcePath || sourcePath === '.' || sourcePath === './';
  const sparsePattern = wholeRepo ? '/*' : sourcePath;

  try {
    execFileSync(
      'git',
      [
        'clone',
        '--depth=1',
        '--filter=blob:none',
        '--sparse',
        '--branch',
        branch,
        '--quiet',
        authUrl,
        tmpdir,
      ],
      { stdio: ['ignore', 'pipe', 'pipe'] },
    );

    execFileSync('git', ['-C', tmpdir, 'sparse-checkout', 'set', '--no-cone', sparsePattern], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    return tmpdir;
  } catch (err) {
    // Best-effort cleanup if the clone half-succeeded
    try {
      fs.rmSync(tmpdir, { recursive: true, force: true });
    } catch {
      // ignore
    }
    const stderr = err.stderr?.toString() || err.message;
    throw new Error(`git sparse-clone failed for ${repo}: ${stderr.trim().split('\n').pop()}`);
  }
}

/**
 * Walk a directory and return [{ path, content }] for every file.
 * Paths are relative to baseDir.
 */
function walkFiles(baseDir, relPrefix = '') {
  const out = [];
  let entries;
  try {
    entries = fs.readdirSync(baseDir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const ent of entries) {
    if (ent.name === '.git') continue;
    const abs = path.join(baseDir, ent.name);
    const rel = relPrefix ? `${relPrefix}/${ent.name}` : ent.name;
    if (ent.isDirectory()) {
      out.push(...walkFiles(abs, rel));
    } else if (ent.isFile()) {
      let content;
      let mode;
      try {
        // Read as a Buffer (not utf8) so exact bytes survive the round-trip —
        // utf8 re-encoding silently corrupts binaries. Capture the upstream
        // file mode so the executable bit can be restored on write (the
        // "Check plugin structure" gate requires scripts/*.sh to stay +x).
        content = fs.readFileSync(abs);
        mode = fs.statSync(abs).mode;
      } catch {
        // Unreadable; skip
        continue;
      }
      out.push({ path: rel, content, mode });
    }
  }
  return out;
}

/**
 * Check if a path matches any of the glob patterns.
 *
 * Pattern semantics (matches sources.yaml's intent):
 *   - Bare filename (`SKILL.md`)   → matches at any depth (treated as `**\/SKILL.md`)
 *   - Plain dir glob (`references/**`) → matches at any depth (treated as `**\/references/**`)
 *   - Leading `**\/` or `/`        → explicit path semantics, no auto-prefix
 *   - `**`                          → zero or more dirs (translated to `.*`)
 *   - `*`                           → one path segment (no `/`)
 *   - `?`                           → single char
 *
 * Why the auto-prefix: sources.yaml includes typically list `SKILL.md`,
 * `README.md`, `references/**` with the intent "any depth," but the older
 * regex anchored at the root of source_path. Many upstream repos nest one
 * extra layer (e.g. skills/tools/<plugin>/skills/<plugin>/SKILL.md), so
 * the strict match dropped real files. Auto-prefixing fixes that without
 * needing every sources.yaml entry rewritten.
 */
function matchesPattern(filePath, patterns) {
  if (!patterns || patterns.length === 0) return true;

  return patterns.some((rawPattern) => {
    // Auto-prefix `**/` unless the pattern already starts with `**` or `/`
    const pattern =
      rawPattern.startsWith('**') || rawPattern.startsWith('/') ? rawPattern : `**/${rawPattern}`;

    // Order matters: handle `?` (single-char glob) BEFORE we insert any
    // literal `?` chars (like `(?:.*/)?`) into the regex pattern. Then
    // substitute glob tokens left-to-right via unique placeholders so
    // they don't overlap.
    const escaped = pattern
      .replace(/\?/g, '<<<Q>>>') // glob `?` placeholder (before we add literal `?`)
      .replace(/\./g, '\\.') // escape literal dots (`.md` etc)
      .replace(/\*\*\//g, '<<<DSS>>>') // `**/` → zero or more dirs
      .replace(/\*\*/g, '<<<DS>>>') // bare `**` → anything
      .replace(/\*/g, '[^/]*') // `*` → single segment
      .replace(/<<<DSS>>>/g, '(?:.*/)?') // ← contains literal `?`, must come AFTER /\?/g
      .replace(/<<<DS>>>/g, '.*')
      .replace(/<<<Q>>>/g, '.');

    const regex = new RegExp('^' + escaped + '$');
    return regex.test(filePath);
  });
}

/**
 * Read marketplace.extended.json and check whether a plugin entry
 * already exists by name.
 */
function catalogHasEntry(pluginName) {
  if (!fs.existsSync(CATALOG_FILE)) return false;
  try {
    const data = JSON.parse(fs.readFileSync(CATALOG_FILE, 'utf8'));
    return (data.plugins || []).some((p) => p.name === pluginName);
  } catch {
    return false;
  }
}

/**
 * Derive the plugin's catalog category from the target_path's filesystem
 * location, not from sources.yaml metadata. The catalog invariant check
 * (validate-catalog-invariants.py) requires category to match the parent
 * directory. e.g., target_path 'plugins/mcp/x-bug-triage' implies
 * category='mcp' regardless of what sources.yaml claims.
 *
 * Falls back to sources.yaml category if the path doesn't follow the
 * plugins/<category>/<name> convention.
 */
function categoryFromTargetPath(targetPath, fallback) {
  const match = /(?:^|\/)plugins\/([^/]+)\//.exec(targetPath);
  return match ? match[1] : fallback || 'community';
}

/**
 * Ensure a minimal .claude-plugin/plugin.json exists for the synced
 * plugin. Some sources.yaml entries only sync SKILL.md + references/
 * because their upstream repo has no plugin.json (skill-only repos like
 * skyvern, ejentum). Without a plugin.json the downstream
 * generate-plugin-package-jsons.mjs can't produce a package.json, which
 * trips validate-catalog-invariants.py.
 *
 * We synthesize a minimal plugin.json from sources.yaml metadata. The
 * file is created ONLY if absent; existing upstream plugin.json files
 * are not overwritten.
 *
 * Returns true if a plugin.json was created, false if one already existed
 * or dry-run mode.
 */
function ensurePluginJson(source) {
  const pluginJsonPath = path.join(ROOT_DIR, source.target_path, '.claude-plugin', 'plugin.json');

  if (fs.existsSync(pluginJsonPath)) {
    return false; // upstream provided one, leave it alone
  }

  if (options.dryRun) {
    log(`   📋 Would synthesize .claude-plugin/plugin.json`, colors.yellow);
    return false;
  }

  const minimalPlugin = {
    name: source.name,
    version: '0.1.0',
    description: source.description || `${source.name} plugin`,
    author: source.author
      ? {
          name: source.author.name || 'External Contributor',
          ...(source.author.github ? { url: `https://github.com/${source.author.github}` } : {}),
          ...(source.author.email ? { email: source.author.email } : {}),
        }
      : { name: 'External Contributor' },
    ...(source.license ? { license: source.license } : {}),
    ...(source.repo ? { repository: `https://github.com/${source.repo}` } : {}),
  };

  const dir = path.dirname(pluginJsonPath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(pluginJsonPath, JSON.stringify(minimalPlugin, null, 2) + '\n');
  log(`   📋 Synthesized .claude-plugin/plugin.json (upstream had none)`, colors.green);
  return true;
}

/**
 * Ensure a README.md exists for the synced plugin. validate-plugins.yml
 * has a job that fails with "Missing README.md in <path>" otherwise.
 * Some upstream skill-only repos (ejentum/*) ship just SKILL.md and the
 * sources.yaml include pattern honestly reflects that.
 *
 * If README.md is missing, synthesize one from sources.yaml metadata.
 * If a SKILL.md exists at the plugin root, prefer that as the body
 * (rendered with a minimal header so reviewers see real content).
 *
 * Existing README.md files (from upstream sync) are never overwritten.
 *
 * Returns true if a README was created, false if one already existed
 * or dry-run mode.
 */
function ensureReadme(source) {
  const readmePath = path.join(ROOT_DIR, source.target_path, 'README.md');

  if (fs.existsSync(readmePath)) {
    return false; // upstream provided one, or earlier sync wrote one
  }

  if (options.dryRun) {
    log(`   📋 Would synthesize README.md`, colors.yellow);
    return false;
  }

  // Try to use the upstream SKILL.md content as the README body if one
  // is present at the plugin root. Falls back to a minimal stub.
  const skillPath = path.join(ROOT_DIR, source.target_path, 'SKILL.md');
  let body = '';
  if (fs.existsSync(skillPath)) {
    body = fs.readFileSync(skillPath, 'utf8');
    // Strip the YAML frontmatter (lines between two `---` lines at start)
    body = body.replace(/^---\n[\s\S]*?\n---\n+/, '');
  } else {
    body = source.description || `${source.name} plugin`;
  }

  const author = source.author?.name || 'External Contributor';
  const repoLink = source.repo ? `https://github.com/${source.repo}` : null;

  const readme = `# ${source.name}

${source.description || ''}

${body}

---

**Author:** ${author}${repoLink ? `  \n**Upstream:** [${source.repo}](${repoLink})` : ''}
${source.license ? `  \n**License:** ${source.license}` : ''}
`;

  const dir = path.dirname(readmePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(readmePath, readme);
  log(`   📋 Synthesized README.md (upstream had none)`, colors.green);
  return true;
}

/**
 * Auto-generate a marketplace.extended.json catalog entry for a freshly
 * synced source. Merges sources.yaml metadata with the synced
 * .claude-plugin/plugin.json (if present) to fill in version/keywords.
 *
 * Strategy: append the new entry to the plugins array. We write with
 * 2-space indent matching the catalog's canonical format, plus a final
 * newline. The check-catalog-format gate budgets +80±300 lines for one
 * added entry; a clean 20-25-line entry is well within that.
 *
 * Returns true if an entry was added, false if catalog already had one
 * or if dry-run mode.
 */
function ensureCatalogEntry(source) {
  if (catalogHasEntry(source.name)) {
    return false; // already present, no action
  }

  // Pull version + license from the synced plugin.json if available.
  const pluginJsonPath = path.join(ROOT_DIR, source.target_path, '.claude-plugin', 'plugin.json');
  let pluginJson = {};
  if (fs.existsSync(pluginJsonPath)) {
    try {
      pluginJson = JSON.parse(fs.readFileSync(pluginJsonPath, 'utf8'));
    } catch {
      // ignore parse errors; fall back to sources.yaml metadata
    }
  }

  // Build the catalog entry. Order matches the canonical layout in
  // marketplace.extended.json so the diff stays tight and check-catalog-format
  // doesn't trip.
  // Name is normalized to lowercase: Astro emits routes at
  // /plugins/<lowercased-name>/ and check-routes.mjs verifies exact match,
  // so a catalog entry named 'Claudebase' would 404 at /plugins/Claudebase/.
  // Category MUST match the target_path's parent dir per
  // validate-catalog-invariants.py — derive from path, not sources.yaml.
  const entry = {
    name: source.name.toLowerCase(),
    source: source.target_path.startsWith('./') ? source.target_path : `./${source.target_path}`,
    description: source.description || pluginJson.description || `${source.name} plugin`,
    version: pluginJson.version || '0.1.0',
    category: categoryFromTargetPath(source.target_path, source.category),
  };

  // Keywords: prefer plugin.json, fall back to sources.yaml, else infer from category
  if (Array.isArray(pluginJson.keywords) && pluginJson.keywords.length > 0) {
    entry.keywords = pluginJson.keywords;
  } else if (Array.isArray(source.keywords) && source.keywords.length > 0) {
    entry.keywords = source.keywords;
  }

  // Author: prefer plugin.json author shape (object), fall back to sources.yaml
  if (pluginJson.author && typeof pluginJson.author === 'object') {
    entry.author = {
      name: pluginJson.author.name || source.author?.name || 'External Contributor',
      ...(pluginJson.author.url ? { url: pluginJson.author.url } : {}),
      ...(pluginJson.author.email ? { email: pluginJson.author.email } : {}),
    };
  } else if (source.author) {
    entry.author = {
      name: source.author.name || 'External Contributor',
      ...(source.author.github ? { url: `https://github.com/${source.author.github}` } : {}),
      ...(source.author.email ? { email: source.author.email } : {}),
    };
  }

  if (pluginJson.homepage) entry.homepage = pluginJson.homepage;
  if (pluginJson.repository) entry.repository = pluginJson.repository;
  if (pluginJson.license || source.license) {
    entry.license = pluginJson.license || source.license;
  }

  if (options.dryRun) {
    log(`   📋 Would add catalog entry: ${source.name}`, colors.yellow);
    return false;
  }

  // Insert the entry. Append at the end of the plugins array, before the
  // closing brace. We avoid full JSON.stringify of the whole file because
  // that reformats every existing entry and trips check-catalog-format.
  const text = fs.readFileSync(CATALOG_FILE, 'utf8');
  const entryJson = JSON.stringify(entry, null, 2)
    .split('\n')
    .map((line, i) => (i === 0 ? `    ${line}` : `    ${line}`))
    .join('\n');

  // Find the last `}` immediately before `]\n}` (the plugins-array close).
  // Replace `    }\n  ]\n}` with `    },\n    <new>\n  ]\n}`.
  const closeMatch = text.match(/(\s*}\s*)(\n\s*]\s*\n\s*}\s*)$/);
  if (!closeMatch) {
    log(`   ⚠️  Could not locate catalog insertion point — skipping entry`, colors.yellow);
    return false;
  }
  const before = text.slice(0, closeMatch.index);
  const lastEntryClose = closeMatch[1];
  const arrayClose = closeMatch[2];
  // Insert a newline between the prior entry's `},` and the new entry so the
  // seam is `},\n    {` (matching the file's canonical formatting) instead of
  // jamming them onto one line as `},    {`, which the catalog-format gate flags.
  const updated = `${before}${lastEntryClose.replace(/}(\s*)$/, '},')}\n${entryJson}${arrayClose}`;

  fs.writeFileSync(CATALOG_FILE, updated);
  log(`   📋 Added catalog entry: ${source.name}`, colors.green);
  return true;
}

/**
 * Sync a single source via sparse git clone.
 */
async function syncSource(source, config) {
  log(`\n📦 Syncing: ${source.name}`, colors.cyan);
  log(`   From: ${source.repo}/${source.source_path}`, colors.dim);
  log(`   To:   ${source.target_path}`, colors.dim);

  const changes = [];
  const branch = source.branch || config?.default_branch || 'main';
  let tmpdir = null;

  try {
    tmpdir = sparseCheckout(source.repo, source.source_path, branch);
    logVerbose(`Sparse-cloned ${source.repo}@${branch} → ${tmpdir}`);

    // Walk the sourcePath subtree (or repo root when source_path is '.' / '').
    const wholeRepo =
      !source.source_path || source.source_path === '.' || source.source_path === './';
    const baseDir = wholeRepo ? tmpdir : path.join(tmpdir, source.source_path);
    const files = walkFiles(baseDir);

    if (files.length === 0) {
      log(`   ⚠️  No files found at source path`, colors.yellow);
      return { source: source.name, changes: [], error: 'No files found at source path' };
    }
    logVerbose(`Discovered ${files.length} files in source`);

    const filteredFiles = files.filter((file) => {
      const included = matchesPattern(file.path, source.include);
      const excluded = matchesPattern(file.path, source.exclude);
      return included && !excluded;
    });
    logVerbose(`${filteredFiles.length} files after filtering`);

    for (const file of filteredFiles) {
      const targetPath = path.join(ROOT_DIR, source.target_path, file.path);
      const targetDir = path.dirname(targetPath);

      let needsUpdate = false;
      let reason = 'new';

      if (fs.existsSync(targetPath)) {
        // Buffer-to-Buffer compare. file.content is now a Buffer; comparing it
        // against a utf8 string would ALWAYS be unequal, marking every synced
        // file "modified" on every run (churning all sources + bloating diffs).
        const existingContent = fs.readFileSync(targetPath);
        if (!existingContent.equals(file.content)) {
          needsUpdate = true;
          reason = 'modified';
        }
      } else {
        needsUpdate = true;
      }

      if (needsUpdate || options.force) {
        if (options.dryRun) {
          log(`   📝 Would ${reason === 'new' ? 'create' : 'update'}: ${file.path}`, colors.yellow);
        } else {
          if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
          }
          fs.writeFileSync(targetPath, file.content);
          // Restore the upstream file mode (rwx bits) so executable scripts
          // stay executable — git records 100755 and the structure gate passes.
          // A non-executable upstream file (e.g. 0644 README) is preserved as-is.
          if (typeof file.mode === 'number') fs.chmodSync(targetPath, file.mode & 0o777);
          log(`   ✅ ${reason === 'new' ? 'Created' : 'Updated'}: ${file.path}`, colors.green);
        }
        changes.push({ path: file.path, action: reason });
      } else {
        logVerbose(`Unchanged: ${file.path}`);
      }
    }

    if (changes.length > 0 && !options.dryRun) {
      const sourceJsonPath = path.join(ROOT_DIR, source.target_path, '.source.json');
      const sourceJson = {
        synced_from: {
          repo: source.repo,
          path: source.source_path,
          branch,
        },
        last_sync: new Date().toISOString(),
        author: source.author,
        license: source.license,
        files_synced: changes.length,
      };
      fs.writeFileSync(sourceJsonPath, JSON.stringify(sourceJson, null, 2));
      logVerbose(`Written .source.json`);
    }

    // Synthesize plugin.json + README.md if the upstream sync didn't
    // include them (skill-only repos like skyvern / ejentum). Required so
    // the downstream validators (generate-plugin-package-jsons.mjs,
    // validate-catalog-invariants.py, the README-check job) all pass.
    if (!options.dryRun) {
      const pluginJsonAdded = ensurePluginJson(source);
      if (pluginJsonAdded) {
        changes.push({ path: '.claude-plugin/plugin.json', action: 'plugin-json' });
      }
      const readmeAdded = ensureReadme(source);
      if (readmeAdded) {
        changes.push({ path: 'README.md', action: 'readme' });
      }
    }

    // Auto-register in the catalog if absent. This is the second half of
    // the sync — without it, files land on disk but the plugin stays
    // invisible to tonsofskills.com / ccpi CLI / search. The 16 stranded
    // entries documented in claude-x1el all stuck here.
    const catalogAdded = ensureCatalogEntry(source);
    if (catalogAdded) {
      changes.push({ path: '.claude-plugin/marketplace.extended.json', action: 'catalog' });
    }

    if (changes.length === 0) {
      log(`   ✓ No changes detected`, colors.dim);
    }

    return { source: source.name, changes, error: null };
  } catch (error) {
    log(`   ❌ Error: ${error.message}`, colors.red);
    return { source: source.name, changes: [], error: error.message };
  } finally {
    if (tmpdir) {
      try {
        fs.rmSync(tmpdir, { recursive: true, force: true });
      } catch {
        // tmpdir cleanup is best-effort
      }
    }
  }
}

/**
 * Main sync function
 */
async function main() {
  log('\n🔄 External Plugin Sync', colors.bright + colors.blue);
  log('='.repeat(50), colors.blue);

  if (options.dryRun) {
    log('DRY RUN MODE - No changes will be made\n', colors.yellow);
  }

  if (!fs.existsSync(SOURCES_FILE)) {
    log(`❌ sources.yaml not found at ${SOURCES_FILE}`, colors.red);
    process.exit(1);
  }

  const sourcesContent = fs.readFileSync(SOURCES_FILE, 'utf8');
  const { sources, config } = yaml.load(sourcesContent);

  if (!sources || sources.length === 0) {
    log('❌ No sources defined in sources.yaml', colors.red);
    process.exit(1);
  }

  log(`Found ${sources.length} source(s) to sync`, colors.dim);

  const sourcesToSync = options.source ? sources.filter((s) => s.name === options.source) : sources;

  if (options.source && sourcesToSync.length === 0) {
    log(`❌ Source "${options.source}" not found in sources.yaml`, colors.red);
    process.exit(1);
  }

  const results = [];
  for (const source of sourcesToSync) {
    const result = await syncSource(source, config);
    results.push(result);
  }

  log('\n' + '='.repeat(50), colors.blue);
  log('📊 Sync Summary', colors.bright + colors.blue);

  const totalChanges = results.reduce((acc, r) => acc + r.changes.length, 0);
  const catalogAdds = results.reduce(
    (acc, r) => acc + r.changes.filter((c) => c.action === 'catalog').length,
    0,
  );
  const errors = results.filter((r) => r.error);

  if (totalChanges > 0) {
    log(`✅ ${totalChanges} file(s) ${options.dryRun ? 'would be ' : ''}synced`, colors.green);
    if (catalogAdds > 0) {
      log(
        `📋 ${catalogAdds} catalog entr${catalogAdds === 1 ? 'y' : 'ies'} auto-added`,
        colors.green,
      );
    }
  } else {
    log('✓ All sources up to date', colors.dim);
  }

  if (errors.length > 0) {
    log(`⚠️  ${errors.length} source(s) had errors`, colors.yellow);
    errors.forEach((e) => log(`   - ${e.source}: ${e.error}`, colors.red));
  }

  if (process.env.GITHUB_OUTPUT) {
    const outputFile = process.env.GITHUB_OUTPUT;
    fs.appendFileSync(outputFile, `changes=${totalChanges}\n`);
    fs.appendFileSync(outputFile, `catalog_adds=${catalogAdds}\n`);
    fs.appendFileSync(outputFile, `sources=${results.map((r) => r.source).join(',')}\n`);
    fs.appendFileSync(outputFile, `has_changes=${totalChanges > 0}\n`);
  }

  log('\n');
  // Exit 1 only on TOTAL failure (no source succeeded). Partial failures
  // print warnings and are surfaced via the GitHub Actions summary, but they
  // shouldn't block downstream steps that need to commit the partial sync.
  const totalFailures = errors.length === sourcesToSync.length;
  process.exit(totalFailures ? 1 : 0);
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
