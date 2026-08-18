import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { STATS_ARTIFACTS, checkAll, evaluateFreshness } from './check-stats-freshness.mjs';

const NOW = Date.parse('2026-08-18T12:00:00.000Z');
const hoursAgo = (h) => new Date(NOW - h * 3_600_000).toISOString();

test('fresh artifact within its declared bound passes', () => {
  assert.equal(
    evaluateFreshness('x.json', { generatedAt: hoursAgo(10), max_age_hours: 72 }, NOW),
    null,
  );
});

test('artifact past its declared bound is a stale-class violation naming age and bound', () => {
  const v = evaluateFreshness('x.json', { generatedAt: hoursAgo(100), max_age_hours: 72 }, NOW);
  assert.equal(v.kind, 'stale');
  assert.match(v.message, /STALE/);
  assert.match(v.message, /100\.0h/);
  assert.match(v.message, /72h/);
});

test('missing or invalid declarations fail closed as structural violations', () => {
  assert.equal(evaluateFreshness('x.json', {}, NOW).kind, 'structural');
  assert.match(evaluateFreshness('x.json', {}, NOW).message, /generatedAt/);
  assert.match(
    evaluateFreshness('x.json', { generatedAt: 'not-a-date', max_age_hours: 72 }, NOW).message,
    /generatedAt/,
  );
  assert.match(
    evaluateFreshness('x.json', { generatedAt: hoursAgo(1) }, NOW).message,
    /max_age_hours/,
  );
  for (const bad of [0, -5, 'seventy-two', NaN, Infinity]) {
    const v = evaluateFreshness('x.json', { generatedAt: hoursAgo(1), max_age_hours: bad }, NOW);
    assert.equal(v.kind, 'structural', `bound ${String(bad)} must be structural`);
    assert.match(v.message, /max_age_hours/, `bound ${String(bad)} must be rejected`);
  }
  assert.match(evaluateFreshness('x.json', null, NOW).message, /not a JSON object/);
});

test('future-dated snapshots fail closed beyond clock-skew tolerance', () => {
  // 10 minutes ahead: inside the 15-minute skew allowance — fresh.
  assert.equal(
    evaluateFreshness('x.json', { generatedAt: hoursAgo(-1 / 6), max_age_hours: 72 }, NOW),
    null,
  );
  // 2 hours ahead: a bad write, structural.
  const v = evaluateFreshness('x.json', { generatedAt: hoursAgo(-2), max_age_hours: 72 }, NOW);
  assert.equal(v.kind, 'structural');
  assert.match(v.message, /future/);
});

test('checkAll reports every governed artifact from a directory', () => {
  const dir = mkdtempSync(join(tmpdir(), 'stats-freshness-'));
  writeFileSync(
    join(dir, 'github-stats.json'),
    JSON.stringify({ generatedAt: hoursAgo(1), max_age_hours: 72 }),
  );
  writeFileSync(
    join(dir, 'npm-stats.json'),
    JSON.stringify({ generatedAt: hoursAgo(200), max_age_hours: 72 }),
  );
  // skills-stats.json deliberately absent → unreadable violation
  const { violations, fresh } = checkAll(NOW, dir);
  assert.equal(fresh.length, 1);
  assert.equal(violations.length, 2);
  assert.equal(violations[0].kind, 'stale');
  assert.match(violations[0].message, /npm-stats\.json: STALE/);
  assert.equal(violations[1].kind, 'structural');
  assert.match(violations[1].message, /skills-stats\.json: unreadable/);
});

test('the governed set is exactly the three external snapshots', () => {
  assert.deepEqual(STATS_ARTIFACTS, ['github-stats.json', 'npm-stats.json', 'skills-stats.json']);
});

test('the tracked artifacts all declare a positive max_age_hours', async () => {
  const { readFileSync } = await import('node:fs');
  for (const name of STATS_ARTIFACTS) {
    const data = JSON.parse(
      readFileSync(new URL(`../marketplace/src/data/${name}`, import.meta.url), 'utf8'),
    );
    assert.equal(typeof data.max_age_hours, 'number', `${name} must declare max_age_hours`);
    assert.ok(data.max_age_hours > 0, `${name} bound must be positive`);
    assert.equal(typeof data.generatedAt, 'string', `${name} must declare generatedAt`);
  }
});
