#!/usr/bin/env node
/**
 * Enrich plugin metadata with JRig behavioral-eval results.
 *
 * Reads `forge_proofs` from `freshie/inventory.sqlite`, picks the
 * LATEST real (non-stub) JRig verification per plugin — and includes
 * it only if that latest eval passed, so a newer failing eval
 * un-verifies — and writes the results to
 * `marketplace/src/data/jrig-data.json` as a flat map keyed by
 * plugin name. The marketplace stopped rendering JRig badges in PR #1046.
 * Epic 1.7 makes this a temporary untracked, build-adjacent inspection output;
 * blueprint bead E9.2 still owns removing the projection and build step.
 *
 * Phase 4 of "Use the Printing Press to Learn" plan, data flow.
 *
 * Output shape:
 * ```json
 * {
 *   "<plugin-name>": {
 *     "verified": true,
 *     "layers_passed": 7,
 *     "total_layers": 7,
 *     "baseline_delta": 0.18,
 *     "verified_at": "2026-05-07T..."
 *   }
 * }
 * ```
 *
 * If the Freshie DB is missing or the table is empty, writes an empty object
 * deterministically. No live page consumes this projection.
 */

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..');
const dbPath = path.join(repoRoot, 'freshie', 'inventory.sqlite');
const outPath = path.join(__dirname, '..', 'src', 'data', 'jrig-data.json');

/**
 * Emit a loud, CI-visible warning. In GitHub Actions this renders as a
 * `::warning::` annotation on the run summary (not just buried in the step
 * log); locally it prints a plain `[enrich-jrig] WARNING:` line. Used instead
 * of a silent `console.log` in every degradation path so an empty inspection
 * projection cannot be mistaken for affirmative evidence.
 */
function warn(message) {
  const rel = path.relative(repoRoot, outPath);
  if (process.env.GITHUB_ACTIONS === 'true') {
    console.log(`::warning file=${rel}::${message}`);
  }
  console.warn(`[enrich-jrig] WARNING: ${message}`);
}

/**
 * Run a SQL query via the `sqlite3` CLI. We avoid the better-sqlite3
 * native module to keep this script dependency-free — the marketplace
 * build already has 9 sequential steps and we'd rather not add a
 * native build for a once-per-build read.
 */
function querySqlite(database, sql) {
  if (!fs.existsSync(database)) return null;

  const result = spawnSync('sqlite3', [database, '-json', sql], {
    encoding: 'utf8',
  });

  if (result.status !== 0) {
    console.warn(`[enrich-jrig] sqlite3 query failed: ${result.stderr}`);
    return null;
  }

  const stdout = result.stdout?.trim();
  if (!stdout) return [];

  try {
    return JSON.parse(stdout);
  } catch (err) {
    console.warn(`[enrich-jrig] failed to parse sqlite3 output: ${err.message}`);
    return null;
  }
}

function tableExists(database, table) {
  const rows = querySqlite(
    database,
    `SELECT name FROM sqlite_master WHERE type='table' AND name='${table}'`,
  );
  return Array.isArray(rows) && rows.length > 0;
}

function main() {
  console.log('[enrich-jrig] Reading forge_proofs from Freshie...');

  const data = {};

  if (!fs.existsSync(dbPath)) {
    warn(
      `Freshie DB not found at ${path.relative(repoRoot, dbPath)}. ` +
        'Writing the untracked JRig projection as an empty map.',
    );
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');
    return;
  }

  if (!tableExists(dbPath, 'forge_proofs')) {
    warn(
      'forge_proofs table not present in the Freshie DB — no JRig behavioral ' +
        'evals have been persisted. Writing the inspection projection as an empty map.',
    );
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');
    return;
  }

  // Pick the LATEST tier3-jrig row per plugin FIRST, then read its passed
  // flag. The old query filtered `passed = 1` BEFORE picking latest, so a
  // newer FAILING eval could never extinguish a stale verified entry. Ordering is
  // deterministic: verified_at DESC, then run_id DESC (the live DB has three
  // databricks-pack rows sharing one verified_at second), then id DESC.
  //
  // Stub rows are excluded outright: `--stub` runs (evidence JSON
  // {"stub": true}, ground_truth: false) are pipeline plumbing, never
  // ground truth — a stub row must not create or extinguish a passing entry.
  //
  // If a plugin has multiple verification_type rows (tier1, tier2,
  // tier3-jrig), we surface the JRig behavioral row specifically rather than
  // the lighter-weight static tiers.
  const rows = querySqlite(
    dbPath,
    `SELECT plugin_name,
            passed,
            layers_passed,
            total_layers,
            baseline_delta,
            verified_at
     FROM (
       SELECT plugin_name,
              passed,
              layers_passed,
              total_layers,
              baseline_delta,
              verified_at,
              ROW_NUMBER() OVER (
                PARTITION BY plugin_name
                ORDER BY verified_at DESC, run_id DESC, id DESC
              ) AS rn
       FROM forge_proofs
       WHERE verification_type = 'tier3-jrig'
         AND CASE
               WHEN evidence IS NULL THEN 1
               WHEN json_valid(evidence)
                 THEN COALESCE(json_extract(evidence, '$.stub'), 0) = 0
               ELSE 1
             END
     )
     WHERE rn = 1
     ORDER BY plugin_name`,
  );

  if (!Array.isArray(rows)) {
    warn('forge_proofs query returned a non-array result (sqlite3 read failed) — writing empty map.');
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');
    return;
  }

  let unverified = 0;
  for (const row of rows) {
    if (!row.plugin_name) continue;
    if (row.passed !== 1) {
      // The plugin's LATEST real eval failed/blocked — it gets no entry, so
      // any stale passing entry is extinguished in this rebuild.
      unverified += 1;
      continue;
    }
    data[row.plugin_name] = {
      verified: true,
      layers_passed: row.layers_passed ?? null,
      total_layers: row.total_layers ?? 7,
      baseline_delta: row.baseline_delta ?? null,
      verified_at: row.verified_at ?? null,
    };
  }
  if (unverified > 0) {
    warn(
      `${unverified} plugin(s) have a FAILING latest tier3-jrig eval — ` +
        'omitted from jrig-data.json (a newer failing eval un-verifies).',
    );
  }

  fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');

  const verifiedCount = Object.keys(data).length;
  if (verifiedCount === 0) {
    warn(
      'forge_proofs exists but has zero passing tier3-jrig rows — no plugin ' +
        'has a completed 7-layer behavioral eval yet. Populate a row with: ' +
        '`scripts/run-jrig-eval.sh ' +
        '--skill-dir <dir> --plugin <name> --inventory-db freshie/inventory.sqlite` ' +
        '(evals against a /dev/shm scratch DB, then records the verdict via ' +
        'scripts/record-jrig-proofs.mjs — never point j-rig itself at the inventory DB).',
    );
    return;
  }
  console.log(
    `[enrich-jrig] Wrote ${verifiedCount} passing JRig inspection entries → ${path.relative(repoRoot, outPath)}`,
  );
}

main();
