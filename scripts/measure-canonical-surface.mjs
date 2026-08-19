#!/usr/bin/env node
/**
 * measure-canonical-surface.mjs — measure the true model-agnostic migration
 * surface (blueprint 727, Epic 3 bead 3.1).
 *
 * WHY THIS EXISTS
 * ---------------
 * Epic 3 replaces vendor literals in the canonical layer with a harness-free
 * contract. Its migration surface was first measured before Epic 1's
 * regeneration discipline existed, and ~50% of `docs.anthropic.com`
 * occurrences sat inside generated artifacts — an inflated surface. This
 * script measures the surface from the tracked tree, classified three ways,
 * so every later Epic 3 bead consumes ONE honest baseline.
 *
 * CLASSIFICATIONS
 * ---------------
 * Surface class (by path):
 *   - mirror      any file below a directory that contains .source.json —
 *                 upstream-owned, NEVER migrated (Epic 3 prohibited scope)
 *   - generated   registered build projections (marketplace/src/data/**,
 *                 skills/.curated/**, freshie exports, the generated docs
 *                 index and scorecard) — regenerated, never edited
 *   - first-party everything else: the actual migration surface
 *
 * Model-identifier role (per occurrence line):
 *   - bead-id     a beads issue handle (claude-<hash>[.n]) that merely LOOKS
 *                 like a model id. Protected: migration tooling must never
 *                 rewrite these. Detected shape-first, before any model match.
 *   - functional  the id configures behavior: a frontmatter/JSON/YAML
 *                 `model:`/`"model"` assignment or a `--model` flag
 *   - prose       a mention in text (comparisons, history, commentary) —
 *                 deliberately preserved per the blueprint
 *
 * Usage:
 *   node scripts/measure-canonical-surface.mjs            # print JSON
 *   node scripts/measure-canonical-surface.mjs --write    # write 000-docs/778 json+md
 */

import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { classifyModelToken, claudeTokensOnLine } from './lib/model-id-classifier.mjs';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');

const GENERATED_PREFIXES = [
  'marketplace/src/data/',
  'skills/.curated/',
  'freshie/grades.csv',
  'freshie/grade-histogram.json',
  '000-docs/000-INDEX.md',
  '000-docs/742-RA-DATA-epic-1-scorecard.json',
];

export function classifyPath(path, mirrorRoots) {
  for (const root of mirrorRoots) {
    if (path.startsWith(root + '/')) return 'mirror';
  }
  for (const g of GENERATED_PREFIXES) {
    if (path === g || path.startsWith(g)) return 'generated';
  }
  return 'first-party';
}

// The classifier semantics were promoted to the shared library in E3.7 —
// re-exported so this module's tests keep exercising the ONE implementation.
export { classifyModelToken };

function trackedFiles() {
  return execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024,
  })
    .split('\n')
    .filter(Boolean);
}

const TEXT_EXT = /\.(md|mjs|cjs|js|ts|tsx|astro|json|ya?ml|py|sh|txt|toml|css|html)$/i;

export function measure() {
  const files = trackedFiles();
  const mirrorRoots = files
    .filter((f) => f.endsWith('/.source.json'))
    .map((f) => f.slice(0, -'/.source.json'.length));

  const zero = () => ({ 'first-party': 0, mirror: 0, generated: 0 });
  const result = {
    anthropic_docs_occurrences: zero(),
    anthropic_docs_files: zero(),
    claude_env_var_occurrences: zero(),
    claude_env_var_files: zero(),
    model_id_occurrences: {
      'first-party': { functional: 0, prose: 0, 'bead-id': 0 },
      mirror: { functional: 0, prose: 0, 'bead-id': 0 },
      generated: { functional: 0, prose: 0, 'bead-id': 0 },
    },
    model_id_functional_files: { 'first-party': 0, mirror: 0, generated: 0 },
    mirror_roots: mirrorRoots.length,
    tracked_files: files.length,
  };

  for (const file of files) {
    if (!TEXT_EXT.test(file)) continue;
    let text;
    try {
      text = readFileSync(join(ROOT, file), 'utf-8');
    } catch {
      continue;
    }
    const cls = classifyPath(file, mirrorRoots);

    const docsHits = (text.match(/docs\.anthropic\.com/g) || []).length;
    if (docsHits > 0) {
      result.anthropic_docs_occurrences[cls] += docsHits;
      result.anthropic_docs_files[cls] += 1;
    }

    const envHits = (text.match(/\$\{?CLAUDE_[A-Z_]+/g) || []).length;
    if (envHits > 0) {
      result.claude_env_var_occurrences[cls] += envHits;
      result.claude_env_var_files[cls] += 1;
    }

    let functionalInFile = false;
    for (const line of text.split('\n')) {
      // ONE token scan + ONE classifier (E3.7's shared library) — the earlier
      // local scan double-owned these semantics.
      for (const token of claudeTokensOnLine(line)) {
        const role = classifyModelToken(token, line);
        result.model_id_occurrences[cls][role] += 1;
        if (role === 'functional') functionalInFile = true;
      }
    }
    if (functionalInFile) result.model_id_functional_files[cls] += 1;
  }

  return result;
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  const head = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: ROOT, encoding: 'utf-8' }).trim();
  const data = { measured_at_commit: head, ...measure() };
  const json = JSON.stringify(data, null, 2) + '\n';
  if (process.argv.includes('--write')) {
    writeFileSync(
      join(ROOT, '000-docs', '778-RA-DATA-model-agnostic-migration-surface.json'),
      json,
    );
    console.log('written: 000-docs/778-RA-DATA-model-agnostic-migration-surface.json');
  } else {
    process.stdout.write(json);
  }
}
