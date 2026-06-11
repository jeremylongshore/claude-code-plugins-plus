#!/usr/bin/env node
/**
 * kernel-shadow-validation.mjs — DR-049 dual-validator shadow mode (ADVISORY ONLY)
 *
 * Consumer-cutover STEP 1 for @intentsolutions/core (the Spec Authority Kernel).
 *
 * WHAT THIS IS
 * ------------
 * Runs the kernel's published machine-spec — the authoring/v1 `skill-frontmatter`
 * JSON Schema from @intentsolutions/core@0.4.0 — over the SAME SKILL.md corpus the
 * existing prose-spec validator (scripts/validate-skills-schema.py) already grades,
 * and reports the per-file AGREE / DISAGREE rate between the two.
 *
 * This is a SHADOW. It NEVER gates, NEVER mutates, NEVER replaces the existing
 * validator. It compares two independent encodings of the SAME contract:
 *
 *   - prose-spec  : the 5,100-line validate-skills-schema.py, MARKETPLACE tier
 *                   (the IS 8-field required set is an ERROR-on-missing there).
 *   - machine-spec: @intentsolutions/core schemas/authoring/v1/skill-frontmatter.schema.json
 *                   (pure allOf composition of upstream-base + universalFolds + is-overlay;
 *                    encodes the SAME IS 8-field required set).
 *
 * The two are deliberately tier-matched: both require the 8-field marketplace set
 * {name, description, allowed-tools, version, author, license, compatibility, tags}.
 * A near-zero deviation rate is the "zero-on-corpus shadow signal" from DR-049 — it
 * means the machine-spec faithfully reproduces the prose-spec's marketplace verdict,
 * which is the precondition for any future blocking cutover (NOT this PR).
 *
 * VERDICT DEFINITION (per file)
 * -----------------------------
 *   existing-PASS  := validate-skills-schema.py --marketplace --json reports errors == 0
 *                     (a `fatal` entry counts as existing-FAIL).
 *   kernel-PASS    := ajv validate against the composed skill-frontmatter schema == true.
 *   AGREE          := existing-PASS === kernel-PASS.
 *   DISAGREE       := otherwise (the file the shadow flags as a deviation).
 *
 * OUTPUT
 * ------
 *   - Human summary + DISAGREE listing to stdout.
 *   - Machine report JSON to scripts/.kernel-shadow/report.json (CI artifact).
 *   - GitHub Step Summary markdown when $GITHUB_STEP_SUMMARY is set.
 *
 * EXIT CODE
 * ---------
 *   Always 0 on a successful run (advisory). A non-zero exit only happens on a
 *   harness error (e.g. the kernel package or the existing validator is missing) —
 *   and even then the calling workflow uses continue-on-error so it can NEVER fail
 *   the build. The deviation rate itself is REPORTED, never enforced.
 *
 * KERNEL PIN: @intentsolutions/core is pinned EXACTLY to 0.4.0 in package.json
 * (no ^/~). This shadow reads the schema straight out of node_modules so the
 * comparison is always against the pinned, published contract.
 *
 * Beads: bd_000-projects-26ef (dual-validator shadow mode).
 */

import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

import Ajv2020 from 'ajv/dist/2020.js';
import addFormats from 'ajv-formats';
import yaml from 'js-yaml';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, '..');
const KERNEL_PIN = '0.4.0';

const SCHEMA_DIR = join(
  REPO_ROOT,
  'node_modules',
  '@intentsolutions',
  'core',
  'schemas',
  'authoring',
  'v1',
);

// The composed skill-frontmatter contract is a pure allOf of three $ref'd layers.
// ajv resolves $ref by $id, so every layer must be registered. marketplace-tier
// supplies the universalFolds $def the composition references.
const SCHEMA_FILES = [
  'upstream-base/skill-frontmatter.v1.json',
  'is-overlay/skill-frontmatter.v1.json',
  'marketplace-tier.schema.json',
  'skill-frontmatter.schema.json', // the composition (validated against)
];

