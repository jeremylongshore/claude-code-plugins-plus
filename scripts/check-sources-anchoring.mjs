#!/usr/bin/env node
/**
 * check-sources-anchoring.mjs — blocking CI gate for sources.yaml include anchoring.
 *
 * THE HAZARD (blocker 62ye.6; bit for real on 2026-07-13, PR #1048): the sync
 * engine's matchesPattern() silently auto-prefixes an unanchored include —
 * one that starts with neither `/` (root-anchored) nor `**` (explicitly
 * recursive) — with `**\/`, so `README.md` matches EVERY README at any depth.
 * A vetter who read `include: [README.md]` as "the root README" actually
 * approved an any-depth match, and the weekly sync mirrored upstream's
 * unvetted onboarding/README.md (carrying a tailnet IP) into the public repo.
 * The engine warns (sync-external.mjs), but a warn-only log line inside a
 * scheduled run is not a review gate.
 *
 * THE GATE: every include pattern in sources.yaml must be explicit about its
 * depth — start it with `/` for root-anchored or `**\/` for deliberate
 * recursion. Unanchored patterns fail this check (exit 1) UNLESS they are
 * grandfathered in scripts/sources-anchoring-allowlist.txt, which enumerates
 * exactly the source/pattern pairs that predate the gate (existing state
 * stays green; only NEW or EDITED entries are forced to anchor). Removing a
 * pattern from the allowlist is a one-way ratchet — anchor the sources.yaml
 * entry instead of re-adding the waiver.
 *
 * Detection is unanchoredIncludes() from scripts/sync-lockfile.mjs — the SAME
 * predicate the sync engine warns with, so gate and engine can never disagree
 * about what "unanchored" means.
 *
 * Runs as a step of the `validate` job in validate-plugins.yml (inside the
 * ci-required aggregate). Pure read-only; no network.
 *
 * Usage:
 *   node scripts/check-sources-anchoring.mjs
 *   node scripts/check-sources-anchoring.mjs --sources=PATH --allowlist=PATH  (fixtures/tests)
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import yaml from 'js-yaml';
import { unanchoredIncludes } from './sync-lockfile.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, '..');

const args = process.argv.slice(2);
const argValue = (name) =>
  args
    .find((a) => a.startsWith(`--${name}=`))
    ?.split('=')
    .slice(1)
    .join('=');

const SOURCES_FILE = path.resolve(ROOT_DIR, argValue('sources') || 'sources.yaml');
const ALLOWLIST_FILE = path.resolve(
  ROOT_DIR,
  argValue('allowlist') || 'scripts/sources-anchoring-allowlist.txt',
);

/**
 * Parse the grandfather allowlist. One waiver per line:
 *   <source-name>  <pattern>
 * `#` starts a comment; blank lines ignored. A malformed line (fewer than two
 * whitespace-separated tokens) is IGNORED with a warning, never honored —
 * same fail-closed posture as scan-allowlist.txt.
 *
 * Returns Map<sourceName, Set<pattern>>.
 */
export function parseAllowlist(text) {
  const map = new Map();
  const malformed = [];
  for (const rawLine of text.split('\n')) {
    const line = rawLine.replace(/#.*$/, '').trim();
    if (!line) continue;
    const tokens = line.split(/\s+/);
    if (tokens.length !== 2) {
      malformed.push(rawLine.trim());
      continue;
    }
    const [name, pattern] = tokens;
    if (!map.has(name)) map.set(name, new Set());
    map.get(name).add(pattern);
  }
  return { map, malformed };
}

/**
 * Core check, pure for testability.
 *
 * @param {Array<{name: string, include?: string[]}>} sources
 * @param {Map<string, Set<string>>} allow
 * @returns {{violations: Array<{source: string, pattern: string}>,
 *            stale: Array<{source: string, pattern: string}>,
 *            grandfathered: number}}
 */
export function checkAnchoring(sources, allow) {
  const violations = [];
  let grandfathered = 0;

  const liveUnanchored = new Map(); // name → Set(pattern) actually unanchored right now
  for (const source of sources) {
    const un = unanchoredIncludes(source.include);
    if (un.length) liveUnanchored.set(source.name, new Set(un));
    const waived = allow.get(source.name) || new Set();
    for (const pattern of un) {
      if (waived.has(pattern)) {
        grandfathered += 1;
      } else {
        violations.push({ source: source.name, pattern });
      }
    }
  }

  // Stale waivers: allowlist rows whose source no longer exists or whose
  // pattern is no longer unanchored. Advisory only (prunable), never blocking —
  // a source removal or an anchoring fix must not red-fail an unrelated PR.
  const stale = [];
  for (const [name, patterns] of allow) {
    const live = liveUnanchored.get(name) || new Set();
    for (const pattern of patterns) {
      if (!live.has(pattern)) stale.push({ source: name, pattern });
    }
  }

  return { violations, stale, grandfathered };
}

function main() {
  if (!fs.existsSync(SOURCES_FILE)) {
    console.error(`❌ sources file not found: ${SOURCES_FILE}`);
    process.exit(1);
  }
  const { sources } = yaml.load(fs.readFileSync(SOURCES_FILE, 'utf8')) || {};
  if (!Array.isArray(sources)) {
    console.error(`❌ ${SOURCES_FILE} has no sources[] list`);
    process.exit(1);
  }

  const allowText = fs.existsSync(ALLOWLIST_FILE) ? fs.readFileSync(ALLOWLIST_FILE, 'utf8') : '';
  const { map: allow, malformed } = parseAllowlist(allowText);
  for (const line of malformed) {
    console.warn(`⚠️  allowlist line ignored (need "<source>  <pattern>"): ${line}`);
  }

  const { violations, stale, grandfathered } = checkAnchoring(sources, allow);

  for (const s of stale) {
    console.warn(
      `⚠️  stale allowlist row (source gone or pattern now anchored — prune it): ${s.source}  ${s.pattern}`,
    );
  }

  if (violations.length) {
    console.error(
      `\n❌ ${violations.length} unanchored include pattern(s) in ${path.basename(SOURCES_FILE)}.`,
    );
    console.error(
      'An include that starts with neither "/" nor "**" is silently auto-prefixed "**/" by the',
    );
    console.error(
      'sync engine and matches at ANY depth — not the root path a vetter likely reviewed.',
    );
    console.error('Fix each pattern to make its depth explicit:');
    for (const v of violations) {
      console.error(
        `   ${v.source}: "${v.pattern}"  →  "/${v.pattern}" (root-only)  or  "**/${v.pattern}" (deliberate recursion)`,
      );
    }
    console.error(
      '\nGrandfathered legacy entries live in scripts/sources-anchoring-allowlist.txt (pre-gate',
    );
    console.error('state only — do NOT add new rows; anchor the sources.yaml pattern instead).');
    process.exit(1);
  }

  console.log(
    `✅ sources.yaml include anchoring OK — ${sources.length} sources, ` +
      `${grandfathered} grandfathered legacy pattern(s), 0 new violations.`,
  );
}

const invokedDirectly =
  process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
if (invokedDirectly) {
  main();
}
