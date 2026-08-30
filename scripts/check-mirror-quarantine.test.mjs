import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createRequire } from 'node:module';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';

import { checkMirrorQuarantine } from './check-mirror-quarantine.mjs';
import {
  assertCatalogPublicationParity,
  ensureCatalogEntry,
  sourceAllowsPublication,
} from './sync-external.mjs';

const require = createRequire(import.meta.url);
const { publishedPlugins } = require('./publication-policy.cjs');

function write(root, relativePath, value) {
  const target = path.join(root, relativePath);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, value);
}

function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'mirror-quarantine-'));
  const skill = 'plugins/community/mirror/skills/example/SKILL.md';
  write(root, skill, '---\nname: example\n---\n# Example\n');
  write(
    root,
    'plugins/community/mirror/.source.json',
    JSON.stringify({ synced_from: { repo: 'owner/repo', path: 'skills' } }),
  );
  write(
    root,
    'freshie/grades.csv',
    'skill_path,grade,score\nplugins/community/mirror/skills/example,B,85\n',
  );
  write(
    root,
    'freshie/disposition-ledger.json',
    JSON.stringify({
      schema_version: 'disposition-ledger/v1',
      artifacts: [
        {
          path: skill,
          disposition: 'QUARANTINE',
          gate: 'G0',
          reason_codes: ['SHELL_SUBSTITUTION'],
        },
      ],
    }),
  );
  write(root, 'skills/.curated/MANIFEST.json', JSON.stringify({ count: 0, skills: [] }));
  write(
    root,
    'sources.yaml',
    `sources:\n  - name: mirror\n    target_path: plugins/community/mirror\n    publication_disposition:\n      status: quarantined\n      channels: []\n      artifacts:\n        - path: ${skill}\n          reason_codes: [SHELL_SUBSTITUTION]\n      rationale: Retain for provenance and upstream repair only.\n`,
  );
  write(
    root,
    '.claude-plugin/marketplace.extended.json',
    JSON.stringify({ plugins: [{ name: 'mirror', publication: 'quarantined' }] }),
  );
  write(root, '.claude-plugin/marketplace.json', JSON.stringify({ plugins: [] }));
  write(root, 'marketplace/src/data/catalog.json', JSON.stringify({ plugins: [] }));
  write(root, 'marketplace/src/data/skills-catalog.json', JSON.stringify({ skills: [] }));
  write(root, 'marketplace/src/data/skills-index.json', JSON.stringify({ skills: [] }));
  write(root, 'marketplace/src/data/unified-search-index.json', JSON.stringify({ items: [] }));
  write(root, 'marketplace/src/data/readme-sections.json', JSON.stringify({}));
  write(root, 'marketplace/src/data/spotlights.json', JSON.stringify({ hallOfFame: [] }));
  write(root, 'marketplace/src/data/cowork-manifest.json', JSON.stringify({ plugins: [] }));
  write(root, 'README.md', '# Marketplace\n');
  return { root, skill };
}

test('G0 mirror findings require exact no-channel source dispositions', () => {
  const { root } = fixture();
  assert.deepEqual(checkMirrorQuarantine({ root }), {
    mirrors: 1,
    quarantined: 1,
    g0Quarantined: 1,
  });
});

test('catalog leakage and stale or missing coverage fail closed', () => {
  const catalogLeak = fixture();
  write(
    catalogLeak.root,
    '.claude-plugin/marketplace.json',
    JSON.stringify({ plugins: [{ name: 'mirror' }] }),
  );
  assert.throws(
    () => checkMirrorQuarantine({ root: catalogLeak.root }),
    /quarantine leaks through CLI install catalog/,
  );

  const missing = fixture();
  write(
    missing.root,
    'sources.yaml',
    'sources:\n  - name: mirror\n    target_path: plugins/community/mirror\n',
  );
  assert.throws(
    () => checkMirrorQuarantine({ root: missing.root }),
    /G0 mirror has no source publication disposition/,
  );

  const readmeLeak = fixture();
  write(
    readmeLeak.root,
    'marketplace/src/data/readme-sections.json',
    JSON.stringify({ mirror: { overview: 'unsafe recommendation' } }),
  );
  assert.throws(() => checkMirrorQuarantine({ root: readmeLeak.root }), /website README sections/);

  const editorialLeak = fixture();
  write(
    editorialLeak.root,
    'marketplace/src/data/spotlights.json',
    JSON.stringify({ hallOfFame: [{ pluginSlug: 'mirror', grade: 'A' }] }),
  );
  assert.throws(() => checkMirrorQuarantine({ root: editorialLeak.root }), /community spotlight/);
});

