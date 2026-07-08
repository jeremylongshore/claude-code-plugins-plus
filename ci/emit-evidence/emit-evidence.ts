#!/usr/bin/env -S node --experimental-strip-types
/**
 * ci/emit-evidence/emit-evidence.ts — produce this repo's own signed-ready
 * testing evidence for the intent-eval-dashboard reports hub
 * (labs.intentsolutions.io, repo row key `ccp`).
 *
 * ── Why this lives in `ci/emit-evidence/`, NOT `scripts/` ──
 *
 * `scripts/` is the repo's operational toolbox (validators, sync, publish
 * helpers) and is linted/formatted under the root gates. This emitter is a
 * CI-only artifact producer with its own pinned dependency
 * (`@intentsolutions/core` — the kernel validators, pinned to the EXACT
 * version the dashboard verifies with). It has its own private, non-workspace
 * `package.json` + lockfile so the root workspace, the publish surfaces
 * (`plugins/**`, `packages/**`, pnpm-workspace globs), and the published npm
 * packages are all untouched. Nothing under `ci/` ships anywhere.
 *
 * This is the DETERMINISTIC half of the emit. It runs two of the repo's real,
 * blocking, deterministic CI gates (both live inside the `validate` job that
 * the `ci-required` aggregate needs), shapes each outcome into a kernel
 * `gate-result/v1` body, wraps each in a kernel `EvidenceBundle`, and writes:
 *
 *   build/evidence/bundle-<i>.json          — CANONICAL EvidenceBundle bytes
 *   build/evidence/gate-result-<i>.json     — the gate-result/v1 predicate body
 *   build/evidence/manifest-skeleton.json   — for ci/emit-evidence/assemble-manifest.ts
 *
 * Signing + Rekor + final report-manifest.json assembly happen in CI
 * (.github/workflows/emit-evidence.yml). This script does NO crypto and
 * writes only to the gitignored `build/` dir.
 *
 * ── Gate selection (honest, no fake evidence) ──
 *
 * Chosen (both are blocking steps of the `validate` job → `ci-required`):
 *   - catalog-invariants  — scripts/validate-catalog-invariants.py
 *                           (plugin FS path == catalog category, entry parity)
 *   - unicode-hygiene     — scripts/validate-unicode-hygiene.py
 *                           (invisible tag chars / Trojan Source / zero-width
 *                           defense; blocks on BLOCKER findings)
 *
 * Deliberately excluded after recon (would be fake/degraded evidence):
 *   - `audit-harness verify`     — its hash-pinning surface is currently EMPTY
 *                                  in this repo (see validate-plugins.yml
 *                                  comment), so it trivially exits 0: no signal.
 *   - full-corpus skill grading  — report-only with hundreds of known errors;
 *                                  not a pass/fail gate on main.
 *   - kernel-shadow / vendor-hash lanes — advisory by design (soak), never
 *                                  blocking; unfit for SIGNED pass evidence.
 *
 * ── Contract (matches the dashboard ingest, verified against its source) ──
 *
 *   - Each `bundle` validates against `EvidenceBundleSchema` (kernel pinned to
 *     the EXACT version the dashboard verifies with).
 *   - Canonical bytes use the dashboard's `stableStringify` so cosign's
 *     signature round-trips through the dashboard's re-canonicalisation.
 *   - `signing_mode: 'rekor_production'`, `rekor_log_indices: []` (real index
 *     lives in the sigstore Bundle the dashboard's Rekor check verifies).
 *
 * Usage:
 *   node --experimental-strip-types ci/emit-evidence/emit-evidence.ts \
 *     [--out build/evidence] [--ref refs/heads/main] [--self-check]
 */

import { execFileSync } from 'node:child_process';
import { createHash, randomBytes } from 'node:crypto';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import {
  GateResultV1Schema,
  GATE_RESULT_V1_URI,
} from '@intentsolutions/core/validators/v1/gate-result-v1';
import { EvidenceBundleSchema } from '@intentsolutions/core/validators/v1/evidence-bundle';

