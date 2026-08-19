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
 */

import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { classifyModelToken, claudeTokensOnLine } from './lib/model-id-classifier.mjs';

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

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
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
