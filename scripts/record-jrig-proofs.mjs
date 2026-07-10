#!/usr/bin/env node
/**
 * record-jrig-proofs.mjs — the eval→forge_proofs write path (issue #935).
 *
 * Takes a `j-rig eval ... --json` result file and upserts one row into the
 * `forge_proofs` table of a Freshie-shaped SQLite inventory DB. This is the
 * missing write end of the "printing press" data flow:
 *
 *   j-rig eval → THIS SCRIPT → forge_proofs row
 *     → marketplace/scripts/enrich-jrig-data.mjs → jrig-data.json
 *     → JRig-Verified badge on the plugin detail page.
 *
 * INPUT SHAPE (what we bind to — inspected from @intentsolutions/jrig-cli
 * 0.1.2, dist/index.js `registerEvalCommand`): `j-rig eval --json` prints a
 * map keyed by model name, one entry per `--models` entry:
 *
 *   {
 *     "<model>": {
 *       "provider":     string,        // e.g. "deepseek" | "stub"
 *       "model":        string,        // e.g. "deepseek-v4-flash"
 *       "ground_truth": boolean,       // false when the stub provider ran
 *       "pkgReport":    { ... },       // Layer 1 package-integrity report
 *       "scoreCard": {                 // computeScoreCard() output
 *         "total_criteria":    number,
 *         "passed":            number,
 *         "failed":            number,
 *         "unsure":            number,
 *         "blocker_failures":  number,
 *         "sacred_regressions": number,
 *         "pass_rate":         number
 *       },
 *       "decision": "ship" | "warn" | "block" | "obsolete_review",
 *       "report": { skill_name, timestamp, decision, score, regressions,
 *                   baseline, blockers, warnings, reasoning }
 *     }
 *   }
 *
 * A bare single-run object (`{ scoreCard, decision, ... }`) is also accepted.
 *
 * ROW CONTRACT (conforms to the real schema in freshie/inventory.sqlite,
 * created by scripts/validate-skills-schema.py — verified 2026-07-09):
 *
 *   CREATE TABLE forge_proofs (
 *     id INTEGER PRIMARY KEY AUTOINCREMENT,
 *     plugin_name TEXT NOT NULL,
 *     run_id INTEGER,
 *     verification_type TEXT NOT NULL,
 *     passed INTEGER NOT NULL,
 *     evidence TEXT,
 *     layers_passed INTEGER DEFAULT NULL,
 *     total_layers INTEGER DEFAULT 7,
 *     baseline_delta REAL DEFAULT NULL,
 *     verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 *     UNIQUE(plugin_name, verification_type, run_id)
 *   );
 *
 *   - verification_type = 'tier3-jrig' (what enrich-jrig-data.mjs selects)
 *   - passed        = 1 iff EVERY model's rollout decision is "ship"
 *   - layers_passed = min(scoreCard.passed) across models (conservative)
 *   - total_layers  = scoreCard.total_criteria (must agree across models)
 *   - baseline_delta = NULL (standalone eval runs carry no baseline compare)
 *   - evidence      = JSON: per-model {provider, model, ground_truth,
 *                     decision, scoreCard, reasoning, timestamp} subset
 *
 * Upsert is idempotent: INSERT ... ON CONFLICT(plugin_name,
 * verification_type, run_id) DO UPDATE. `--run-id` is REQUIRED and must be a
 * non-negative integer — SQLite treats NULLs as distinct in UNIQUE
 * constraints, so a NULL run_id would break idempotency.
 *
 * STUB GUARD: results produced by the stub provider (`ground_truth: false`)
 * are refused unless `--allow-stub` is passed — a stub row would light a
 * JRig-Verified badge with non-ground-truth evidence. `--allow-stub` exists
 * for pipeline plumbing against scratch DB copies only.
 *
 * Uses only node built-ins + the `sqlite3` CLI via child_process (same
 * pattern as marketplace/scripts/enrich-jrig-data.mjs — no better-sqlite3
 * native dep for a once-per-run write).
 *
 * Usage:
 *   node scripts/record-jrig-proofs.mjs \
 *     --db <inventory.sqlite> --plugin <name> --run-id <int> \
 *     --result <result.json> [--allow-stub]
 */

import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const VERIFICATION_TYPE = 'tier3-jrig';
const VALID_DECISIONS = new Set(['ship', 'warn', 'block', 'obsolete_review']);

