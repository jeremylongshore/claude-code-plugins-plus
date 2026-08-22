import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import {
  mkdtempSync,
  mkdirSync,
  readFileSync,
  renameSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import test from 'node:test';

import {
  compareOrdinal,
  countAgentsAndHooks,
  parseDocFrontmatter,
  readDocs,
  renderUnifiedSearch,
  renderUnifiedSearchBytes,
  syncUnifiedSearch,
} from './generate-unified-search.mjs';

const CATALOG = {
  plugins: [
    {
      slug: 'alpha',
      name: '001-alpha',
      displayName: 'Alpha',
      description: 'Alpha plugin',
      category: 'testing',
      keywords: ['alpha'],
      author: { name: 'Intent Solutions' },
      version: '1.0.0',
      skillCount: 1,
    },
  ],
};

const SKILLS = {
  count: 1,
  allowedToolsUsed: ['Read'],
  skills: [
    {
      slug: 'alpha',
      name: 'Alpha skill',
      description: 'Does work',
      version: '1.0.0',
      allowedTools: ['Read'],
      compatibleWith: ['claude-code'],
      parentPlugin: { name: '001-alpha', slug: 'alpha', category: 'testing' },
    },
  ],
};

const EXTENDED = {
  plugins: [
    {
      name: '001-alpha',
      verification: { score: 99, grade: 'A', badge: 'verified' },
    },
  ],
};

const DOCS = [
  {
    type: 'docs',
    id: 'docs/start',
    slug: 'start',
    name: 'Start',
    description: 'Start here',
    category: 'guide',
    keywords: ['start'],
    url: '/docs/start/',
    searchText: 'start start here guide start',
  },
];

const SURFACE_STATS = {
  totalAgents: 2,
  totalHooks: 1,
  pluginsWithAgents: 2,
  pluginsWithHooks: 1,
};

function write(root, repositoryPath, contents) {
  const target = join(root, repositoryPath);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, contents);
}

function writeJson(root, repositoryPath, value) {
  write(root, repositoryPath, `${JSON.stringify(value, null, 2)}\n`);
}