const GITHUB_REPO = 'jeremylongshore/claude-code-plugins-plus-skills';
const REPO_KEY = 'ccp';

/** The two gate scripts whose bytes ARE the policy this emit attests under. */
const POLICY_FILES = [
  'scripts/validate-catalog-invariants.py',
  'scripts/validate-unicode-hygiene.py',
] as const;

interface GateOutcome {
  readonly gateName: string;
  readonly gateVersion: string;
  readonly decision: 'pass' | 'fail' | 'advisory' | 'error';
  readonly reasons: readonly string[];
  readonly dimensionsEvaluated: readonly string[];
  readonly dimensionsSkipped: readonly string[];
  readonly advisorySeverity?: 'info' | 'warn' | 'error';
  readonly failureMode?: string;
}

interface EmitContext {
  readonly nowIso: string;
  readonly nowMs: number;
  readonly commitSha: string;
  readonly sourceSha: string;
  readonly policyHash: string;
  readonly runnerVersion: string;
  readonly rand16: () => Uint8Array;
}

// ── Canonicalisation (MUST match the dashboard's content-address.ts) ──

function sortDeep(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sortDeep);
  if (value !== null && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
      .map(([k, v]) => [k, sortDeep(v)] as const);
    return Object.fromEntries(entries);
  }
  return value;
}

/** Canonical JSON string (sorted keys, no whitespace) — dashboard-identical. */
export function stableStringify(value: unknown): string {
  return JSON.stringify(sortDeep(value));
}

function sha256Hex(s: string): string {
  return createHash('sha256').update(Buffer.from(s, 'utf8')).digest('hex');
}

/** Generate a kernel-valid UUIDv7 from a 16-byte source + ms timestamp. */
export function uuidv7(nowMs: number, rand: Uint8Array): string {
  const b = Buffer.from(rand.slice(0, 16));
  const ts = BigInt(nowMs);
  b[0] = Number((ts >> 40n) & 0xffn);
  b[1] = Number((ts >> 32n) & 0xffn);
  b[2] = Number((ts >> 24n) & 0xffn);
  b[3] = Number((ts >> 16n) & 0xffn);
  b[4] = Number((ts >> 8n) & 0xffn);
  b[5] = Number(ts & 0xffn);
  b[6] = (b[6]! & 0x0f) | 0x70; // version 7
  b[8] = (b[8]! & 0x3f) | 0x80; // variant 10
  const h = b.toString('hex');
  return `${h.slice(0, 8)}-${h.slice(8, 12)}-${h.slice(12, 16)}-${h.slice(16, 20)}-${h.slice(20, 32)}`;
}

/** A built row: the kernel-valid bundle + its canonical bytes + the gate body. */
export interface EmitRow {
  readonly bundle: unknown;
  readonly canonicalBundle: string;
  readonly gateResult: unknown;
  readonly sourceSha: string;
}

/**
 * Build + kernel-validate a gate-result/v1 body for one outcome. Throws (fail
 * closed) if the result is not kernel-schema-valid.
 */
export function buildGateResult(o: GateOutcome, ctx: EmitContext): Record<string, unknown> {
  const gateId = `${REPO_KEY}:ci:${o.gateName}`;
  const inputHash = `sha256:${sha256Hex(`${ctx.commitSha}:${o.gateName}:${ctx.policyHash}`)}`;
  const body: Record<string, unknown> = {
    gate_id: gateId,
    gate_name: o.gateName,
    gate_version: o.gateVersion,
    gate_decision: o.decision,
    gate_reasons: [...o.reasons],
    coverage: {
      dimensions_evaluated: [...o.dimensionsEvaluated],
      dimensions_skipped: [...o.dimensionsSkipped],
    },
    policy_ref: `${ctx.policyHash}:${POLICY_FILES.join('+')}`,
    policy_hash: ctx.policyHash,
    input_hash: inputHash,
    evaluated_at: ctx.nowIso,
    runner: `ccpi-emit@${ctx.runnerVersion}`,
    commit_sha: ctx.commitSha,
    ...(o.advisorySeverity !== undefined ? { advisory_severity: o.advisorySeverity } : {}),
    ...(o.failureMode !== undefined ? { failure_mode: o.failureMode } : {}),
  };
  GateResultV1Schema.parse(body); // fail-closed
  return body;
}

