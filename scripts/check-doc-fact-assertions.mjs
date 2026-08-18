#!/usr/bin/env node
/**
 * check-doc-fact-assertions.mjs — keep the two most rot-prone documented facts
 * mechanically equal to the code (blueprint 727, Epic 2 beads 2.7 and 2.8).
 *
 * WHY THIS EXISTS
 * ---------------
 * E2.6 corrected a governing-doc corpus in which GOVERNANCE.md stated the
 * merge gate as two required contexts (actual: three), the reviewer guide
 * told triagers 19 gate jobs (actual: 21), and three surfaces disagreed about
 * the validator schema version. Corrections rot without assertions; these two
 * facts have rotted before and are cheap to pin.
 *
 * ASSERTION 1 (E2.7) — the ci-required contract:
 *   - CLAUDE.md's enumerated gate-job list ("needs: all N gate jobs (a, b,
 *     ...)") must equal the actual `needs:` block of the ci-required job in
 *     .github/workflows/validate-plugins.yml — same count, same names.
 *   - CLAUDE.md and GOVERNANCE.md must each name all three required
 *     branch-protection contexts (ci-required, gitleaks, skill-conform)
 *     — the regression guard for the two-contexts understatement.
 *
 * ASSERTION 2 (E2.8) — the schema version:
 *   - scripts/validate-skills-schema.py's SCHEMA_VERSION is the authority.
 *   - CLAUDE.md's "(schema X.Y.Z" reference, 6767-b's "CURRENT SCHEMA: X.Y.Z"
 *     banner, and SCHEMA_CHANGELOG.md's newest "## [X.Y.Z]" entry must all
 *     equal it.
 *
 * Historical version strings inside dated changelog entries or record-class
 * docs are deliberately NOT scanned — only the live claim surfaces above.
 */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');

const read = (p) => readFileSync(join(REPO_ROOT, p), 'utf8');

/** The actual gate list: ci-required's needs in the workflow. */
export function actualCiRequiredNeeds(workflowText) {
  const wf = yaml.load(workflowText);
  const needs = wf?.jobs?.['ci-required']?.needs;
  if (!Array.isArray(needs) || needs.length === 0) {
    throw new Error('validate-plugins.yml: ci-required job has no needs array');
  }
  return needs.map(String);
}

/** CLAUDE.md's enumerated claim: "`needs:` all N gate jobs (a, b, c...)". */
export function documentedCiRequiredClaim(claudeText) {
  const m = claudeText.match(/`needs:`\s+all\s+(\d+)\s+gate jobs\s*\(([^)]+)\)/);
  if (!m) {
    throw new Error(
      'CLAUDE.md: could not find the "`needs:` all N gate jobs (…)" enumeration — the assertion anchor moved',
    );
  }
  return {
    count: Number(m[1]),
    names: m[2]
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean),
  };
}

export function compareCiRequired(claim, actual) {
  const problems = [];
  if (claim.count !== actual.length) {
    problems.push(`documented count ${claim.count} != actual needs length ${actual.length}`);
  }
  const claimSet = new Set(claim.names);
  const actualSet = new Set(actual);
  for (const n of actual) if (!claimSet.has(n)) problems.push(`missing from prose: ${n}`);
  for (const n of claim.names)
    if (!actualSet.has(n)) problems.push(`prose names unknown job: ${n}`);
  return problems;
}

const REQUIRED_CONTEXTS = ['ci-required', 'gitleaks', 'skill-conform'];

export function missingContexts(text) {
  return REQUIRED_CONTEXTS.filter((c) => !text.includes(c));
}

/** The authority: SCHEMA_VERSION in the validator. */
export function validatorSchemaVersion(pyText) {
  const m = pyText.match(/^SCHEMA_VERSION\s*=\s*"(\d+\.\d+\.\d+)"/m);
  if (!m) throw new Error('validate-skills-schema.py: SCHEMA_VERSION literal not found');
  return m[1];
}

export function schemaClaims({ claudeText, specText, changelogText }) {
  const claims = [];
  const claude = claudeText.match(/\(schema (\d+\.\d+\.\d+)/);
  if (claude) claims.push({ surface: 'CLAUDE.md "(schema …)"', version: claude[1] });
  else claims.push({ surface: 'CLAUDE.md "(schema …)"', version: null });
  const spec = specText.match(/CURRENT SCHEMA:\s*(\d+\.\d+\.\d+)/);
  claims.push({ surface: '6767-b banner "CURRENT SCHEMA"', version: spec ? spec[1] : null });
  const changelog = changelogText.match(/^## \[(\d+\.\d+\.\d+)\]/m);
  claims.push({
    surface: 'SCHEMA_CHANGELOG newest entry',
    version: changelog ? changelog[1] : null,
  });
  return claims;
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  const violations = [];

  // E2.7 — ci-required contract
  try {
    const actual = actualCiRequiredNeeds(read('.github/workflows/validate-plugins.yml'));
    const claudeText = read('CLAUDE.md');
    const claim = documentedCiRequiredClaim(claudeText);
    for (const p of compareCiRequired(claim, actual)) violations.push(`ci-required prose: ${p}`);
    for (const c of missingContexts(claudeText))
      violations.push(`CLAUDE.md never names required context "${c}"`);
    for (const c of missingContexts(read('GOVERNANCE.md')))
      violations.push(`GOVERNANCE.md never names required context "${c}"`);
  } catch (err) {
    violations.push(err.message);
  }

  // E2.8 — schema version
  try {
    const authority = validatorSchemaVersion(read('scripts/validate-skills-schema.py'));
    const claims = schemaClaims({
      claudeText: read('CLAUDE.md'),
      specText: read('000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md'),
      changelogText: read('000-docs/SCHEMA_CHANGELOG.md'),
    });
    for (const { surface, version } of claims) {
      if (version === null) violations.push(`${surface}: claim surface not found — anchor moved`);
      else if (version !== authority)
        violations.push(`${surface}: states ${version}, validator SCHEMA_VERSION is ${authority}`);
    }
  } catch (err) {
    violations.push(err.message);
  }

  for (const v of violations) console.error(`doc-fact-assertions: VIOLATION — ${v}`);
  if (violations.length > 0) {
    console.error(`doc-fact-assertions: FAIL — ${violations.length} violation(s).`);
    process.exit(1);
  }
  console.log(
    'doc-fact-assertions: OK (ci-required prose == workflow; schema claims == SCHEMA_VERSION)',
  );
}