function fixtureRoot(t) {
  const root = mkdtempSync(join(tmpdir(), 'unified-search-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  writeJson(root, 'marketplace/src/data/catalog.json', CATALOG);
  writeJson(root, 'marketplace/src/data/skills-catalog.json', SKILLS);
  writeJson(root, '.claude-plugin/marketplace.extended.json', EXTENDED);
  write(
    root,
    'marketplace/src/content/docs/zeta.md',
    '---\ntitle: Zeta\ndescription: Last\nsection: guide\nkeywords: ["zeta", "last"]\n---\n',
  );
  write(
    root,
    'marketplace/src/content/docs/alpha.md',
    '---\ntitle: Alpha\ndescription: First\nsection: guide\nkeywords:\n  - alpha\n  - first\n---\n',
  );
  write(root, 'plugins/testing/alpha/agents/alpha.md', '# agent\n');
  write(root, 'plugins/testing/alpha/hooks/hook.json', '{}\n');
  write(root, 'plugins/testing/pack/plugins/sub/agents/sub.md', '# nested agent\n');
  return root;
}

test('renders the compatibility shape without runtime metadata or global cross-type rejection', () => {
  const retiredDomain = ['claudecode', 'plugins.io'].join('');
  const catalog = structuredClone(CATALOG);
  catalog.plugins[0].description = `Visit https://${retiredDomain}`;
  const result = renderUnifiedSearch({
    catalogData: catalog,
    skillsData: SKILLS,
    extendedData: EXTENDED,
    docs: DOCS,
    agentHookStats: SURFACE_STATS,
  });

  assert.equal('generated' in result.meta, false);
  assert.equal(result.meta.generator, 'marketplace/scripts/generate-unified-search.mjs');
  assert.equal(result.stats.totalPlugins, 1);
  assert.equal(result.stats.totalSkills, 1);
  assert.equal(result.stats.totalDocs, 1);
  assert.equal(result.stats.totalItems, 3);
  assert.equal(result.stats.totalAgents, 2);
  assert.equal(result.items[0].verificationGrade, 'A');
  assert.equal(result.items[0].authorType, 'official');
  assert.equal(result.items[0].description, 'Visit https://tonsofskills.com');
  assert.deepEqual(
    result.items.map((item) => item.type),
    ['plugin', 'skill', 'docs'],
  );
  assert.equal(result.items[0].id, result.items[1].id, 'legacy cross-type ids remain compatible');
});

test('parses governed scalar, block-list, inline-list, and CRLF frontmatter deterministically', () => {
  assert.deepEqual(
    parseDocFrontmatter(
      '---\r\ntitle: Example\r\ndescription: Demo\r\nsection: guide\r\nkeywords: ["one", "two"]\r\n---\r\n',
    ),
    { title: 'Example', description: 'Demo', section: 'guide', keywords: ['one', 'two'] },
  );
  assert.deepEqual(
    parseDocFrontmatter('---\ntitle: Example\nkeywords:\n  - one\n  - two\n---\n').keywords,
    ['one', 'two'],
  );
  assert.throws(() => parseDocFrontmatter('no frontmatter'), /missing YAML frontmatter/);
  assert.throws(
    () => parseDocFrontmatter('---\ntitle: Example\nkeywords: [one]\n---\n'),
    /inline list is invalid/,
  );
});

test('fails closed on contradictory identities, counts, and surface measurements', () => {
  const duplicateCatalog = structuredClone(CATALOG);
  duplicateCatalog.plugins.push({ ...duplicateCatalog.plugins[0], slug: 'ALPHA' });
  assert.throws(
    () =>
      renderUnifiedSearch({
        catalogData: duplicateCatalog,
        skillsData: SKILLS,
        extendedData: EXTENDED,
        docs: DOCS,
        agentHookStats: SURFACE_STATS,
      }),
    /duplicate plugin slug/,
  );

  assert.throws(
    () =>
      renderUnifiedSearch({
        catalogData: CATALOG,
        skillsData: { ...SKILLS, count: 2 },
        extendedData: EXTENDED,
        docs: DOCS,
        agentHookStats: SURFACE_STATS,
      }),
    /count does not match/,
  );
  assert.throws(
    () =>
      renderUnifiedSearch({
        catalogData: CATALOG,
        skillsData: SKILLS,
        extendedData: EXTENDED,
        docs: DOCS,
        agentHookStats: { ...SURFACE_STATS, totalAgents: -1 },
      }),
    /totalAgents must be a non-negative integer/,
  );

  for (const slug of ['../escape', '/absolute', ' alpha ']) {
    const unsafeCatalog = structuredClone(CATALOG);
    unsafeCatalog.plugins[0].slug = slug;
    assert.throws(
      () =>
        renderUnifiedSearch({
          catalogData: unsafeCatalog,
          skillsData: SKILLS,
          extendedData: EXTENDED,
          docs: DOCS,
          agentHookStats: SURFACE_STATS,
        }),
      /lowercase kebab-case path segment/,
    );
  }

  const duplicateExtended = structuredClone(EXTENDED);
  duplicateExtended.plugins.push({ ...duplicateExtended.plugins[0], name: '001-ALPHA' });
  assert.throws(
    () =>
      renderUnifiedSearch({
        catalogData: CATALOG,
        skillsData: SKILLS,
        extendedData: duplicateExtended,
        docs: DOCS,
        agentHookStats: SURFACE_STATS,
      }),
    /duplicate extended plugin name/,
  );
});

test('filesystem renderer sorts docs, counts regular surfaces, and is byte deterministic', (t) => {
  const root = fixtureRoot(t);
  assert.deepEqual(countAgentsAndHooks(root), SURFACE_STATS);
  assert.deepEqual(
    readDocs(root).map((doc) => doc.slug),
    ['alpha', 'zeta'],
  );
  const first = renderUnifiedSearchBytes({ root });
  const second = renderUnifiedSearchBytes({ root });
  assert.equal(first, second);
  const rendered = JSON.parse(first);
  assert.equal(rendered.stats.totalDocs, 2);
  assert.equal(rendered.stats.totalItems, 4);
  assert.deepEqual(rendered.items.at(-2).keywords, ['alpha', 'first']);
});

test('check compares rendered bytes with the staged Git index and never repairs drift', (t) => {
  const root = fixtureRoot(t);
  execFileSync('git', ['init', '-q'], { cwd: root });
  writeJson(root, 'marketplace/src/data/unified-search-index.json', { poisoned: true });
  syncUnifiedSearch({ root });
  const first = readFileSync(join(root, 'marketplace/src/data/unified-search-index.json'));
  syncUnifiedSearch({ root });
  assert.deepEqual(
    readFileSync(join(root, 'marketplace/src/data/unified-search-index.json')),
    first,
  );
  assert.equal(
    first.includes(Buffer.from('poisoned')),
    false,
    'tracked output must never be an input',
  );
  execFileSync('git', ['add', '.'], { cwd: root });
  assert.doesNotThrow(() => syncUnifiedSearch({ root, check: true }));

  const drift = JSON.parse(first);
  drift.stats.totalItems = 999;
  writeJson(root, 'marketplace/src/data/unified-search-index.json', drift);
  execFileSync('git', ['add', 'marketplace/src/data/unified-search-index.json'], { cwd: root });
  const planted = readFileSync(join(root, 'marketplace/src/data/unified-search-index.json'));
  assert.throws(
    () => syncUnifiedSearch({ root, check: true }),
    /generated content drift.*unified-search-index\.json/,
  );
  assert.deepEqual(
    readFileSync(join(root, 'marketplace/src/data/unified-search-index.json')),
    planted,
  );
});

test('symlinked documentation and plugin surfaces are refused', (t) => {
  const root = fixtureRoot(t);
  symlinkSync('/etc/passwd', join(root, 'marketplace/src/content/docs/escape.md'));
  assert.throws(() => readDocs(root), /must not be a symlink/);
  rmSync(join(root, 'marketplace/src/content/docs/escape.md'));
  symlinkSync('/etc/passwd', join(root, 'plugins/testing/alpha/agents/escape.md'));
  assert.throws(() => countAgentsAndHooks(root), /must not be a symlink/);
});

test('symlinked required inputs and source roots are refused', (t) => {
  const root = fixtureRoot(t);
  const catalog = join(root, 'marketplace/src/data/catalog.json');
  rmSync(catalog);
  symlinkSync('skills-catalog.json', catalog);
  assert.throws(() => renderUnifiedSearchBytes({ root }), /catalog\.json must not be a symlink/);

  const docs = join(root, 'marketplace/src/content/docs');
  const realDocs = join(root, 'marketplace/src/content/docs-real');
  renameSync(docs, realDocs);
  symlinkSync('docs-real', docs, 'dir');
  assert.throws(() => readDocs(root), /docs must not be a symlink/);

  const secondRoot = fixtureRoot(t);
  const data = join(secondRoot, 'marketplace/src/data');
  const realData = join(secondRoot, 'marketplace/src/data-real');
  renameSync(data, realData);
  symlinkSync('data-real', data, 'dir');
  assert.throws(() => renderUnifiedSearchBytes({ root: secondRoot }), /data must not be a symlink/);
});

test('unreadable counted surface files fail closed', (t) => {
  const root = fixtureRoot(t);
  assert.throws(
    () =>
      countAgentsAndHooks(root, {
        readFile(path) {
          if (path.endsWith('/agents/alpha.md')) throw new Error('EACCES: permission denied');
          return readFileSync(path);
        },
      }),
    /cannot read .*alpha\.md.*EACCES/,
  );
});

test('missing required source surfaces fail closed', (t) => {
  const root = fixtureRoot(t);
  rmSync(join(root, 'marketplace/src/content/docs'), { recursive: true });
  assert.throws(() => readDocs(root), /cannot inspect marketplace\/src\/content\/docs/);
});

test('ordinal comparator is locale-independent for non-ASCII labels', () => {
  assert.deepEqual(['éclair', 'Zulu', 'ångström', 'alpha'].sort(compareOrdinal), [
    'Zulu',
    'alpha',
    'ångström',
    'éclair',
  ]);
});
