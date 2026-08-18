import assert from 'node:assert/strict';
import test from 'node:test';

import {
  GENERATED_ARTIFACT_REGISTRY,
  artifactRegistration,
  artifactRegistrationsByTracking,
} from './generated-artifact-registry.mjs';

const EXAMPLES = new Map([
  ['epic-1-scorecard', '000-docs/742-RA-DATA-epic-1-scorecard.json'],
  ['marketplace-catalog-projection', 'marketplace/src/data/catalog.json'],
  ['marketplace-skills-catalog-projection', 'marketplace/src/data/skills-catalog.json'],
  ['marketplace-skills-index-projection', 'marketplace/src/data/skills-index.json'],
  ['marketplace-search-projection', 'marketplace/src/data/unified-search-index.json'],
  ['marketplace-external-stats', 'marketplace/src/data/npm-stats.json'],
  ['marketplace-spotlight-editorial-data', 'marketplace/src/data/spotlights.json'],
  ['marketplace-canonical-data', 'marketplace/src/data/collections.json'],
  ['marketplace-jrig-build-data', 'marketplace/src/data/jrig-data.json'],
  ['marketplace-readme-sections-build-data', 'marketplace/src/data/readme-sections.json'],
  ['marketplace-plugin-content', 'marketplace/src/content/plugins/example.json'],
  ['plugin-package-manifests', 'plugins/example/example/package.json'],
  ['curated-skill-mirror', 'skills/.curated/example/SKILL.md'],
  ['marketplace-public-data', 'marketplace/public/data/catalog.json'],
  ['cowork-downloads', 'marketplace/public/downloads/example.zip'],
  ['freshie-run-snapshots', 'freshie/exports/run-1/plugin_values.json'],
  ['frozen-prose-anchor-manifest', 'tests/fixtures/prose-anchors/expected-output.json'],
]);

test('every registry entry owns exactly one representative path', () => {
  assert.equal(EXAMPLES.size, GENERATED_ARTIFACT_REGISTRY.length);
  for (const entry of GENERATED_ARTIFACT_REGISTRY) {
    const example = EXAMPLES.get(entry.id);
    assert.ok(example, `missing fixture for ${entry.id}`);
    assert.equal(artifactRegistration(example)?.id, entry.id);
  }
});

test('unregistered source paths remain unclassified', () => {
  assert.equal(artifactRegistration('README.md'), null);
  assert.equal(artifactRegistration('plugins/example/example/README.md'), null);
});

test('tracking indexes partition the registry without loss', () => {
  const indexed = [
    ...artifactRegistrationsByTracking('tracked'),
    ...artifactRegistrationsByTracking('untracked'),
  ];
  assert.deepEqual(
    indexed.map((entry) => entry.id).sort(),
    GENERATED_ARTIFACT_REGISTRY.map((entry) => entry.id).sort(),
  );
});

test('every tracked generated JSON class declares the retired-domain postprocessor', () => {
  const trackedJsonExamples = [...EXAMPLES].filter(
    ([id, path]) =>
      path.endsWith('.json') &&
      GENERATED_ARTIFACT_REGISTRY.find((entry) => entry.id === id)?.tracking === 'tracked' &&
      GENERATED_ARTIFACT_REGISTRY.find((entry) => entry.id === id)?.kind === 'generated_projection',
  );
  for (const [id] of trackedJsonExamples) {
    const entry = GENERATED_ARTIFACT_REGISTRY.find((candidate) => candidate.id === id);
    assert.equal(entry?.postprocess, 'pnpm run normalize:dead-domain-projections', id);
  }
});

test('marketplace data authority separates deterministic, network, and editorial populations', () => {
  const index = artifactRegistration('marketplace/src/data/skills-index.json');
  const catalog = artifactRegistration('marketplace/src/data/skills-catalog.json');
  const pluginCatalog = artifactRegistration('marketplace/src/data/catalog.json');
  const search = artifactRegistration('marketplace/src/data/unified-search-index.json');
  assert.equal(index?.contentCheck, true);
  assert.equal(catalog?.contentCheck, true);
  assert.equal(pluginCatalog?.contentCheck, true);
  assert.equal(search?.contentCheck, true);
  assert.equal(index?.regenerate, catalog?.regenerate);
  assert.equal(pluginCatalog?.regenerate, 'node marketplace/scripts/sync-catalog.mjs --check');
  assert.equal(search?.regenerate, 'node marketplace/scripts/generate-unified-search.mjs --check');
  assert.equal(
    artifactRegistration('marketplace/src/data/npm-stats.json')?.kind,
    'external_snapshot',
  );
  assert.equal(
    artifactRegistration('marketplace/src/data/spotlights.json')?.kind,
    'canonical_data',
  );
  assert.equal(artifactRegistration('marketplace/src/data/partners.json')?.kind, 'canonical_data');
});
