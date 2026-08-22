#!/usr/bin/env node
// check-gitleaks-config.mjs — the E4.5 allowlist-shape ratchet (blueprint 727).
//
// The pre-E4.5 .gitleaks.toml excluded ~67% of tracked files through file-TYPE
// blankets (every SKILL.md / README.md / CHANGELOG.md / references/*.md /
// tests/ / fixtures/ / 000-docs/*.md), including the exact tests/fixtures/
// location other docs recommend for test secrets. This gate keeps that class
// of allowlist from coming back:
//
//   1. No path entry may re-introduce a banned file-type blanket.
//   2. Every path entry must be governed by a contiguous comment block
//      directly above it (shared blocks cover consecutive entries) carrying
//      both "reason:" and "expiry:" — a specific surface with a written
//      justification, never an anonymous exclusion.
//
// Values (placeholder examples) belong in the [allowlist] regexes/stopwords
// sections, which this gate deliberately does not police — a value allowlist
// leaves the file scanned, so a real credential beside an example still fires.

import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

// A path entry containing any of these re-creates a type blanket. Substring
// match against the raw TOML literal-string entry.
export const BANNED_FRAGMENTS = [
  'README\\.md',
  'CHANGELOG\\.md',
  'SKILL\\.md',
  '/references/',
  'tests?/',
  '__tests__',
  'fixtures/',
  '^000-docs/',
  '\\.(test|spec)\\.',
];

export function analyzeConfig(text) {
  const issues = [];
  const lines = text.split('\n');
  let inPaths = false;
  let commentBlock = [];
  let blockGoverns = false; // current comment block has reason: + expiry:
  let entries = 0;

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const trimmed = line.trim();
    if (!inPaths) {
      if (/^paths\s*=\s*\[/.test(trimmed)) inPaths = true;
      continue;
    }
    if (trimmed === ']') break;
    if (trimmed === '') {
      commentBlock = [];
      blockGoverns = false;
      continue;
    }
    if (trimmed.startsWith('#')) {
      commentBlock.push(trimmed);
      const joined = commentBlock.join(' ');
      blockGoverns = /reason:/.test(joined) && /expiry:/.test(joined);
      continue;
    }
    const entry = trimmed.match(/^'''(.*)''',?$/);
    if (!entry) {
      issues.push({ code: 'UNPARSEABLE_PATH_LINE', line: i + 1, text: trimmed });
      continue;
    }
    entries += 1;
    const pattern = entry[1];
    for (const banned of BANNED_FRAGMENTS) {
      if (pattern.includes(banned)) {
        issues.push({ code: 'TYPE_BLANKET', line: i + 1, pattern, banned });
      }
    }
    if (!blockGoverns) {
      issues.push({ code: 'UNDOCUMENTED_EXCEPTION', line: i + 1, pattern });
    }
    // A shared comment block may govern consecutive entries; keep it active.
  }

  if (!inPaths) issues.push({ code: 'NO_PATHS_SECTION' });
  return { entries, issues, allow: issues.length === 0 };
}

function main() {
  const text = readFileSync(resolve(ROOT, '.gitleaks.toml'), 'utf8');
  const result = analyzeConfig(text);
  if (!result.allow) {
    for (const issue of result.issues) {
      console.error(
        `gitleaks-config: ${issue.code}${issue.pattern ? ` — ${issue.pattern}` : ''}${issue.banned ? ` (banned fragment: ${issue.banned})` : ''} at line ${issue.line ?? '?'}`,
      );
    }
    console.error('gitleaks-config: FAIL — see the allowlist policy header in .gitleaks.toml');
    process.exit(1);
  }
  console.log(
    `gitleaks-config: OK (${result.entries} documented path exceptions; no type blankets)`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
