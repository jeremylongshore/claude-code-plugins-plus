/**
 * kernel-vendor-hash.test.mjs — VERSION-ORDERING INVARIANT TEST CORPUS
 *
 * Closes F-MK-003 (bead: "Version ordering invariant V <= C <= K formalized in
 * test corpus"). Formalizes the V ≤ C ≤ K ordering invariant + bounded-staleness
 * model from plan 033 § 14.15.1 as an executable fixture corpus.
 *
 * The corpus drives the SAME comparator the CLI uses — `evaluateCoupling` is the
 * pure core that `main()` in kernel-vendor-hash.mjs delegates to, so there is no
 * logic fork between what CI runs and what these tests assert. A handful of
 * end-to-end subprocess smokes additionally assert the CLI's advisory vs --strict
 * EXIT CODE contract (advisory exits 0 even on a violation; --strict exits 1).
 *
 * Run: node --test scripts/kernel-vendor-hash.test.mjs
 *
 * FIXTURE SHAPE (one row per scenario)
 *   { name, V, C, K, ranged?, kernelAgeDays?, expect: { violations, stale, ordering } }
 *     - ordering: 'ok' (V<=C<=K holds + within staleness budget) | 'violation'
 *     - violations: expected count of reported ordering/staleness violations
 *     - stale: expected boolean staleness flag
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { evaluateCoupling, semverCompare } from './kernel-vendor-hash.mjs';

const __dirname = dirname(fileURLToPath(import.meta.url));
const CLI = join(__dirname, 'kernel-vendor-hash.mjs');

// ─────────────────────────────────────────────────────────────────────────────
// semverCompare — the primitive the ordering invariant is built on.
// ─────────────────────────────────────────────────────────────────────────────
test('semverCompare: equal cores compare to 0', () => {
  assert.equal(semverCompare('0.4.1', '0.4.1'), 0);
  assert.equal(semverCompare('1.0.0', '1.0.0'), 0);
  assert.equal(semverCompare('v0.4.1', '0.4.1'), 0, 'leading v is tolerated');
});

test('semverCompare: orders by major.minor.patch', () => {
  assert.equal(semverCompare('0.4.1', '0.4.2'), -1);
  assert.equal(semverCompare('0.5.0', '0.4.9'), 1);
  assert.equal(semverCompare('1.0.0', '0.99.99'), 1);
  assert.equal(semverCompare('0.4.0', '0.4.0'), 0);
});

test('semverCompare: a pre-release sorts BEFORE the same core without one (semver §11)', () => {
  assert.equal(semverCompare('1.0.0-draft', '1.0.0'), -1);
  assert.equal(semverCompare('1.0.0', '1.0.0-draft'), 1);
  assert.equal(semverCompare('1.0.0-alpha', '1.0.0-beta'), -1);
});

// ─────────────────────────────────────────────────────────────────────────────
// The V ≤ C ≤ K fixture corpus — POSITIVE cases (the bead's (a),(b),(c)).
// ─────────────────────────────────────────────────────────────────────────────
const POSITIVE_FIXTURES = [
  {
    // (a) canonical happy path — all three identities equal (the steady state).
    name: '(a) vendored = CCP = kernel — canonical steady state',
    V: '0.4.1',
    C: '0.4.1',
    K: '0.4.1',
    expect: { violations: 0, stale: false, ordering: 'ok' },
  },
  {
    // (b) legitimate lag within the 7-day budget — vendored < CCP = kernel, and
    //     since V < K, staleness is evaluated against the publish age (3 days ≤ 7).
    name: '(b) vendored < CCP = kernel within the 7-day staleness budget',
    V: '0.4.0',
    C: '0.4.1',
    K: '0.4.1',
    kernelAgeDays: 3,
    expect: { violations: 0, stale: false, ordering: 'ok' },
  },
  {
    // (c) kernel ahead, CCP not yet bumped — vendored = CCP < kernel. V < K so
    //     staleness is evaluated; with a 2-day age it is within budget.
    name: '(c) vendored = CCP < kernel (kernel ahead, CCP not yet bumped), fresh',
    V: '0.4.1',
    C: '0.4.1',
    K: '0.5.0',
    kernelAgeDays: 2,
    expect: { violations: 0, stale: false, ordering: 'ok' },
  },
  {
    // Variant of (b)/(c): vendored < CCP < kernel, both lags legitimate, fresh.
    name: 'vendored < CCP < kernel, fully ordered, fresh kernel',
    V: '0.4.0',
    C: '0.4.1',
    K: '0.5.0',
    kernelAgeDays: 1,
    expect: { violations: 0, stale: false, ordering: 'ok' },
  },
];

// ─────────────────────────────────────────────────────────────────────────────
// NEGATIVE cases — the invariant MUST report a violation (vendored>kernel,
// vendored>CCP, CCP>kernel) and the bounded-staleness breach (>7-day lag).
// ─────────────────────────────────────────────────────────────────────────────
const NEGATIVE_FIXTURES = [
  {
    // vendored AHEAD of CCP-declared pin (V > C) — you cannot validate against a
    // schema newer than your pin.
    name: 'vendored > CCP — snapshot ahead of the declared pin (V > C)',
    V: '0.5.0',
    C: '0.4.1',
    K: '0.5.0',
    kernelAgeDays: 1,
    expect: { violations: 1, stale: false, ordering: 'violation', match: /V \(0\.5\.0\) > C/ },
  },
  {
    // CCP-declared pin AHEAD of latest published kernel (C > K) — you cannot pin a
    // version that does not exist yet.
    name: 'CCP > kernel — declared pin ahead of latest published kernel (C > K)',
    V: '0.4.1',
    C: '0.5.0',
    K: '0.4.1',
    expect: { violations: 1, stale: false, ordering: 'violation', match: /C \(0\.5\.0\) > K/ },
  },
  {
    // vendored AHEAD of kernel latest (V > K) — surfaces via the V>C and/or C>K
    // legs. Here V=0.6.0 > C=0.5.0 (V>C) AND C=0.5.0 > K=0.4.1 (C>K): two legs.
    name: 'vendored > kernel — both ordering legs break (V > C and C > K)',
    V: '0.6.0',
    C: '0.5.0',
    K: '0.4.1',
    expect: { violations: 2, stale: false, ordering: 'violation' },
  },
  {
    // bounded-staleness breach: V < K but the kernel has been published >7 days,
    // so the vendored snapshot is STALE beyond budget.
    name: 'staleness breach — vendored lags kernel by >7 days of publish age',
    V: '0.4.1',
    C: '0.4.1',
    K: '0.5.0',
    kernelAgeDays: 30,
    expect: { violations: 1, stale: true, ordering: 'violation', match: /STALENESS/ },
  },
];

for (const fx of POSITIVE_FIXTURES) {
  test(`ordering POSITIVE: ${fx.name}`, () => {
    const r = evaluateCoupling({
      V: fx.V,
      C: fx.C,
      K: fx.K,
      ranged: fx.ranged ?? false,
      kernelAgeDays: fx.kernelAgeDays ?? null,
    });
    assert.equal(
      r.violations.length,
      fx.expect.violations,
      `expected ${fx.expect.violations} violation(s), got: ${JSON.stringify(r.violations)}`,
    );
    assert.equal(r.stale, fx.expect.stale, 'stale flag mismatch');
    // A positive fixture: the ordering invariant holds at the comparator level.
    assert.ok(semverCompare(fx.V, fx.C) <= 0, 'V <= C must hold for a positive fixture');
    assert.ok(semverCompare(fx.C, fx.K) <= 0, 'C <= K must hold for a positive fixture');
  });
}

for (const fx of NEGATIVE_FIXTURES) {
  test(`ordering NEGATIVE: ${fx.name}`, () => {
    const r = evaluateCoupling({
      V: fx.V,
      C: fx.C,
      K: fx.K,
      ranged: fx.ranged ?? false,
      kernelAgeDays: fx.kernelAgeDays ?? null,
    });
    assert.equal(
      r.violations.length,
      fx.expect.violations,
      `expected ${fx.expect.violations} violation(s), got: ${JSON.stringify(r.violations)}`,
    );
    assert.ok(r.violations.length > 0, 'a negative fixture MUST report at least one violation');
    assert.equal(r.stale, fx.expect.stale, 'stale flag mismatch');
    if (fx.expect.match) {
      assert.ok(
        r.violations.some((v) => fx.expect.match.test(v)),
        `expected a violation matching ${fx.expect.match}, got: ${JSON.stringify(r.violations)}`,
      );
    }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Staleness boundary — exactly at the 7-day bound is WITHIN budget (≤ not <).
// ─────────────────────────────────────────────────────────────────────────────
test('staleness boundary: lag at exactly 7 days is within budget (not stale)', () => {
  const r = evaluateCoupling({ V: '0.4.1', C: '0.4.1', K: '0.5.0', kernelAgeDays: 7 });
  assert.equal(r.stale, false);
  assert.equal(r.violations.length, 0);
  assert.ok(r.warnings.some((w) => /STALENESS OK/.test(w)));
});

test('staleness boundary: lag at 8 days is OVER budget (stale)', () => {
  const r = evaluateCoupling({ V: '0.4.1', C: '0.4.1', K: '0.5.0', kernelAgeDays: 8 });
  assert.equal(r.stale, true);
  assert.equal(r.violations.length, 1);
});

test('staleness with UNKNOWN kernel age does not fire (warns instead)', () => {
  const r = evaluateCoupling({ V: '0.4.1', C: '0.4.1', K: '0.5.0', kernelAgeDays: null });
  assert.equal(r.stale, false);
  assert.equal(r.violations.length, 0);
  assert.ok(r.warnings.some((w) => /publish age is UNKNOWN/.test(w)));
});

// ─────────────────────────────────────────────────────────────────────────────
// Existence guards — absent inputs warn + SKIP the relevant comparison, never
// crash and never produce a violation. (The whole check is existence-guarded.)
// ─────────────────────────────────────────────────────────────────────────────
test('existence guard: all inputs absent → warnings only, no violations', () => {
  const r = evaluateCoupling({ V: null, C: null, K: null });
  assert.equal(r.violations.length, 0);
  assert.equal(r.stale, false);
  assert.equal(r.warnings.length, 3, 'one warning per absent identity (V, C, K)');
});

test('existence guard: missing K skips the C≤K + staleness legs', () => {
  const r = evaluateCoupling({ V: '0.4.1', C: '0.4.1', K: null });
  assert.equal(r.violations.length, 0);
  assert.ok(r.warnings.some((w) => /K \(kernel latest published\) UNRESOLVED/.test(w)));
});

test('ranged pin warns but still orders on the floor', () => {
  const r = evaluateCoupling({ V: '0.4.1', C: '0.4.1', K: '0.4.1', ranged: true });
  assert.equal(r.violations.length, 0);
  assert.ok(r.warnings.some((w) => /RANGE operator/.test(w)));
});

// ─────────────────────────────────────────────────────────────────────────────
// CLI exit-code contract (end-to-end subprocess) — advisory exits 0 even when the
// ordering is violated; --strict exits 1 on a real violation. Drives the resolved
// V/C from this repo's disk (both 0.4.1) with K injected via --kernel-latest.
// ─────────────────────────────────────────────────────────────────────────────
function runCli(args) {
  try {
    const stdout = execFileSync('node', [CLI, ...args], { encoding: 'utf8' });
    return { code: 0, stdout };
  } catch (err) {
    return { code: err.status ?? 1, stdout: err.stdout?.toString() ?? '' };
  }
}

test('CLI advisory: a C>K ordering violation still EXITS 0 (report-only)', () => {
  // C resolves to 0.4.1 from package.json; K=0.1.0 forces C > K.
  const { code, stdout } = runCli(['--kernel-latest', '0.1.0', '--json']);
  assert.equal(code, 0, 'advisory mode must exit 0 regardless of violations');
  const report = JSON.parse(stdout);
  assert.ok(
    report.violations.some((v) => /C \(0\.4\.1\) > K \(0\.1\.0\)/.test(v)),
    'expected the C>K ordering violation to be reported',
  );
  assert.equal(report.advisory, true);
});

test('CLI --strict: a C>K ordering violation EXITS 1', () => {
  const { code } = runCli(['--strict', '--kernel-latest', '0.1.0']);
  assert.equal(code, 1, '--strict must exit non-zero on a real ordering violation');
});

test('CLI --strict: a clean ordering (C=K) EXITS 0', () => {
  // K=0.4.1 matches the declared pin → V=C=K → no violation.
  const { code } = runCli([
    '--strict',
    '--kernel-latest',
    '0.4.1',
    '--kernel-published',
    new Date().toISOString(),
  ]);
  assert.equal(code, 0, '--strict must exit 0 when the invariant holds');
});
