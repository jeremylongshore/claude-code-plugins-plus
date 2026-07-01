#!/usr/bin/env node
/**
 * Enrich plugin metadata with JRig behavioral-eval results.
 *
 * Reads `forge_proofs` from `freshie/inventory.sqlite`, picks the
 * latest passing JRig verification per plugin, and writes the
 * results to `marketplace/src/data/jrig-data.json` as a flat map
 * keyed by plugin name. The detail-page Astro template
 * (`src/pages/plugins/[name].astro`) overlays this onto the
 * `plugin` prop at render time so the JRig-Verified badge lights
 * up on plugins with passing eval results — without polluting
 * `marketplace.extended.json` with computed eval data.
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
 * If the Freshie DB is missing or the table is empty, writes an empty
 * object to keep the build deterministic. The detail page's optional
 * chaining (`plugin.jrig?.verified`) gracefully handles absence.
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
 * of a silent `console.log` in every degradation path: writing `{}` silently
 * blanks every "JRig-Verified" badge with no signal that the data source is
 * missing or empty.
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
 * build already has 6 sequential steps and we'd rather not add a
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
      `Freshie DB not found at ${path.relative(repoRoot, dbPath)} — every ` +
        `JRig-Verified badge will render "pending". Writing empty map.`,
    );
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');
    return;
  }

  if (!tableExists(dbPath, 'forge_proofs')) {
    warn(
      'forge_proofs table not present in the Freshie DB — no JRig behavioral ' +
        'evals have been persisted. Every JRig-Verified badge will render ' +
        '"pending". Writing empty map.',
    );
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');
    return;
  }

  // Pick the latest passing JRig verification per plugin. If a plugin has
  // multiple verification_type rows (tier1, tier2, tier3-jrig), we surface
  // the JRig behavioral row specifically — the badge represents JRig
  // verification, not the lighter-weight static tiers.
  const rows = querySqlite(
    dbPath,
    `SELECT plugin_name,
            passed,
            layers_passed,
            total_layers,
            baseline_delta,
            verified_at
     FROM forge_proofs
     WHERE verification_type = 'tier3-jrig'
       AND passed = 1
     GROUP BY plugin_name
     HAVING MAX(verified_at)
     ORDER BY plugin_name`,
  );

  if (!Array.isArray(rows)) {
    warn('forge_proofs query returned a non-array result (sqlite3 read failed) — writing empty map.');
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');
    return;
  }

  for (const row of rows) {
    if (!row.plugin_name) continue;
    data[row.plugin_name] = {
      verified: row.passed === 1,
      layers_passed: row.layers_passed ?? null,
      total_layers: row.total_layers ?? 7,
      baseline_delta: row.baseline_delta ?? null,
      verified_at: row.verified_at ?? null,
    };
  }

  fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');

  const verifiedCount = Object.keys(data).length;
  if (verifiedCount === 0) {
    warn(
      'forge_proofs exists but has zero passing tier3-jrig rows — no plugin ' +
        'has a completed 7-layer behavioral eval yet, so every JRig-Verified ' +
        'badge renders "pending". Populate a row with: `j-rig eval <plugin> ' +
        '--models haiku,sonnet,opus --db freshie/inventory.sqlite` (once the ' +
        'eval→forge_proofs write path lands).',
    );
    return;
  }
  console.log(
    `[enrich-jrig] Wrote ${verifiedCount} JRig-verified plugin entries → ${path.relative(repoRoot, outPath)}`,
  );
}

main();
