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
    console.log(`[enrich-jrig] Freshie DB not found at ${dbPath} — writing empty map`);
    fs.writeFileSync(outPath, JSON.stringify(data, null, 2) + '\n');
    return;
  }

  if (!tableExists(dbPath, 'forge_proofs')) {
    console.log('[enrich-jrig] forge_proofs table not yet created — writing empty map');
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
    console.warn('[enrich-jrig] query returned non-array — writing empty map');
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
  console.log(
    `[enrich-jrig] Wrote ${verifiedCount} JRig-verified plugin entries → ${path.relative(repoRoot, outPath)}`,
  );
}

main();
