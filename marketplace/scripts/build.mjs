#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
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
run('catalog:sync', 'node', ['scripts/sync-catalog.mjs']);
run('search:generate', 'node', ['scripts/generate-unified-search.mjs']);
run('cowork:zips', 'node', [resolve(repoRoot, 'scripts/build-cowork-zips.mjs')]);
run('astro build', 'astro', ['build']);
