import { test } from 'node:test';
import { equal, ok, deepEqual } from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyzeConfig, BANNED_FRAGMENTS } from './check-gitleaks-config.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

const governed = (pattern) =>
  `paths = [\n    # reason: because.\n    # expiry: 2027-01-01\n    '''${pattern}''',\n]\n`;

test('live config passes with zero issues', () => {
  const result = analyzeConfig(readFileSync(resolve(ROOT, '.gitleaks.toml'), 'utf8'));
  equal(result.allow, true, JSON.stringify(result.issues));
  ok(result.entries > 0);
});

test('every historical blanket fragment is banned even when documented', () => {
  for (const banned of BANNED_FRAGMENTS) {
    const result = analyzeConfig(governed(`(?i).*${banned}$`));
    equal(result.allow, false, banned);
    ok(
      result.issues.some((issue) => issue.code === 'TYPE_BLANKET'),
      banned,
    );
  }
});

test('a path entry without reason and expiry fails', () => {
  const result = analyzeConfig(`paths = [\n    '''^some/dir/.*''',\n]\n`);
  deepEqual(
    result.issues.map((issue) => issue.code),
    ['UNDOCUMENTED_EXCEPTION'],
  );
});

test('reason without expiry is not enough', () => {
  const result = analyzeConfig(`paths = [\n    # reason: because.\n    '''^some/dir/.*''',\n]\n`);
  deepEqual(
    result.issues.map((issue) => issue.code),
    ['UNDOCUMENTED_EXCEPTION'],
  );
});

test('a shared comment block governs consecutive entries', () => {
  const result = analyzeConfig(
    `paths = [\n    # reason: generated projections.\n    # expiry: 2027-01-01\n    '''^a/.*''',\n    '''^b/.*''',\n]\n`,
  );
  equal(result.allow, true, JSON.stringify(result.issues));
  equal(result.entries, 2);
});

test('a blank line ends a governing block', () => {
  const result = analyzeConfig(
    `paths = [\n    # reason: covered.\n    # expiry: 2027-01-01\n    '''^a/.*''',\n\n    '''^b/.*''',\n]\n`,
  );
  deepEqual(
    result.issues.map((issue) => issue.code),
    ['UNDOCUMENTED_EXCEPTION'],
  );
});

test('missing paths section is an explicit failure', () => {
  const result = analyzeConfig('[allowlist]\nregexes = []\n');
  deepEqual(
    result.issues.map((issue) => issue.code),
    ['NO_PATHS_SECTION'],
  );
});
