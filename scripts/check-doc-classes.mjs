#!/usr/bin/env node

/**
 * Enforce the machine-readable class of every tracked Markdown document.
 *
 * This check deliberately owns only class syntax and the frozen/generated
 * boundaries. Authority remains owned by STANDARDS.md and the authority gate.
 */
import { execFileSync, spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(fileURLToPath(new URL('..', import.meta.url)));
export const VALID_CLASSES = new Set(['canonical', 'generated', 'frozen', 'record']);
const MARKER = /^<!-- doc-class: ([a-z-]+) -->\n/;
const DOC_PREFIX = '000-docs/';
const INDEX = `${DOC_PREFIX}000-INDEX.md`;
const BASELINE_REF = process.env.DOC_CLASS_BASELINE_REF || 'origin/main';

const FROZEN = new Set([
  `${DOC_PREFIX}6767-a-SPEC-DR-STND-claude-code-plugins-standard.md`,
  `${DOC_PREFIX}6767-c-DR-STND-claude-code-extensions-standard.md`,
  `${DOC_PREFIX}6767-d-AT-APIS-claude-code-extensions-schema.md`,
  `${DOC_PREFIX}6767-e-WA-WFLW-extensions-validation-ci-gates.md`,
  `${DOC_PREFIX}6767-h-SPEC-DR-STND-claude-code-extensions-master.md`,
]);

// These are the repository's current contract owners from blueprint 727 §11.
// A class marker never grants authority; STANDARDS.md remains the authority
// pointer and scripts/check-doc-authority.mjs remains the authority gate.
const CANONICAL = new Set([
  `${DOC_PREFIX}000-DR-STND-document-filing-system.md`,
  `${DOC_PREFIX}6767-b-SPEC-DR-STND-claude-skills-standard.md`,
  `${DOC_PREFIX}694-AT-DECR-external-sync-mirror-by-default-model.md`,
  `${DOC_PREFIX}700-DR-GUID-skill-submission-standard.md`,
  `${DOC_PREFIX}709-DR-GUID-reviewing-external-prs.md`,
  `${DOC_PREFIX}718-AT-ARCH-source-of-truth-map.md`,
  `${DOC_PREFIX}727-AT-ARCH-master-modernization-blueprint.md`,
  `${DOC_PREFIX}728-RA-DATA-reference-architecture-benchmark.md`,
  `${DOC_PREFIX}729-AT-ADEC-reference-architecture-synthesis.md`,
  `${DOC_PREFIX}790-DR-STND-safety-enforcement-register.md`,
  `${DOC_PREFIX}806-AT-ARCH-cross-repo-authority-contract.md`,
  `${DOC_PREFIX}807-DR-STND-evaluation-evidence.md`,
  `${DOC_PREFIX}808-DR-STND-certification-standard.md`,
  `${DOC_PREFIX}SCHEMA_CHANGELOG.md`,
]);

export function expectedClass(path) {
  if (FROZEN.has(path)) return 'frozen';
  if (path === INDEX) return 'generated';
  if (CANONICAL.has(path)) return 'canonical';
  return 'record';
}

export function parseDocClass(text) {
  const match = text.match(MARKER);
  if (!match) {
    return {
      className: null,
      reason: text.startsWith('<!-- doc-class:') ? 'MALFORMED_MARKER' : 'MISSING_MARKER',
    };
  }
  const className = match[1];
  if (!VALID_CLASSES.has(className)) return { className, reason: 'UNKNOWN_CLASS' };
  return { className, reason: null };
}

export function compareFrozenBytes(current, baseline, path = '<fixture>') {
  return current === baseline ? [] : [{ code: 'FROZEN_CONTENT_DRIFT', path }];
}

function bodyWithoutClassMarker(text) {
  return text.replace(/^<!-- doc-class: (?:canonical|generated|frozen|record) -->\n\n?/, '');
}

export function compareGeneratedBytes(actual, expected, path = INDEX) {
  return actual === expected ? [] : [{ code: 'GENERATED_CONTENT_DRIFT', path }];
}

export function trackedMarkdownDocs(root = ROOT) {
  const output = execFileSync('git', ['-C', root, 'ls-files', '-z', '--', '000-docs'], {
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
  });
  return output
    .split('\0')
    .filter((path) => path.startsWith(DOC_PREFIX) && path.endsWith('.md'))
    .sort();
}

function frozenDiffs(root, docs) {
  const issues = [];
  for (const path of docs.filter((candidate) => FROZEN.has(candidate))) {
    let baseline;
    try {
      baseline = execFileSync('git', ['-C', root, 'show', `${BASELINE_REF}:${path}`], {
        encoding: 'utf8',
      });
    } catch (error) {
      issues.push({
        code: 'FROZEN_BASELINE_UNAVAILABLE',
        path,
        detail: error.message,
      });
      continue;
    }
    let current;
    try {
      current = readFileSync(resolve(root, path), 'utf8');
    } catch (error) {
      issues.push({ code: 'UNREADABLE_DOCUMENT', path, detail: error.message });
      continue;
    }
    if (bodyWithoutClassMarker(current) !== bodyWithoutClassMarker(baseline)) {
      issues.push(...compareFrozenBytes('drift', 'baseline', path));
    }
  }
  return issues;
}

function generatedDrift(root) {
  const result = spawnSync('node', ['scripts/generate-docs-index.mjs', '--check', root], {
    cwd: root,
    encoding: 'utf8',
  });
  return result.status === 0
    ? []
    : compareGeneratedBytes(result.stdout, 'expected-generated-output', INDEX).map((issue) => ({
        ...issue,
        detail: result.stderr || result.stdout,
      }));
}

export function checkDocClasses(root = ROOT) {
  const docs = trackedMarkdownDocs(root);
  if (docs.length === 0) throw new Error('no tracked Markdown documents under 000-docs');
  const issues = [];
  const counts = Object.fromEntries([...VALID_CLASSES].map((className) => [className, 0]));

  for (const path of docs) {
    let text;
    try {
      text = readFileSync(resolve(root, path), 'utf8');
    } catch (error) {
      issues.push({ code: 'UNREADABLE_DOCUMENT', path, detail: error.message });
      continue;
    }
    const parsed = parseDocClass(text);
    if (parsed.reason) {
      issues.push({ code: parsed.reason, path, detail: parsed.className ?? undefined });
      continue;
    }
    const expected = expectedClass(path);
    if (parsed.className !== expected) {
      issues.push({ code: 'CLASS_MISMATCH', path, expected, actual: parsed.className });
      continue;
    }
    counts[parsed.className] += 1;
  }

  issues.push(...frozenDiffs(root, docs), ...generatedDrift(root));
  return {
    docs: docs.length,
    counts,
    frozen: FROZEN.size,
    generated: 1,
    issues,
    allow: issues.length === 0,
  };
}

function applyMarkers(root) {
  for (const path of trackedMarkdownDocs(root)) {
    const file = resolve(root, path);
    const text = readFileSync(file, 'utf8');
    if (MARKER.test(text)) continue;
    writeFileSync(file, `<!-- doc-class: ${expectedClass(path)} -->\n\n${text}`);
  }
}

function main() {
  const args = process.argv.slice(2);
  const fix = args.includes('--fix');
  const positional = args.filter((arg) => arg !== '--fix');
  if (positional.length > 1 || positional.some((arg) => arg.startsWith('-'))) {
    console.error('Usage: node scripts/check-doc-classes.mjs [--fix] [repository-root]');
    process.exitCode = 2;
    return;
  }
  const root = positional[0] ? resolve(positional[0]) : ROOT;
  if (fix) {
    applyMarkers(root);
    return;
  }
  try {
    const result = checkDocClasses(root);
    console.log(JSON.stringify(result, null, 2));
    if (!result.allow) process.exitCode = 1;
  } catch (error) {
    console.error(`doc-classes: ${error.message}`);
    process.exitCode = 1;
  }
}

if (process.argv[1] === fileURLToPath(import.meta.url)) main();
