#!/usr/bin/env node
/**
 * check-stats-freshness.mjs — enforce the declared freshness bound on the
 * external stats artifacts (blueprint 727, Epic 1 bead 1.10).
 *
 * WHY THIS EXISTS
 * ---------------
 * The three external stats artifacts (GitHub stars, npm downloads, skills.sh
 * installs) are snapshots of systems this repo does not control. Every other
 * number on the marketplace is regenerated at build time from the corpus and
 * cannot rot; these three CAN — the fetch scripts deliberately fail soft, and
 * the daily refresh lands via an automation PR that a human must merge. Before
 * this gate existed, main's copies silently drifted 16–20 days stale while the
 * homepage rendered them as current.
 *
 * THE CONTRACT
 * ------------
 * Each artifact must declare its own bound:
 *   { "generatedAt": "<ISO-8601>", "max_age_hours": <positive number>, ... }
 *
 * A missing file, missing/malformed declaration, or an age over the bound is a
 * loud failure (exit 1) naming every violation. The bound lives IN the
 * artifact, not in this script, so a future artifact with a different refresh
 * cadence declares its own tolerance and this checker needs no edit.
 *
 * MODES
 * -----
 *   default        exit 1 on any violation (wired into the daily stats
 *                  workflow after the fetch steps — catches upstream API rot
 *                  that fail-soft fetches would otherwise hide forever)
 *   --report       age breaches are advisory (a stale artifact is a
 *                  time-based condition unrelated to a PR's content, and must
 *                  not spontaneously block unrelated merges), but STRUCTURAL
 *                  violations — unreadable artifact, missing generatedAt or
 *                  max_age_hours — still exit 1, because those are
 *                  content-based and deterministic. Wired into PR CI and
 *                  before the daily fetch steps.
 *   --now=<ISO>    clock override for deterministic tests
 *
 * The render-side protection is separate: marketplace/src/pages/index.astro
 * treats an out-of-bound artifact exactly like a missing one, so the site
 * never renders a stale number as current even if this gate is bypassed.
 */

import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const DATA_DIR = join(REPO_ROOT, 'marketplace', 'src', 'data');

/** The governed artifact set. Adding an external snapshot? Register it here. */
export const STATS_ARTIFACTS = ['github-stats.json', 'npm-stats.json', 'skills-stats.json'];

/**
 * Evaluate one artifact object against its own declared bound.
 * Returns null when fresh, or { kind: 'structural' | 'stale', message }.
 * Structural violations are content-based (deterministic in PR CI); stale
 * violations are time-based (advisory in --report mode).
 */
export function evaluateFreshness(name, data, nowMs) {
  if (data === null || typeof data !== 'object') {
    return { kind: 'structural', message: `${name}: artifact is not a JSON object` };
  }
  const { generatedAt, max_age_hours: maxAgeHours } = data;
  if (typeof generatedAt !== 'string' || Number.isNaN(Date.parse(generatedAt))) {
    return {
      kind: 'structural',
      message: `${name}: missing or unparseable generatedAt (${JSON.stringify(generatedAt)})`,
    };
  }
  if (typeof maxAgeHours !== 'number' || !Number.isFinite(maxAgeHours) || maxAgeHours <= 0) {
    return {
      kind: 'structural',
      message: `${name}: missing or invalid max_age_hours (${JSON.stringify(maxAgeHours)}) — every external stats artifact must declare its freshness bound`,
    };
  }
  const ageHours = (nowMs - Date.parse(generatedAt)) / 3_600_000;
  // A future generatedAt would make the age negative and sail through the
  // one-sided maximum check. Runner clocks can skew a little, so allow 15
  // minutes; anything further ahead is a bad write, not a fresh one.
  if (ageHours < -0.25) {
    return {
      kind: 'structural',
      message: `${name}: generatedAt is ${(-ageHours).toFixed(1)}h in the future (${generatedAt}) — a snapshot cannot postdate the clock checking it`,
    };
  }
  if (ageHours > maxAgeHours) {
    return {
      kind: 'stale',
      message: `${name}: STALE — generated ${ageHours.toFixed(1)}h ago, bound is ${maxAgeHours}h (generatedAt ${generatedAt})`,
    };
  }
  return null;
}

export function checkAll(nowMs, dataDir = DATA_DIR) {
  const violations = [];
  const fresh = [];
  for (const name of STATS_ARTIFACTS) {
    let data;
    try {
      data = JSON.parse(readFileSync(join(dataDir, name), 'utf8'));
    } catch (err) {
      violations.push({ kind: 'structural', message: `${name}: unreadable (${err.message})` });
      continue;
    }
    const violation = evaluateFreshness(name, data, nowMs);
    if (violation) violations.push(violation);
    else {
      const ageHours = (nowMs - Date.parse(data.generatedAt)) / 3_600_000;
      fresh.push(`${name}: fresh (${ageHours.toFixed(1)}h old, bound ${data.max_age_hours}h)`);
    }
  }
  return { violations, fresh };
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  const args = process.argv.slice(2);
  const report = args.includes('--report');
  const nowArg = args.find((a) => a.startsWith('--now='));
  const nowMs = nowArg ? Date.parse(nowArg.slice('--now='.length)) : Date.now();
  if (Number.isNaN(nowMs)) {
    console.error('stats-freshness: unparseable --now value');
    process.exit(2);
  }

  const { violations, fresh } = checkAll(nowMs);
  for (const line of fresh) console.log(`stats-freshness: ${line}`);
  for (const v of violations)
    console.error(`stats-freshness: VIOLATION (${v.kind}) — ${v.message}`);

  const structural = violations.filter((v) => v.kind === 'structural');
  const fatal = report ? structural : violations;
  if (fatal.length > 0) {
    console.error(
      `stats-freshness: FAIL — ${fatal.length} enforced violation(s). ` +
        'Merge the daily automation/npm-stats PR, or investigate the fetch scripts if the refresh itself is failing.',
    );
    process.exit(1);
  }
  if (violations.length > 0) {
    console.error('stats-freshness: report mode — stale ages above are advisory for this run.');
  }
  console.log(
    `stats-freshness: OK (${fresh.length}/${STATS_ARTIFACTS.length} fresh${report ? ', report mode' : ''})`,
  );
}
