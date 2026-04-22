#!/usr/bin/env node
/**
 * One-shot fixup: rewrite `repository.url` and `bugs` in every
 * plugins/**\/package.json from the legacy `claude-code-plugins` slug to
 * the canonical `claude-code-plugins-plus-skills`. npm provenance validates
 * repository.url against the actual GitHub Actions repo slug at publish
 * time, and a mismatch causes HTTP 422 for every package.
 *
 * Run this once, commit the diff, then re-dispatch publish-all-packages.yml.
 */

import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const PLUGINS = join(ROOT, 'plugins');

const OLD_GIT = 'git+https://github.com/jeremylongshore/claude-code-plugins.git';
const NEW_GIT = 'git+https://github.com/jeremylongshore/claude-code-plugins-plus-skills.git';
const OLD_BUGS = 'https://github.com/jeremylongshore/claude-code-plugins/issues';
const NEW_BUGS = 'https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues';

const SKIP = new Set(['node_modules', '.git']);

function walkPkgJson(dir, out = []) {
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const e of entries) {
    if (SKIP.has(e.name)) continue;
    const p = join(dir, e.name);
    if (e.isDirectory()) walkPkgJson(p, out);
    else if (e.isFile() && e.name === 'package.json') out.push(p);
  }
  return out;
}

let fixed = 0;
let untouched = 0;
const files = walkPkgJson(PLUGINS);
for (const f of files) {
  const src = readFileSync(f, 'utf-8');
  let pkg;
  try {
    pkg = JSON.parse(src);
  } catch {
    continue;
  }
  let changed = false;
  if (pkg.repository?.url === OLD_GIT) {
    pkg.repository.url = NEW_GIT;
    changed = true;
  }
  if (pkg.bugs === OLD_BUGS) {
    pkg.bugs = NEW_BUGS;
    changed = true;
  } else if (pkg.bugs?.url === OLD_BUGS) {
    pkg.bugs.url = NEW_BUGS;
    changed = true;
  }
  if (changed) {
    writeFileSync(f, JSON.stringify(pkg, null, 2) + '\n');
    fixed++;
  } else {
    untouched++;
  }
}

console.log(`Scanned: ${files.length} package.json files`);
console.log(`Rewrote: ${fixed}`);
console.log(`Untouched: ${untouched}`);
