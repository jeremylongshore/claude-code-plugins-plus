#!/usr/bin/env node
/**
 * check-generated-artifacts.mjs — assert that deterministically-regenerated
 * projections are NOT tracked in git.
 *
 * A generated file that is also committed has two claimants to one fact: the
 * generator and the tree. They diverge silently, because nothing compares them —
 * exactly how `marketplace/public/data/*.json` came to duplicate ~28.5 MB of
 * `marketplace/src/data/*.json` byte-for-byte (identical blob SHAs), and how the
 * kobiton binary reached `skills/.curated/` (bead claude-5awj.2 / .1).
 *
 * This gate is the RECURRENCE PREVENTION for that class: re-adding such a file
 * fails CI with the regeneration command in the message. It deliberately checks
 * TRACKING, not content — content equality is the generator's job, and a gate
 * that regenerated to compare would be slow and would mask a broken generator.
 *
 * Exit 0 = clean. Exit 1 = a projection is tracked (each one named).
 */
import { execFileSync } from 'node:child_process';

/** @type {{glob: string, canonical: string, regenerate: string, why: string}[]} */
const PROJECTIONS = [
  {
    glob: 'marketplace/public/data/*.json',
    canonical: 'marketplace/src/data/*.json',
    regenerate: 'cd marketplace && npm run build   (or: node scripts/copy-public-data.mjs)',
    why: 'runtime static-asset copy of the canonical build data; ~28.5MB when tracked',
  },
  {
    glob: 'marketplace/public/downloads/**',
    canonical: '.claude-plugin/marketplace.extended.json',
    regenerate: 'cd marketplace && npm run build   (cowork:zips)',
    why: 'cowork zips are rebuilt from the catalog on every build',
  },
];

const BUF = { maxBuffer: 64 * 1024 * 1024 };
let failures = 0;

for (const p of PROJECTIONS) {
  let tracked = '';
  try {
    tracked = execFileSync('git', ['ls-files', '--', p.glob], BUF).toString().trim();
  } catch {
    tracked = '';
  }
  const files = tracked ? tracked.split('\n') : [];
  if (files.length) {
    failures += files.length;
    console.error(
      `\n✗ ${files.length} tracked file(s) matching ${p.glob} — this is a GENERATED projection.`,
    );
    console.error(`    canonical:  ${p.canonical}`);
    console.error(`    why:        ${p.why}`);
    console.error(`    regenerate: ${p.regenerate}`);
    console.error(
      `    fix:        git rm --cached <file>   (it is already ignored; do not commit it)`,
    );
    for (const f of files.slice(0, 10)) console.error(`      ${f}`);
    if (files.length > 10) console.error(`      … and ${files.length - 10} more`);
  }
}

if (failures) {
  console.error(
    `\ngenerated-artifacts: ${failures} tracked projection file(s). A generated file must have exactly one claimant — its generator.`,
  );
  process.exit(1);
}
console.log(`generated-artifacts: OK (${PROJECTIONS.length} projection globs, 0 tracked)`);
