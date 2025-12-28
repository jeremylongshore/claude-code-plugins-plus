#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';

function run(label, command, args) {
  const result = spawnSync(command, args, {
    stdio: 'inherit',
    env: process.env
  });

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}

function resolveEsbuildBinaryPath() {
  try {
    const require = createRequire(import.meta.url);
    const astroRequire = createRequire(require.resolve('astro/package.json'));
    const esbuildPackageJsonPath = astroRequire.resolve('esbuild/package.json');
    const esbuildDir = dirname(esbuildPackageJsonPath);
    const esbuildBinaryPath = join(esbuildDir, 'bin', 'esbuild');
    return existsSync(esbuildBinaryPath) ? esbuildBinaryPath : null;
  } catch {
    return null;
  }
}

const resolvedEsbuildBinaryPath = resolveEsbuildBinaryPath();
if (resolvedEsbuildBinaryPath && !process.env.ESBUILD_BINARY_PATH) {
  process.env.ESBUILD_BINARY_PATH = resolvedEsbuildBinaryPath;
}

run('skills:generate', 'node', ['scripts/discover-skills.mjs']);
run('catalog:sync', 'node', ['scripts/sync-catalog.mjs']);
run('search:generate', 'node', ['scripts/generate-unified-search.mjs']);
run('astro build', 'astro', ['build']);
