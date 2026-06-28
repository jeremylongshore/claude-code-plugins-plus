#!/usr/bin/env node
/**
 * kernel-vendor-hash.mjs — VERSION-COUPLING CONSISTENCY MODEL (ADVISORY ONLY)
 *
 * Implements the V ≤ C ≤ K ordering invariant + bounded-staleness check from
 * plan 033 § 14.15 (intent-eval-lab/000-docs/033-PP-PLAN-skill-refiner-sak-amendment-v7).
 * Spec doc co-located in CCPI: 000-docs/<NNN>-DR-STND-kernel-vendor-version-coupling.md.
 *
 * THE THREE VERSION IDENTITIES (§ 14.15.1)
 * ----------------------------------------
 *   (V) Vendored snapshot   — the kernel schema version CCPI has CACHED. CCPI does
 *                             NOT yet maintain a .kernel-vendor/authoring/v1/index.json
 *                             snapshot; today it "vendors" the kernel by pinning the
 *                             @intentsolutions/core PACKAGE EXACTLY in package.json and
 *                             reading schemas out of node_modules. V is therefore the
 *                             INSTALLED kernel package version (the realised pin). When
 *                             CCPI next materialises a .kernel-vendor/ snapshot (spec
 *                             § "Required snapshot shape"), V reads from that index.json's
 *                             $schemaVersion instead. Either source resolves to a semver.
 *   (C) CCPI-declared kernel — the kernel version CCPI DECLARES it consumes. Lives in
 *                             package.json `dependencies["@intentsolutions/core"]` (the
 *                             exact pin) and is mirrored by KERNEL_PIN in
 *                             scripts/kernel-shadow-validation.mjs. (CCPI's OWN validator
 *                             schema version — SCHEMA_VERSION in validate-skills-schema.py
 *                             — is a DIFFERENT axis and is reported for context, not
 *                             ordered: it versions the prose-spec encoding, not the kernel.)
 *   (K) Kernel latest       — the latest PUBLISHED kernel package version (npm
 *                             @intentsolutions/core). Owns schema evolution. Read from the
 *                             read-only kernel repo's package.json when present locally,
 *                             else from an explicit --kernel-latest argument, else the
 *                             check degrades to advisory-unknown (loud warn, exit 0).
 *
 * THE ORDERING INVARIANT (§ 14.15.1 / § 14.15.2)
 * ----------------------------------------------
 *   V ≤ C ≤ K   (semver comparison; vendored ≤ CCPI-declared ≤ kernel-latest)
 *
 *   - V ≤ C : the cached snapshot must never be AHEAD of what CCPI declares it
 *             consumes (you cannot validate against a schema newer than your pin).
 *   - C ≤ K : CCPI's declared pin must never be AHEAD of the latest published
 *             kernel (you cannot pin a version that does not exist yet).
 *   Equality across all three (V = C = K) is the steady state.
 *
 * BOUNDED STALENESS ≤ 7 DAYS (§ 14.15.2)
 * --------------------------------------
 *   The vendored snapshot MAY lag the kernel latest, but only by ≤ 7 calendar
 *   days of kernel-publish age. Beyond 7 days this check REPORTS staleness (and,
 *   post-DR-049-flip, the CI workflow would open a bump PR — deferred action,
 *   see below). Staleness age is computed from the kernel's publish timestamp
 *   when available (kernel package.json mtime locally, or --kernel-published ISO
 *   date), else reported as "unknown-age" without firing.
 *
 * SOAK DISCIPLINE — ADVISORY BY DEFAULT (CRITICAL)
 * ------------------------------------------------
 *   The CCPI kernel pin tracks the latest published kernel (currently 0.9.0). This
 *   check is ORTHOGONAL to the advisory→blocking authority flip — it polices
 *   VERSION ORDERING + STALENESS, never validator authority. It must NOT, by
 *   existing or being added, change any validator's authority and it must NOT
 *   pressure a pin bump on its own.
 *
 *   Therefore: ADVISORY by default — it REPORTS and EXITS 0 even when the
 *   ordering is violated or the snapshot is stale. `--strict` flips it to exit
 *   non-zero on a real violation (for opt-in local enforcement only). It becomes
 *   BLOCKING in CI only when the DR-049 advisory→authoritative flip lands; until
 *   then the workflow runs with continue-on-error.
 *
 * EXISTENCE-GUARDED
 * -----------------
 *   Every input is optional. A missing kernel repo, missing vendored snapshot, or
 *   missing package pin produces a LOUD WARNING and a SKIPPED comparison — never a
 *   crash and (default) never a non-zero exit. The whole point is that this lands
 *   BEFORE CCPI materialises a .kernel-vendor/ snapshot and tolerates its absence.
 *
 * USAGE
 * -----
 *   node scripts/kernel-vendor-hash.mjs                 # advisory; auto-resolve sources
 *   node scripts/kernel-vendor-hash.mjs --strict        # exit 1 on a real V≤C≤K / staleness violation
 *   node scripts/kernel-vendor-hash.mjs --json          # machine report to stdout
 *   node scripts/kernel-vendor-hash.mjs --kernel-latest 0.6.0 --kernel-published 2026-06-09T00:00:00Z
 *
 * Beads: k8wo (kernel-vendor consistency model — version-coupling).
 */

