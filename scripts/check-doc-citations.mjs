#!/usr/bin/env node
/**
 * check-doc-citations.mjs — the citation gate: no governance-scope tracked file
 * may cite a root 000-docs path that is absent from tracking.
 *
 * Why: gitignore glob-adds skip ignored files SILENTLY, so a doc can be filed
 * locally, cited from tracked governance, and invisible to every clone (the
 * Mission 01 "681-class" break — root CLAUDE.md cited a doc no clone had).
 * This gate turns that silent state into a loud CI failure.
 *
 * Scope (citing files): root governance files, root 000-docs/*.md, scripts/,
 * tests/ (excluding fixture corpora), .github/. Excluded as citation sources:
 * plugins/** and skills/.curated/** (their `000-docs/` refs resolve to their
 * OWN nested docs dirs), test fixtures (fabricated paths), freshie/exports
 * (data), marketplace/** (generated data + historical blog prose), and the
 * doc-filing rename ledger 257 (historical by design).
 *
 * A citation passes if it resolves to a tracked root path OR a tracked path
 * relative to the citing file's directory. Pre-existing dead citations are
 * pinned in scripts/doc-citation-baseline.json — shrink it, never grow it.
 *
 * Usage: node scripts/check-doc-citations.mjs [--emit-baseline]
 */
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const BASELINE_PATH = 'scripts/doc-citation-baseline.json';
// POSIX ERE for git grep (no JS-only syntax like (?:...) here)
const CITE_ERE = '000-docs/[0-9]{3,4}[A-Za-z0-9._-]*\\.(md|json)';

const INCLUDE = (f) =>
  /^(CLAUDE|AGENTS|README|CHANGELOG|SECURITY|SUPPORT|STANDARDS|RELEASING|CONTRIBUTING)\.md$/.test(
    f,
  ) ||
  (f.startsWith('000-docs/') && f.endsWith('.md')) ||
  f.startsWith('scripts/') ||
  f.startsWith('tests/') ||
  f.startsWith('.github/');
const EXCLUDE = (f) =>
  f.startsWith('tests/fixtures/') ||
  f.startsWith('tests/pr-classifier/fixtures/') ||
  f === '000-docs/257-AA-AACR-doc-filing-cleanup.md' ||
  // hypothetical fixture paths, not citations (review finding F1):
  f === 'scripts/check-docs-ignore-policy.mjs' ||
  // the baseline must not keep its own entries "alive" (review finding F2):
  f === BASELINE_PATH;

const BUF = { maxBuffer: 64 * 1024 * 1024 };
const tracked = new Set(execFileSync('git', ['ls-files'], BUF).toString().trim().split('\n'));

let grep = '';
try {
  // -I: skip binary files (a PDF-bearing doc previously produced a phantom match)
  grep = execFileSync('git', ['grep', '-I', '-oE', CITE_ERE], BUF).toString();
} catch (e) {
  if (e.status !== 1) throw e; // 1 = no matches, fine
}

// Keyed by "citer -> citation" PAIR, not by citation alone: a NEW file citing an
// already-baselined dead target is itself a new dead citation and must fail.
// (Greptile P1 on PR #1175; independently raised as F3 by the review agent.)
const dead = new Set();
for (const line of grep.split('\n')) {
  if (!line) continue;
  const idx = line.indexOf(':');
  const file = line.slice(0, idx);
  const cite = line.slice(idx + 1);
  if (!INCLUDE(file) || EXCLUDE(file)) continue;
  if (tracked.has(cite)) continue;
  // relative resolution: `000-docs/...` written inside a dir that has its own 000-docs
  if (tracked.has(path.posix.join(path.posix.dirname(file), cite))) continue;
  dead.add(`${file} -> ${cite}`);
}

const current = [...dead].sort();

if (process.argv.includes('--emit-baseline')) {
  writeFileSync(
    BASELINE_PATH,
    JSON.stringify(
      {
        $comment:
          'Pre-existing dead 000-docs citations as "citer -> citation" PAIRS, pinned 2026-08-12 (bead claude-5awj.6). Pair-keyed so a NEW file citing an already-listed dead target still fails the gate. Shrink by filing the cited doc or fixing the citation — NEVER add entries to silence the gate.',
        baseline: current,
      },
      null,
      2,
    ) + '\n',
  );
  console.log(`baseline written: ${current.length} entries`);
  process.exit(0);
}

const baseline = new Set(JSON.parse(readFileSync(BASELINE_PATH, 'utf8')).baseline);
const newDead = current.filter((c) => !baseline.has(c));
const healed = [...baseline].filter((c) => !dead.has(c));

if (healed.length) {
  console.log(`ℹ ${healed.length} baseline citation(s) healed — shrink ${BASELINE_PATH}:`);
  for (const h of healed) console.log(`    ${h}`);
}
if (newDead.length) {
  console.error(
    `✗ ${newDead.length} NEW dead citation(s) — a tracked file cites a 000-docs path no clone has.`,
  );
  console.error(
    '  Fix: `git add` the cited doc (ledger it in 000-docs/.gitignore) or correct the citation.',
  );
  for (const c of newDead) console.error(`    ${c}`);
  process.exit(1);
}
console.log(`doc-citations: OK (${current.length} pre-existing baselined, 0 new)`);
