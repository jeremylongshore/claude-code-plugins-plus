import { deepEqual, equal, match, throws } from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { afterEach, test } from 'node:test';
import {
  COUNT_COHORT,
  COUNT_COMMAND,
  COUNT_PROVENANCE,
  COUNT_SOURCE,
  buildCountContract,
  buildHtml,
  readIndexStats,
} from './generate-og-image.mjs';

const temporaryRoots = [];

afterEach(async () => {
  await Promise.all(
    temporaryRoots.splice(0).map((root) => rm(root, { recursive: true, force: true })),
  );
});

async function indexFixture(stats) {
  const root = await mkdtemp(path.join(os.tmpdir(), 'og-image-contract-'));
  temporaryRoots.push(root);
  const index = path.join(root, 'unified-search-index.json');
  await writeFile(index, JSON.stringify({ stats }));
  return index;
}

test('social-card contract labels the embedded counts with their cohort and command', () => {
  const contract = buildCountContract({ totalSkills: 3068, totalPlugins: 467 });
  deepEqual(contract, {
    cohort: COUNT_COHORT,
    command: COUNT_COMMAND,
    source: COUNT_SOURCE,
    provenance: COUNT_PROVENANCE,
    label: 'marketplace-visible skills',
    skills: 3068,
    plugins: 467,
  });

  const html = buildHtml(contract);
  match(html, /marketplace-visible skills/);
  match(html, /marketplace\/src\/data\/unified-search-index\.json/);
  match(html, /node scripts\/corpus-resolver\.mjs --cohort marketplace-visible --json/);
});

test('social-card source stats are read from valid integer totals', async () => {
  const index = await indexFixture({ totalSkills: 9, totalPlugins: 3 });
  deepEqual(readIndexStats(index), { totalSkills: 9, totalPlugins: 3 });
});

test('red proof: unreadable or malformed source stats fail closed', async () => {
  const missing = path.join(os.tmpdir(), 'does-not-exist-og-index.json');
  throws(() => readIndexStats(missing));

  const index = await indexFixture({ totalSkills: '9', totalPlugins: 3 });
  throws(() => readIndexStats(index));
});

test('red proof: non-integer counts cannot become a rendered social-card contract', () => {
  equal(
    (() => {
      try {
        buildCountContract({ totalSkills: 3.5, totalPlugins: 2 });
        return false;
      } catch {
        return true;
      }
    })(),
    true,
  );
});
