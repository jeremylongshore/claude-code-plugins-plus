import { deepEqual, equal, match, throws } from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { test } from 'node:test';
import { indexedDocuments, renderDocsIndex, trackedDocumentPaths } from './generate-docs-index.mjs';

const repositoryRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const command = join(repositoryRoot, 'scripts', 'generate-docs-index.mjs');
// Build the fixture root at runtime so the repository citation auditor does not
// mistake synthetic test paths for live documentation references.
const docsDirectory = ['000', 'docs'].join('-');
const docsPath = (path) => `${docsDirectory}/${path}`;

function temporaryRepository() {
  const root = mkdtempSync(join(tmpdir(), 'docs-index-'));
  mkdirSync(join(root, docsDirectory, '_archive', 'ms-oldv'), { recursive: true });
  execFileSync('git', ['init', '--quiet'], { cwd: root });
  for (const [path, contents = 'fixture\n'] of [
    [docsPath('.gitignore'), '*\n!000-INDEX.md\n'],
    [docsPath('000-INDEX.md'), 'stale\n'],
    [docsPath('010-AA-AACR-review.md')],
    [docsPath('002-RA-DATA-data.json'), '{}\n'],
    [docsPath('_archive/ms-oldv/003-MS-OLDV-old.md')],
    [docsPath('legacy-note.md')],
  ]) {
    const absolute = join(root, path);
    mkdirSync(dirname(absolute), { recursive: true });
    writeFileSync(absolute, contents);
  }
  execFileSync('git', ['add', '-f', docsDirectory], { cwd: root });
  writeFileSync(join(root, docsDirectory, '999-AA-AACR-untracked.md'), 'untracked\n');
  return root;
}

test('inventory excludes only controls and orders numbered, archived, and legacy documents', () => {
  const tracked = [
    docsPath('.gitignore'),
    docsPath('000-INDEX.md'),
    docsPath('020-AA-AACR-later.md'),
    docsPath('003b-AA-AACR-subdoc.md'),
    docsPath('003-2-AA-AACR-subpart.md'),
    docsPath('_archive/ms-oldv/003-AA-AACR-archive.md'),
    docsPath('003-AA-AACR-root.md'),
    docsPath('20260131-RL-REPT-release.md'),
    docsPath('6767-b-SPEC-DR-STND-standard.md'),
    docsPath('README.md'),
    docsPath('SCHEMA_CHANGELOG.md'),
    docsPath('asset.png'),
    docsPath('z/A.md'),
    docsPath('a/a.md'),
    docsPath('diagram.mmd'),
    docsPath('data.json'),
    docsPath('license.txt'),
  ];
  deepEqual(indexedDocuments(tracked), [
    docsPath('003-2-AA-AACR-subpart.md'),
    docsPath('_archive/ms-oldv/003-AA-AACR-archive.md'),
    docsPath('003-AA-AACR-root.md'),
    docsPath('003b-AA-AACR-subdoc.md'),
    docsPath('020-AA-AACR-later.md'),
    docsPath('20260131-RL-REPT-release.md'),
    docsPath('6767-b-SPEC-DR-STND-standard.md'),
    docsPath('a/a.md'),
    docsPath('z/A.md'),
    docsPath('asset.png'),
    docsPath('data.json'),
    docsPath('diagram.mmd'),
    docsPath('license.txt'),
    docsPath('README.md'),
    docsPath('SCHEMA_CHANGELOG.md'),
  ]);
});