// Exact DDL from scripts/validate-skills-schema.py so the adapter also works
// against a fresh scratch DB (CREATE TABLE IF NOT EXISTS is a no-op on the
// real inventory DB, which already carries the table).
const FORGE_PROOFS_DDL = `CREATE TABLE IF NOT EXISTS forge_proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_name TEXT NOT NULL,
    run_id INTEGER,
    verification_type TEXT NOT NULL,
    passed INTEGER NOT NULL,
    evidence TEXT,
    layers_passed INTEGER DEFAULT NULL,
    total_layers INTEGER DEFAULT 7,
    baseline_delta REAL DEFAULT NULL,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(plugin_name, verification_type, run_id)
);
CREATE INDEX IF NOT EXISTS idx_forge_proofs_plugin ON forge_proofs(plugin_name);
CREATE INDEX IF NOT EXISTS idx_forge_proofs_passed ON forge_proofs(passed);`;

export function fail(message) {
  const err = new Error(message);
  err.isCliFailure = true;
  throw err;
}

/** SQLite string literal escaping: double the single quotes. */
export function sqlString(value) {
  return `'${String(value).replace(/'/g, "''")}'`;
}

export function parseArgs(argv) {
  const args = { allowStub: false };
  const takesValue = {
    '--db': 'db',
    '--plugin': 'plugin',
    '--run-id': 'runId',
    '--result': 'result',
  };
  for (let i = 0; i < argv.length; i++) {
    const flag = argv[i];
    if (flag === '--allow-stub') {
      args.allowStub = true;
    } else if (takesValue[flag]) {
      const value = argv[++i];
      if (value === undefined) fail(`Missing value for ${flag}`);
      args[takesValue[flag]] = value;
    } else {
      fail(`Unknown argument: ${flag}`);
    }
  }
  for (const [flag, key] of Object.entries(takesValue)) {
    if (!args[key]) fail(`Missing required argument: ${flag}`);
  }
  if (!/^\d+$/.test(args.runId)) {
    fail(
      `--run-id must be a non-negative integer (got: ${args.runId}) — it is part of the UNIQUE(plugin_name, verification_type, run_id) upsert key.`,
    );
  }
  args.runId = Number(args.runId);
  return args;
}

/**
 * Extract per-model result entries from a parsed `j-rig eval --json` result.
 * Accepts the canonical model-keyed map or a bare single-run object.
 */
export function extractModelEntries(parsed) {
  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    fail('Result JSON must be an object (the `j-rig eval --json` model-keyed map).');
  }
  if (parsed.error) {
    fail(`Result JSON records a failed eval run: ${parsed.error}`);
  }
  const entries = parsed.scoreCard
    ? [parsed]
    : Object.values(parsed).filter(
        (v) => v !== null && typeof v === 'object' && !Array.isArray(v) && 'scoreCard' in v,
      );
  if (entries.length === 0) {
    fail(
      'No model entries with a scoreCard found in the result JSON — is this really `j-rig eval --json` output?',
    );
  }
  for (const entry of entries) {
    const sc = entry.scoreCard;
    if (
      sc === null ||
      typeof sc !== 'object' ||
      !Number.isInteger(sc.passed) ||
      sc.passed < 0 ||
      !Number.isInteger(sc.total_criteria) ||
      sc.total_criteria < 0
    ) {
      fail(`Malformed scoreCard (need integer passed/total_criteria >= 0): ${JSON.stringify(sc)}`);
    }
    if (!VALID_DECISIONS.has(entry.decision)) {
      fail(
        `Malformed model entry: decision must be one of ${[...VALID_DECISIONS].join('|')} (got: ${JSON.stringify(entry.decision)})`,
      );
    }
  }
  return entries;
}

/**
 * Fold N per-model entries into the single forge_proofs row contract.
 * Conservative: the row only reads as passed when every model ships, and
 * layers_passed is the weakest model's count.
 */
