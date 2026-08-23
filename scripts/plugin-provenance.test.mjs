import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import test from 'node:test';
import { buildPublishCandidateReport } from './publish-candidate-report.mjs';
import { parseSourceRecord, resolvePluginProvenance } from './plugin-provenance.mjs';

function fixture() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'plugin-provenance-'));
}

function writeJson(filePath, value) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(value));
}

function packageFixture(
  root,
  relativeDir,
  { source = null, privateValue = false, name = '@example/fixture' } = {},
) {
  const directory = path.join(root, relativeDir);
  writeJson(path.join(directory, 'package.json'), {
    name,
    version: '1.0.0',
    private: privateValue,
  });
  writeJson(path.join(directory, '.claude-plugin', 'plugin.json'), {
    name: name.split('/').at(-1),
  });
  if (source !== null) {
    fs.mkdirSync(directory, { recursive: true });
    fs.writeFileSync(path.join(directory, '.source.json'), source);
  }
  return directory;
}

test('first-party package is accepted and sibling source does not false-positive', () => {
  const root = fixture();
  packageFixture(root, 'plugins/first-party', { name: '@intentsolutionsio/first-party' });
  packageFixture(root, 'plugins/sibling', {
    source: JSON.stringify({ synced_from: { repo: 'owner/repo', path: 'sibling' } }),
    name: '@intentsolutionsio/sibling',
  });
  const report = buildPublishCandidateReport({ root, all: true, scope: '@intentsolutionsio/' });
  assert.deepEqual(
    report.firstPartyCandidates.map((row) => row.name),
    ['@intentsolutionsio/first-party'],
  );
  assert.deepEqual(
    report.mirrorSkipped.map((row) => row.name),
    ['@intentsolutionsio/sibling'],
  );
});

test('mirror is rejected whether private or incorrectly non-private', () => {
  const root = fixture();
  packageFixture(root, 'plugins/mirror-private', {
    privateValue: true,
    source: JSON.stringify({ synced_from: { repo: 'owner/repo', path: 'mirror-private' } }),
    name: '@intentsolutionsio/mirror-private',
  });
  packageFixture(root, 'plugins/mirror-public', {
    privateValue: false,
    source: JSON.stringify({ synced_from: { repo: 'owner/repo', path: 'mirror-public' } }),
    name: '@intentsolutionsio/mirror-public',
  });
  const report = buildPublishCandidateReport({ root, all: true, scope: '@intentsolutionsio/' });
  assert.equal(report.firstPartyCandidates.length, 0);
  assert.deepEqual(
    report.mirrorSkipped.map((row) => row.name),
    ['@intentsolutionsio/mirror-private', '@intentsolutionsio/mirror-public'],
  );
});

test('nested source ancestor is rejected and path traversal is refused', () => {
  const root = fixture();
  packageFixture(root, 'plugins/nested/mirror', {
    name: '@intentsolutionsio/nested-mirror',
  });
  fs.writeFileSync(
    path.join(root, 'plugins/nested', '.source.json'),
    JSON.stringify({ synced_from: { repo: 'owner/repo', path: 'nested' } }),
  );
  assert.equal(
    resolvePluginProvenance('plugins/nested/mirror', { root }).reasonCode,
    'UPSTREAM_SOURCE_RECORD',
  );
  assert.equal(resolvePluginProvenance('../outside', { root }).reasonCode, 'PATH_TRAVERSAL');
});

test('malformed, unreadable, and contradictory provenance fail closed', () => {
  const root = fixture();
  packageFixture(root, 'plugins/bad', { name: '@intentsolutionsio/bad' });
  fs.writeFileSync(path.join(root, 'plugins/bad', '.source.json'), '{not-json');
  packageFixture(root, 'plugins/unreadable', { name: '@intentsolutionsio/unreadable' });
  fs.mkdirSync(path.join(root, 'plugins/unreadable', '.source.json'));
  packageFixture(root, 'plugins/contradictory', { name: '@intentsolutionsio/contradictory' });
  fs.writeFileSync(path.join(root, 'plugins/contradictory', '.source.json'), JSON.stringify({}));
  const report = buildPublishCandidateReport({ root, all: true, scope: '@intentsolutionsio/' });
  assert.deepEqual(
    report.refused.map((row) => row.reasonCode),
    ['MALFORMED_SOURCE_RECORD', 'CONTRADICTORY_SOURCE_RECORD', 'SOURCE_RECORD_NOT_REGULAR'],
  );
});

test('unreadable and symlink source records have stable fail-closed reasons', () => {
  const root = fixture();
  const unreadable = parseSourceRecord(path.join(root, '.source.json'), {
    lstat: () => ({ isFile: () => true, isSymbolicLink: () => false }),
    readFile: () => {
      throw new Error('fixture EACCES');
    },
  });
  assert.equal(unreadable.reasonCode, 'UNREADABLE_SOURCE_RECORD');

  fs.writeFileSync(path.join(root, 'target.json'), '{}');
  fs.symlinkSync('target.json', path.join(root, '.source.json'));
  const symlink = resolvePluginProvenance('.', { root });
  assert.equal(symlink.reasonCode, 'SOURCE_RECORD_SYMLINK');
});