import { readFileSync, existsSync, statSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..');

// Read-only kernel repo (sibling under the intent-eval-platform umbrella). Used to
// resolve K (kernel latest published) when running locally. Absent in CI → pass
// --kernel-latest or accept advisory-unknown.
const KERNEL_REPO_PKG = resolve(
  REPO_ROOT,
  '..',
  '..',
  'intent-eval-platform',
  'intent-eval-core',
  'package.json',
);

// V source #1 (preferred once it exists): the CCPI-side vendored snapshot index.
const VENDOR_INDEX = join(REPO_ROOT, '.kernel-vendor', 'authoring', 'v1', 'index.json');
// V source #2 (current reality): the installed kernel package in node_modules.
const INSTALLED_KERNEL_PKG = join(
  REPO_ROOT,
  'node_modules',
  '@intentsolutions',
  'core',
  'package.json',
);

const STALENESS_LIMIT_DAYS = 7;
const MS_PER_DAY = 24 * 60 * 60 * 1000;

function parseArgs(argv) {
  const out = { strict: false, json: false, kernelLatest: null, kernelPublished: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--strict') out.strict = true;
    else if (a === '--json') out.json = true;
    else if (a === '--kernel-latest') out.kernelLatest = argv[++i] ?? null;
    else if (a === '--kernel-published') out.kernelPublished = argv[++i] ?? null;
  }
  return out;
}

/** Minimal, dependency-free semver compare. Returns -1 / 0 / 1. Pre-release tags
 *  (e.g. "1.0.0-draft") are compared core-first, then a present pre-release sorts
 *  BEFORE the same core with no pre-release, per semver §11.
 *
 *  Exported so the version-ordering test corpus can exercise the SAME comparator
 *  the CLI uses (no logic fork). See scripts/kernel-vendor-hash.test.mjs. */
export function semverCompare(a, b) {
  const split = (v) => {
    const [core, pre = ''] = String(v).trim().replace(/^v/, '').split('-');
    const nums = core.split('.').map((n) => parseInt(n, 10) || 0);
    while (nums.length < 3) nums.push(0);
    return { nums, pre };
  };
  const x = split(a);
  const y = split(b);
  for (let i = 0; i < 3; i++) {
    if (x.nums[i] !== y.nums[i]) return x.nums[i] < y.nums[i] ? -1 : 1;
  }
  if (x.pre === y.pre) return 0;
  if (x.pre === '') return 1; // no pre-release > has pre-release
  if (y.pre === '') return -1;
  return x.pre < y.pre ? -1 : 1;
}

/** Read a `version` field from a package.json-shaped file. Returns null if absent. */
function readPkgVersion(path) {
  if (!existsSync(path)) return null;
  try {
    return JSON.parse(readFileSync(path, 'utf8')).version ?? null;
  } catch {
    return null;
  }
}

/** Resolve V — the vendored snapshot version. Prefer .kernel-vendor/ index, fall
 *  back to the installed kernel package. Reports which source was used. */
function resolveVendored() {
  if (existsSync(VENDOR_INDEX)) {
    try {
      const idx = JSON.parse(readFileSync(VENDOR_INDEX, 'utf8'));
      const v = idx.$schemaVersion ?? idx.version ?? null;
      if (v) return { version: v, source: '.kernel-vendor/authoring/v1/index.json' };
    } catch {
      /* fall through to installed-package fallback */
    }
  }
  const installed = readPkgVersion(INSTALLED_KERNEL_PKG);
  if (installed) {
    return { version: installed, source: 'node_modules/@intentsolutions/core (installed pin)' };
  }
  return { version: null, source: null };
}

/** Resolve C — the kernel version CCPI DECLARES it consumes (the exact package.json
 *  pin). Strips a leading ^/~/= since the pin is meant to be exact, but reports if
 *  a range operator was present (a soft warning, not a failure). */
function resolveDeclared() {
  const pkgPath = join(REPO_ROOT, 'package.json');
  if (!existsSync(pkgPath)) return { version: null, ranged: false };
  try {
    const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'));
    const raw =
      pkg.dependencies?.['@intentsolutions/core'] ??
      pkg.devDependencies?.['@intentsolutions/core'] ??
      null;
    if (!raw) return { version: null, ranged: false };
    const ranged = /^[\^~>=<]/.test(raw.trim());
    return { version: raw.trim().replace(/^[\^~>=<\s]+/, ''), ranged };
  } catch {
    return { version: null, ranged: false };
  }
}

/** Resolve K — the latest PUBLISHED kernel version. Priority: explicit arg, then
 *  the read-only sibling kernel repo's package.json. Returns version + publish age. */
function resolveKernelLatest(args) {
  if (args.kernelLatest) {
    return {
      version: args.kernelLatest,
      ageDays: ageFromIso(args.kernelPublished),
      source: '--kernel-latest',
    };
  }
  if (existsSync(KERNEL_REPO_PKG)) {
    const v = readPkgVersion(KERNEL_REPO_PKG);
    if (v) {
      let ageDays = ageFromIso(args.kernelPublished);
      if (ageDays === null) {
        try {
          ageDays = Math.floor((Date.now() - statSync(KERNEL_REPO_PKG).mtimeMs) / MS_PER_DAY);
        } catch {
          ageDays = null;
        }
      }
      return { version: v, ageDays, source: 'intent-eval-core/package.json (read-only sibling)' };
    }
  }
  return { version: null, ageDays: null, source: null };
}

function ageFromIso(iso) {
  if (!iso) return null;
  const t = Date.parse(iso);
  if (Number.isNaN(t)) return null;
  return Math.floor((Date.now() - t) / MS_PER_DAY);
}

/**
 * PURE comparator core — the V ≤ C ≤ K ordering invariant + bounded-staleness
 * evaluation, with no filesystem / process / clock dependency. The CLI (`main`)
 * resolves V/C/K from disk and passes them here; the version-ordering test corpus
 * (scripts/kernel-vendor-hash.test.mjs) drives this directly with synthetic
 * fixtures so the SAME logic is exercised end-to-end without a fork.
 *
 * @param {object} input
 * @param {string|null} input.V          vendored snapshot version (semver) or null/absent
 * @param {string|null} input.C          CCPI-declared kernel pin (semver) or null/absent
 * @param {string|null} input.K          kernel latest published (semver) or null/absent
 * @param {boolean}     [input.ranged]   whether C was declared with a range operator
 * @param {number|null} [input.kernelAgeDays] kernel publish age in days, or null if unknown
 * @param {number}      [input.stalenessLimitDays] day bound (defaults to STALENESS_LIMIT_DAYS)
 * @returns {{ violations: string[], warnings: string[], stale: boolean }}
 */
export function evaluateCoupling(input) {
  const {
    V = null,
    C = null,
    K = null,
    ranged = false,
    kernelAgeDays = null,
    stalenessLimitDays = STALENESS_LIMIT_DAYS,
  } = input ?? {};
  const warnings = [];
  const violations = [];

  // --- existence guards (loud warn, never crash) -----------------------------
  if (!V) {
    warnings.push(
      'V (vendored snapshot) UNRESOLVED: no .kernel-vendor/authoring/v1/index.json AND ' +
        'no installed @intentsolutions/core in node_modules. Run pnpm install, or materialise ' +
        'the .kernel-vendor/ snapshot per the spec. V≤C check SKIPPED.',
    );
  }
  if (!C) {
    warnings.push(
      'C (CCPI-declared kernel) UNRESOLVED: package.json has no @intentsolutions/core dependency. ' +
        'V≤C and C≤K checks SKIPPED.',
    );
  } else if (ranged) {
    warnings.push(
      `C pin "${C}" uses a RANGE operator. The kernel pin must be EXACT (no ^/~) per the ` +
        'shadow-validation pin discipline. Treating the floor as C for ordering.',
    );
  }
  if (!K) {
    warnings.push(
      'K (kernel latest published) UNRESOLVED: no --kernel-latest argument AND the read-only ' +
        'sibling intent-eval-core/package.json is not present. C≤K and staleness checks SKIPPED.',
    );
  }

  // --- ordering invariant V ≤ C ≤ K ------------------------------------------
  if (V && C && semverCompare(V, C) > 0) {
    violations.push(
      `ORDERING: V (${V}) > C (${C}) — vendored snapshot is AHEAD of the CCPI-declared pin.`,
    );
  }
  if (C && K && semverCompare(C, K) > 0) {
    violations.push(
      `ORDERING: C (${C}) > K (${K}) — CCPI pin is AHEAD of the latest published kernel.`,
    );
  }

  // --- bounded staleness ≤ N days --------------------------------------------
  let stale = false;
  if (V && K && semverCompare(V, K) < 0) {
    // The vendored snapshot lags the latest kernel. Only a >N-day lag is reported
    // as staleness (per § 14.15.2). Age comes from the kernel publish timestamp.
    if (kernelAgeDays === null) {
      warnings.push(
        `STALENESS: V (${V}) lags K (${K}) but kernel publish age is UNKNOWN ` +
          '(pass --kernel-published <ISO> for a precise age). Not firing staleness.',
      );
    } else if (kernelAgeDays > stalenessLimitDays) {
      stale = true;
      violations.push(
        `STALENESS: V (${V}) lags K (${K}) and the kernel has been published for ` +
          `${kernelAgeDays} days (> ${stalenessLimitDays}-day bound). ` +
          'DEFERRED ACTION (post-DR-049-flip): CI would open a kernel-bump PR here.',
      );
    } else {
      warnings.push(
        `STALENESS OK: V (${V}) lags K (${K}) by ${kernelAgeDays} day(s) ` +
          `(within the ${stalenessLimitDays}-day bound).`,
      );
    }
  }

  return { violations, warnings, stale };
}

function main() {
  const args = parseArgs(process.argv.slice(2));

  const vendored = resolveVendored();
  const declared = resolveDeclared();
  const kernel = resolveKernelLatest(args);
  // CCPI's own validator schema version — reported for context, NOT part of V≤C≤K.
  const ccpSchemaVersion = readCcpSchemaVersion();

  const V = vendored.version;
  const C = declared.version;
  const K = kernel.version;

  const { violations, warnings, stale } = evaluateCoupling({
    V,
    C,
    K,
    ranged: declared.ranged,
    kernelAgeDays: kernel.ageDays,
    stalenessLimitDays: STALENESS_LIMIT_DAYS,
  });

  const report = {
    schema: 'kernel-vendor-hash/v1',
    timestamp: new Date().toISOString(),
    identities: {
      V_vendored: { version: V, source: vendored.source },
      C_ccpDeclaredKernel: { version: C, ranged: declared.ranged },
      K_kernelLatest: { version: K, source: kernel.source, publishedAgeDays: kernel.ageDays },
      ccpSchemaVersion: { version: ccpSchemaVersion, note: 'context only — NOT part of V≤C≤K' },
    },
    orderingInvariant: 'V <= C <= K',
    stale,
    stalenessLimitDays: STALENESS_LIMIT_DAYS,
    violations,
    warnings,
    advisory: !args.strict,
    soak: 'DR-049 shadow soak — kernel pin tracks latest published (0.9.0); this check stays ADVISORY.',
  };

  // Persist a CI artifact alongside the shadow report.
  try {
    const outDir = join(REPO_ROOT, 'scripts', '.kernel-vendor-hash');
    mkdirSync(outDir, { recursive: true });
    writeFileSync(join(outDir, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  } catch {
    /* artifact write is best-effort; never fatal */
  }

  if (args.json) {
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  } else {
    printHuman(report);
  }

  // --- exit semantics --------------------------------------------------------
  // ADVISORY default: always exit 0. --strict: non-zero only on a REAL violation
  // (ordering or >7-day staleness). Warnings (unresolved inputs) never fail even
  // under --strict — absence is tolerated by design.
  if (args.strict && violations.length > 0) {
    process.exitCode = 1;
  }
}

function readCcpSchemaVersion() {
  const p = join(REPO_ROOT, 'scripts', 'validate-skills-schema.py');
  if (!existsSync(p)) return null;
  try {
    const m = readFileSync(p, 'utf8').match(/^SCHEMA_VERSION\s*=\s*["']([^"']+)["']/m);
    return m ? m[1] : null;
  } catch {
    return null;
  }
}

function printHuman(r) {
  const line = (s) => process.stdout.write(s + '\n');
  line('');
  line('━━━ kernel-vendor-hash — version-coupling consistency (ADVISORY) ━━━');
  line(
    `  V vendored snapshot     : ${r.identities.V_vendored.version ?? '(unresolved)'} ` +
      `${r.identities.V_vendored.source ? `[${r.identities.V_vendored.source}]` : ''}`,
  );
  line(
    `  C CCPI-declared kernel   : ${r.identities.C_ccpDeclaredKernel.version ?? '(unresolved)'}`,
  );
  line(
    `  K kernel latest         : ${r.identities.K_kernelLatest.version ?? '(unresolved)'} ` +
      `${r.identities.K_kernelLatest.publishedAgeDays != null ? `(${r.identities.K_kernelLatest.publishedAgeDays}d old)` : ''}`,
  );
  line(
    `  CCPI SCHEMA_VERSION      : ${r.identities.ccpSchemaVersion.version ?? '(unknown)'} (context only)`,
  );
  line(`  invariant               : V <= C <= K`);
  line('');
  for (const w of r.warnings) line(`  ⚠️  WARN: ${w}`);
  for (const v of r.violations) line(`  ❌ VIOLATION: ${v}`);
  if (r.violations.length === 0)
    line('  ✅ ordering + staleness OK (or skipped where inputs absent)');
  line('');
  line(`  mode: ${r.advisory ? 'ADVISORY (exit 0 regardless)' : 'STRICT (exit 1 on violation)'}`);
  line(`  ${r.soak}`);
  line('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  line('');
}

// Run main() ONLY when invoked directly as a CLI (node scripts/kernel-vendor-hash.mjs),
// never when imported as a module (the test corpus imports evaluateCoupling +
// semverCompare without triggering the disk-reading / process-exiting main()).
if (import.meta.url === pathToFileURL(process.argv[1] ?? '').href) {
  main();
}
