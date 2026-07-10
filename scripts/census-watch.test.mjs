/**
 * census-watch.test.mjs — fixture corpus for the --enforce decision logic.
 *
 * Covers the pure functions the enforcement run is built on (clusterVerdict,
 * parseOnClockSources, buildSourcesRemoval, swapAllowlistTempLine, guards) with
 * in-memory fixtures — NO network, NO gh, NO validator subprocess. The verdict
 * table below is the executable form of the fix-or-removed policy from the
 * retired cloud one-shot: PASS only when every notified skill has 0 validator
 * errors at upstream HEAD; deleted/private/archived upstream = FAIL; partial
 * pass = FAIL.
 *
 * Run: node --test scripts/census-watch.test.mjs
 * (Deliberately not wired into CI: census-watch is a dev-box cron script that
 * retires after 2026-07-22; the test runs locally as the enforce-mode evidence.)
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';

import {
  clusterVerdict,
  parseOnClockSources,
  buildSourcesRemoval,
  swapAllowlistTempLine,
  isNeverTouch,
  isNotifyIssueTitle,
  enforcementDue,
} from './census-watch.mjs';

// ─────────────────────────────────────────────────────────────────────────────
// clusterVerdict — the fix-or-removed policy table.
// ─────────────────────────────────────────────────────────────────────────────

test('verdict: all skills 0 errors → PASS', () => {
  const r = clusterVerdict({
    upstream: { gone: false },
    skills: [
      { name: 'a', found: true, errors: 0 },
      { name: 'b', found: true, errors: 0 },
    ],
  });
  assert.equal(r.verdict, 'PASS');
  assert.equal(r.reasons.length, 0);
});

test('verdict: one failing skill among passing ones → partial pass = cluster FAIL', () => {
  const r = clusterVerdict({
    upstream: { gone: false },
    skills: [
      { name: 'a', found: true, errors: 0 },
      { name: 'b', found: true, errors: 7 },
      { name: 'c', found: true, errors: 0 },
    ],
  });
  assert.equal(r.verdict, 'FAIL');
  assert.equal(r.reasons.length, 1);
  assert.match(r.reasons[0], /b: 7 validator error/);
});

test('verdict: a notified skill missing at upstream HEAD → FAIL', () => {
  const r = clusterVerdict({
    upstream: { gone: false },
    skills: [
      { name: 'a', found: true, errors: 0 },
      { name: 'b', found: false, errors: null },
    ],
  });
  assert.equal(r.verdict, 'FAIL');
  assert.match(r.reasons[0], /b: SKILL\.md not found/);
});

test('verdict: deleted/private upstream → FAIL', () => {
  const r = clusterVerdict({ upstream: { gone: true }, skills: [] });
  assert.equal(r.verdict, 'FAIL');
  assert.match(r.reasons[0], /deleted or private/);
});

test('verdict: archived upstream → FAIL (distinct reason)', () => {
  const r = clusterVerdict({ upstream: { gone: true, archived: true }, skills: [] });
  assert.equal(r.verdict, 'FAIL');
  assert.match(r.reasons[0], /archived/);
});

test('verdict: upstream alive but zero resolvable skills → FAIL', () => {
  const r = clusterVerdict({ upstream: { gone: false }, skills: [] });
  assert.equal(r.verdict, 'FAIL');
  assert.match(r.reasons[0], /no notified skills resolvable/);
});

// ─────────────────────────────────────────────────────────────────────────────
// parseOnClockSources — live-clock selection from sources.yaml text.
// ─────────────────────────────────────────────────────────────────────────────

const FIXTURE_SOURCES = `# header comment
sources:
  # ============================================================
  # Some Upstream (author)
  # ============================================================

  - name: on-clock-one
    description: first flagged skill
    repo: someone/some-repo
    source_path: skills/one
    target_path: plugins/community/on-clock-one
    # census 2026-07-08: graded D/F — verified flips back to true when the upstream fix lands (deadline 2026-07-22)
    verified: false
    include:
      - 'SKILL.md'

  - name: clean-entry
    description: not on the clock
    repo: fine/repo
    source_path: .
    target_path: plugins/devops/clean-entry
    verified: true
    include:
      - 'SKILL.md'

  - name: on-clock-two
    description: second flagged skill
    repo: someone/some-repo
    source_path: skills/two
    target_path: plugins/community/on-clock-two
    # census 2026-07-08: graded D/F — verified flips back to true when the upstream fix lands (deadline 2026-07-22)
    verified: false
    include:
      - 'SKILL.md'
`;

test('parseOnClockSources: selects only deadline-marked entries, with paths', () => {
  const entries = parseOnClockSources(FIXTURE_SOURCES);
  assert.deepEqual(
    entries.map((e) => e.name),
    ['on-clock-one', 'on-clock-two'],
  );
  assert.equal(entries[0].repo, 'someone/some-repo');
  assert.equal(entries[0].sourcePath, 'skills/one');
  assert.equal(entries[0].targetPath, 'plugins/community/on-clock-one');
});

// ─────────────────────────────────────────────────────────────────────────────
// buildSourcesRemoval — the sources.yaml edit the removal PR ships.
// ─────────────────────────────────────────────────────────────────────────────

test('buildSourcesRemoval: removes the cluster entries, keeps the clean entry, plants one NOTE', () => {
  const { text, removedNames } = buildSourcesRemoval(FIXTURE_SOURCES, [
    {
      names: ['on-clock-one', 'on-clock-two'],
      noteLines: ['NOTE 2026-07-23: removed per census deadline', 'notify issue: <url>'],
    },
  ]);
  assert.deepEqual(removedNames, ['on-clock-one', 'on-clock-two']);
  assert.ok(!text.includes('- name: on-clock-one'), 'first entry removed');
  assert.ok(!text.includes('- name: on-clock-two'), 'second entry removed');
  assert.ok(text.includes('- name: clean-entry'), 'unflagged entry retained');
  assert.ok(text.includes('  # NOTE 2026-07-23: removed per census deadline'), 'NOTE planted');
  assert.equal(
    (text.match(/# NOTE 2026-07-23/g) || []).length,
    1,
    'exactly one NOTE per removal group',
  );
  assert.ok(!/\n\s*\n\s*\n/.test(text), 'no blank-line pileups left behind');
  // The surviving entry's fields are intact (no partial-block bleed).
  assert.ok(text.includes('repo: fine/repo'));
  assert.ok(text.includes('verified: true'));
});

test('buildSourcesRemoval: names not present in the file remove nothing', () => {
  const { text, removedNames } = buildSourcesRemoval(FIXTURE_SOURCES, [
    { names: ['ghost-entry'], noteLines: ['NOTE: n/a'] },
  ]);
  assert.deepEqual(removedNames, []);
  assert.ok(text.includes('- name: on-clock-one'), 'nothing removed on a no-match');
});

// ─────────────────────────────────────────────────────────────────────────────
// swapAllowlistTempLine — the one-temp-line convention in scan-allowlist.txt.
// ─────────────────────────────────────────────────────────────────────────────

const FIXTURE_ALLOWLIST = `# scan-synced-content.mjs — CHALLENGE / FLAG waivers
plugins/**/README.md:pipe-to-shell  documented upstream installer