test('external sync publishes by default and refuses malformed or quarantined dispositions', () => {
  assert.equal(sourceAllowsPublication({ name: 'clean' }), true);
  assert.equal(
    sourceAllowsPublication({
      name: 'held',
      publication_disposition: { status: 'quarantined', channels: [] },
    }),
    false,
  );
  assert.throws(
    () =>
      sourceAllowsPublication({
        name: 'unknown',
        publication_disposition: { status: 'pending', channels: [] },
      }),
    /must be `status: quarantined`/,
  );
  assert.throws(
    () =>
      sourceAllowsPublication({
        name: 'leaky',
        publication_disposition: { status: 'quarantined', channels: ['marketplace'] },
      }),
    /empty `channels` list/,
  );
  assert.equal(
    sourceAllowsPublication({
      name: 'copyleft',
      copyleft_disposition: { status: 'quarantined', channels: [] },
    }),
    false,
  );
  assert.throws(
    () =>
      sourceAllowsPublication({
        name: 'contradictory',
        publication_disposition: { status: 'quarantined', channels: [] },
        copyleft_disposition: { status: 'quarantined', channels: [] },
      }),
    /multiple publication dispositions/,
  );
});

test('external sync refuses existing catalog rows that contradict source disposition', () => {
  const held = {
    name: 'held',
    publication_disposition: { status: 'quarantined', channels: [] },
  };
  assert.equal(
    assertCatalogPublicationParity(held, { name: 'held', publication: 'quarantined' }),
    false,
  );
  assert.throws(
    () => assertCatalogPublicationParity(held, { name: 'held' }),
    /source disposition and catalog publication state disagree/,
  );
  assert.throws(
    () =>
      assertCatalogPublicationParity(
        { name: 'public' },
        { name: 'public', publication: 'quarantined' },
      ),
    /source disposition and catalog publication state disagree/,
  );

  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'sync-catalog-quarantine-'));
  const catalogFile = path.join(root, 'marketplace.extended.json');
  write(root, 'marketplace.extended.json', JSON.stringify({ plugins: [{ name: 'held' }] }));
  assert.throws(
    () => ensureCatalogEntry(held, { root, catalogFile, dryRun: false }),
    /source disposition and catalog publication state disagree/,
  );
  write(
    root,
    'marketplace.extended.json',
    JSON.stringify({ plugins: [{ name: 'held', publication: 'quarantined' }] }),
  );
  assert.equal(ensureCatalogEntry(held, { root, catalogFile, dryRun: false }), false);
});

test('catalog publication policy omits quarantine and refuses unknown states', () => {
  assert.deepEqual(
    publishedPlugins([{ name: 'public' }, { name: 'held', publication: 'quarantined' }]).map(
      (plugin) => plugin.name,
    ),
    ['public'],
  );
  assert.throws(
    () => publishedPlugins([{ name: 'ambiguous', publication: 'pending' }]),
    /unknown publication state/,
  );
});

test('every install and download projection consumes the canonical publication policy', () => {
  const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
  for (const relativePath of [
    'scripts/sync-marketplace.cjs',
    'scripts/corpus-resolver.mjs',
    'scripts/build-cowork-zips.mjs',
    'scripts/validate-cowork-manifest.mjs',
    'scripts/generate-readme-toc.mjs',
    'marketplace/scripts/sync-catalog.mjs',
    'marketplace/scripts/discover-skills.mjs',
    'marketplace/scripts/extract-readme-sections.mjs',
  ]) {
    const source = fs.readFileSync(path.join(root, relativePath), 'utf8');
    assert.match(source, /publication-policy\.cjs/);
    assert.match(source, /publishedPlugins\(/);
  }
});
