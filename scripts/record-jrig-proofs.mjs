#!/usr/bin/env node
/**
 * record-jrig-proofs.mjs — the eval→forge_proofs write path (issue #935).
 *
 * Takes a `j-rig eval ... --json` result file and upserts one row into the
 * `forge_proofs` table of a Freshie-shaped SQLite inventory DB. This is the
 * governed write end of the behavioral-evaluation evidence flow:
 *
 *   j-rig eval → THIS SCRIPT → forge_proofs row
 *
 * This script does not publish a marketplace verification claim. A future
 * public projection must first meet the retained, hash-matched evidence
 * requirements owned by Blueprint 727.
 *
 * INPUT SHAPE (what we bind to — inspected from @intentsolutions/jrig-cli
 * 0.2.0, dist/index.js `registerEvalCommand`): `j-rig eval --json` prints a
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
 *     jrig_run_id INTEGER,
 *     verification_type TEXT NOT NULL,
 *     passed INTEGER NOT NULL,
 *     evidence TEXT,
 *     layers_passed INTEGER DEFAULT NULL,
 *     total_layers INTEGER DEFAULT 7,
 *     baseline_delta REAL DEFAULT NULL,
 *     verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 *     UNIQUE(plugin_name, verification_type, jrig_run_id)
 *   );
 *
 *   - verification_type = 'tier3-jrig' (the governed behavioral-evaluation evidence class)
 *   - passed        = 1 iff EVERY model's rollout decision is "ship"
 *   - layers_passed = min(scoreCard.passed) across models (conservative)
 *   - total_layers  = scoreCard.total_criteria (must agree across models)
 *   - baseline_delta = NULL (standalone eval runs carry no baseline compare)
 *   - evidence      = JSON: per-model {provider, model, ground_truth,
 *                     decision, scoreCard, reasoning, timestamp} subset
 *
 * Upsert is idempotent: INSERT ... ON CONFLICT(plugin_name,
 * verification_type, jrig_run_id) DO UPDATE. `--jrig-run-id` is REQUIRED and must be a
 * non-negative integer — SQLite treats NULLs as distinct in UNIQUE
 * constraints, so a NULL jrig_run_id would break idempotency.
 *
 * STUB GUARD: results produced by the stub provider (`ground_truth: false`)
 * are refused unless `--allow-stub` is passed — a stub row cannot be treated
 * as grounded behavioral-evaluation evidence. `--allow-stub` exists for
 * pipeline plumbing against scratch DB copies only.
 *
 * Uses only node built-ins + the `sqlite3` CLI via child_process; no
 * better-sqlite3 native dependency is needed for this once-per-run write.
 *
 * Usage:
 *   node scripts/record-jrig-proofs.mjs \
 *     --db <inventory.sqlite> --plugin <name> --jrig-run-id <int> \
 *     --result <result.json> [--allow-stub]
 */

import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const VERIFICATION_TYPE = 'tier3-jrig';
const VALID_DECISIONS = new Set(['ship', 'warn', 'block', 'obsolete_review']);

