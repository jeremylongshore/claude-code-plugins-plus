#!/usr/bin/env node
// check-structural-ratchet.mjs — Blueprint 727 E8 structural-debt boundary.
//
// The canonical validator owns classification. This gate pins editable,
// first-party missing-required-frontmatter records by count, sorted-set hash,
// and members. Growth and equal-count swaps fail. Provenance-marked mirror
// findings are not "fixed" locally: every affected skill must instead have a
// QUARANTINE row in the disposition ledger.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BASELINE = resolve(ROOT, 'scripts/structural-ratchet-baseline.json');
const LEDGER = resolve(ROOT, 'freshie/disposition-ledger.json');
const WRITE = process.argv.includes('--write');
const REQUIRED_CLASS = 'first_party_missing_required_frontmatter';

const sha = (items) => createHash('sha256').update(items.join('\n')).digest('hex');

function collectMetrics() {
  const output = execFileSync(
    'python3',
    ['scripts/validate-skills-schema.py', '--structural-metrics'],
    { cwd: ROOT, encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
  );
  return JSON.parse(output);
}

function skillPath(member) {
  const separator = member.lastIndexOf('::');
  if (separator <= 0 || separator === member.length - 2) {
    throw new Error(`structural-ratchet: malformed validator member: ${member}`);
  }
  return member.slice(0, separator);
}

export function validateBaseline(baseline) {
  const failures = [];
  if (!baseline || typeof baseline !== 'object' || typeof baseline.schema_version !== 'string') {
    failures.push('baseline must declare a string schema_version');
    return failures;
  }
  if (!baseline.classes || typeof baseline.classes !== 'object') {
    failures.push('baseline must declare classes');
    return failures;
  }
  if (!Object.hasOwn(baseline.classes, REQUIRED_CLASS)) {
    failures.push(`baseline is missing required class ${REQUIRED_CLASS}`);
  }
  for (const [name, entry] of Object.entries(baseline.classes)) {
    if (!Number.isInteger(entry?.count) || entry.count < 0 || !Array.isArray(entry.members)) {
      failures.push(`${name}: baseline count/members are malformed`);
      continue;
    }
    if (entry.members.length !== entry.count) {
      failures.push(`${name}: baseline member length does not equal count`);
    }
    if (entry.set_sha256 !== sha(entry.members)) {
      failures.push(`${name}: baseline set_sha256 does not match members`);
    }
    if (name === REQUIRED_CLASS && entry.count !== 0) {
      failures.push(`${name}: the achieved zero target may not be raised`);
    }
  }
  return failures;
}

export function compare(baseline, current) {
  const failures = validateBaseline(baseline);
  if (baseline.schema_version !== current.schema_version) {
    failures.push(
      `schema version changed ${baseline.schema_version} → ${current.schema_version}; review and re-pin`,
    );
  }
  for (const [name, baseEntry] of Object.entries(baseline.classes ?? {})) {
    const nowMembers = current[name];
    if (!Array.isArray(nowMembers)) {
      failures.push(`${name}: current validator metrics must be an array`);
      continue;
    }
    const baseSet = new Set(baseEntry.members ?? []);
    if (nowMembers.length > baseEntry.count) {
      failures.push(
        `${name}: count grew ${baseEntry.count} → ${nowMembers.length} (monotone non-increasing)`,
      );
    }
    const newcomers = nowMembers.filter((member) => !baseSet.has(member));
    if (newcomers.length > 0) {
      failures.push(
        `${name}: ${newcomers.length} member(s) not in the baseline (a swap is new debt): ${newcomers
          .slice(0, 5)
          .join(' | ')}`,
      );
    }
  }
  return failures;
}

export function checkMirrorDisposition(members, ledger) {
  const rows = new Map((ledger?.artifacts ?? []).map((row) => [row.path, row]));
  const paths = [...new Set(members.map(skillPath))].sort();
  const failures = [];
  for (const path of paths) {
    const row = rows.get(path);
    if (!row) {
      failures.push(`${path}: mirror finding is absent from the disposition ledger`);
    } else if (row.disposition !== 'QUARANTINE') {
      failures.push(
        `${path}: mirror finding must be QUARANTINE, found ${row.disposition ?? '(missing)'}`,
      );
    }
  }
  return { failures, paths };
}

function main() {
  const metrics = collectMetrics();
  const classMembers = metrics.first_party_missing_required_frontmatter;
  const mirrorMembers = metrics.mirror_missing_required_frontmatter;
  if (!Array.isArray(classMembers) || !Array.isArray(mirrorMembers)) {
    console.error('structural-ratchet: FAIL — canonical validator omitted a required metric array');
    process.exit(1);
  }
  const ledger = JSON.parse(readFileSync(LEDGER, 'utf8'));
  const mirrorCheck = checkMirrorDisposition(mirrorMembers, ledger);
  if (mirrorCheck.failures.length > 0) {
    for (const failure of mirrorCheck.failures) {
      console.error(`structural-ratchet: FAIL — ${failure}`);
    }
    process.exit(1);
  }

  if (WRITE) {
    if (classMembers.length !== 0) {
      console.error(
        `structural-ratchet: FAIL — refusing to write a nonzero first-party baseline (${classMembers.length})`,
      );
      process.exit(1);
    }
    const pinned = {
      $comment:
        'E8 structural-ratchet baseline. Regenerate ONLY via `node scripts/check-structural-ratchet.mjs --write` in the PR that shrinks editable first-party debt. Mirror records are never edited; the gate requires their ledger disposition to remain QUARANTINE.',
      pinned_at: new Date().toISOString().slice(0, 10),
      schema_version: metrics.schema_version,
      historical_reconciliation: {
        blueprint_base: '478aaf17731714fed9b1779284de6a5b3729ef6e',
        missing_required_frontmatter_records: 728,
        first_party_records: 1,
        mirror_records: 727,
      },
      classes: {
        first_party_missing_required_frontmatter: {
          count: classMembers.length,
          set_sha256: sha(classMembers),
          members: classMembers,
        },
      },
    };
    writeFileSync(BASELINE, `${JSON.stringify(pinned, null, 2)}\n`);
    console.log(
      `structural-ratchet: baseline written (first_party_missing_required_frontmatter=${classMembers.length}; ${mirrorMembers.length} mirror records quarantined)`,
    );
    return;
  }

  const baseline = JSON.parse(readFileSync(BASELINE, 'utf8'));
  const failures = compare(baseline, metrics);
  if (failures.length > 0) {
    for (const failure of failures) console.error(`structural-ratchet: FAIL — ${failure}`);
    console.error(
      'structural-ratchet: fix first-party debt; mirror-owned files have no local-edit or waiver path',
    );
    process.exit(1);
  }

  const baselineCount = baseline.classes.first_party_missing_required_frontmatter.count;
  if (classMembers.length < baselineCount) {
    console.log(
      `structural-ratchet: OK — first-party debt SHRANK (${baselineCount} → ${classMembers.length}); lock it in with --write`,
    );
    return;
  }
  console.log(
    `structural-ratchet: OK (first-party missing-required-frontmatter=${classMembers.length}; ` +
      `${mirrorMembers.length} mirror records across ${mirrorCheck.paths.length} quarantined skills; ` +
      `schema ${baseline.schema_version})`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
