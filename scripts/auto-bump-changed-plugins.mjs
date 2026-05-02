#!/usr/bin/env node
/**
 * auto-bump-changed-plugins.mjs
 *
 * Per-PR auto-bump of plugin patch versions.
 *
 * Runs in CI on every pull request. For each plugin whose source changed in
 * the PR (any file other than its own package.json), bump the plugin's
 * patch version. The CI workflow then commits the bump back to the PR
 * branch so `publish-changed-packages.yml` will republish that plugin
 * when the PR merges to main.
 *
 * Without this script the freeze regrows: a human edit to a plugin's
 * SKILL.md doesn't change the package.json version, so the publish
 * workflow no-ops, so `pnpm update` users never see the change. With
 * this script every code-touching PR ships.
 *
 * Plugin layout supported:
 *   plugins/<category>/<plugin>/                          (3-level)
 *   plugins/saas-packs/skill-databases/<plugin>/          (4-level nested)
 *   packages/<pkg>/                                       (root packages)
 *
 * Decisions per plugin:
 *   - Only its own package.json changed     →  no-op (bumper is idempotent)
 *   - Source files changed (not pkg.json)   →  bump patch
 *   - Source files + pkg.json changed       →  bump patch (use the new local
 *                                              version as the base, not what's
 *                                              on origin/main)
 *
 * Versions are bumped in JSON-text order so we don't reformat unrelated keys.
 *
 * Usage:
 *   node scripts/auto-bump-changed-plugins.mjs            # apply (default)
 *   node scripts/auto-bump-changed-plugins.mjs --dry-run  # preview
 *   BASE_REF=main node scripts/auto-bump-changed-plugins.mjs  # override base
 *
 * Exit codes:
 *   0 — success (any number of bumps including zero)
 *   1 — git diff failed or a package.json couldn't be parsed
 */

import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const SCOPE = '@intentsolutionsio/';

function parseVersion(v) {
  if (!v || typeof v !== 'string') return null;
  const m = /^(\d+)\.(\d+)\.(\d+)$/.exec(v.trim());
  if (!m) return null;
  return { major: +m[1], minor: +m[2], patch: +m[3] };
}

function fmtVersion(p) {
  return `${p.major}.${p.minor}.${p.patch}`;
}

function bumpPatch(v) {
  return { major: v.major, minor: v.minor, patch: v.patch + 1 };
}

// Map a changed file to its plugin/package directory, or null if it's not
// inside one we manage. Returns the path *relative to ROOT* (no leading slash).
function pluginDirFor(relPath) {
  const parts = relPath.split('/');

  if (parts[0] === 'packages' && parts.length >= 2) {
    return parts.slice(0, 2).join('/');
  }

  if (parts[0] !== 'plugins' || parts.length < 3) return null;

  // Special-case: saas-packs/skill-databases hosts nested plugins one level
  // deeper. Same rule publish-changed-packages.yml uses.
  if (parts[1] === 'saas-packs' && parts[2] === 'skill-databases' && parts.length >= 4) {
    return parts.slice(0, 4).join('/');
  }

  return parts.slice(0, 3).join('/');
}

// git ref characters per `git check-ref-format` simplified to a safe subset:
// alphanumerics, `_`, `.`, `/`, `-`. No spaces, no shell metachars. Refuse
// anything else so a hostile env var can't influence the spawned argv.
const SAFE_REF_RE = /^[A-Za-z0-9._/-]+$/;

function detectBaseRef() {
  let candidate;
  if (process.env.BASE_REF) candidate = process.env.BASE_REF;
  else if (process.env.GITHUB_BASE_REF) candidate = `origin/${process.env.GITHUB_BASE_REF}`;
  else candidate = 'origin/main';
  if (!SAFE_REF_RE.test(candidate)) {
    throw new Error(
      `Refusing to use unsafe base ref "${candidate}". Allowed chars: A-Z a-z 0-9 . _ / -`
    );
  }
  return candidate;
}

function gitDiff(args) {
  // Use spawnSync with argv-form (shell: false default) so untrusted ref
  // content can't be interpreted as shell. CodeQL js/indirect-command-line-
  // injection is satisfied because no input is concatenated into a string.
  return spawnSync('git', ['diff', '--name-only', ...args], {
    cwd: ROOT,
    encoding: 'utf-8',
    shell: false,
  });
}

