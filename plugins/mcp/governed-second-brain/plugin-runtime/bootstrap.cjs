#!/usr/bin/env node
'use strict';

/**
 * Marketplace-safe launcher for the committed MCP bundle.
 *
 * Claude/Codex plugin installs copy files but do not run this repository's npm
 * installer. Team mode is dependency-free, while local mode needs the two
 * native modules externalized by build.mjs. Provision those exact, lockfile-
 * pinned modules on first local start, then execute the bundled server.
 */
const { createRequire } = require('node:module');
const { existsSync, mkdirSync, rmSync, statSync } = require('node:fs');
const { homedir } = require('node:os');
const { join } = require('node:path');
const { spawnSync } = require('node:child_process');

const RUNTIME_DIR = __dirname;
const BUNDLE = join(RUNTIME_DIR, 'governed-brain.cjs');
const LOCK_DIR = join(RUNTIME_DIR, '.native-install.lock');
const LOCK_STALE_MS = 5 * 60 * 1000;
const WAIT_LIMIT_MS = 2 * 60 * 1000;
const WAIT_STEP_MS = 250;

function isConfigured(value) {
  const normalized = value?.trim();
  return normalized !== undefined && normalized !== '' && !normalized.startsWith('${');
}

function teamConfigPath(env = process.env) {
  const base = env.TEAMKB_BASE_PATH?.trim() || env.TEAMKB_HOME?.trim() || join(homedir(), '.teamkb');
  return join(base, 'team.json');
}

function teamModeRequested(env = process.env) {
  return isConfigured(env.TEAMKB_API_URL) || existsSync(teamConfigPath(env));
}

function nativeDependenciesReady() {
  try {
    const runtimeRequire = createRequire(BUNDLE);
    runtimeRequire('better-sqlite3');
    runtimeRequire('fs-ext');
    return true;
  } catch {
    return false;
  }
}

function sleep(milliseconds) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, milliseconds);
}

function acquireInstallLock() {
  const started = Date.now();
  while (true) {
    try {
      mkdirSync(LOCK_DIR);
      return true;
    } catch (error) {
      if (error?.code !== 'EEXIST') throw error;
      if (nativeDependenciesReady()) return false;
      try {
        if (Date.now() - statSync(LOCK_DIR).mtimeMs > LOCK_STALE_MS) {
          rmSync(LOCK_DIR, { recursive: true, force: true });
          continue;
        }
      } catch (statError) {
        if (statError?.code !== 'ENOENT') throw statError;
        continue;
      }
      if (Date.now() - started > WAIT_LIMIT_MS) {
        throw new Error('timed out waiting for another governed-brain native dependency install');
      }
      sleep(WAIT_STEP_MS);
    }
  }
}

function provisionNativeDependencies() {
  if (nativeDependenciesReady()) return;
  const ownsLock = acquireInstallLock();
  if (!ownsLock) return;
  try {
    if (nativeDependenciesReady()) return;
    process.stderr.write('[governed-brain] first local start: provisioning lockfile-pinned native runtime dependencies\n');
    const npm = process.platform === 'win32' ? 'npm.cmd' : 'npm';
    const result = spawnSync(
      npm,
      ['ci', '--omit=dev', '--no-audit', '--no-fund'],
      { cwd: RUNTIME_DIR, stdio: ['ignore', 'ignore', 'inherit'], timeout: WAIT_LIMIT_MS },
    );
    if (result.error) throw result.error;
    if (result.status !== 0) throw new Error(`npm ci exited ${result.status ?? 'without a status'}`);
    if (!nativeDependenciesReady()) {
      throw new Error('native dependencies are still unavailable after npm ci');
    }
  } finally {
    rmSync(LOCK_DIR, { recursive: true, force: true });
  }
}

function main() {
  if (!existsSync(BUNDLE)) throw new Error(`bundled MCP runtime missing: ${BUNDLE}`);
  // A valid or invalid team.json both belong to the dependency-free team path.
  // The bundle remains authoritative for parsing it and failing closed.
  if (!teamModeRequested()) provisionNativeDependencies();
  require(BUNDLE);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`[governed-brain] REFUSING TO START — ${error?.message || String(error)}\n`);
    process.exit(1);
  }
}

module.exports = {
  isConfigured,
  nativeDependenciesReady,
  provisionNativeDependencies,
  teamConfigPath,
  teamModeRequested,
};
