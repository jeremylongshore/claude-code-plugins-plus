import { Buffer } from 'node:buffer';
import { execFile as execFileCallback } from 'node:child_process';
import { chmod, mkdir, mkdtemp, readFile, rm, utimes, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { promisify } from 'node:util';
import Ajv2020 from 'ajv/dist/2020.js';
import { describe, expect, test } from 'vitest';

import {
  PORTABLE_INSTALL_RECEIPT_SCHEMA_VERSION,
  PORTABLE_TREE_ALGORITHM,
  PORTABLE_TREE_FORMAT,
  assertReceiptMatchesAcquisition,
  digestPortableTreeEntries,
  hashPortableTree,
  normalizePortablePath,
  parsePortableInstallReceipt,
  readPortableTreeFromCleanCommit,
  serializePortableInstallReceipt,
  validateCanonicalSkillSourcePath,
  validatePortableInstallReceipt,
  type PortableInstallReceiptV1,
  type PortableTreeInput,
} from './portable-integrity.js';

const execFile = promisify(execFileCallback);
const sourcePath = 'plugins/testing/demo-plugin/skills/demo-skill';
const repository = 'https://github.com/example/portable-skills';

const text = (
  filePath: string,
  value: string,
  mode: '100644' | '100755' = '100644',
): PortableTreeInput => ({
  path: filePath,
  bytes: Buffer.from(value, 'utf8'),
  mode,
});

const checkoutA: PortableTreeInput[] = [
  text('SKILL.md', '---\nname: portable-fixture\n---\n'),
  text('references/guide.md', '# Guide\n'),
  { path: 'fixtures/probe.bin', bytes: Uint8Array.from([0, 255, 1, 128]), mode: '100644' },
];

async function git(cwd: string, ...args: string[]): Promise<string> {
  const result = await execFile('git', args, { cwd, encoding: 'utf8' });
  return result.stdout.trim();
}

async function createRepository(): Promise<{ root: string; commit: string; repository: string }> {
  const root = await mkdtemp(path.join(tmpdir(), 'ccpi-portable-contract-'));
  const skill = path.join(root, sourcePath);
  await mkdir(path.join(skill, 'references'), { recursive: true });
  await mkdir(path.join(skill, 'scripts'), { recursive: true });
  await writeFile(path.join(root, '.gitignore'), 'secret.env\nnode_modules/\n', 'utf8');
  await writeFile(path.join(skill, 'SKILL.md'), '---\nname: demo-skill\n---\n', 'utf8');
  await writeFile(path.join(skill, 'references', 'guide.md'), '# Guide\n', 'utf8');
  await writeFile(path.join(skill, 'scripts', 'run.sh'), '#!/bin/sh\nprintf ok\n', 'utf8');
  await chmod(path.join(skill, 'scripts', 'run.sh'), 0o755);
  await git(root, 'init', '--quiet');
  await git(root, 'config', 'user.name', 'Portable Contract Test');
  await git(root, 'config', 'user.email', 'portable@example.invalid');
  await git(root, 'config', 'core.filemode', 'false');
  await git(root, 'remote', 'add', 'origin', repository);
  await git(root, 'add', '.');
  await git(root, 'update-index', '--chmod=+x', '--', `${sourcePath}/scripts/run.sh`);
  await git(root, 'commit', '--quiet', '-m', 'test: fixture');
  return { root, commit: await git(root, 'rev-parse', 'HEAD'), repository };
}

function receipt(tree = hashPortableTree(checkoutA)): PortableInstallReceiptV1 {
  return {
    schemaVersion: PORTABLE_INSTALL_RECEIPT_SCHEMA_VERSION,
    source: {
      repository,
      commit: { algorithm: 'sha1', digest: 'a'.repeat(40) },
      tree: { algorithm: 'sha1', digest: 'b'.repeat(40) },
      path: sourcePath,
    },
    installation: { harness: 'claude-code', scope: 'project' },
    validation: {
      validator: { name: 'intent-skills-validator', version: '4.2.0' },
      skillSchemaVersion: '4.2.0',
      harnessRegistryVersion: 2,
    },
    tree,
    evidence: [
      {
        kind: 'static-validation',
        uri: `urn:sha256:${'c'.repeat(64)}`,
        sha256: `sha256:${'c'.repeat(64)}`,
        retention: 'indefinite',
      },
    ],
  };
}

describe('portable tree identity', () => {
  test('identical trees hash identically regardless of path order or host metadata', () => {
    const checkoutB = [
      { ...checkoutA[2], bytes: Uint8Array.from([0, 255, 1, 128]) },
      { ...checkoutA[0], bytes: Buffer.from(checkoutA[0].bytes) },
      { ...checkoutA[1], bytes: Buffer.from(checkoutA[1].bytes) },
    ];
    expect(hashPortableTree(checkoutB)).toEqual(hashPortableTree(checkoutA));
  });

  test('content, path, binary, line-ending, and executable-mode changes alter identity', () => {
    const baseline = hashPortableTree(checkoutA).digest;
    const variant = (): PortableTreeInput[] =>
      checkoutA.map((entry) => ({ ...entry, bytes: Uint8Array.from(entry.bytes) }));
    const changedContent = variant();
    changedContent[1].bytes = Buffer.from('# Changed\n');
    const changedLineEnding = variant();
    changedLineEnding[1].bytes = Buffer.from('# Guide\r\n');
    const changedPath = variant();
    changedPath[1].path = 'references/renamed.md';
    const changedBinary = variant();
    changedBinary[2].bytes = Uint8Array.from([0, 255, 1, 129]);
    const changedMode = variant();
    changedMode[0].mode = '100755';
    const variants = [changedContent, changedLineEnding, changedPath, changedBinary, changedMode];
    for (const variant of variants) expect(hashPortableTree(variant).digest).not.toBe(baseline);
  });

  test.each([
    '../escape',
    '/absolute',
    'C:/drive.md',
    '//server/share',
    'references\\windows.md',
    'references//empty.md',
    'references/café.md',
    'references/bidi\u202emd',
    'CON',
    '.git/config',
    '.ccpi-portable-install.json',
  ])('rejects unsafe or non-portable path %s', (filePath) => {
    expect(() => hashPortableTree([checkoutA[0], text(filePath, 'bad')])).toThrow();
  });

  test('rejects duplicate, case-folded, and file/directory prefix collisions', () => {
    expect(() =>
      hashPortableTree([checkoutA[0], text('README.md', 'one'), text('README.md', 'two')]),
    ).toThrow(/duplicate/);
    expect(() =>
      hashPortableTree([checkoutA[0], text('README.md', 'one'), text('readme.md', 'two')]),
    ).toThrow(/case-insensitive/);
    expect(() => hashPortableTree([checkoutA[0], text('a', 'one'), text('a/b', 'two')])).toThrow(
      /prefix collision/,
    );
  });

  test('requires regular supported modes and a root SKILL.md', () => {
    expect(() => hashPortableTree([{ ...checkoutA[0], mode: '120000' as '100644' }])).toThrow(
      /mode/,
    );
    expect(() => hashPortableTree([text('README.md', 'missing')])).toThrow(/SKILL\.md/);
  });

  test('binds the manifest to canonical path, mode, size, and byte digest framing', () => {
    const tree = hashPortableTree(checkoutA);
    expect(tree.format).toBe(PORTABLE_TREE_FORMAT);
    expect(tree.algorithm).toBe(PORTABLE_TREE_ALGORITHM);
    expect(tree.digest).toBe(digestPortableTreeEntries(tree.entries));
    expect(tree.fileCount).toBe(3);
    expect(tree.byteCount).toBe(checkoutA.reduce((sum, entry) => sum + entry.bytes.byteLength, 0));
  });
});

describe('immutable Git source acquisition', { timeout: 20_000 }, () => {
  test('two clean checkouts at different host paths produce the same tree identity', async () => {
    const fixture = await createRepository();
    const cloneParent = await mkdtemp(path.join(tmpdir(), 'ccpi-portable-clone-'));
    const cloneRoot = path.join(cloneParent, 'different-checkout-root');
    try {
      await git(cloneParent, 'clone', '--quiet', '--no-local', fixture.root, cloneRoot);
      await git(cloneRoot, 'remote', 'set-url', 'origin', repository);
      const first = await readPortableTreeFromCleanCommit({
        ...fixture,
        repoRoot: fixture.root,
        sourcePath,
      });
      const second = await readPortableTreeFromCleanCommit({
        repoRoot: cloneRoot,
        repository,
        commit: fixture.commit,
        sourcePath,
      });
      expect(second.manifest).toEqual(first.manifest);
      expect(first.sourceTree.digest).toMatch(/^[0-9a-f]{40}$/);
      expect(first.manifest.entries.find((entry) => entry.path === 'scripts/run.sh')?.mode).toBe(
        '100755',
      );

      await utimes(path.join(cloneRoot, sourcePath, 'SKILL.md'), new Date(0), new Date());
      const changedMtime = await readPortableTreeFromCleanCommit({
        repoRoot: cloneRoot,
        repository,
        commit: fixture.commit,
        sourcePath,
      });
      expect(changedMtime.manifest).toEqual(first.manifest);
    } finally {
      await rm(fixture.root, { recursive: true, force: true });
      await rm(cloneParent, { recursive: true, force: true });
    }
  });

  test.each(['untracked', 'ignored', 'modified', 'deleted', 'staged'])(
    'rejects %s source state',
    async (state) => {
      const fixture = await createRepository();
      try {
        if (state === 'untracked')
          await writeFile(path.join(fixture.root, sourcePath, 'untracked.txt'), 'no');
        if (state === 'ignored')
          await writeFile(path.join(fixture.root, sourcePath, 'secret.env'), 'TOKEN=no');
        if (state === 'modified')
          await writeFile(path.join(fixture.root, sourcePath, 'SKILL.md'), 'changed');
        if (state === 'deleted')
          await rm(path.join(fixture.root, sourcePath, 'references', 'guide.md'));
        if (state === 'staged') {
          await writeFile(path.join(fixture.root, sourcePath, 'SKILL.md'), 'changed');
          await git(fixture.root, 'add', path.join(sourcePath, 'SKILL.md'));
        }
        await expect(
          readPortableTreeFromCleanCommit({ ...fixture, repoRoot: fixture.root, sourcePath }),
        ).rejects.toThrow(/staged, modified, deleted, untracked, or ignored/);
      } finally {
        await rm(fixture.root, { recursive: true, force: true });
      }
    },
  );

  test('rejects mutable refs, generated roots, upstream mirrors, and Git symlinks', async () => {
    expect(() => validateCanonicalSkillSourcePath('skills/.curated/demo-skill')).toThrow(
      /generated root/,
    );
    expect(normalizePortablePath('references/quick-start-(5-minutes).md')).toBe(
      'references/quick-start-(5-minutes).md',
    );

    const mutable = await createRepository();
    try {
      await expect(
        readPortableTreeFromCleanCommit({
          repoRoot: mutable.root,
          repository: 'https://github.com/example/wrong-repository',
          commit: mutable.commit,
          sourcePath,
        }),
      ).rejects.toThrow(/origin repository identity/);
      await expect(
        readPortableTreeFromCleanCommit({
          repoRoot: mutable.root,
          repository,
          commit: 'HEAD',
          sourcePath,
        }),
      ).rejects.toThrow(/full lowercase Git/);
    } finally {
      await rm(mutable.root, { recursive: true, force: true });
    }

    for (const marker of [
      '.source.json',
      'plugins/.source.json',
      'plugins/testing/.source.json',
      'plugins/testing/demo-plugin/.source.json',
      `${sourcePath}/.source.json`,
    ]) {
      const mirror = await createRepository();
      try {
        await writeFile(path.join(mirror.root, marker), '{}');
        await git(mirror.root, 'add', '.');
        await git(mirror.root, 'commit', '--quiet', '-m', 'test: mirror');
        mirror.commit = await git(mirror.root, 'rev-parse', 'HEAD');
        await expect(
          readPortableTreeFromCleanCommit({ ...mirror, repoRoot: mirror.root, sourcePath }),
        ).rejects.toThrow(/mirror/);
      } finally {
        await rm(mirror.root, { recursive: true, force: true });
      }
    }

    const linked = await createRepository();
    try {
      const linkedPath = `${sourcePath}/linked.md`;
      await writeFile(path.join(linked.root, linkedPath), '../../../../../../outside');
      const linkedBlob = await git(linked.root, 'hash-object', '-w', '--', linkedPath);
      await git(
        linked.root,
        'update-index',
        '--add',
        '--cacheinfo',
        `120000,${linkedBlob},${linkedPath}`,
      );
      await git(linked.root, 'commit', '--quiet', '-m', 'test: symlink');
      await git(linked.root, 'config', 'core.symlinks', 'false');
      await git(linked.root, 'reset', '--hard', '--quiet', 'HEAD');
      linked.commit = await git(linked.root, 'rev-parse', 'HEAD');
      await expect(
        readPortableTreeFromCleanCommit({ ...linked, repoRoot: linked.root, sourcePath }),
      ).rejects.toThrow(/unsupported Git entry/);
    } finally {
      await rm(linked.root, { recursive: true, force: true });
    }
  });
});

describe('portable install receipt v1', () => {
  test('accepts, canonically serializes, and parses a complete immutable receipt', () => {
    const expected = receipt();
    expect(validatePortableInstallReceipt(expected)).toEqual(expected);
    const encoded = serializePortableInstallReceipt(expected);
    expect(parsePortableInstallReceipt(encoded)).toEqual(expected);
  });

  test('binds repository, commit, source tree, source path, and manifest to acquisition', async () => {
    const fixture = await createRepository();
    try {
      const acquisition = await readPortableTreeFromCleanCommit({
        ...fixture,
        repoRoot: fixture.root,
        sourcePath,
      });
      const bound = receipt(acquisition.manifest);
      bound.source.repository = acquisition.repository;
      bound.source.commit = acquisition.commit;
      bound.source.tree = acquisition.sourceTree;
      expect(assertReceiptMatchesAcquisition(bound, acquisition)).toEqual(bound);

      const wrongRepository = structuredClone(bound);
      wrongRepository.source.repository = 'https://github.com/example/other-skills';
      expect(() => assertReceiptMatchesAcquisition(wrongRepository, acquisition)).toThrow(
        /repository does not match/,
      );
      const wrongCommit = structuredClone(bound);
      wrongCommit.source.commit.digest = 'd'.repeat(40);
      expect(() => assertReceiptMatchesAcquisition(wrongCommit, acquisition)).toThrow(
        /commit does not match/,
      );
      const wrongTree = structuredClone(bound);
      wrongTree.source.tree.digest = 'd'.repeat(40);
      expect(() => assertReceiptMatchesAcquisition(wrongTree, acquisition)).toThrow(
        /source tree does not match/,
      );
      const wrongPath = structuredClone(bound);
      wrongPath.source.path = 'plugins/testing/demo-plugin/skills/other-skill';
      expect(() => assertReceiptMatchesAcquisition(wrongPath, acquisition)).toThrow(
        /source path does not match/,
      );
      const wrongManifest = structuredClone(bound);
      wrongManifest.tree = hashPortableTree(checkoutA);
      expect(() => assertReceiptMatchesAcquisition(wrongManifest, acquisition)).toThrow(
        /tree manifest does not match/,
      );
    } finally {
      await rm(fixture.root, { recursive: true, force: true });
    }
  });

  test('rejects mutable provenance, noncanonical sources, mismatched object formats, and private data', () => {
    const obsoleteRegistry = structuredClone(receipt());
    obsoleteRegistry.validation.harnessRegistryVersion = 1;
    expect(() => validatePortableInstallReceipt(obsoleteRegistry)).toThrow(/must be 2 or newer/);

    const badCommit = structuredClone(receipt());
    badCommit.source.commit.digest = 'main';
    expect(() => validatePortableInstallReceipt(badCommit)).toThrow(/does not match sha1/);

    const generated = structuredClone(receipt());
    generated.source.path = 'skills/.curated/demo-skill';
    expect(() => validatePortableInstallReceipt(generated)).toThrow(/generated root/);

    const mixedHashes = structuredClone(receipt());
    mixedHashes.source.tree = { algorithm: 'sha256', digest: 'd'.repeat(64) };
    expect(() => validatePortableInstallReceipt(mixedHashes)).toThrow(/algorithms must match/);

    const leakedDestination = structuredClone(receipt()) as unknown as Record<string, unknown>;
    leakedDestination.destination = '/Users/alice/private';
    expect(() => validatePortableInstallReceipt(leakedDestination)).toThrow(
      /receipt must contain exactly/,
    );
  });

  test('rejects malformed, noncanonical, duplicate-key, unknown-field, and oversized JSON', () => {
    for (const invalid of [
      '',
      'null',
      '[]',
      '{',
      '{"__proto__":{}}',
      ' '.repeat(1024 * 1024 + 1),
    ]) {
      expect(() => parsePortableInstallReceipt(invalid)).toThrow();
    }
    const encoded = serializePortableInstallReceipt(receipt());
    expect(() => parsePortableInstallReceipt(` ${encoded}`)).toThrow(/canonical minified/);
    expect(() =>
      parsePortableInstallReceipt(
        encoded.replace(
          '{"schemaVersion":',
          '{"schemaVersion":"portable-install-receipt/v1","schemaVersion":',
        ),
      ),
    ).toThrow(/duplicate keys/);
  });

  test('rejects internally inconsistent tree and evidence assertions', () => {
    const changedDigest = structuredClone(receipt());
    changedDigest.tree.entries[0].sha256 = `sha256:${'d'.repeat(64)}`;
    expect(() => validatePortableInstallReceipt(changedDigest)).toThrow(/tree\.digest/);

    const evidenceMismatch = structuredClone(receipt());
    evidenceMismatch.evidence[0].sha256 = `sha256:${'e'.repeat(64)}`;
    expect(() => validatePortableInstallReceipt(evidenceMismatch)).toThrow(/URI and digest/);

    const noEvidence = structuredClone(receipt());
    noEvidence.evidence = [];
    expect(() => validatePortableInstallReceipt(noEvidence)).toThrow(/non-empty/);

    const oversized = structuredClone(receipt());
    oversized.tree.entries[0].size = 64 * 1024 * 1024 + 1;
    oversized.tree.byteCount = oversized.tree.entries.reduce((sum, entry) => sum + entry.size, 0);
    oversized.tree.digest = digestPortableTreeEntries(oversized.tree.entries);
    expect(() => validatePortableInstallReceipt(oversized)).toThrow(/portable limit/);
  });

  test('ships a strict versioned JSON Schema with the receipt contract', async () => {
    const schemaUrl = new URL(
      '../../schemas/portable-install-receipt-v1.schema.json',
      import.meta.url,
    );
    const schema = JSON.parse(await readFile(schemaUrl, 'utf8')) as Record<string, unknown>;
    expect(schema.$id).toBe('urn:tonsofskills:schema:portable-install-receipt:v1');
    expect(schema.additionalProperties).toBe(false);
    expect(schema.required).toEqual([
      'schemaVersion',
      'source',
      'installation',
      'validation',
      'tree',
      'evidence',
    ]);
    const validateSchema = new Ajv2020({ strict: true }).compile(schema);
    expect(validateSchema(receipt())).toBe(true);

    const wrongCommitLength = structuredClone(receipt());
    wrongCommitLength.source.commit.digest = 'a'.repeat(64);
    expect(validateSchema(wrongCommitLength)).toBe(false);
    const gitSuffix = structuredClone(receipt());
    gitSuffix.source.repository = 'https://github.com/example/portable-skills.git';
    expect(validateSchema(gitSuffix)).toBe(false);
    const nonPortablePath = structuredClone(receipt());
    nonPortablePath.tree.entries[0].path = 'references/café.md';
    expect(validateSchema(nonPortablePath)).toBe(false);
    const obsoleteRegistry = structuredClone(receipt());
    obsoleteRegistry.validation.harnessRegistryVersion = 1;
    expect(validateSchema(obsoleteRegistry)).toBe(false);

    for (const [candidate, expected] of [
      [sourcePath, true],
      ['skills/demo-skill', false],
      ['plugins/testing/demo-plugin/skills/demo-skill/extra', false],
      ['plugins/Testing/demo-plugin/skills/demo-skill', false],
      ['plugins/testing/demo-plugin/skills/demo_skill', false],
    ] as const) {
      const candidateReceipt = structuredClone(receipt());
      candidateReceipt.source.path = candidate;
      expect(validateSchema(candidateReceipt), `JSON Schema source path: ${candidate}`).toBe(
        expected,
      );
      expect(
        (() => {
          try {
            validateCanonicalSkillSourcePath(candidate);
            return true;
          } catch {
            return false;
          }
        })(),
        `runtime source path: ${candidate}`,
      ).toBe(expected);
    }

    const registryUrl = new URL('../../../../config/harness-registry.json', import.meta.url);
    const registry = JSON.parse(await readFile(registryUrl, 'utf8')) as {
      schemaVersion: number;
      portableArtifact: { source: string };
    };
    expect(registry.schemaVersion).toBe(2);
    expect(registry.portableArtifact.source).toBe('plugins/<category>/<plugin>/skills/<skill>/');
  });
});