function listChangedFiles(baseRef) {
  // Three-dot diff = "everything in HEAD that's not in baseRef" — exactly
  // the PR's footprint, ignoring main's own progress while the PR was open.
  let res = gitDiff([`${baseRef}...HEAD`]);
  if (res.status !== 0) {
    // Fall back to two-dot if the merge base isn't computable (shallow clone).
    res = gitDiff([baseRef, 'HEAD']);
  }
  if (res.status !== 0) {
    throw new Error(
      `git diff failed for base ref "${baseRef}": ${res.stderr || res.error?.message || 'non-zero exit'}. ` +
        `Set BASE_REF env var or ensure full fetch.`
    );
  }
  return res.stdout
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean);
}

function loadPackageJson(absPath) {
  if (!existsSync(absPath)) return null;
  const raw = readFileSync(absPath, 'utf-8');
  try {
    const pkg = JSON.parse(raw);
    return { raw, pkg };
  } catch {
    throw new Error(`Cannot parse JSON: ${absPath}`);
  }
}

function applyPatchBump(absPath, raw, oldVersion, newVersion) {
  const oldLine = `"version": "${oldVersion}"`;
  const newLine = `"version": "${newVersion}"`;
  if (!raw.includes(oldLine)) {
    throw new Error(
      `Cannot find exact "${oldLine}" line in ${absPath}; refusing to edit`
    );
  }
  writeFileSync(absPath, raw.replace(oldLine, newLine));
}

function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes('--dry-run');
  const baseRef = detectBaseRef();

  const changed = listChangedFiles(baseRef);
  if (!changed.length) {
    console.log(`No files changed vs ${baseRef}; nothing to bump.`);
    return;
  }

  const groups = new Map();
  for (const file of changed) {
    const dir = pluginDirFor(file);
    if (!dir) continue;
    const isPkgJson = file === `${dir}/package.json`;
    const g = groups.get(dir) || {
      changedFiles: [],
      pkgJsonChanged: false,
      sourceChanged: false,
    };
    g.changedFiles.push(file);
    if (isPkgJson) g.pkgJsonChanged = true;
    else g.sourceChanged = true;
    groups.set(dir, g);
  }

  const bumps = [];
  const skips = [];
  for (const [dir, g] of groups) {
    const absPkg = join(ROOT, dir, 'package.json');
    const loaded = loadPackageJson(absPkg);
    if (!loaded) {
      skips.push({ dir, reason: 'no package.json' });
      continue;
    }
    const { raw, pkg } = loaded;
    if (!pkg.name || !pkg.name.startsWith(SCOPE) || pkg.private) {
      skips.push({ dir, reason: `not @intentsolutionsio/* or private: ${pkg.name}` });
      continue;
    }
    if (!g.sourceChanged) {
      // Only the package.json itself changed. Don't double-bump.
      skips.push({ dir, reason: 'only package.json changed' });
      continue;
    }
    const declared = parseVersion(pkg.version);
    if (!declared) {
      skips.push({
        dir,
        reason: `local version "${pkg.version}" is not strict X.Y.Z`,
      });
      continue;
    }
    const next = bumpPatch(declared);
    bumps.push({
      dir,
      absPkg,
      raw,
      name: pkg.name,
      from: fmtVersion(declared),
      to: fmtVersion(next),
    });
  }

  if (!bumps.length) {
    console.log(`No plugin source changes vs ${baseRef}; nothing to bump.`);
    if (skips.length) {
      console.log(`Skipped ${skips.length} dir(s):`);
      for (const s of skips) console.log(`  ${s.dir}: ${s.reason}`);
    }
    return;
  }

  console.log(`Plan (vs ${baseRef}):`);
  for (const b of bumps) {
    console.log(`  ${b.name.padEnd(50)}  ${b.from} → ${b.to}  (${b.dir})`);
  }
  if (skips.length) {
    console.log('Skipped:');
    for (const s of skips) console.log(`  ${s.dir}: ${s.reason}`);
  }

  if (dryRun) {
    console.log('\n(--dry-run; no files written)');
    return;
  }

  for (const b of bumps) {
    applyPatchBump(b.absPkg, b.raw, b.from, b.to);
  }

  console.log('');
  console.log(`bumped: ${bumps.length}`);
  console.log(`no-op:  ${skips.length}`);
}

try {
  main();
} catch (err) {
  console.error(err.message || err);
  process.exit(1);
}
