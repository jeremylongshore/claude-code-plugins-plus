import { test } from 'node:test';
import { equal, ok, deepEqual } from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  analyzeConfig,
  analyzeIgnore,
  formatIssue,
  verifyFingerprintInRepository,
  validateFingerprintSourceLine,
  APPROVED_PATH_PATTERNS,
  BANNED_FRAGMENTS,
} from './check-gitleaks-config.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const APPROVED_EXACT = '^scripts/validate-skills-schema\\.py$';
const APPROVED_EXACT_2 =
  '^plugins/security/penetration-tester/skills/scanning-for-hardcoded-secrets/scripts/scan_secrets\\.py$';

const governed = (pattern) =>
  `[allowlist]\npaths = [\n    # reason: because.\n    # expiry: 2999-01-01\n    '''${pattern}''',\n]\n`;

test('live config passes with zero issues', () => {
  const result = analyzeConfig(readFileSync(resolve(ROOT, '.gitleaks.toml'), 'utf8'));
  equal(result.allow, true, JSON.stringify(result.issues));
  ok(result.entries > 0);
  deepEqual(result.entries, APPROVED_PATH_PATTERNS.length);
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
  const result = analyzeConfig(`[allowlist]\npaths = [\n    '''${APPROVED_EXACT}''',\n]\n`);
  ok(result.issues.some((issue) => issue.code === 'UNDOCUMENTED_EXCEPTION'));
});

test('reason without expiry is not enough', () => {
  const result = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: because.\n    '''${APPROVED_EXACT}''',\n]\n`,
  );
  ok(result.issues.some((issue) => issue.code === 'UNDOCUMENTED_EXCEPTION'));
});

test('a shared comment block governs consecutive entries', () => {
  const result = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: generated projections.\n    # expiry: 2027-01-01\n    '''${APPROVED_EXACT}''',\n    '''${APPROVED_EXACT_2}''',\n]\n`,
  );
  equal(result.allow, true, JSON.stringify(result.issues));
  equal(result.entries, 2);
});

test('a blank line ends a governing block', () => {
  const result = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: covered.\n    # expiry: 2027-01-01\n    '''${APPROVED_EXACT}''',\n\n    '''${APPROVED_EXACT_2}''',\n]\n`,
  );
  ok(result.issues.some((issue) => issue.code === 'UNDOCUMENTED_EXCEPTION'));
});

test('missing paths section is an explicit failure', () => {
  const result = analyzeConfig('[allowlist]\nregexes = []\n');
  ok(result.issues.some((issue) => issue.code === 'NO_PATHS_SECTION'));
});

test('credential-shaped Google API keys cannot be retained as allowlist values', () => {
  const key = ['AI', 'za', 'A'.repeat(35)].join('');
  const result = analyzeConfig(`[allowlist]\npaths = []\nregexes = [\n    '''${key}''',\n]\n`);
  ok(result.issues.some((issue) => issue.code === 'CREDENTIAL_LITERAL'));
});

test('TOML escapes cannot conceal a credential-shaped Google API key', () => {
  const encodedKey = ['\\u0041', 'Iza', 'A'.repeat(35)].join('');
  const result = analyzeConfig(`${governed(APPROVED_EXACT)}regexes = ["${encodedKey}"]\n`);
  ok(result.issues.some((issue) => issue.code === 'CREDENTIAL_LITERAL'));
});

test('inline path arrays are rejected rather than silently skipped', () => {
  const result = analyzeConfig('[allowlist]\npaths = ["^specific/path$"]\n');
  ok(result.issues.some((issue) => issue.code === 'UNSUPPORTED_PATHS_SYNTAX'));
  ok(result.issues.some((issue) => issue.code === 'PATH_ENTRY_COUNT_MISMATCH'));
});

test('a decoy paths array outside allowlist cannot hide semantic allowlist paths', () => {
  const result = analyzeConfig(
    `paths = [\n    # reason: decoy.\n    # expiry: 2999-01-01\n    '''^specific/path$''',\n]\n[allowlist]\npaths = ["^.*\\\\.md$"]\n`,
  );
  ok(result.issues.some((issue) => issue.code === 'UNSUPPORTED_PATHS_SYNTAX'));
  ok(result.issues.some((issue) => issue.code === 'PATH_ENTRY_COUNT_MISMATCH'));
});