const COMPOSED_SCHEMA_ID =
  'https://github.com/jeremylongshore/intent-eval-core/schemas/authoring/v1/skill-frontmatter.schema.json';

const FRONTMATTER_RE = /^---\s*\n([\s\S]*?)\n---\s*\n/;

function die(msg) {
  console.error(`[kernel-shadow] HARNESS ERROR: ${msg}`);
  process.exit(1);
}

function loadKernelVersion() {
  const pkgPath = join(REPO_ROOT, 'node_modules', '@intentsolutions', 'core', 'package.json');
  if (!existsSync(pkgPath)) {
    die(
      `@intentsolutions/core not installed at ${pkgPath}. Run: pnpm install --filter claude-code-plugins-monorepo`,
    );
  }
  const v = JSON.parse(readFileSync(pkgPath, 'utf8')).version;
  if (v !== KERNEL_PIN) {
    die(
      `kernel version drift: expected EXACTLY ${KERNEL_PIN} (the pinned contract), found ${v}. ` +
        `package.json must pin @intentsolutions/core to an exact version, never a range.`,
    );
  }
  return v;
}

function buildKernelValidator() {
  const ajv = new Ajv2020({ allErrors: true, strict: false });
  addFormats(ajv);
  for (const rel of SCHEMA_FILES) {
    const p = join(SCHEMA_DIR, rel);
    if (!existsSync(p)) {
      die(`kernel schema layer missing: ${p}. Is @intentsolutions/core@${KERNEL_PIN} intact?`);
    }
    ajv.addSchema(JSON.parse(readFileSync(p, 'utf8')));
  }
  const validate = ajv.getSchema(COMPOSED_SCHEMA_ID);
  if (!validate) {
    die(`could not resolve composed schema by $id ${COMPOSED_SCHEMA_ID}`);
  }
  return validate;
}

/**
 * Drive the existing prose-spec validator to get its per-file MARKETPLACE verdict.
 * Returns Map<absPath, { pass: boolean, errors: number, fatal: boolean }>.
 */
function loadExistingVerdicts() {
  // Prefer the venv interpreter (the validator needs pyyaml). Fall back to python3.
  const venvPy = join(REPO_ROOT, '.venv', 'bin', 'python3');
  const py = existsSync(venvPy) ? venvPy : 'python3';
  const script = join(REPO_ROOT, 'scripts', 'validate-skills-schema.py');
  if (!existsSync(script)) {
    die(`existing validator not found at ${script}`);
  }
  const res = spawnSync(py, [script, '--marketplace', '--json'], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    maxBuffer: 256 * 1024 * 1024,
  });
  if (res.error) {
    die(`failed to spawn existing validator: ${res.error.message}`);
  }
  // The validator may exit non-zero on findings; --json still emits the array on stdout.
  let parsed;
  try {
    parsed = JSON.parse(res.stdout);
  } catch {
    die(
      `could not parse existing validator --json output (exit ${res.status}). ` +
        `stderr head: ${(res.stderr || '').slice(0, 400)}`,
    );
  }
  const map = new Map();
  for (const entry of parsed) {
    const abs = resolve(REPO_ROOT, entry.path);
    if ('fatal' in entry) {
      map.set(abs, { pass: false, errors: 0, fatal: true });
    } else {
      const errors = entry.errors ?? 0;
      map.set(abs, { pass: errors === 0, errors, fatal: false });
    }
  }
  return map;
}

