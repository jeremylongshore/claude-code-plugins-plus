import assert from 'node:assert/strict';
import test from 'node:test';

import prettier from 'prettier';

import { buildReadmeBlock, prepareStatsArtifacts, spliceReadmeStats } from './fetch-npm-stats.mjs';

const SAMPLE = {
  generatedAt: '2026-09-02T03:47:05.535Z',
  max_age_hours: 72,
  publishedCount: 394,
  establishedCount: 394,
  candidateCount: 423,
  totalDay: 641,
  totalWeek: 3272,
  totalMonth: 11794,
  establishedDay: 641,
  establishedWeek: 3272,
  establishedMonth: 11794,
  top: [
    {
      name: '@intentsolutionsio/openrouter-pack',
      status: 'published',
      lastDay: 21,
      lastWeek: 100,
      lastMonth: 400,
      createdAt: 1,
      latestVersion: '1.0.0',
    },
  ],
  telemetry: {
    candidates: 423,
    probed: 423,
    published: 394,
    unpublished: 27,
    foreign: 2,
    rateLimited: 0,
    errors: 0,
  },
};

const README_FIXTURE = [
  '# Marketplace',
  '',
  '<!-- NPM-STATS:START — do not edit; daily cron updates this -->',
  'stale stats',
  '<!-- NPM-STATS:END -->',
  '',
  'Footer',
  '',
].join('\n');

test('prepared JSON and README describe the same exact snapshot', async () => {
  const { jsonOutput, readmeOutput } = await prepareStatsArtifacts(SAMPLE, {
    readme: README_FIXTURE,
    prettierOptions: { proseWrap: 'preserve' },
    filepath: 'README.md',
  });

  assert.deepEqual(JSON.parse(jsonOutput), SAMPLE);
  assert.match(readmeOutput, /Across \*\*394 published packages\*\*/);
  assert.match(readmeOutput, /\| Last 24 hours\s+\|\s+641 \|\s+641 \|/);
  assert.match(readmeOutput, /\| Last 7 days\s+\|\s+3,272 \|\s+3,272 \|/);
  assert.match(readmeOutput, /\| Last 30 days\s+\|\s+11,794 \|\s+11,794 \|/);
  assert.match(readmeOutput, /Last refreshed 2026-09-02T03:47:05\.535Z/);
  assert.doesNotMatch(readmeOutput, /stale stats/);
});

test('missing README sentinels fail instead of producing a partial snapshot', async () => {
  await assert.rejects(
    prepareStatsArtifacts(SAMPLE, { readme: '# No generated block\n' }),
    /missing NPM-STATS sentinels/,
  );
});

test('formatter failures propagate instead of silently skipping the README', async () => {
  const failingFormatter = {
    async format() {
      throw new Error('formatter unavailable');
    },
  };

  await assert.rejects(
    prepareStatsArtifacts(SAMPLE, {
      readme: README_FIXTURE,
      formatter: failingFormatter,
    }),
    /formatter unavailable/,
  );
});

test('the rendered block can only replace its bounded README region', () => {
  const block = buildReadmeBlock(SAMPLE);
  const updated = spliceReadmeStats(README_FIXTURE, block);

  assert.ok(updated.startsWith('# Marketplace\n\n'));
  assert.ok(updated.endsWith('\n\nFooter\n'));
});