test('plural global and rule-level allowlists are rejected', () => {
  const global = analyzeConfig(
    `${governed(APPROVED_EXACT)}\n[[allowlists]]\ndescription = "bypass"\nregexes = [".*"]\n`,
  );
  ok(global.issues.some((issue) => issue.code === 'UNSUPPORTED_GLOBAL_ALLOWLISTS'));

  const rule = analyzeConfig(
    `${governed(APPROVED_EXACT)}\n[[rules]]\nid = "fixture"\ndescription = "fixture"\nregex = "fixture"\n[[rules.allowlists]]\nregexes = [".*"]\n`,
  );
  ok(rule.issues.some((issue) => issue.code === 'UNSUPPORTED_RULE_ALLOWLIST'));

  const inlineRulesObject = analyzeConfig(
    `rules = { id = "fixture", regex = "fixture", allowlist = { regexes = [".*"] } }\n${governed(APPROVED_EXACT)}`,
  );
  ok(inlineRulesObject.issues.some((issue) => issue.code === 'INVALID_RULES_SHAPE'));

  const rulesTable = analyzeConfig(
    `[rules]\nid = "fixture"\nregex = "fixture"\nallowlist = { regexes = [".*"] }\n${governed(APPROVED_EXACT)}`,
  );
  ok(rulesTable.issues.some((issue) => issue.code === 'INVALID_RULES_SHAPE'));
});

test('unknown global fields and unreviewed values are rejected', () => {
  const unknownField = analyzeConfig(
    `${governed(APPROVED_EXACT)}\ncommits = ["${'a'.repeat(40)}"]\nregexes = []\nstopwords = []\n`,
  );
  ok(unknownField.issues.some((issue) => issue.code === 'UNSUPPORTED_GLOBAL_ALLOWLIST_FIELD'));

  const unknownRegex = analyzeConfig(
    `${governed(APPROVED_EXACT)}\nregexes = [".*"]\nstopwords = []\n`,
  );
  ok(unknownRegex.issues.some((issue) => issue.code === 'UNAPPROVED_ALLOWLIST_REGEX'));

  const unknownStopword = analyzeConfig(
    `${governed(APPROVED_EXACT)}\nregexes = []\nstopwords = ["anything"]\n`,
  );
  ok(unknownStopword.issues.some((issue) => issue.code === 'UNAPPROVED_ALLOWLIST_STOPWORD'));
});

test('behaviorally broad path regexes fail even without banned literal fragments', () => {
  const result = analyzeConfig(governed('^.*\\.md$'));
  ok(result.issues.some((issue) => issue.code === 'UNAPPROVED_PATH_PATTERN'));
});

test('unreviewed file-type blankets fail even when finite probes would miss them', () => {
  const result = analyzeConfig(governed('^.*\\.yaml$'));
  ok(result.issues.some((issue) => issue.code === 'UNAPPROVED_PATH_PATTERN'));
});

test('expiry metadata must be a real ISO date or an explained permanent exception', () => {
  const invalid = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: because.\n    # expiry: tomorrow\n    '''${APPROVED_EXACT}''',\n]\n`,
  );
  ok(invalid.issues.some((issue) => issue.code === 'INVALID_EXPIRY'));

  const impossible = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: because.\n    # expiry: 2027-02-30\n    '''${APPROVED_EXACT}''',\n]\n`,
  );
  ok(impossible.issues.some((issue) => issue.code === 'INVALID_EXPIRY'));

  const expired = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: because.\n    # expiry: 2000-01-01\n    '''${APPROVED_EXACT}''',\n]\n`,
  );
  ok(expired.issues.some((issue) => issue.code === 'INVALID_EXPIRY'));

  equal(analyzeConfig(governed(APPROVED_EXACT)).allow, true);
  equal(
    analyzeConfig(
      `[allowlist]\npaths = [\n    # reason: this config file itself holds the detector regexes and example\n    # expiry: none (self-referential by construction)\n    '''^\\.gitleaks\\.toml$''',\n]\n`,
    ).allow,
    true,
  );
  const unrelatedPermanent = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: because.\n    # expiry: none (unrelated reason)\n    '''${APPROVED_EXACT}''',\n]\n`,
  );
  ok(unrelatedPermanent.issues.some((issue) => issue.code === 'INVALID_EXPIRY'));
});

