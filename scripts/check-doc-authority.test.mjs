import { deepEqual, equal, match, throws } from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import {
  canonicalDocumentLinks,
  checkAuthorityGraph,
  effectiveAuthorityClaim,
  formatAuthorityReport,
  scanRepository,
} from './check-doc-authority.mjs';

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const fixtureRoot = join(repositoryRoot, 'tests', 'fixtures', 'doc-authority');
const fixture = (path) => readFileSync(join(fixtureRoot, path), 'utf8');
const document = (path) => ({ path: `000-docs/${path}`, contents: fixture(`documents/${path}`) });

test('linked direct and activated-conditional statuses pass while doc-class grants no authority', () => {
  const result = checkAuthorityGraph({
    standardsText: fixture('STANDARDS.md'),
    documents: [document('linked.md'), document('conditional.md'), document('canonical-class.md')],
  });
  deepEqual(
    result.claimants.map((item) => [item.path, item.kind]),
    [
      ['000-docs/linked.md', 'STATUS_AUTHORITATIVE'],
      ['000-docs/conditional.md', 'STATUS_AUTHORITATIVE'],
    ],
  );
  deepEqual(result.findings, []);
});

test('unlinked authority claim is a stable red proof', () => {
  const result = checkAuthorityGraph({
    standardsText: fixture('STANDARDS.md'),
    documents: [document('unlinked.md'), document('masked.md')],
  });
  equal(result.findings.length, 2);
  equal(result.findings[0].reason, 'DOC_AUTHORITY_UNLINKED');
  equal(result.findings[1].reason, 'DOC_AUTHORITY_AMBIGUOUS_STATUS');
  match(formatAuthorityReport(result), /unlinked\.md:3 declares STATUS_CANONICAL/);
});