test('rendered index owns its marker, count, archived target, reference tail, and newline', () => {
  const rendered = renderDocsIndex([
    docsPath('.gitignore'),
    docsPath('000-INDEX.md'),
    docsPath('001-AA-AACR-root.md'),
    docsPath('_archive/ms-oldv/002-MS-OLDV-old.md'),
  ]);
  match(rendered, /^<!-- doc-class: generated -->\n\n# 000-INDEX/);
  match(rendered, /tracked\*\* documentation estate \(2 files\)/);
  match(rendered, /\[002-MS-OLDV-old\.md\]\(_archive\/ms-oldv\/002-MS-OLDV-old\.md\)/);
  match(rendered, /## Category \/ type quick reference/);
  match(rendered, /Filename grammar:/);
  equal(rendered.endsWith('\n'), true);
});

test('unsafe, duplicate, outside, and empty inventories fail closed', () => {
  throws(() => indexedDocuments([]), /inventory is empty/);
  throws(() => indexedDocuments(['outside.md']), /outside 000-docs/);
  throws(() => indexedDocuments([docsPath('a.md'), docsPath('a.md')]), /duplicate tracked path/);
  throws(() => indexedDocuments([docsPath('bad(name).md')]), /unsafe for Markdown/);
  for (const path of [
    docsPath('../outside.md'),
    docsPath('bad#fragment.md'),
    docsPath('bad?query.md'),
    docsPath('bad%20name.md'),
    docsPath('bad\\name.md'),
    docsPath('bad name.md'),
    docsPath('bad\tname.md'),
  ])
    throws(() => indexedDocuments([path]), /unsafe for Markdown/, path);
});

test('write mode uses tracked files and check mode detects drift without repairing it', () => {
  const root = temporaryRepository();
  try {
    const write = spawnSync(process.execPath, [command, root], { cwd: root, encoding: 'utf8' });
    equal(write.status, 0, write.stderr);
    match(write.stdout, /docs-index: generated \(4 tracked documents\)/);
    const generated = readFileSync(join(root, docsDirectory, '000-INDEX.md'), 'utf8');
    match(generated, /\(4 files\)/);
    match(generated, /_archive\/ms-oldv\/003-MS-OLDV-old\.md/);
    equal(generated.includes('999-AA-AACR-untracked.md'), false);

    const clean = spawnSync(process.execPath, [command, '--check', root], {
      cwd: root,
      encoding: 'utf8',
    });
    equal(clean.status, 0, clean.stderr);

    const dataRow = '- [002-RA-DATA-data.json](002-RA-DATA-data.json)';
    const archiveRow = '- [003-MS-OLDV-old.md](_archive/ms-oldv/003-MS-OLDV-old.md)';
    const mutations = [
      generated.replace('(4 files)', '(999 files)'),
      generated.replace(`${dataRow}\n`, ''),
      generated.replace(`${dataRow}\n${archiveRow}`, `${archiveRow}\n${dataRow}`),
      generated.replace('MS  | Miscellaneous', 'MS  | Mutated'),
    ];
    for (const stale of mutations) {
      writeFileSync(join(root, docsDirectory, '000-INDEX.md'), stale);
      const red = spawnSync(process.execPath, [command, '--check', root], {
        cwd: root,
        encoding: 'utf8',
      });
      equal(red.status, 1);
      match(red.stderr, /docs-index: DRIFT/);
      equal(readFileSync(join(root, docsDirectory, '000-INDEX.md'), 'utf8'), stale);
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('new documents enter the index only after they are staged', () => {
  const root = temporaryRepository();
  try {
    execFileSync(process.execPath, [command, root], { cwd: root });
    const before = readFileSync(join(root, docsDirectory, '000-INDEX.md'), 'utf8');
    const newPath = join(root, docsDirectory, '011-AA-AACR-new.md');
    writeFileSync(newPath, 'new filing\n');
    execFileSync(process.execPath, [command, root], { cwd: root });
    equal(readFileSync(join(root, docsDirectory, '000-INDEX.md'), 'utf8'), before);

    execFileSync('git', ['add', '-f', docsPath('011-AA-AACR-new.md')], { cwd: root });
    execFileSync(process.execPath, [command, root], { cwd: root });
    const after = readFileSync(join(root, docsDirectory, '000-INDEX.md'), 'utf8');
    match(after, /\(5 files\)/);
    match(after, /011-AA-AACR-new\.md/);
    equal(after.includes('999-AA-AACR-untracked.md'), false);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('Git inventory failure and unknown arguments are visible and non-destructive', () => {
  const root = mkdtempSync(join(tmpdir(), 'docs-index-no-git-'));
  try {
    mkdirSync(join(root, docsDirectory));
    const sentinel = 'do not truncate\n';
    writeFileSync(join(root, docsDirectory, '000-INDEX.md'), sentinel);
    const failedGit = spawnSync(process.execPath, [command, root], { cwd: root, encoding: 'utf8' });
    equal(failedGit.status, 1);
    match(failedGit.stderr, /DOCS_INDEX_ERROR/);
    equal(readFileSync(join(root, docsDirectory, '000-INDEX.md'), 'utf8'), sentinel);

    const usage = spawnSync(process.execPath, [command, '--write'], {
      cwd: repositoryRoot,
      encoding: 'utf8',
    });
    equal(usage.status, 2);
    match(usage.stderr, /Usage:/);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});

test('live Git inventory renders the committed index exactly', () => {
  const tracked = trackedDocumentPaths(repositoryRoot);
  equal(indexedDocuments(tracked).length, tracked.length - 2);
  equal(
    renderDocsIndex(tracked),
    readFileSync(join(repositoryRoot, docsDirectory, '000-INDEX.md'), 'utf8'),
  );
});