test('metadata labels must be unique and anchored', () => {
  const duplicateExpiry = analyzeConfig(
    `[allowlist]\npaths = [\n    # reason: because.\n    # expiry: 2999-01-01\n    # expiry: 2998-01-01\n    '''${APPROVED_EXACT}''',\n]\n`,
  );
  ok(duplicateExpiry.issues.some((issue) => issue.code === 'UNDOCUMENTED_EXCEPTION'));

  const prefixedLabels = analyzeConfig(
    `[allowlist]\npaths = [\n    # historical reason: because.\n    # historical expiry: 2999-01-01\n    '''${APPROVED_EXACT}''',\n]\n`,
  );
  ok(prefixedLabels.issues.some((issue) => issue.code === 'UNDOCUMENTED_EXCEPTION'));
});

test('ignore entries must bind commit, path, rule, and line', () => {
  const exact = `${'a'.repeat(40)}:path/to/file:gcp-api-key:52`;
  equal(analyzeIgnore(`# reason: fixture\n${exact}\n`, () => ({ ok: true })).allow, true);
  deepEqual(
    analyzeIgnore('path/to/file:gcp-api-key:52\n').issues.map((issue) => issue.code),
    ['NON_COMMIT_BOUND_FINGERPRINT'],
  );
});

test('duplicate ignore fingerprints fail closed', () => {
  const exact = `${'b'.repeat(40)}:path/to/file:gcp-api-key:52`;
  deepEqual(
    analyzeIgnore(`${exact}\n${exact}\n`, () => ({ ok: true })).issues.map((issue) => issue.code),
    ['DUPLICATE_FINGERPRINT'],
  );
});

test('fingerprint paths must be normalized repository-relative paths', () => {
  for (const path of ['/absolute/path', '../outside', 'a/../b', './relative', 'a\\b', 'a//b']) {
    const exact = `${'b'.repeat(40)}:${path}:gcp-api-key:52`;
    ok(
      analyzeIgnore(exact, () => ({ ok: true })).issues.some(
        (issue) => issue.code === 'INVALID_FINGERPRINT_PATH',
      ),
    );
  }
});

test('one fingerprint cannot suppress multiple same-line findings', () => {
  const first = ['AI', 'za', 'A'.repeat(35)].join('');
  const second = ['AI', 'za', 'B'.repeat(35)].join('');
  equal(validateFingerprintSourceLine(`first=${first}`).ok, true);
  deepEqual(validateFingerprintSourceLine(`first=${first} second=${second}`), {
    ok: false,
    code: 'AMBIGUOUS_FINGERPRINT_LINE',
  });
});

test('ignore analysis verifies provenance by default', () => {
  const nonexistent = `${'d'.repeat(40)}:path/to/file:gcp-api-key:52`;
  const result = analyzeIgnore(nonexistent);
  equal(result.allow, false);
  ok(result.issues.some((issue) => issue.code === 'FINGERPRINT_SOURCE_UNREACHABLE'));
});

test('ignore analysis rejects an explicitly missing verifier', () => {
  const exact = `${'e'.repeat(40)}:path/to/file:gcp-api-key:52`;
  const result = analyzeIgnore(exact, null);
  equal(result.allow, false);
  ok(result.issues.some((issue) => issue.code === 'MISSING_FINGERPRINT_VERIFIER'));
});

test('diagnostics never render source patterns or possible credentials', () => {
  const key = ['AI', 'za', 'A'.repeat(35)].join('');
  const message = formatIssue({ code: 'UNAPPROVED_PATH_PATTERN', line: 7, pattern: key });
  equal(message, 'gitleaks-config: UNAPPROVED_PATH_PATTERN at line 7');
  equal(message.includes(key), false);
});

test('fingerprint provenance is verified without exposing source content', () => {
  const ignoreText = readFileSync(resolve(ROOT, '.gitleaksignore'), 'utf8');
  const result = analyzeIgnore(ignoreText, (entry) => verifyFingerprintInRepository(entry));
  equal(result.allow, true, JSON.stringify(result.issues));
  equal(result.entries, 1);
});

test('fingerprint provenance failures fail closed', () => {
  const exact = `${'c'.repeat(40)}:path/to/file:gcp-api-key:52`;
  const result = analyzeIgnore(exact, () => ({ ok: false, code: 'FINGERPRINT_SOURCE_MISSING' }));
  deepEqual(
    result.issues.map((issue) => issue.code),
    ['FINGERPRINT_SOURCE_MISSING'],
  );
});