// Exact DDL from scripts/validate-skills-schema.py so the adapter also works
// against a fresh scratch DB (CREATE TABLE IF NOT EXISTS is a no-op on the
// real inventory DB, which already carries the table).
const FORGE_PROOFS_DDL = `CREATE TABLE IF NOT EXISTS discovery_runs (
    id INTEGER PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS forge_proofs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_name TEXT NOT NULL,
    jrig_run_id INTEGER,
    discovery_run_id INTEGER REFERENCES discovery_runs(id),
    verification_type TEXT NOT NULL,
    passed INTEGER NOT NULL,
    evidence TEXT,
    evidence_class TEXT NOT NULL DEFAULT 'E0' CHECK(evidence_class IN ('E0', 'E1', 'E2', 'E3')),
    artifact_sha256 TEXT,
    artifact_uri TEXT,
    spec_sha256 TEXT,
    tool_version TEXT,
    kernel_version TEXT,
    provider TEXT,
    model TEXT,
    recorded_by_identity TEXT,
    producing_identity TEXT,
    layers_passed INTEGER DEFAULT NULL,
    total_layers INTEGER DEFAULT 7,
    baseline_delta REAL DEFAULT NULL,
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(plugin_name, verification_type, jrig_run_id)
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
    '--jrig-run-id': 'jrigRunId',
    '--discovery-run-id': 'discoveryRunId',
    '--evidence-class': 'evidenceClass',
    '--recorded-by-identity': 'recordedByIdentity',
    '--producing-identity': 'producingIdentity',
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
  for (const flag of ['--db', '--plugin', '--jrig-run-id', '--result']) {
    if (!args[takesValue[flag]]) fail(`Missing required argument: ${flag}`);
  }
  if (!/^\d+$/.test(args.jrigRunId)) {
    fail(
      `--jrig-run-id must be a non-negative integer (got: ${args.jrigRunId}) — it is part of the UNIQUE(plugin_name, verification_type, jrig_run_id) upsert key.`,
    );
  }
  args.jrigRunId = Number(args.jrigRunId);
  if (args.discoveryRunId !== undefined) {
    if (!/^\d+$/.test(args.discoveryRunId)) {
      fail(`--discovery-run-id must be a non-negative integer (got: ${args.discoveryRunId})`);
    }
    args.discoveryRunId = Number(args.discoveryRunId);
  }
  return args;
}

export function enforceRecorderIdentity({
  evidenceClass,
  recordedByIdentity,
  producingIdentity,
  dbPath,
  realInventoryPath = path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    '..',
    'freshie',
    'inventory.sqlite',
  ),
}) {
  if (!['E0', 'E1', 'E2', 'E3'].includes(evidenceClass))
    fail(`Invalid evidence class: ${evidenceClass}`);
  if (evidenceClass === 'E0' || evidenceClass === 'E1') return;
  if (!recordedByIdentity || !producingIdentity) {
    fail(`${evidenceClass} writes require both --recorded-by-identity and --producing-identity`);
  }
  if (recordedByIdentity === producingIdentity) {
    fail(`${evidenceClass} write refused: producing and recording identities must be independent`);
  }
  if (
    path.resolve(dbPath) === path.resolve(realInventoryPath) &&
    !recordedByIdentity.startsWith('github-actions:')
  ) {
    fail(
      `${evidenceClass} write refused: local recorder identity cannot target the real Freshie inventory`,
    );
  }
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

/**
 * Hash the exact retained primary artifact that this ledger row names. The
 * hash is computed here rather than accepted as caller input, so a shell
 * wrapper cannot accidentally record a digest for different bytes.
 */
export function retainedArtifactEvidence(resultPath) {
  const resolved = path.resolve(resultPath);
  if (resolved === '/dev/shm' || resolved.startsWith('/dev/shm/')) {
    fail(`Result artifact must be retained outside /dev/shm (got: ${resolved})`);
  }
  let bytes;
  try {
    bytes = fs.readFileSync(resolved);
  } catch (err) {
    fail(`Cannot read retained result artifact (${resolved}): ${err.message}`);
  }
  if (bytes.length === 0) fail(`Retained result artifact is empty: ${resolved}`);
  return {
    artifact_uri: resolved,
    artifact_sha256: createHash('sha256').update(bytes).digest('hex'),
  };
}

/** Build the idempotent upsert SQL for one forge_proofs row. */
export function buildUpsertSql({ plugin, jrigRunId, row }) {
  return `${FORGE_PROOFS_DDL}
INSERT INTO forge_proofs
  (plugin_name, jrig_run_id, discovery_run_id, verification_type, passed, evidence,
   evidence_class, artifact_sha256, artifact_uri, spec_sha256, tool_version,
   kernel_version, provider, model, recorded_by_identity, producing_identity,
   layers_passed, total_layers, baseline_delta)
VALUES
  (${sqlString(plugin)}, ${jrigRunId}, ${row.discovery_run_id ?? 'NULL'},
   ${sqlString(VERIFICATION_TYPE)}, ${row.passed}, ${sqlString(JSON.stringify(row.evidence))},
   ${sqlString(row.evidence_class)}, ${sqlString(row.artifact_sha256)}, ${sqlString(row.artifact_uri)},
   ${row.spec_sha256 ? sqlString(row.spec_sha256) : 'NULL'},
   ${row.tool_version ? sqlString(row.tool_version) : 'NULL'},
   ${row.kernel_version ? sqlString(row.kernel_version) : 'NULL'},
   ${row.provider ? sqlString(row.provider) : 'NULL'}, ${row.model ? sqlString(row.model) : 'NULL'},
   ${sqlString(row.recorded_by_identity)}, ${sqlString(row.producing_identity)},
   ${row.layers_passed}, ${row.total_layers}, NULL)
