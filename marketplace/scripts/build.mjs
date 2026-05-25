#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, '..', '..');

function run(label, command, args) {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    env: process.env
  });

  if (result.error) {
    console.error(`[${label}] Failed to spawn: ${result.error.message}`);
    process.exit(1);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

run('skills:generate', 'node', ['scripts/discover-skills.mjs']);
run('readme:extract', 'node', ['scripts/extract-readme-sections.mjs']);
run('catalog:sync', 'node', ['scripts/sync-catalog.mjs']);
run('jrig:enrich', 'node', ['scripts/enrich-jrig-data.mjs']);
run('search:generate', 'node', ['scripts/generate-unified-search.mjs']);
run('cowork:zips', 'node', [resolve(repoRoot, 'scripts/build-cowork-zips.mjs')]);
run('cowork:validate', 'node', [resolve(repoRoot, 'scripts/validate-cowork-manifest.mjs')]);

// Copy large data files to public/data/ so they are served as static assets at runtime.
// Source-of-truth remains in src/data/ for build scripts; public/data/ is the runtime copy.
const publicDataDir = resolve(__dirname, '..', 'public', 'data');
mkdirSync(publicDataDir, { recursive: true });
for (const file of ['unified-search-index.json', 'skills-catalog.json']) {
  copyFileSync(resolve(__dirname, '..', 'src', 'data', file), resolve(publicDataDir, file));
  console.log(`[data:copy] Copied ${file} → public/data/${file}`);
}

run('astro build', 'astro', ['build']);