export function aggregateEntries(entries, { allowStub = false } = {}) {
  const stubEntries = entries.filter((e) => e.ground_truth === false);
  if (stubEntries.length > 0 && !allowStub) {
    fail(
      `Result contains ${stubEntries.length} stub-provider entr${stubEntries.length === 1 ? 'y' : 'ies'} ` +
        '(ground_truth: false). Refusing to record non-ground-truth evidence into forge_proofs — ' +
        'a stub row would light a JRig-Verified badge dishonestly. Pass --allow-stub only for ' +
        'pipeline plumbing against a scratch DB copy.',
    );
  }
  const totals = new Set(entries.map((e) => e.scoreCard.total_criteria));
  if (totals.size > 1) {
    fail(
      `Model entries disagree on total_criteria (${[...totals].join(', ')}) — same eval spec should yield the same criteria count. Refusing to record an ambiguous row.`,
    );
  }
  return {
    passed: entries.every((e) => e.decision === 'ship') ? 1 : 0,
    layers_passed: Math.min(...entries.map((e) => e.scoreCard.passed)),
    total_layers: [...totals][0],
    baseline_delta: null,
    evidence: {
      source: 'j-rig eval --json',
      recorded_by: 'scripts/record-jrig-proofs.mjs',
      stub: stubEntries.length > 0,
      models: entries.map((e) => ({
        provider: e.provider ?? null,
        model: e.model ?? null,
        ground_truth: e.ground_truth ?? null,
        decision: e.decision,
        scoreCard: e.scoreCard,
        reasoning: e.report?.reasoning ?? null,
        timestamp: e.report?.timestamp ?? null,
      })),
    },
  };
}

/** Build the idempotent upsert SQL for one forge_proofs row. */
export function buildUpsertSql({ plugin, runId, row }) {
  return `${FORGE_PROOFS_DDL}
INSERT INTO forge_proofs
  (plugin_name, run_id, verification_type, passed, evidence, layers_passed, total_layers, baseline_delta)
VALUES
  (${sqlString(plugin)}, ${runId}, ${sqlString(VERIFICATION_TYPE)}, ${row.passed},
   ${sqlString(JSON.stringify(row.evidence))}, ${row.layers_passed}, ${row.total_layers}, NULL)
ON CONFLICT(plugin_name, verification_type, run_id) DO UPDATE SET
  passed = excluded.passed,
  evidence = excluded.evidence,
  layers_passed = excluded.layers_passed,
  total_layers = excluded.total_layers,
  baseline_delta = excluded.baseline_delta,
  verified_at = CURRENT_TIMESTAMP;`;
}

function runSqlite(dbPath, sql) {
  const result = spawnSync('sqlite3', ['-batch', dbPath], { input: sql, encoding: 'utf8' });
  if (result.error) fail(`Failed to spawn sqlite3 CLI: ${result.error.message}`);
  if (result.status !== 0) fail(`sqlite3 exited ${result.status}: ${result.stderr.trim()}`);
  return result.stdout;
}

export function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);

  if (!fs.existsSync(args.db)) {
    fail(
      `DB not found: ${args.db} — refusing to create a fresh database at an arbitrary path. Point --db at the inventory DB (or a copy of it).`,
    );
  }
  if (!fs.existsSync(args.result)) {
    fail(`Result file not found: ${args.result}`);
  }

  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(args.result, 'utf8'));
  } catch (err) {
    fail(`Result file is not valid JSON (${args.result}): ${err.message}`);
  }

  const entries = extractModelEntries(parsed);
  const row = aggregateEntries(entries, { allowStub: args.allowStub });

  runSqlite(args.db, buildUpsertSql({ plugin: args.plugin, runId: args.runId, row }));

  // Read the row back so the log line is evidence, not hope.
  const echo = runSqlite(
    args.db,
    `.mode json
SELECT plugin_name, run_id, verification_type, passed, layers_passed, total_layers, baseline_delta, verified_at
FROM forge_proofs
WHERE plugin_name = ${sqlString(args.plugin)}
  AND verification_type = ${sqlString(VERIFICATION_TYPE)}
  AND run_id = ${args.runId};`,
  ).trim();
  if (!echo)
    fail('Upsert reported success but the row is not readable back — refusing to report success.');

  const written = JSON.parse(echo)[0];
  console.log(
    `[record-jrig-proofs] Upserted ${VERIFICATION_TYPE} row for '${args.plugin}' (run_id=${args.runId}): ` +
      `passed=${written.passed}, layers=${written.layers_passed}/${written.total_layers}, ` +
      `models=${row.evidence.models.map((m) => m.model).join(',')}${row.evidence.stub ? ' [STUB — not ground truth]' : ''}`,
  );
  return written;
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (isMain) {
  try {
    main();
  } catch (err) {
    console.error(`[record-jrig-proofs] ERROR: ${err.message}`);
    process.exit(1);
  }
}
