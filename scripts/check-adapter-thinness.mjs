#!/usr/bin/env node
/**
 * check-adapter-thinness.mjs — an adapter must be THIN (blueprint 727, Epic 3
 * bead 3.5; § 6's rule that a copied skill tree is not an adapter).
 *
 * An "adapter subtree" is a harness-named hidden directory inside a plugin
 * (a `.codex/`, `.openclaw/`, or `.gemini-cli/` directory under plugins) or a
 * future generated `adapters/<harness>/` directory. For every file in an
 * adapter subtree this gate fails on:
 *
 *   1. BYTE-IDENTICAL duplication — the adapter file equals its canonical
 *      counterpart (same relative path outside the adapter dir). A fork is
 *      not an adapter; it is double-graded drift waiting to diverge.
 *   2. FORBIDDEN CONTENT CLASSES inside an adapter — reference material
 *      (references/), executable payloads (scripts/), eval specs, licenses,
 *      version manifests. An adapter carries only the thin harness mapping;
 *      everything else lives once, in canonical.
 *
 * Waivers: schemas/canonical/v0/adapter-thinness-waivers.json — every entry
 * carries a reason AND a dated removal owner. The known Kobiton `.codex` fork
 * is waived DATED, and that waiver is deleted in the same PR that converts
 * the fork (E3.6). An expired-intent waiver is tech debt on the record, not
 * an exemption class.
 */

import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');

const ADAPTER_DIR = /\/\.(codex|openclaw|gemini(?:-cli)?|cursor|copilot)\//;
const FORBIDDEN_INSIDE_ADAPTER = [
  { re: /\/references\//, why: 'reference material lives once, in canonical' },
  { re: /\/scripts\//, why: 'executable payloads live once, in canonical' },
  { re: /eval-spec\.ya?ml$/, why: 'eval specs are canonical, harness-neutral' },
  { re: /(^|\/)LICENSE[^/]*$/, why: 'license lives once, in canonical' },
  { re: /(^|\/)package\.json$/, why: 'version manifests live once, in canonical' },
];

export function loadWaivers(root = ROOT) {
  try {
    return JSON.parse(
      readFileSync(
        join(root, 'schemas', 'canonical', 'v0', 'adapter-thinness-waivers.json'),
        'utf-8',
      ),
    );
  } catch {
    return { waivers: [] };
  }
}

export function adapterFiles(files) {
  // Anchored under plugins/: the repo-root .gemini/ reviewer config and any
  // future root-level dotdir are host configuration, not harness adapters.
  return files.filter(
    (f) =>
      f.startsWith('plugins/') &&
      (ADAPTER_DIR.test('/' + f) || /\/adapters\/[^/]+\//.test('/' + f)),
  );
}

export function canonicalCounterpart(file) {
  const m = ('/' + file).match(ADAPTER_DIR);
  if (m) return ('/' + file).replace(ADAPTER_DIR, '/').slice(1);
  return ('/' + file).replace(/\/adapters\/[^/]+\//, '/').slice(1);
}

export function isWaived(file, waivers) {
  return (waivers.waivers || []).some((w) => file.startsWith(w.path_prefix));
}

export function checkAdapters(files, readFile, waivers) {
  const violations = [];
  for (const file of adapterFiles(files)) {
    if (isWaived(file, waivers)) continue;
    for (const rule of FORBIDDEN_INSIDE_ADAPTER) {
      if (rule.re.test('/' + file)) {
        violations.push({ file, kind: 'forbidden-class', why: rule.why });
      }
    }
    const counterpart = canonicalCounterpart(file);
    if (counterpart !== file && files.includes(counterpart)) {
      const a = readFile(file);
      const b = readFile(counterpart);
      if (a !== null && a === b) {
        violations.push({
          file,
          kind: 'byte-identical',
          why: `identical to canonical ${counterpart} — a fork is not an adapter`,
        });
      }
    }
  }
  return violations;
}

const isMain = process.argv[1] && import.meta.url === new URL(`file://${process.argv[1]}`).href;
if (isMain) {
  const files = execFileSync('git', ['ls-files'], {
    cwd: ROOT,
    encoding: 'utf-8',
    maxBuffer: 256 * 1024 * 1024,
  })
    .split('\n')
    .filter(Boolean);
  const waivers = loadWaivers();
  const read = (f) => {
    try {
      return readFileSync(join(ROOT, f), 'utf-8');
    } catch {
      return null;
    }
  };
  const violations = checkAdapters(files, read, waivers);
  for (const v of violations)
    console.error(`adapter-thinness: VIOLATION (${v.kind}) — ${v.file}: ${v.why}`);
  const waived = adapterFiles(files).filter((f) => isWaived(f, waivers)).length;
  if (violations.length > 0) {
    console.error(`adapter-thinness: FAIL — ${violations.length} violation(s).`);
    process.exit(1);
  }
  console.log(
    `adapter-thinness: OK (${adapterFiles(files).length} adapter file(s); ${waived} under dated waiver)`,
  );
}
