import { test } from 'node:test';
import { deepEqual, equal, match, ok } from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { checkMirrorDisposition, compare, validateBaseline } from './check-structural-ratchet.mjs';

const digest = (members) => createHash('sha256').update(members.join('\n')).digest('hex');
const baselineOf = (members = []) => ({
  schema_version: '4.1.0',
  classes: {
    first_party_missing_required_frontmatter: {
      count: members.length,
      set_sha256: digest(members),
      members,
    },
  },
});
const currentOf = (members = []) => ({
  schema_version: '4.1.0',
  first_party_missing_required_frontmatter: members,
});

test('the achieved zero first-party target passes', () => {
  deepEqual(compare(baselineOf([]), currentOf([])), []);
});

test('growth and an equal-count swap fail', () => {
  const growth = compare(baselineOf([]), currentOf(['a/SKILL.md::tags']));
  equal(growth.length, 2);
  match(growth[0], /count grew 0 → 1/);
  const swap = compare(baselineOf(['a/SKILL.md::tags']), currentOf(['b/SKILL.md::tags']));
  ok(swap.some((failure) => /zero target may not be raised/.test(failure)));
  ok(swap.some((failure) => /swap is new debt/.test(failure)));
});

test('schema drift and a corrupt baseline fail closed', () => {
  const baseline = baselineOf([]);
  baseline.classes.first_party_missing_required_frontmatter.set_sha256 = '0'.repeat(64);
  ok(validateBaseline(baseline).some((failure) => /set_sha256/.test(failure)));
  ok(
    compare(baselineOf([]), { ...currentOf([]), schema_version: '4.2.0' }).some((failure) =>
      /schema version changed/.test(failure),
    ),
  );
});

test('removing the required class or current metric cannot disable the gate', () => {
  const baseline = baselineOf([]);
  delete baseline.classes.first_party_missing_required_frontmatter;
  ok(validateBaseline(baseline).some((failure) => /missing required class/.test(failure)));
  ok(
    compare(baselineOf([]), { schema_version: '4.1.0' }).some((failure) =>
      /current validator metrics must be an array/.test(failure),
    ),
  );
});

test('every mirror record resolves to one quarantined ledger row', () => {
  const members = ['a/SKILL.md::tags', 'a/SKILL.md::version', 'b/SKILL.md::author'];
  const ledger = {
    artifacts: [
      { path: 'a/SKILL.md', disposition: 'QUARANTINE' },
      { path: 'b/SKILL.md', disposition: 'QUARANTINE' },
    ],
  };
  deepEqual(checkMirrorDisposition(members, ledger), {
    failures: [],
    paths: ['a/SKILL.md', 'b/SKILL.md'],
  });
});

test('missing and publishable mirror ledger rows fail', () => {
  const result = checkMirrorDisposition(['a/SKILL.md::tags', 'b/SKILL.md::version'], {
    artifacts: [{ path: 'a/SKILL.md', disposition: 'CERTIFY-PENDING-EVIDENCE' }],
  });
  equal(result.failures.length, 2);
  match(result.failures[0], /must be QUARANTINE/);
  match(result.failures[1], /absent from the disposition ledger/);
});

test('the live baseline carries count, set hash, and members with no waiver mechanism', () => {
  const baseline = JSON.parse(
    readFileSync(new URL('./structural-ratchet-baseline.json', import.meta.url), 'utf8'),
  );
  deepEqual(validateBaseline(baseline), []);
  const source = readFileSync(new URL('./check-structural-ratchet.mjs', import.meta.url), 'utf8');
  ok(!/allowlist\.txt|waiver.*\.txt|WAIVERS\s*=/.test(source));
});