function parseFrontmatter(absPath) {
  let content;
  try {
    content = readFileSync(absPath, 'utf8');
  } catch (e) {
    return { ok: false, reason: `unreadable: ${e.message}` };
  }
  const m = FRONTMATTER_RE.exec(content);
  if (!m) {
    return { ok: false, reason: 'no YAML frontmatter block' };
  }
  let data;
  try {
    data = yaml.load(m[1]);
  } catch (e) {
    return { ok: false, reason: `YAML parse error: ${e.message}` };
  }
  if (data === null || typeof data !== 'object' || Array.isArray(data)) {
    return { ok: false, reason: 'frontmatter is not a mapping' };
  }
  return { ok: true, data };
}

function relTo(absPath) {
  return absPath.startsWith(REPO_ROOT + '/') ? absPath.slice(REPO_ROOT.length + 1) : absPath;
}

function main() {
  const kernelVersion = loadKernelVersion();
  const validateKernel = buildKernelValidator();
  const existing = loadExistingVerdicts();

  let total = 0;
  let agree = 0;
  const disagreements = [];
  let kernelParseFailures = 0;

  for (const [absPath, ex] of existing.entries()) {
    total += 1;
    const fm = parseFrontmatter(absPath);

    let kernelPass;
    let kernelErrors = [];
    if (!fm.ok) {
      // The kernel schema cannot validate a file with no parseable frontmatter
      // mapping; treat as kernel-FAIL (matches the prose-spec's fatal handling).
      kernelPass = false;
      kernelErrors = [{ instancePath: '', message: fm.reason }];
      kernelParseFailures += 1;
    } else {
      kernelPass = validateKernel(fm.data) === true;
      if (!kernelPass) {
        kernelErrors = (validateKernel.errors || []).map((e) => ({
          instancePath: e.instancePath,
          message: e.message,
          params: e.params,
        }));
      }
    }

    if (ex.pass === kernelPass) {
      agree += 1;
    } else {
      disagreements.push({
        path: relTo(absPath),
        existing: ex.pass ? 'PASS' : ex.fatal ? 'FATAL' : 'FAIL',
        existingErrorCount: ex.errors,
        kernel: kernelPass ? 'PASS' : 'FAIL',
        kernelErrors: kernelErrors.slice(0, 6),
        direction: ex.pass ? 'existing-PASS / kernel-FAIL' : 'existing-FAIL / kernel-PASS',
      });
    }
  }

  const disagree = disagreements.length;
  const rate = total === 0 ? 0 : (disagree / total) * 100;
  const rateStr = rate.toFixed(2);

  // Direction breakdown
  const existingPassKernelFail = disagreements.filter(
    (d) => d.direction === 'existing-PASS / kernel-FAIL',
  ).length;
  const existingFailKernelPass = disagreements.filter(
    (d) => d.direction === 'existing-FAIL / kernel-PASS',
  ).length;

  const report = {
    mode: 'shadow-advisory',
    blocking: false,
    kernelPackage: '@intentsolutions/core',
    kernelVersion,
    kernelPin: KERNEL_PIN,
    comparedAgainst: 'scripts/validate-skills-schema.py --marketplace --json',
    composedSchema: COMPOSED_SCHEMA_ID,
    totals: {
      files: total,
      agree,
      disagree,
      deviationRatePct: Number(rateStr),
      kernelUnparseableFrontmatter: kernelParseFailures,
    },
    directionBreakdown: {
      'existing-PASS / kernel-FAIL': existingPassKernelFail,
      'existing-FAIL / kernel-PASS': existingFailKernelPass,
    },
    disagreements,
    generatedAt: new Date().toISOString(),
  };

  const outDir = join(REPO_ROOT, 'scripts', '.kernel-shadow');
  mkdirSync(outDir, { recursive: true });
  const outPath = join(outDir, 'report.json');
  writeFileSync(outPath, JSON.stringify(report, null, 2) + '\n');

  // ---- Human console summary ----
  console.log('');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log('  KERNEL SHADOW VALIDATION (advisory · non-blocking · DR-049)');
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`  kernel        : @intentsolutions/core@${kernelVersion} (pinned ${KERNEL_PIN})`);
  console.log('  prose-spec    : validate-skills-schema.py --marketplace --json');
  console.log('  machine-spec  : authoring/v1 skill-frontmatter.schema.json (composed)');
  console.log('  ───────────────────────────────────────────────────────────');
  console.log(`  corpus files  : ${total}`);
  console.log(`  AGREE         : ${agree}`);
  console.log(`  DISAGREE      : ${disagree}`);
  console.log(`  DEVIATION RATE: ${rateStr}%`);
  console.log(`     existing-PASS / kernel-FAIL : ${existingPassKernelFail}`);
  console.log(`     existing-FAIL / kernel-PASS : ${existingFailKernelPass}`);
  console.log('  ───────────────────────────────────────────────────────────');

  if (disagree > 0) {
    const shown = disagreements.slice(0, 40);
    console.log(`  Disagreeing files (showing ${shown.length} of ${disagree}):`);
    for (const d of shown) {
      const k0 = d.kernelErrors[0];
      const why = k0 ? `${k0.instancePath || '/'} ${k0.message}` : '';
      console.log(`    [${d.direction}] ${d.path}  ${why}`);
    }
    if (disagree > shown.length) {
      console.log(`    … and ${disagree - shown.length} more (see ${relTo(outPath)})`);
    }
  } else {
    console.log('  Zero deviations — machine-spec reproduces the prose-spec verdict.');
  }
  console.log('═══════════════════════════════════════════════════════════════');
  console.log(`  Full machine report: ${relTo(outPath)}`);
  console.log('  ADVISORY ONLY — this run never fails CI or blocks a PR.');
  console.log('');

  // ---- GitHub Step Summary ----
  if (process.env.GITHUB_STEP_SUMMARY) {
    const lines = [];
    lines.push('## Kernel shadow validation (advisory · non-blocking)');
    lines.push('');
    lines.push(
      'Dual-validator shadow per DR-049. The kernel machine-spec ' +
        `(\`@intentsolutions/core@${kernelVersion}\`, pinned \`${KERNEL_PIN}\`) is run over the ` +
        'same SKILL.md corpus the existing prose-spec validator grades, at **marketplace tier**, ' +
        'and the per-file PASS/FAIL verdicts are compared. **This gate is advisory — it can never ' +
        'fail the build or block a PR.**',
    );
    lines.push('');
    lines.push('| metric | value |');
    lines.push('| --- | --- |');
    lines.push(`| corpus files | ${total} |`);
    lines.push(`| AGREE | ${agree} |`);
    lines.push(`| DISAGREE | ${disagree} |`);
    lines.push(`| **deviation rate** | **${rateStr}%** |`);
    lines.push(`| existing-PASS / kernel-FAIL | ${existingPassKernelFail} |`);
    lines.push(`| existing-FAIL / kernel-PASS | ${existingFailKernelPass} |`);
    lines.push('');
    if (disagree > 0) {
      lines.push('<details><summary>Disagreeing files (first 40)</summary>');
      lines.push('');
      lines.push('| direction | file | first kernel error |');
      lines.push('| --- | --- | --- |');
      for (const d of disagreements.slice(0, 40)) {
        const k0 = d.kernelErrors[0];
        const why = k0 ? `\`${k0.instancePath || '/'}\` ${k0.message}` : '';
        lines.push(`| ${d.direction} | \`${d.path}\` | ${why} |`);
      }
      lines.push('');
      lines.push('</details>');
    } else {
      lines.push(
        'Zero deviations — the machine-spec reproduces the prose-spec verdict on the corpus.',
      );
    }
    lines.push('');
    try {
      writeFileSync(process.env.GITHUB_STEP_SUMMARY, lines.join('\n') + '\n', { flag: 'a' });
    } catch (e) {
      console.error(`[kernel-shadow] could not write step summary: ${e.message}`);
    }
  }

  // Advisory: always succeed on a completed run.
  process.exit(0);
}

main();
