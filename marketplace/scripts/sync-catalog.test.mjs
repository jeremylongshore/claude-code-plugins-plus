import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';

import {
  normalizePluginPath,
  renderCatalog,
  renderCatalogBytes,
  syncCatalog,
} from './sync-catalog.mjs';

function plugin(name, source, extra = {}) {
  return {
    name,
    source: `./${source}`,
    description: `${name} description`,
    version: '1.0.0',
    category: 'testing',
    keywords: [name],
    ...extra,
  };
}

function skill(parentPath, filePath) {
  return { parentPlugin: { path: parentPath }, filePath };
}

const EXTENDED = {
  plugins: [
    plugin('002-jeremy-beta', 'plugins/testing/shared', {
      components: { commands: 2 },
      featured: true,
      author: { name: 'Owner' },
    }),
    plugin('alpha', 'plugins/testing/shared'),
    plugin('empty', 'plugins/testing/empty'),
  ],
};
const SKILLS = {
  skills: [
    skill('plugins/testing/shared', 'plugins/testing/shared/skills/one/SKILL.md'),
    skill('plugins/testing/shared', 'plugins/testing/shared/skills/two/SKILL.md'),
  ],
};

test('renders only canonical deterministic fields in canonical plugin order', () => {
  const catalog = renderCatalog(EXTENDED, SKILLS);
  assert.deepEqual(
    catalog.plugins.map((entry) => entry.name),
    ['002-jeremy-beta', 'alpha', 'empty'],
  );
  assert.deepEqual(
    catalog.plugins.map((entry) => entry.skillCount),
    [2, 2, 0],
    'aliases sharing one canonical source receive the same source-derived count',
  );
  assert.equal(catalog.stats.totalPlugins, 3);
  assert.equal(catalog.stats.totalSkills, 2, 'distinct skills are not double-counted through aliases');
  assert.equal(catalog.stats.totalCommands, 2);
  assert.equal(catalog.stats.pluginsWithSkills, 2);
  assert.equal(catalog.stats.featured, 1);
  assert.equal(catalog.plugins[0].slug, 'beta');
  assert.equal(catalog.plugins[0].displayName, 'beta');
  assert.deepEqual(catalog.plugins[1].author, { name: 'Claude Code Plugins' });
  assert.deepEqual(catalog.plugins[2].author, { name: 'Claude Code Plugins' });
  for (const forbidden of [
    'generated',
    'generatedAt',
    'lastUpdatedEpoch',
    'lastUpdatedDate',
    'status',
    'badges',
    'isNew',
  ]) {
    assert.equal(JSON.stringify(catalog).includes(`"${forbidden}"`), false, forbidden);
  }
});

test('preserves the compatibility author default and normalizes the complete projection', () => {
  const retiredDomain = ['claudecode', 'plugins.io'].join('');
  const catalog = renderCatalog(
    {
      plugins: [
        plugin('alpha', 'plugins/testing/a', {
          description: `Visit https://${retiredDomain}`,
          keywords: [retiredDomain],
          author: { name: retiredDomain, url: `https://${retiredDomain}` },
        }),
        plugin('without-author', 'plugins/testing/b'),
      ],
    },
    { skills: [] },
  );

  assert.equal(JSON.stringify(catalog).includes(retiredDomain), false);
  assert.equal(catalog.plugins[0].description, 'Visit https://tonsofskills.com');
  assert.deepEqual(catalog.plugins[0].keywords, ['tonsofskills.com']);
  assert.deepEqual(catalog.plugins[0].author, {
    name: 'tonsofskills.com',
    url: 'https://tonsofskills.com',
  });
  assert.deepEqual(catalog.plugins[1].author, { name: 'Claude Code Plugins' });
});

