#!/usr/bin/env node
/**
 * classify-model-ids.mjs — emit the three disjoint model-identifier sets for
 * the tracked tree (blueprint 727, Epic 3 bead 3.7).
 *
 * For every `claude-…` token in every tracked text file, classifies the
 * occurrence as bead-id (protected), functional (E3.8's migration work list),
 * or prose (preserved), through THE shared classifier
 * (scripts/lib/model-id-classifier.mjs) and the committed exclusion list.
 *
 * Usage:
 *   node scripts/classify-model-ids.mjs                # summary counts
 *   node scripts/classify-model-ids.mjs --functional   # the E3.8 work list
 *                                                        (file:line "token")
 *   node scripts/classify-model-ids.mjs --json         # full machine output
 *   node scripts/classify-model-ids.mjs --check        # gate mode: exit 1 on
 *                                                        census drift
 *   node scripts/classify-model-ids.mjs --generate-exclusions
 *                                                      # regenerate from
 *                                                        authoritative Dolt
 *   node scripts/classify-model-ids.mjs --audit-live   # compare projection
 *                                                        with live Dolt
 */

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import {
  BEAD_ID,
  BEAD_ID_SCAN,
  MODEL_FAMILY,
  classifyModelToken,
  claudeTokensOnLine,
  loadExclusions,
} from './lib/model-id-classifier.mjs';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const TEXT_EXT = /\.(md|mjs|cjs|js|ts|tsx|astro|json|ya?ml|py|sh|txt|toml|css|html)$/i;

export function classifyTree() {
  const files = execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024,
  })
    .split('\n')
    .filter(Boolean);

  const sets = { 'bead-id': [], functional: [], prose: [] };
  for (const file of files) {
    if (!TEXT_EXT.test(file)) continue;
    let text;
    try {
      text = readFileSync(join(ROOT, file), 'utf-8');
    } catch {
      continue;
    }
    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
      for (const token of claudeTokensOnLine(lines[i])) {
        sets[classifyModelToken(token, lines[i])].push({ file, line: i + 1, token });
      }
    }
  }
  return sets;
}

/**
 * Handle prefixes that match the bead shape but are product vocabulary, never
 * beads-issue handles in this repo. If bd ever minted one of these, the
 * local-workspace census (classify-model-ids.test.mjs, live-Dolt leg) would
 * still catch it at generation time.
 */
const NOT_A_HANDLE = new Set(['claude-code']);

export function issueRowsToHandleRoots(rows) {
  const roots = new Set();
  for (const row of rows) {
    const id = row?.id;
    if (typeof id !== 'string' || !BEAD_ID.test(id)) continue;
    roots.add(id.split('.')[0]);
  }
  return [...roots].sort();
}

export function diffHandleRoots(liveRoots, pinned = loadExclusions().protected_handles) {
  const live = new Set(liveRoots);
  const projected = new Set(pinned);
  return {
    missing: [...live].filter((root) => !projected.has(root)).sort(),
    extra: [...projected].filter((root) => !live.has(root)).sort(),
  };
}

function primaryBeadsRoot() {
  let commonDirectory;
  try {
    commonDirectory = execFileSync(
      'git',
      ['rev-parse', '--path-format=absolute', '--git-common-dir'],
      { cwd: ROOT, encoding: 'utf-8' },
    ).trim();
  } catch {
    return null;
  }
  const primaryRoot = dirname(commonDirectory);
  if (existsSync(join(primaryRoot, '.beads'))) return primaryRoot;
  if (existsSync(join(ROOT, '.beads'))) return ROOT;
  return null;
}

export function liveBeadRootHandles() {
  const beadsRoot = primaryBeadsRoot();
  if (beadsRoot === null) return null;
  const rows = JSON.parse(
    execFileSync('bd', ['--readonly', '-C', beadsRoot, 'list', '--all', '--limit', '0', '--json'], {
      cwd: ROOT,
      encoding: 'utf-8',
      maxBuffer: 256 * 1024 * 1024,
    }),
  );
  if (!Array.isArray(rows)) throw new TypeError('bd list did not return an issue array');
  return issueRowsToHandleRoots(rows);
}