test('command-line gate exits non-zero for a planted unlinked claimant', () => {
  const root = mkdtempSync(join(tmpdir(), 'doc-authority-red-'));
  try {
    mkdirSync(join(root, '000-docs'), { recursive: true });
    writeFileSync(join(root, 'STANDARDS.md'), fixture('STANDARDS.md'));
    writeFileSync(join(root, '000-docs', 'linked.md'), fixture('documents/linked.md'));
    writeFileSync(join(root, '000-docs', 'conditional.md'), fixture('documents/conditional.md'));
    writeFileSync(join(root, '000-docs', 'unlinked.md'), fixture('documents/unlinked.md'));
    execFileSync('git', ['init', '--quiet'], { cwd: root });
    execFileSync(
      'git',
      [
        'add',
        'STANDARDS.md',
        '000-docs/linked.md',
        '000-docs/conditional.md',
        '000-docs/unlinked.md',
      ],
      { cwd: root },
    );

    const result = spawnSync(
      process.execPath,
      [join(repositoryRoot, 'scripts/check-doc-authority.mjs'), root],
      {
        encoding: 'utf8',
      },
    );
    equal(result.status, 1);
    match(result.stderr, /DOC_AUTHORITY_UNLINKED 000-docs\/unlinked\.md:3/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('ordinary prose, fenced examples, doc-class, frozen history, and references grant no authority', () => {
  for (const path of [
    'ordinary.md',
    'fenced.md',
    'canonical-class.md',
    'frozen.md',
    'reference.md',
  ])
    equal(effectiveAuthorityClaim(fixture(`documents/${path}`)), null, path);
  equal(effectiveAuthorityClaim(fixture('documents/near-frozen.md')).kind, 'STATUS_CANONICAL');
});

test('equivalent preamble status metadata forms cannot evade detection', () => {
  for (const status of [
    '**Status:** **AUTHORITATIVE**',
    '> **Status:** `CANONICAL`',
    '> > **Status:** AUTHORITATIVE',
    '- **Status:** CANONICAL',
  ]) {
    match(effectiveAuthorityClaim(`# Fixture\n\n${status}\n`).kind, /^STATUS_/);
  }
  equal(effectiveAuthorityClaim('# Fixture\n\n## History\n\n**Status:** CANONICAL\n'), null);
  equal(effectiveAuthorityClaim('# Fixture\n\n---\n\n**Status:** CANONICAL\n'), null);
  equal(effectiveAuthorityClaim('# Fixture\n\n<!-- **Status:** AUTHORITATIVE -->\n'), null);
});

test('canonical table parser fails closed when its section or links disappear', () => {
  throws(() => canonicalDocumentLinks('# Standards\n'), /exactly one/);
  throws(
    () => canonicalDocumentLinks('## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n'),
    /no data rows/,
  );
  throws(
    () => canonicalDocumentLinks(`${fixture('STANDARDS.md')}\n## Canonical documents\n`),
    /found 2/,
  );
  throws(
    () =>
      canonicalDocumentLinks(
        '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Bad | [external](https://example.com/x.md) |\n',
      ),
    /invalid canonical Document link/,
  );
  throws(
    () => canonicalDocumentLinks(fixture('STANDARDS.md'), new Set(['000-docs/linked.md'])),
    /not tracked: 000-docs\/conditional.md/,
  );
  throws(
    () =>
      canonicalDocumentLinks(
        '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Bad | [escape](../outside.md) |\n',
      ),
    /escapes the repository/,
  );
  throws(
    () =>
      canonicalDocumentLinks(
        '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Missing document cell |\n',
      ),
    /malformed Canonical documents row/,
  );
  throws(
    () =>
      canonicalDocumentLinks(
        '## Canonical documents\n\n| Topic | Document |\n| --- | invalid |\n| Bad | [linked](000-docs/linked.md) |\n',
      ),
    /delimiter row/,
  );
  throws(
    () =>
      canonicalDocumentLinks(
        '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Bad | ~~[linked](000-docs/linked.md)~~ |\n',
      ),
    /one active link/,
  );
  const noncontiguous = canonicalDocumentLinks(
    '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Good | [linked](000-docs/linked.md) |\n\nProse ends the table.\n\n| Bad | [later](000-docs/later.md) |\n',
  );
  deepEqual([...noncontiguous], ['000-docs/linked.md']);
  const fencedFake = canonicalDocumentLinks(
    '```markdown\n## Canonical documents\n| Topic | Document |\n| --- | --- |\n| Fake | [fake](000-docs/fake.md) |\n```\n\n## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Good | [linked](000-docs/linked.md) |\n',
  );
  deepEqual([...fencedFake], ['000-docs/linked.md']);
  const commentedFake = canonicalDocumentLinks(
    '<!--\n## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Hidden | [hidden](000-docs/hidden.md) |\n-->\n\n## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Good | [linked](000-docs/linked.md) |\n',
  );
  deepEqual([...commentedFake], ['000-docs/linked.md']);
  throws(
    () =>
      canonicalDocumentLinks(
        '```markdown\n## Canonical documents\n| Topic | Document |\n| --- | --- |\n| Hidden | [hidden](000-docs/hidden.md) |\n```not-a-closing-fence\n| Still hidden | [hidden](000-docs/hidden.md) |\n```\n',
      ),
    /found 0/,
  );
  const fourSpacePseudoFence = canonicalDocumentLinks(
    '    ```markdown\n## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Good | [linked](000-docs/linked.md) |\n',
  );
  deepEqual([...fourSpacePseudoFence], ['000-docs/linked.md']);
  const tildeFake = canonicalDocumentLinks(
    '~~~markdown\n## Canonical documents\n| Topic | Document |\n| --- | --- |\n| Hidden | [hidden](000-docs/hidden.md) |\n~~~\n\n## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| Good | [linked](000-docs/linked.md) |\n',
  );
  deepEqual([...tildeFake], ['000-docs/linked.md']);
});

test('Topic-column and later prose links cannot grant authority', () => {
  const standardsText =
    '## Canonical documents\n\n| Topic | Document |\n| --- | --- |\n| [unlinked](000-docs/unlinked.md) | [linked](000-docs/linked.md) |\n\n[unlinked](000-docs/unlinked.md)\n';
  const result = checkAuthorityGraph({ standardsText, documents: [document('unlinked.md')] });
  equal(result.findings[0].reason, 'DOC_AUTHORITY_UNLINKED');
});

test('live repository has only linked effective claimants', () => {
  const result = scanRepository(repositoryRoot);
  deepEqual(result.findings, []);
  // 14 since E9.1 added the cross-repository authority contract (13 was the
  // E4.1 state after the safety enforcement register joined the table).
  equal(result.canonicalLinks.size, 14);
  deepEqual(result.claimants.map((item) => item.path).sort(), [
    '000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md',
    '000-docs/727-AT-ARCH-master-modernization-blueprint.md',
    '000-docs/790-DR-STND-safety-enforcement-register.md',
    '000-docs/806-AT-ARCH-cross-repo-authority-contract.md',
  ]);
  equal(
    result.claimants.find((item) => item.path.startsWith('000-docs/727-')).kind,
    'STATUS_AUTHORITATIVE',
  );
});