test('retains quarantined records only in the extended authority, never the public projection', () => {
  const catalog = renderCatalog(
    {
      plugins: [
        plugin('public', 'plugins/testing/public'),
        plugin('held', 'plugins/testing/held', { publication: 'quarantined' }),
      ],
    },
    { skills: [] },
  );
  assert.deepEqual(catalog.plugins.map((entry) => entry.name), ['public']);
  assert.equal(catalog.stats.totalPlugins, 1);
  assert.throws(
    () =>
      renderCatalog(
        { plugins: [plugin('ambiguous', 'plugins/testing/ambiguous', { publication: 'pending' })] },
        { skills: [] },
      ),
    /unknown publication state/,
  );
});

test('fails closed on duplicate identities, paths, and contradictory skill ancestry', () => {
  assert.throws(
    () =>
      renderCatalog(
        { plugins: [plugin('Alpha', 'plugins/testing/a'), plugin('alpha', 'plugins/testing/b')] },
        { skills: [] },
      ),
    /duplicate catalog plugin identity/,
  );
  assert.throws(
    () => normalizePluginPath('../plugins/testing/a'),
    /escapes the repository/,
  );
  assert.throws(
    () =>
      renderCatalog(
        { plugins: [plugin('alpha', 'plugins/testing/a')] },
        {
          skills: [
            skill('plugins/testing/a', 'plugins/testing/a/skills/one/SKILL.md'),
            skill('plugins/testing/a', 'plugins/testing/a/skills/one/SKILL.md'),
          ],
        },
      ),
    /duplicate skill filePath/,
  );
  assert.throws(
    () =>
      renderCatalog(
        { plugins: [plugin('alpha', 'plugins/testing/a')] },
        { skills: [skill('plugins/testing/a', 'plugins/testing/b/skills/one/SKILL.md')] },
      ),
    /outside parent plugin/,
  );
  assert.throws(
    () =>
      renderCatalog(
        { plugins: [plugin('alpha', 'plugins/testing/a')] },
        { skills: [skill('plugins/testing/missing', 'plugins/testing/missing/SKILL.md')] },
      ),
    /no canonical plugin source/,
  );
  assert.throws(
    () => renderCatalog({ plugins: [plugin('alpha', 'plugins/testing/a')] }, { count: 2, skills: [] }),
    /count does not match/,
  );
  assert.throws(
    () =>
      renderCatalog(
        { plugins: [plugin('alpha', 'plugins/testing/a', { components: 'one' })] },
        { skills: [] },
      ),
    /components must be an object/,
  );
});

function writeJson(root, path, value) {
  const target = join(root, path);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, `${JSON.stringify(value, null, 2)}\n`);
}

test('check compares rendered bytes with the Git index and never mutates the worktree', (t) => {
  const root = mkdtempSync(join(tmpdir(), 'catalog-renderer-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  execFileSync('git', ['init', '-q'], { cwd: root });
  writeJson(root, '.claude-plugin/marketplace.extended.json', EXTENDED);
  writeJson(root, 'marketplace/src/data/skills-catalog.json', SKILLS);
  const output = 'marketplace/src/data/catalog.json';
  writeJson(root, output, { stale: true });
  syncCatalog({ root });
  const firstRender = readFileSync(join(root, output));
  syncCatalog({ root });
  const secondRender = readFileSync(join(root, output));
  assert.deepEqual(firstRender, secondRender, 'successive renders must be byte-identical');
  assert.deepEqual(firstRender, Buffer.from(renderCatalogBytes(EXTENDED, SKILLS)));
  execFileSync('git', ['add', '.'], { cwd: root });

  const before = readFileSync(join(root, output));
  assert.doesNotThrow(() => syncCatalog({ root, check: true }));
  assert.deepEqual(readFileSync(join(root, output)), before);

  const stale = JSON.parse(before);
  stale.stats.totalPlugins = 999;
  writeJson(root, output, stale);
  execFileSync('git', ['add', output], { cwd: root });
  const planted = readFileSync(join(root, output));
  assert.throws(() => syncCatalog({ root, check: true }), /generated content drift.*catalog\.json/);
  assert.deepEqual(readFileSync(join(root, output)), planted, 'red check must not repair the file');
});