/**
 * The CI-reachable census: every bead-handle-shaped token on a bead-context
 * line in the TRACKED tree (a corpus CI can see, unlike the untracked
 * .beads/issues.jsonl) whose prefix is missing from the committed exclusion
 * list. A new epic bead lands in tracked AARs ("Bead: `claude-<hash>.1`")
 * before anything else, so this trips on exactly the drift class that once
 * went CI-invisible: an epic created after the census was committed.
 * Placeholder mentions ("claude-7yz...") are skipped by the ellipsis guard.
 *
 * `pinned` is injectable so the regression test can prove the DETECTION path
 * end-to-end (empty pin set → the scan must surface real handles), not just
 * the all-pinned empty result.
 */
export function unpinnedTrackedHandles(pinned = new Set(loadExclusions().protected_handles)) {
  const files = execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024,
  })
    .split('\n')
    .filter(Boolean);

  const missing = new Map(); // prefix → first "file:line" sighting
  for (const file of files) {
    if (!TEXT_EXT.test(file)) continue;
    let text;
    try {
      text = readFileSync(join(ROOT, file), 'utf-8');
    } catch {
      continue;
    }
    const lines = text.split('\n');
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (!/bead/i.test(line)) continue;
      for (const token of line.match(BEAD_ID_SCAN) || []) {
        if (!BEAD_ID.test(token) || MODEL_FAMILY.test(token)) continue;
        if (line.includes(token + '...')) continue;
        const prefix = token.split('.')[0];
        if (NOT_A_HANDLE.has(prefix) || pinned.has(prefix)) continue;
        if (!missing.has(prefix)) missing.set(prefix, `${file}:${i + 1}`);
      }
    }
  }
  return missing;
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  if (process.argv.includes('--generate-exclusions')) {
    const liveRoots = liveBeadRootHandles();
    if (liveRoots === null) {
      console.error('model-id-generate: FAIL — no local authoritative Beads/Dolt database');
      process.exit(1);
    }
    const path = join(ROOT, 'schemas', 'canonical', 'v0', 'model-id-exclusions.json');
    const projection = loadExclusions();
    projection.protected_handles = liveRoots;
    writeFileSync(path, JSON.stringify(projection, null, 2) + '\n');
    console.log(`model-id-generate: wrote ${liveRoots.length} authoritative Beads root handles`);
    process.exit(0);
  }
  if (process.argv.includes('--audit-live')) {
    const liveRoots = liveBeadRootHandles();
    if (liveRoots === null) {
      console.error('model-id-live-audit: FAIL — no local authoritative Beads/Dolt database');
      process.exit(1);
    }
    const diff = diffHandleRoots(liveRoots);
    if (diff.missing.length > 0 || diff.extra.length > 0) {
      for (const root of diff.missing) console.error(`model-id-live-audit: MISSING ${root}`);
      for (const root of diff.extra) console.error(`model-id-live-audit: EXTRA ${root}`);
      process.exit(1);
    }
    console.log(`model-id-live-audit: PASS — ${liveRoots.length} authoritative roots match`);
    process.exit(0);
  }
  if (process.argv.includes('--check')) {
    const missing = unpinnedTrackedHandles();
    if (missing.size > 0) {
      for (const [prefix, where] of missing) {
        console.error(
          `model-id-check: FAIL — handle ${prefix} referenced at ${where} is missing from ` +
            'schemas/canonical/v0/model-id-exclusions.json (run --generate-exclusions locally)',
        );
      }
      process.exit(1);
    }
    console.log('model-id-check: PASS — every tracked bead-handle reference is pinned');
    process.exit(0);
  }
  const sets = classifyTree();
  if (process.argv.includes('--json')) {
    process.stdout.write(JSON.stringify(sets, null, 2) + '\n');
  } else if (process.argv.includes('--functional')) {
    for (const o of sets.functional) console.log(`${o.file}:${o.line} "${o.token}"`);
    console.log(`# ${sets.functional.length} functional occurrence(s)`);
  } else {
    console.log(
      `model-id-classify: bead-id=${sets['bead-id'].length} functional=${sets.functional.length} prose=${sets.prose.length} (disjoint by construction)`,
    );
  }
}
