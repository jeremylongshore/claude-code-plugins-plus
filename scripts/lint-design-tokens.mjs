#!/usr/bin/env node
/**
 * lint-design-tokens.mjs — RATCHETING COLOR-TOKEN GATE
 *
 * WHY
 * ---
 * marketplace/DESIGN.md is the design constitution: colors are OKLCH and live in
 * `src/styles/tokens.css`; components reference TOKENS, never raw values. That
 * rule had drifted to 227 raw color literals across 72 files with nothing in CI
 * enforcing it — which is precisely how a design system stops being a system.
 *
 * `scripts/lint-design-tells.mjs` is a different gate (AI-writing tells:
 * em-dash density and friends). It does not look at color at all.
 *
 * WHAT IT DOES
 * ------------
 * Counts raw color literals (`#rrggbb`, `rgb()`, `rgba()`) under marketplace/src,
 * excluding `tokens.css` — the one file allowed to define literal color, and
 * which is now itself 100% OKLCH.
 *
 * RATCHET, NOT A CLIFF
 * --------------------
 * Failing outright on 227 pre-existing violations would block every PR and get
 * the gate disabled within a day. Instead it fails only when the count RISES
 * above the recorded baseline. Existing debt is grandfathered; new drift cannot
 * land. As files get migrated the baseline is lowered with --update-baseline,
 * and it can never be raised silently: raising it requires editing the committed
 * baseline file in a reviewable diff.
 *
 * USAGE
 *   node scripts/lint-design-tokens.mjs                  # gate (exit 1 if over)
 *   node scripts/lint-design-tokens.mjs --report         # per-file breakdown
 *   node scripts/lint-design-tokens.mjs --update-baseline # ratchet DOWN only
 */

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { readdirSync, statSync } from 'node:fs';
import { join, dirname, relative, extname, basename } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(__dirname, '..');
const SCAN_ROOT = join(REPO_ROOT, 'marketplace', 'src');
const BASELINE_FILE = join(__dirname, '.design-tokens-baseline.json');

/** The single file permitted to declare literal color values. */
const ALLOWED_LITERAL_FILES = new Set(['tokens.css']);
const SCAN_EXTENSIONS = new Set(['.astro', '.css']);

/** Raw color literals. Deliberately NOT matching `oklch(` — that's the target state. */
const COLOR_LITERAL = /#[0-9a-fA-F]{3,8}\b|rgba?\(/g;

function walk(dir, out = []) {
  let entries;
  try {
    entries = readdirSync(dir);
  } catch {
    return out;
  }
  for (const name of entries) {
    const full = join(dir, name);
    let st;
    try {
      st = statSync(full);
    } catch {
      continue;
    }
    if (st.isDirectory()) walk(full, out);
    else if (SCAN_EXTENSIONS.has(extname(name))) out.push(full);
  }
  return out;
}

function scan() {
  const perFile = [];
  let total = 0;
  for (const file of walk(SCAN_ROOT)) {
    if (ALLOWED_LITERAL_FILES.has(basename(file))) continue;
    const text = readFileSync(file, 'utf8');
    const n = (text.match(COLOR_LITERAL) || []).length;
    if (n > 0) {
      perFile.push({ file: relative(REPO_ROOT, file), count: n });
      total += n;
    }
  }
  perFile.sort((a, b) => b.count - a.count || a.file.localeCompare(b.file));
  return { total, perFile };
}

function readBaseline() {
  if (!existsSync(BASELINE_FILE)) return null;
  try {
    return JSON.parse(readFileSync(BASELINE_FILE, 'utf8'));
  } catch {
    return null;
  }
}

const args = process.argv.slice(2);
const { total, perFile } = scan();
const baseline = readBaseline();

if (args.includes('--update-baseline')) {
  const prev = baseline?.maxRawColorLiterals ?? Infinity;
  if (total > prev) {
    console.error(
      `refusing to RAISE the baseline (${prev} -> ${total}). The ratchet only goes down.\n` +
        `If an increase is genuinely intended, edit ${relative(REPO_ROOT, BASELINE_FILE)} by hand so it shows up in review.`,
    );
    process.exit(1);
  }
  writeFileSync(
    BASELINE_FILE,
    JSON.stringify(
      {
        $comment:
          'Ratchet baseline for lint-design-tokens.mjs. Lower it as files migrate to tokens; it must never be raised except by a hand-edit visible in review.',
        maxRawColorLiterals: total,
        filesWithLiterals: perFile.length,
      },
      null,
      2,
    ) + '\n',
  );
  console.log(`baseline updated: ${prev === Infinity ? 'none' : prev} -> ${total}`);
  process.exit(0);
}

console.log('━━━ lint-design-tokens — DESIGN.md color discipline ━━━');
console.log(`  raw color literals outside tokens.css : ${total}`);
console.log(`  files containing them                 : ${perFile.length}`);
console.log(
  `  baseline                              : ${baseline?.maxRawColorLiterals ?? '(none recorded)'}`,
);

if (args.includes('--report')) {
  console.log('\n  per-file:');
  for (const { file, count } of perFile) console.log(`    ${String(count).padStart(4)}  ${file}`);
}

if (baseline == null) {
  console.log('\n  No baseline recorded — run with --update-baseline to establish one.');
  process.exit(0);
}

if (total > baseline.maxRawColorLiterals) {
  console.error(
    `\n  ❌ FAIL: raw color literals rose ${baseline.maxRawColorLiterals} -> ${total}.\n` +
      `     DESIGN.md: colors are OKLCH and live in tokens.css; components reference tokens.\n` +
      `     Use an existing token (or add one to tokens.css) instead of a literal.\n` +
      `     Run with --report to see which files changed.`,
  );
  process.exit(1);
}

if (total < baseline.maxRawColorLiterals) {
  console.log(
    `\n  ✅ PASS — and ${baseline.maxRawColorLiterals - total} fewer than baseline.\n` +
      `     Ratchet it down: node scripts/lint-design-tokens.mjs --update-baseline`,
  );
} else {
  console.log('\n  ✅ PASS — at baseline, no new drift.');
}
process.exit(0);