ON CONFLICT(plugin_name, verification_type, jrig_run_id) DO UPDATE SET
  passed = excluded.passed,
  evidence = excluded.evidence,
  discovery_run_id = excluded.discovery_run_id,
  evidence_class = excluded.evidence_class,
  artifact_sha256 = excluded.artifact_sha256,
  artifact_uri = excluded.artifact_uri,
  spec_sha256 = excluded.spec_sha256,
  tool_version = excluded.tool_version,
  kernel_version = excluded.kernel_version,
  provider = excluded.provider,
  model = excluded.model,
  recorded_by_identity = excluded.recorded_by_identity,
  producing_identity = excluded.producing_identity,
  layers_passed = excluded.layers_passed,
  total_layers = excluded.total_layers,
  baseline_delta = excluded.baseline_delta,
  verified_at = CURRENT_TIMESTAMP;`;
}

function runSqlite(dbPath, sql) {
  const result = spawnSync('sqlite3', ['-batch', dbPath], {
    input: `PRAGMA foreign_keys = ON;\n${sql}`,
    encoding: 'utf8',
  });
  if (result.error) fail(`Failed to spawn sqlite3 CLI: ${result.error.message}`);
  if (result.status !== 0) fail(`sqlite3 exited ${result.status}: ${result.stderr.trim()}`);
  return result.stdout;
}

function ensureForgeProofsSchema(dbPath) {
  // Standalone recorder tests and scratch inventory copies may predate both
  // tables. Bootstrap the canonical definitions before inspecting columns.
  runSqlite(dbPath, FORGE_PROOFS_DDL);
  const columns = runSqlite(dbPath, 'PRAGMA table_info(forge_proofs);')
    .trim()
    .split('\n')
    .filter(Boolean)
    .map((line) => line.split('|')[1]);
  if (columns.includes('run_id') && !columns.includes('jrig_run_id')) {
    runSqlite(dbPath, 'ALTER TABLE forge_proofs RENAME COLUMN run_id TO jrig_run_id;');
  }
  const currentColumns = new Set(
    runSqlite(dbPath, 'PRAGMA table_info(forge_proofs);')
      .trim()
      .split('\n')
      .filter(Boolean)
      .map((line) => line.split('|')[1]),
  );
  for (const [name, definition] of [
    ['discovery_run_id', 'INTEGER REFERENCES discovery_runs(id)'],
    [
      'evidence_class',
      "TEXT NOT NULL DEFAULT 'E0' CHECK(evidence_class IN ('E0', 'E1', 'E2', 'E3'))",
    ],
    ['artifact_sha256', 'TEXT'],
    ['artifact_uri', 'TEXT'],
    ['spec_sha256', 'TEXT'],
    ['tool_version', 'TEXT'],
    ['kernel_version', 'TEXT'],
    ['provider', 'TEXT'],
    ['model', 'TEXT'],
    ['recorded_by_identity', 'TEXT'],
    ['producing_identity', 'TEXT'],
  ]) {
    if (!currentColumns.has(name))
      runSqlite(dbPath, `ALTER TABLE forge_proofs ADD COLUMN ${name} ${definition};`);
  }
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
  const retained = retainedArtifactEvidence(args.result);
  Object.assign(row.evidence, retained);
  const unique = (key) => [...new Set(entries.map((entry) => entry[key]).filter(Boolean))];
  row.evidence_class = 'E0';
  row.evidence_class = args.evidenceClass ?? 'E0';
  row.discovery_run_id = args.discoveryRunId;
  row.artifact_sha256 = retained.artifact_sha256;
  row.artifact_uri = retained.artifact_uri;
  row.spec_sha256 = process.env.JRIG_SPEC_SHA256 || null;
  row.tool_version = process.env.JRIG_TOOL_VERSION || null;
  row.kernel_version = process.env.JRIG_KERNEL_VERSION || null;
  row.provider = unique('provider').length === 1 ? unique('provider')[0] : null;
  row.model = unique('model').length === 1 ? unique('model')[0] : null;
  row.recorded_by_identity =
    args.recordedByIdentity ??
    (process.env.GITHUB_ACTOR ? `github-actions:${process.env.GITHUB_ACTOR}` : 'local-untrusted');
  row.producing_identity = args.producingIdentity ?? 'local-evaluator';
  enforceRecorderIdentity({
    evidenceClass: row.evidence_class,
    recordedByIdentity: row.recorded_by_identity,
    producingIdentity: row.producing_identity,
    dbPath: args.db,
  });

  ensureForgeProofsSchema(args.db);
  runSqlite(args.db, buildUpsertSql({ plugin: args.plugin, jrigRunId: args.jrigRunId, row }));

  // Read the row back so the log line is evidence, not hope.
  const echo = runSqlite(
    args.db,
    `.mode json
SELECT plugin_name, jrig_run_id, verification_type, passed, layers_passed, total_layers, baseline_delta, verified_at
FROM forge_proofs
WHERE plugin_name = ${sqlString(args.plugin)}
  AND verification_type = ${sqlString(VERIFICATION_TYPE)}
  AND jrig_run_id = ${args.jrigRunId};`,
  ).trim();
  if (!echo)
    fail('Upsert reported success but the row is not readable back — refusing to report success.');

  const written = JSON.parse(echo)[0];
  console.log(
    `[record-jrig-proofs] Upserted ${VERIFICATION_TYPE} row for '${args.plugin}' (jrig_run_id=${args.jrigRunId}): ` +
      `passed=${written.passed}, layers=${written.layers_passed}/${written.total_layers}, ` +
      `models=${row.evidence.models.map((m) => m.model).join(',')}, artifact_sha256=${row.evidence.artifact_sha256}${row.evidence.stub ? ' [STUB — not ground truth]' : ''}`,
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
