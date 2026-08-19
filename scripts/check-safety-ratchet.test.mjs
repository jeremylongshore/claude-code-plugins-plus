import { test } from 'node:test';
import { deepEqual, equal, ok, match } from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { compare } from './check-safety-ratchet.mjs';

const baselineOf = (members) => ({
  classes: { shell_substitution: { count: members.length, members } },
});
const currentOf = (members) => ({ classes: { shell_substitution: members } });

test('unchanged debt passes', () => {
  deepEqual(compare(baselineOf(['a::x', 'b::y']), currentOf(['a::x', 'b::y'])), []);
});

test('growth fails on count', () => {
  const failures = compare(baselineOf(['a::x']), currentOf(['a::x', 'b::y']));
  equal(failures.length, 2); // count growth + newcomer
  match(failures[0], /count grew 1 → 2/);
});

test('a swap fails even at equal count', () => {
  const failures = compare(baselineOf(['a::x']), currentOf(['b::y']));
  equal(failures.length, 1);
  match(failures[0], /not in the baseline/);
});

test('a shrink passes compare', () => {
  deepEqual(compare(baselineOf(['a::x', 'b::y']), currentOf(['a::x'])), []);
});

test('the live baseline carries all three keys per class', () => {
  const baseline = JSON.parse(
    readFileSync(new URL('./safety-ratchet-baseline.json', import.meta.url), 'utf8'),
  );
  ok(baseline.schema_version);
  for (const entry of Object.values(baseline.classes)) {
    equal(typeof entry.count, 'number');
    match(entry.set_sha256, /^[0-9a-f]{64}$/);
    equal(entry.members.length, entry.count);
  }
  // E4.11: the agents lane is one of the pinned classes.
  ok(baseline.classes.agents_only_errors);
});

test('there is no waiver mechanism in the gate source', () => {
  const source = readFileSync(new URL('./check-safety-ratchet.mjs', import.meta.url), 'utf8');
  ok(!/allowlist\.txt|waiver.*\.txt|WAIVERS\s*=/.test(source));
});
