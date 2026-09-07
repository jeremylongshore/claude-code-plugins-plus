import assert from 'node:assert/strict';
import test from 'node:test';

import { aggregateByPlugin, applyVerifications } from './run-verification-pipeline.mjs';

test('aggregates repository-relative and absolute validator paths', () => {
  const result = aggregateByPlugin([
    {
      path: 'plugins/saas-packs/snowflake-pack/skills/one/SKILL.md',
      score: 94,
      grade: 'A',
    },
    {
      path: '/checkout/plugins/saas-packs/snowflake-pack/skills/two/SKILL.md',
      score: 96,
      grade: 'A',
    },
    {
      path: '/checkout/plugins/saas-packs/other-pack/skills/one/SKILL.md',
      score: 80,
      grade: 'B',
    },
    { path: '/checkout/not-plugins/ignored/SKILL.md', score: 100, grade: 'A' },
    { path: '/checkout/plugins/saas-packs/fatal/skills/x/SKILL.md', fatal: true },
  ]);

  assert.deepEqual(result.get('./plugins/saas-packs/snowflake-pack'), {
    score: 95,
    grade: 'A',
    badge: 'gold',
    skillCount: 2,
  });
  assert.equal(result.size, 2);
});

test('targeted catalog update cannot rewrite an unrelated plugin', () => {
  const catalog = {
    plugins: [
      {
        name: 'snowflake-pack',
        source: './plugins/saas-packs/snowflake-pack',
        verification: { score: 1, grade: 'F', badge: null, lastValidated: 'old' },
      },
      {
        name: 'other-pack',
        source: './plugins/saas-packs/other-pack',
        verification: { score: 80, grade: 'B', badge: 'silver', lastValidated: 'keep' },
      },
    ],
  };
  const unrelatedBefore = JSON.parse(JSON.stringify(catalog.plugins[1]));
  const verifications = new Map([
    [
      './plugins/saas-packs/snowflake-pack',
      { score: 95, grade: 'A', badge: 'gold', skillCount: 6 },
    ],
    ['./plugins/saas-packs/other-pack', { score: 100, grade: 'A', badge: 'gold', skillCount: 1 }],
  ]);

  const updated = applyVerifications(
    catalog,
    verifications,
    'snowflake-pack',
    '2026-08-31T00:00:00.000Z',
  );

  assert.equal(updated, 1);
  assert.deepEqual(catalog.plugins[0].verification, {
    score: 95,
    grade: 'A',
    badge: 'gold',
    lastValidated: '2026-08-31T00:00:00.000Z',
  });
  assert.deepEqual(catalog.plugins[1], unrelatedBefore);
});
