import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, rmSync, symlinkSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';

import { checkChangelogCoverage } from './check-changelog-coverage.mjs';

function fixture(t, { notes = ['4.14.0'], tags = ['v4.13.0', 'v4.14.0'] } = {}) {
  const root = mkdtempSync(join(tmpdir(), 'changelog-coverage-'));
  const notesDirectory = join(root, 'marketplace', 'src', 'content', 'blog');
  mkdirSync(notesDirectory, { recursive: true });
  for (const [index, version] of notes.entries()) {
    writeFileSync(
      join(notesDirectory, `release-${index}.md`),
      `---\ntitle: Release ${version}\nversion: "${version}"\n---\n`,
    );
  }
  t.after(() => rmSync(root, { force: true, recursive: true }));
  return { root, readTags: () => `${tags.join('\n')}\n` };
}

test('complete release notes pass with older tags explicitly grandfathered', (t) => {
  const input = fixture(t, {
    notes: ['4.14.0', '4.15.0'],
    tags: ['v4.13.0', 'v4.14.0', 'v4.15.0', 'not-a-version'],
  });
  assert.deepEqual(checkChangelogCoverage(input), {
    documented: 2,
    floor: '4.14.0',
    grandfathered: 1,
    inScope: 2,
    missing: [],
    tags: 3,
  });
});

test('red proof: a tagless checkout is refused instead of silently passing', (t) => {
  assert.throws(
    () => checkChangelogCoverage(fixture(t, { tags: [] })),
    /no strict vX\.Y\.Z tags are visible/,
  );
});

test('Git enumeration failure is refused', (t) => {
  const input = fixture(t);
  input.readTags = () => {
    throw new Error('fixture Git failure');
  };
  assert.throws(() => checkChangelogCoverage(input), /Git tag enumeration failed/);
});

test('an incomplete tag set without the pinned floor is refused', (t) => {
  assert.throws(
    () => checkChangelogCoverage(fixture(t, { notes: ['4.15.0'], tags: ['v4.15.0'] })),
    /pinned floor tag v4\.14\.0 is not visible/,
  );
});

test('deleting the pinned floor note cannot raise the ratchet', (t) => {
  assert.throws(
    () => checkChangelogCoverage(fixture(t, { notes: ['4.15.0'] })),
    /pinned floor v4\.14\.0 has no release notes/,
  );
});

test('a released version without notes is refused', (t) => {
  assert.throws(
    () => checkChangelogCoverage(fixture(t, { notes: ['4.14.0'], tags: ['v4.14.0', 'v4.15.0'] })),
    /v4\.15\.0/,
  );
});

test('malformed release metadata is refused', (t) => {
  const input = fixture(t);
  writeFileSync(
    join(input.root, 'marketplace', 'src', 'content', 'blog', 'malformed.md'),
    '---\ntitle: Broken\nversion: latest\n---\n',
  );
  assert.throws(() => checkChangelogCoverage(input), /malformed release-note version/);
});

test('duplicate release-note versions are refused as ambiguous', (t) => {
  const input = fixture(t, { notes: ['4.14.0', '4.14.0'] });
  assert.throws(() => checkChangelogCoverage(input), /duplicate release notes/);
});

test('a release-note symlink is refused instead of followed', (t) => {
  const input = fixture(t);
  const notesDirectory = join(input.root, 'marketplace', 'src', 'content', 'blog');
  writeFileSync(join(input.root, 'outside.md'), '---\nversion: 4.15.0\n---\n');
  symlinkSync(join(input.root, 'outside.md'), join(notesDirectory, 'linked.md'));
  assert.throws(() => checkChangelogCoverage(input), /release-note path is not a regular file/);
});

test('release notes may be grouped recursively', (t) => {
  const input = fixture(t);
  const nested = join(input.root, 'marketplace', 'src', 'content', 'blog', '2026');
  mkdirSync(nested);
  writeFileSync(join(nested, 'release.md'), '---\nversion: 4.15.0\n---\n');
  input.readTags = () => 'v4.14.0\nv4.15.0\n';
  assert.equal(checkChangelogCoverage(input).documented, 2);
});
