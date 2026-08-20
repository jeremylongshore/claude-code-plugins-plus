#!/usr/bin/env node
/**
 * check-portability-claims.mjs — the unbacked-portability ratchet (blueprint
 * 727, Epic 3 bead 3.11).
 *
 * A skill may not claim a harness it has no adapter artifact for. The
 * registered adapter set is the canonical contract's `adapters` enum
 * (claude-code only at v0, growing ONLY with generated adapter artifacts).
 * This gate scans every FIRST-PARTY tracked SKILL.md's `compatibility` value
 * for known harness names and fails when a named harness has no registered
 * adapter — the untested-claim class that once spanned 2,700 first-party
 * files ("also compatible with Codex and OpenClaw") with zero artifacts
 * behind it.
 *
 * Withdrawing a claim is not removing a capability: `Designed for Claude
 * Code` backed by a working harness is a STRONGER statement than an
 * unverifiable sentence (§ 5.4 rule 2).
 *
 * Mirror files (.source.json subtrees) are upstream-owned: their claims are
 * counted and reported, never edited or failed here — repair flows by
 * upstreaming.
 */

import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { KNOWN_HARNESSES } from './lib/harness-lexicon.mjs';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');

// Re-exported for existing consumers; the definition lives in scripts/lib/.
export { KNOWN_HARNESSES };

/** The registered adapter set — grows only with generated adapter artifacts. */
export const REGISTERED_ADAPTERS = new Set(['claude-code']);

export function unbackedClaims(compatibilityValue) {
  const named = KNOWN_HARNESSES.filter(([, re]) => re.test(compatibilityValue)).map(([id]) => id);
  return named.filter((id) => !REGISTERED_ADAPTERS.has(id));
}

export function sweep() {
  const files = execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024,
  })
    .split('\n')
    .filter(Boolean);
  const mirrorRoots = files
    .filter((f) => f.endsWith('/.source.json'))
    .map((f) => f.slice(0, -'/.source.json'.length));
  const isMirror = (f) => mirrorRoots.some((r) => f.startsWith(r + '/'));

  const violations = [];
  let mirrorClaims = 0;
  let firstParty = 0;
  for (const file of files) {
    if (!/(^|\/)SKILL\.md$/.test(file)) continue;
    let text;
    try {
      text = readFileSync(join(ROOT, file), 'utf-8');
    } catch {
      continue;
    }
    const fm = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!fm) continue;
    const cm = fm[1].match(/^compatibility:\s*(.+)$/m);
    if (!cm) continue;
    const value = cm[1].trim().replace(/^["']|["']$/g, '');
    const unbacked = unbackedClaims(value);
    if (unbacked.length === 0) continue;
    if (isMirror(file)) {
      mirrorClaims += 1; // upstream-owned: reported, never failed
    } else {
      firstParty += 1;
      violations.push({ file, unbacked, value: value.slice(0, 80) });
    }
  }
  return { violations, mirrorClaims, firstParty };
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  const { violations, mirrorClaims } = sweep();
  for (const v of violations) {
    console.error(
      `portability-claims: VIOLATION — ${v.file}: claims [${v.unbacked.join(', ')}] with no registered adapter ("${v.value}…")`,
    );
  }
  if (violations.length > 0) {
    console.error(
      `portability-claims: FAIL — ${violations.length} first-party unbacked claim(s). ` +
        'A harness may be named only when a generated adapter artifact exists; withdraw the claim.',
    );
    process.exit(1);
  }
  console.log(
    `portability-claims: OK (zero first-party unbacked claims; ${mirrorClaims} mirror-owned claim(s) reported, upstream-repair only)`,
  );
}
