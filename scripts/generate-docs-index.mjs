#!/usr/bin/env node

/** Generate the tracked documentation estate index deterministically. */
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { basename, dirname, posix, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const defaultRoot = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const INDEX_PATH = '000-docs/000-INDEX.md';
const EXCLUDED_PATHS = new Set([INDEX_PATH, '000-docs/.gitignore']);
const SAFE_MARKDOWN_PATH = /^[A-Za-z0-9._/-]+$/;

const REFERENCE_TAIL = `## Category / type quick reference

| CC  | Category                |     | CC  | Category                  |
| --- | ----------------------- | --- | --- | ------------------------- |
| PP  | Product & Planning      |     | AT  | Architecture & Technical  |
| DC  | Development & Code      |     | TQ  | Testing & Quality         |
| OD  | Operations & Deployment |     | LS  | Logs & Status             |
| RA  | Reports & Analysis      |     | MC  | Meetings & Communication  |
| PM  | Project Management      |     | DR  | Documentation & Reference |
| UC  | User & Customer         |     | BL  | Business & Legal          |
| RL  | Research & Learning     |     | AA  | After Action & Review     |
| WA  | Workflows & Automation  |     | DD  | Data & Datasets           |
| MS  | Miscellaneous           |     |     |                           |

Filename grammar: \`NNN-CC-ABCD-short-description.ext\` — full standard: the \`/doc-filing\` skill (v4.4).`;

function compareAscii(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function foldAscii(value) {
  return value.replace(/[A-Z]/g, (character) => String.fromCharCode(character.charCodeAt(0) + 32));
}

function sortKey(path) {
  const name = basename(path);
  const numbered = name.match(/^(\d{3})(?:[a-z]|-\d+)?-/i);
  return {
    number: numbered ? Number(numbered[1]) : Number.POSITIVE_INFINITY,
    foldedName: foldAscii(name),
    path,
  };
}

export function trackedDocumentPaths(root = defaultRoot) {
  const output = execFileSync('git', ['-C', root, 'ls-files', '-z', '--', '000-docs'], {
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  });
  const paths = output.split('\0').filter(Boolean);
  if (paths.length === 0) throw new Error('Git reported no tracked paths under 000-docs');
  return paths;
}

export function indexedDocuments(trackedPaths) {
  const seen = new Set();
  const documents = [];
  for (const path of trackedPaths) {
    if (EXCLUDED_PATHS.has(path)) continue;
    if (!path.startsWith('000-docs/'))
      throw new Error(`tracked document path is outside 000-docs: ${JSON.stringify(path)}`);
    const relative = path.slice('000-docs/'.length);
    if (
      !relative ||
      !SAFE_MARKDOWN_PATH.test(relative) ||
      posix.isAbsolute(relative) ||
      posix.normalize(relative) !== relative ||
      relative.split('/').some((segment) => segment === '.' || segment === '..')
    )
      throw new Error(`tracked document path is unsafe for Markdown: ${JSON.stringify(path)}`);
    if (seen.has(path)) throw new Error(`Git returned a duplicate tracked path: ${path}`);
    seen.add(path);
    documents.push(path);
  }
  if (documents.length === 0) throw new Error('tracked documentation inventory is empty');

  return documents.sort((left, right) => {
    const a = sortKey(left);
    const b = sortKey(right);
    return (
      a.number - b.number ||
      compareAscii(a.foldedName, b.foldedName) ||
      compareAscii(a.path.slice('000-docs/'.length), b.path.slice('000-docs/'.length))
    );
  });
}

export function renderDocsIndex(trackedPaths) {
  const documents = indexedDocuments(trackedPaths);
  const rows = documents.map((path) => {
    const target = path.slice('000-docs/'.length);
    return `- [${basename(path)}](${target})`;
  });

  return `<!-- doc-class: generated -->

# 000-INDEX — Documentation Estate Index

> **Generated — do not edit.** Stage newly filed documents, then run
> \`node scripts/generate-docs-index.mjs\`.

Covers the **tracked** documentation estate (${documents.length} files). Local-only working
documents are counted in doc 720 but deliberately not listed here. The inventory excludes only this
index and \`000-docs/.gitignore\`.

## Files (global chronological order)

${rows.join('\n')}

${REFERENCE_TAIL}
`;
}

export function expectedDocsIndex(root = defaultRoot) {
  return renderDocsIndex(trackedDocumentPaths(root));
}

export function checkDocsIndex(root = defaultRoot) {
  const expected = expectedDocsIndex(root);
  const indexPath = resolve(root, INDEX_PATH);
  let actual = '';
  try {
    actual = readFileSync(indexPath, 'utf8');
  } catch (error) {
    throw new Error(`cannot read ${INDEX_PATH}: ${error.message}`);
  }
  return { actual, expected, matches: actual === expected };
}

function main() {
  const args = process.argv.slice(2);
  const check = args[0] === '--check';
  const positional = check ? args.slice(1) : args;
  if (positional.length > 1 || positional.some((argument) => argument.startsWith('-'))) {
    console.error('Usage: node scripts/generate-docs-index.mjs [--check] [repository-root]');
    process.exitCode = 2;
    return;
  }

  try {
    const root = positional[0] ? resolve(positional[0]) : defaultRoot;
    const indexPath = resolve(root, INDEX_PATH);
    const expected = expectedDocsIndex(root);
    if (check) {
      let actual = '';
      try {
        actual = readFileSync(indexPath, 'utf8');
      } catch (error) {
        throw new Error(`cannot read ${INDEX_PATH}: ${error.message}`);
      }
      if (actual !== expected) {
        console.error(
          `docs-index: DRIFT (${INDEX_PATH} is not generated from the tracked inventory)\n` +
            'Run: node scripts/generate-docs-index.mjs',
        );
        process.exitCode = 1;
        return;
      }
      console.log(
        `docs-index: OK (${indexedDocuments(trackedDocumentPaths(root)).length} tracked documents)`,
      );
      return;
    }

    let actual = null;
    try {
      actual = readFileSync(indexPath, 'utf8');
    } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    if (actual !== expected) writeFileSync(indexPath, expected, 'utf8');
    console.log(
      `docs-index: ${actual === expected ? 'unchanged' : 'generated'} (${indexedDocuments(trackedDocumentPaths(root)).length} tracked documents)`,
    );
  } catch (error) {
    console.error(`DOCS_INDEX_ERROR ${error.message}`);
    process.exitCode = 1;
  }
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