/**
 * Wrap a gate-result body in a kernel EvidenceBundle. Throws if the bundle is
 * not kernel-schema-valid.
 */
export function buildEvidenceBundle(
  gateResult: Record<string, unknown>,
  ctx: EmitContext,
): Record<string, unknown> {
  const grHashHex = sha256Hex(stableStringify(gateResult));
  const inputHash = String(gateResult['input_hash']);
  const subjectDigest = inputHash.startsWith('sha256:')
    ? inputHash.slice('sha256:'.length)
    : inputHash;
  const bundle: Record<string, unknown> = {
    id: uuidv7(ctx.nowMs, ctx.rand16()),
    eval_run_id: uuidv7(ctx.nowMs, ctx.rand16()),
    created_at: ctx.nowIso,
    predicate_uri_set: [GATE_RESULT_V1_URI],
    row_count: 1,
    subject_set: [{ name: String(gateResult['gate_id']), digest: { sha256: subjectDigest } }],
    storage_key: `sha256:${grHashHex}`,
    signing_mode: 'rekor_production',
    rekor_log_indices: [], // real index lives in the sigstore Bundle (see header)
    verification_status: 'unverified', // the dashboard re-verifies; we don't self-attest
    verification_last_checked_at: ctx.nowIso,
  };
  EvidenceBundleSchema.parse(bundle); // fail-closed
  return bundle;
}

/** Build all rows from outcomes. */
export function buildRows(outcomes: readonly GateOutcome[], ctx: EmitContext): EmitRow[] {
  return outcomes.map((o) => {
    const gateResult = buildGateResult(o, ctx);
    const bundle = buildEvidenceBundle(gateResult, ctx);
    return {
      bundle,
      canonicalBundle: stableStringify(bundle),
      gateResult,
      sourceSha: ctx.sourceSha,
    };
  });
}

/** The manifest skeleton CI signs + assembles into the final report-manifest.json. */
export interface ManifestSkeleton {
  readonly repo: string;
  readonly signing: {
    readonly issuer: string;
    readonly subject: string;
    readonly workflowRef: string;
  };
  readonly rows: readonly {
    readonly bundleFile: string;
    readonly gateResults: readonly unknown[];
    readonly sourceSha: string;
  }[];
}

/**
 * Compute the OIDC signing claims this CI run will assert. The emit workflow
 * runs on push to main (plus a main-only workflow_dispatch guard), so `ref` is
 * always `refs/heads/main` in CI — these are exactly the claims the dashboard
 * pins for the `ccp` row:
 *   issuer      https://token.actions.githubusercontent.com
 *   subject     repo:jeremylongshore/claude-code-plugins-plus-skills:ref:refs/heads/main
 *   workflowRef jeremylongshore/claude-code-plugins-plus-skills/.github/workflows/emit-evidence.yml@refs/heads/main
 */
export function signingClaims(ref: string): ManifestSkeleton['signing'] {
  return {
    issuer: 'https://token.actions.githubusercontent.com',
    subject: `repo:${GITHUB_REPO}:ref:${ref}`,
    workflowRef: `${GITHUB_REPO}/.github/workflows/emit-evidence.yml@${ref}`,
  };
}

/** Write all emit artifacts under `outDir`. Returns the skeleton written. */
export function writeEmit(rows: readonly EmitRow[], ref: string, outDir: string): ManifestSkeleton {
  mkdirSync(outDir, { recursive: true });
  const skeletonRows = rows.map((row, i) => {
    const bundleFile = `bundle-${i}.json`;
    writeFileSync(join(outDir, bundleFile), row.canonicalBundle, 'utf8');
    writeFileSync(join(outDir, `gate-result-${i}.json`), stableStringify(row.gateResult), 'utf8');
    return { bundleFile, gateResults: [row.gateResult], sourceSha: row.sourceSha };
  });
  const skeleton: ManifestSkeleton = {
    repo: REPO_KEY,
    signing: signingClaims(ref),
    rows: skeletonRows,
  };
  writeFileSync(join(outDir, 'manifest-skeleton.json'), JSON.stringify(skeleton, null, 2), 'utf8');
  return skeleton;
}