# TEMPORARY per-PR source-vetting sign-off block
sources.yaml:sources-change-unscanned  2026-07-10 previous PR reason
sources.lock.json:sources-change-unscanned  2026-07-10 previous PR lock reason

plugins/security/scanner.py:outbound-network  defensive scanner regex
`;

test('swapAllowlistTempLine: replaces all stale temp lines with exactly one new line, in place', () => {
  const newLine =
    'sources.yaml:sources-change-unscanned  2026-07-23 census-deadline enforcement PR';
  const out = swapAllowlistTempLine(FIXTURE_ALLOWLIST, newLine);
  assert.ok(!out.includes('previous PR reason'), 'old sources.yaml temp line gone');
  assert.ok(!out.includes('previous PR lock reason'), 'old sources.lock.json temp line gone');
  assert.equal(
    out.split('\n').filter((l) => l.startsWith('sources.yaml:sources-change-unscanned')).length,
    1,
    'exactly one temp line remains',
  );
  assert.ok(out.includes(newLine));
  assert.ok(out.includes('plugins/**/README.md:pipe-to-shell'), 'permanent waivers untouched');
  assert.ok(
    out.includes('plugins/security/scanner.py:outbound-network'),
    'permanent waivers untouched',
  );
  // New line sits where the old temp block was (before the scanner waiver).
  assert.ok(out.indexOf(newLine) < out.indexOf('plugins/security/scanner.py'));
});

test('swapAllowlistTempLine: appends when no temp line exists', () => {
  const base = '# waivers\nplugins/**/README.md:pipe-to-shell  reason\n';
  const newLine = 'sources.yaml:sources-change-unscanned  2026-07-23 reason';
  const out = swapAllowlistTempLine(base, newLine);
  assert.equal(
    out.split('\n').filter((l) => l.startsWith('sources.yaml:sources-change-unscanned')).length,
    1,
  );
});

// ─────────────────────────────────────────────────────────────────────────────
// Guards.
// ─────────────────────────────────────────────────────────────────────────────

test('isNeverTouch: courtesy-tier and partner repos are protected', () => {
  assert.ok(isNeverTouch('Skyvern-AI/skyvern'));
  assert.ok(isNeverTouch('someone/x-twitter-scraper'));
  assert.ok(isNeverTouch('kobiton/some-repo'));
  assert.ok(!isNeverTouch('wondelai/skills'));
  assert.ok(!isNeverTouch('numman-ali/n-skills'));
});

test('isNotifyIssueTitle: matches the 2026-07-08 notify wave titles', () => {
  assert.ok(
    isNotifyIssueTitle(
      'Action needed: your claude-code-plugins marketplace listing is below the A-grade bar — fix by 2026-07-22 or it will be delisted',
    ),
  );
  assert.ok(!isNotifyIssueTitle('Bug: something unrelated'));
});

test('enforcementDue: false before the deadline, true after it passes', () => {
  assert.equal(enforcementDue(new Date('2026-07-10T12:00:00Z')), false);
  assert.equal(
    enforcementDue(new Date('2026-07-22T12:00:00Z')),
    false,
    'deadline day itself is still fix time',
  );
  assert.equal(
    enforcementDue(new Date('2026-07-23T08:23:00Z')),
    true,
    'enforcement fires the morning after',
  );
});