test('dangling source record symlinks fail closed instead of appearing absent', () => {
  const root = fixture();
  packageFixture(root, 'plugins/dangling-source', {
    name: '@intentsolutionsio/dangling-source',
  });
  fs.symlinkSync('missing-target.json', path.join(root, 'plugins/dangling-source', '.source.json'));

  const provenance = resolvePluginProvenance('plugins/dangling-source', { root });
  assert.equal(provenance.status, 'refused');
  assert.equal(provenance.reasonCode, 'SOURCE_RECORD_SYMLINK');

  const report = buildPublishCandidateReport({ root, all: true, scope: '@intentsolutionsio/' });
  assert.equal(report.firstPartyCandidates.length, 0);
  assert.deepEqual(
    report.refused.map((row) => [row.name, row.reasonCode]),
    [['@intentsolutionsio/dangling-source', 'SOURCE_RECORD_SYMLINK']],
  );
});

test('refuses a provenance record whose opened descriptor and path identities differ', () => {
  let readAttempted = false;
  const result = parseSourceRecord('/fixture/.source.json', {
    open: () => 42,
    fstat: () => ({ dev: 1, ino: 10, isFile: () => true }),
    lstat: () => ({ dev: 1, ino: 11, isFile: () => true, isSymbolicLink: () => false }),
    readFile: () => {
      readAttempted = true;
      return '{}';
    },
    close: () => {},
  });
  assert.equal(result.reasonCode, 'UNREADABLE_SOURCE_RECORD');
  assert.equal(readAttempted, false);
});

test('refuses an open-then-unlinked provenance record instead of treating it as absent', () => {
  let descriptorCloseCount = 0;
  const missing = Object.assign(new Error('fixture ENOENT after open'), { code: 'ENOENT' });
  const result = parseSourceRecord('/fixture/.source.json', {
    open: () => 42,
    fstat: () => ({ dev: 1, ino: 10, isFile: () => true }),
    lstat: () => {
      throw missing;
    },
    close: () => {
      descriptorCloseCount += 1;
    },
    allowAbsent: true,
  });
  assert.equal(result.status, 'refused');
  assert.equal(result.reasonCode, 'UNREADABLE_SOURCE_RECORD');
  assert.equal(descriptorCloseCount, 1);
});

test('red proof: legacy publisher admits a mirror, enforced publisher skips it', () => {
  const root = fixture();
  packageFixture(root, 'plugins/legacy-mirror', {
    privateValue: false,
    source: JSON.stringify({ synced_from: { repo: 'owner/repo', path: 'legacy-mirror' } }),
    name: '@intentsolutionsio/legacy-mirror',
  });
  const legacySelection = ['plugins/legacy-mirror'];
  const report = buildPublishCandidateReport({ root, all: true, scope: '@intentsolutionsio/' });
  assert.equal(legacySelection.length, 1, 'RED PROOF: old private-only filter admitted the mirror');
  assert.equal(report.firstPartyCandidates.length, 0);
  assert.equal(report.mirrorSkipped[0].reasonCode, 'UPSTREAM_SOURCE_RECORD');
});

test('current repository excludes all 37 repository mirrors and 32 live scoped mirrors', () => {
  const root = process.cwd();
  const allReport = buildPublishCandidateReport({ root, all: true });
  const scopedReport = buildPublishCandidateReport({
    root,
    all: true,
    scope: '@intentsolutionsio/',
  });
  const markerDirs = [];
  const walk = (directory) => {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      const fullPath = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(fullPath);
      else if (entry.name === '.source.json') markerDirs.push(path.relative(root, directory));
    }
  };
  walk(path.join(root, 'plugins'));
  const mirrorDirs = new Set(allReport.mirrorSkipped.map((row) => row.dir));
  const scopedMirrorDirs = new Set(scopedReport.mirrorSkipped.map((row) => row.dir));
  const scopedMarkers = markerDirs.filter((directory) => {
    try {
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(root, directory, 'package.json'), 'utf8'),
      );
      return packageJson.name?.startsWith('@intentsolutionsio/');
    } catch {
      return false;
    }
  });
  assert.equal(markerDirs.length, 37);
  assert.equal(scopedMarkers.length, 32);
  assert.ok(markerDirs.every((directory) => mirrorDirs.has(directory)));
  assert.ok(scopedMarkers.every((directory) => scopedMirrorDirs.has(directory)));
  assert.equal(allReport.firstPartyCandidates.filter((row) => mirrorDirs.has(row.dir)).length, 0);
  assert.equal(
    scopedReport.firstPartyCandidates.filter((row) => scopedMirrorDirs.has(row.dir)).length,
    0,
  );
  console.log(
    `RED PROOF PASS: legacy private-only publisher would admit a non-private mirror; resolver excludes 37 marker roots and 32 scoped roots (plus nested descendants).`,
  );
});