// ── Gate collection (CI-run; runs the repo's real blocking gates) ──

function run(cmd: string, args: readonly string[]): { ok: boolean; out: string } {
  try {
    const out = execFileSync(cmd, args as string[], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    return { ok: true, out };
  } catch (err: unknown) {
    const e = err as { stdout?: string; stderr?: string; message?: string };
    return { ok: false, out: `${e.stdout ?? ''}${e.stderr ?? ''}${e.message ?? ''}` };
  }
}

/**
 * Catalog invariant gate: every catalog entry's filesystem path matches its
 * declared category (and entry parity holds). Real, deterministic, stdlib-only
 * Python; a blocking step of the `validate` job on main.
 */
function catalogInvariantsOutcome(): GateOutcome {
  const r = run('python3', ['scripts/validate-catalog-invariants.py']);
  return {
    gateName: 'catalog-invariants',
    gateVersion: '1.0.0',
    decision: r.ok ? 'pass' : 'fail',
    reasons: r.ok
      ? [firstLines(r.out, 1) || 'catalog invariant check passed']
      : [firstLines(r.out, 8) || 'catalog invariants violated'],
    dimensionsEvaluated: ['catalog-path-category-parity'],
    dimensionsSkipped: [],
    ...(r.ok ? {} : { failureMode: 'catalog-invariant-violation' }),
  };
}

/**
 * Unicode-hygiene gate: invisible tag characters (Socket TrapDoor vector),
 * bidi overrides (Trojan Source), zero-width/format chars, mixed-script
 * identifiers. Blocks on BLOCKER findings. Real, deterministic, stdlib-only
 * Python; a blocking step of the `validate` job on main.
 */
function unicodeHygieneOutcome(): GateOutcome {
  const r = run('python3', ['scripts/validate-unicode-hygiene.py']);
  return {
    gateName: 'unicode-hygiene',
    gateVersion: '1.0.0',
    decision: r.ok ? 'pass' : 'fail',
    reasons: r.ok
      ? ['no BLOCKER-severity unicode findings (tag chars, bidi overrides)']
      : [firstLines(r.out, 8) || 'BLOCKER-severity unicode findings present'],
    dimensionsEvaluated: ['invisible-tag-chars', 'bidi-overrides', 'zero-width-format-chars'],
    dimensionsSkipped: [],
    ...(r.ok ? {} : { failureMode: 'unicode-hygiene-blocker' }),
  };
}

function firstLines(s: string, n: number): string {
  return s
    .split('\n')
    .filter((l) => l.trim().length > 0)
    .slice(0, n)
    .join(' ')
    .slice(0, 500);
}

function gitSha(): string {
  const r = run('git', ['rev-parse', 'HEAD']);
  return r.ok ? r.out.trim() : '0'.repeat(40);
}

/**
 * policy_hash = sha256 over the raw bytes of the two gate scripts (in fixed
 * order, filename-delimited). The policy an emitted row attests under IS the
 * validator source at this commit — recomputable by any auditor from the tree.
 */
function gatePolicyHash(): string {
  const h = createHash('sha256');
  for (const f of POLICY_FILES) {
    h.update(Buffer.from(`${f}\n`, 'utf8'));
    h.update(readFileSync(join(process.cwd(), f)));
  }
  return `sha256:${h.digest('hex')}`;
}

// ── Self-check (locally-runnable correctness proof) ──

function selfCheck(): void {
  const ctx = synthCtx();
  const outcomes: GateOutcome[] = [
    {
      gateName: 'catalog-invariants',
      gateVersion: '1.0.0',
      decision: 'pass',
      reasons: ['catalog invariant check passed (462 plugins)'],
      dimensionsEvaluated: ['catalog-path-category-parity'],
      dimensionsSkipped: [],
    },
    {
      gateName: 'unicode-hygiene',
      gateVersion: '1.0.0',
      decision: 'fail',
      reasons: ['BLOCKER: U+E0041 invisible tag character in install command'],
      dimensionsEvaluated: ['invisible-tag-chars', 'bidi-overrides', 'zero-width-format-chars'],
      dimensionsSkipped: [],
      failureMode: 'unicode-hygiene-blocker',
    },
  ];
  const rows = buildRows(outcomes, ctx); // throws if any artifact is kernel-invalid
  for (const row of rows) {
    if (stableStringify(JSON.parse(row.canonicalBundle)) !== row.canonicalBundle) {
      throw new Error('canonical bundle is not stable under re-canonicalisation');
    }
  }
  if (rows.length !== 2) throw new Error('expected 2 rows');
  console.log(`self-check OK: ${rows.length} kernel-valid, canonical-stable rows built`);
}

function synthCtx(): EmitContext {
  let n = 0;
  return {
    nowIso: '2026-07-08T00:00:00.000Z',
    nowMs: 1783209600000,
    commitSha: 'a'.repeat(40),
    sourceSha: 'a'.repeat(40),
    policyHash: `sha256:${'b'.repeat(64)}`,
    runnerVersion: '4.33.0',
    // Deterministic, non-random 16-byte source so self-check output is stable.
    rand16: () => {
      n += 1;
      return Uint8Array.from(Array.from({ length: 16 }, (_v, i) => (n * 31 + i) & 0xff));
    },
  };
}

function packageVersion(): string {
  try {
    const pkg = JSON.parse(readFileSync(join(process.cwd(), 'package.json'), 'utf8')) as {
      version?: string;
    };
    return pkg.version ?? '0.0.0';
  } catch {
    return '0.0.0';
  }
}

function ciCtx(): EmitContext {
  const sha = gitSha();
  return {
    nowIso: new Date().toISOString(),
    nowMs: Date.now(),
    commitSha: sha,
    sourceSha: sha,
    policyHash: gatePolicyHash(),
    runnerVersion: packageVersion(),
    rand16: () => Uint8Array.from(randomBytes(16)),
  };
}

function parseArgs(argv: readonly string[]): { out: string; selfCheck: boolean; ref: string } {
  let out = 'build/evidence';
  let ref = process.env['GITHUB_REF'] ?? 'refs/heads/main';
  let sc = false;
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--out') {
      out = argv[i + 1] ?? out;
      i++;
    } else if (argv[i] === '--ref') {
      ref = argv[i + 1] ?? ref;
      i++;
    } else if (argv[i] === '--self-check') {
      sc = true;
    }
  }
  return { out, selfCheck: sc, ref };
}

