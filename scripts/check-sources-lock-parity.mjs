#!/usr/bin/env node
/**
 * check-sources-lock-parity.mjs — assert the external-source registry and its
 * content-pinning lockfile agree on exactly which sources exist (blueprint
 * 727, Epic 1 bead 1.12).
 *
 * WHY THIS EXISTS
 * ---------------
 * sources.yaml is the human intake registry; sources.lock.json is the
 * security baseline that pins each mirror's upstream commit and file digests
 * (see scripts/sync-lockfile.mjs for the threat model). The two are only
 * meaningful together: a source registered but never locked has no reviewed
 * baseline — its next sync mirrors whatever upstream serves, unpinned — and a
 * lock entry with no registration is an orphaned approval that outlives its
 * source. The `uizze` source sat registered-but-unlocked for weeks before
 * this gate existed.
 *
 * THE CONTRACT
 * ------------
 * key set of sources.yaml `sources[].name` == key set of
 * sources.lock.json `.sources` — both directions, no exceptions. Curated
 * (frozen-mirror) sources still carry lock entries, so they satisfy parity.
 * New-source intake is not penalized: the sync engine writes the lock entry
 * on the first sync of a human-listed source, and that sync (or an explicit
 * --relock) belongs in the same PR that registers the source.
 */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');

/** Pure comparison so tests can exercise the contract without touching disk. */
export function compareKeySets(registryNames, lockNames) {
  const registry = new Set(registryNames);
  const lock = new Set(lockNames);
  const unlocked = [...registry].filter((n) => !lock.has(n)).sort();
  const orphaned = [...lock].filter((n) => !registry.has(n)).sort();
  return { unlocked, orphaned, ok: unlocked.length === 0 && orphaned.length === 0 };
}

export function loadKeySets(repoRoot = REPO_ROOT) {
  const registry = yaml.load(readFileSync(join(repoRoot, 'sources.yaml'), 'utf8'));
  const lock = JSON.parse(readFileSync(join(repoRoot, 'sources.lock.json'), 'utf8'));
  if (!Array.isArray(registry?.sources)) {
    throw new Error('sources.yaml: expected a top-level `sources` array');
  }
  if (lock === null || typeof lock?.sources !== 'object') {
    throw new Error('sources.lock.json: expected a top-level `sources` object');
  }
  const names = registry.sources.map((s) => s?.name);
  if (names.some((n) => typeof n !== 'string' || n.length === 0)) {
    throw new Error('sources.yaml: every source entry must have a non-empty `name`');
  }
  return { registryNames: names, lockNames: Object.keys(lock.sources) };
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  let sets;
  try {
    sets = loadKeySets();
  } catch (err) {
    console.error(`sources-lock-parity: STRUCTURAL — ${err.message}`);
    process.exit(1);
  }
  const { unlocked, orphaned, ok } = compareKeySets(sets.registryNames, sets.lockNames);
  for (const n of unlocked) {
    console.error(
      `sources-lock-parity: VIOLATION — "${n}" is registered in sources.yaml but has no ` +
        `sources.lock.json baseline. Run: node scripts/sync-external.mjs --source=${n} --relock=${n} ` +
        `after reviewing the upstream content, in the same PR.`,
    );
  }
  for (const n of orphaned) {
    console.error(
      `sources-lock-parity: VIOLATION — "${n}" has a sources.lock.json entry but is not ` +
        `registered in sources.yaml. Remove the stale lock entry (or restore the registration).`,
    );
  }
  if (!ok) {
    console.error(
      `sources-lock-parity: FAIL — ${unlocked.length} unlocked, ${orphaned.length} orphaned.`,
    );
    process.exit(1);
  }
  console.log(
    `sources-lock-parity: OK (${sets.registryNames.length} registered == ${sets.lockNames.length} locked)`,
  );
}