function main(argv: readonly string[]): number {
  const args = parseArgs(argv);
  if (args.selfCheck) {
    selfCheck();
    return 0;
  }
  const ctx = ciCtx();
  mkdirSync(args.out, { recursive: true });
  const outcomes: GateOutcome[] = [catalogInvariantsOutcome(), unicodeHygieneOutcome()];
  const rows = buildRows(outcomes, ctx);
  writeEmit(rows, args.ref, args.out);
  console.log(
    `emit-evidence OK: ${rows.length} kernel-valid gate-result/v1 row(s) written to ${args.out}\n` +
      `  decisions: ${outcomes.map((o) => `${o.gateName}=${o.decision}`).join(', ')}\n` +
      `  next (CI): cosign sign-blob each bundle-<i>.json -> assemble-manifest.ts -> report-manifest.json`,
  );
  return 0;
}

// Only run when invoked directly (not when imported by a sibling assembler).
const invokedDirectly = process.argv[1]?.endsWith('emit-evidence.ts') === true;
if (invokedDirectly) {
  try {
    process.exit(main(process.argv.slice(2)));
  } catch (err: unknown) {
    console.error(
      'emit-evidence FAILED (fail-closed):',
      err instanceof Error ? err.message : String(err),
    );
    process.exit(1);
  }
}
