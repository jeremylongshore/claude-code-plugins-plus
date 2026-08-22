#!/usr/bin/env node
/**
 * generate-og-image.mjs — render marketplace/public/og-image.png.
 *
 * WHY THIS EXISTS
 * ---------------
 * `BaseLayout.astro` sets `image = "/og-image.png"` and emits it as BOTH
 * `og:image` and `twitter:image` on every page. The file had never been
 * committed — `git log --all -- marketplace/public/og-image.png` returns
 * nothing — so 3,830 built pages pointed at a URL that returned 404. Every link
 * preview of tonsofskills.com on X, LinkedIn, Slack, Discord and iMessage has
 * been rendering without an image for the life of the site. That is a silent
 * click-through tax on every share, and it does not show up in any CI gate
 * because a missing og:image breaks nothing at build time.
 *
 * WHY RENDER RATHER THAN HAND-DRAW
 * --------------------------------
 * The card carries live counts. Hand-exporting a PNG from a design tool means
 * the numbers freeze at export time and rot exactly the way the "244 searchable
 * agent skills" fallback description did. Rendering from the same
 * unified-search-index.json the site builds from means `npm run build`-adjacent
 * regeneration keeps it honest.
 *
 * It also renders in the real design language — JetBrains Mono, zero radius,
 * the hard offset shadow, the single signal accent — so the preview looks like
 * the page it links to. See marketplace/DESIGN.md.
 *
 * USAGE
 *   node scripts/generate-og-image.mjs            # writes marketplace/public/og-image.png
 *   node scripts/generate-og-image.mjs --check    # validate the committed card
 *
 * --check does NOT merely test existence. It verifies the PNG signature and
 * IHDR, asserts 1200x630, and rejects a suspiciously small (truncated) file —
 * because a stale, corrupt or unrelated PNG would otherwise keep the gate
 * green while every page publishes a broken preview. It also requires the
 * cohort and reproduction command in the sidecar, so a rendered count cannot
 * lose its meaning. Count drift is reported as a note, never a failure: the
 * catalogue grows daily, and a gate that fails on ordinary growth is a gate
 * somebody deletes.
 *
 * Requires the Playwright chromium browser (already a repo devDependency).
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const OUT = join(ROOT, 'marketplace', 'public', 'og-image.png');
const INDEX = join(ROOT, 'marketplace', 'src', 'data', 'unified-search-index.json');

const EXPECTED_W = 1200;
const EXPECTED_H = 630;
const META = join(ROOT, 'marketplace', 'public', 'og-image.meta.json');
const REGEN = 'Run: node scripts/generate-og-image.mjs';
// Published count label: marketplace-visible skills (see the rendered card).
export const COUNT_COHORT = 'marketplace-visible';
export const COUNT_COMMAND = 'node scripts/corpus-resolver.mjs --cohort marketplace-visible --json';
export const COUNT_SOURCE = 'marketplace/src/data/unified-search-index.json';
export const COUNT_PROVENANCE = '<CountProvenance cohort="marketplace-visible" />';

/**
 * Read dimensions straight out of the PNG IHDR chunk — 8-byte signature, then
 * an 8-byte chunk header, then width/height as big-endian uint32. No image
 * library needed, and it doubles as a format check: anything that is not a real
 * PNG fails the signature test.
 */
function pngSize(buf) {
  const SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  if (buf.length < 24 || !buf.subarray(0, 8).equals(SIG)) return null;
  if (buf.subarray(12, 16).toString('ascii') !== 'IHDR') return null;
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

export function readIndexStats(indexPath = INDEX) {
  const stats = JSON.parse(readFileSync(indexPath, 'utf8')).stats;
  const countLabel = 'marketplace-visible skills';
  if (
    !stats ||
    !Number.isInteger(stats.totalSkills) ||
    stats.totalSkills < 0 ||
    !Number.isInteger(stats.totalPlugins) ||
    stats.totalPlugins < 0
  ) {
    throw new Error(`${countLabel} stats are missing valid integer totals: ${indexPath}`);
  }
  return stats;
}

export function buildCountContract(stats) {
  if (!Number.isInteger(stats?.totalSkills) || !Number.isInteger(stats?.totalPlugins)) {
    throw new Error('OG image counts require integer totalSkills and totalPlugins values');
  }
  return {
    cohort: COUNT_COHORT,
    command: COUNT_COMMAND,
    source: COUNT_SOURCE,
    provenance: COUNT_PROVENANCE,
    label: 'marketplace-visible skills',
    skills: stats.totalSkills,
    plugins: stats.totalPlugins,
  };
}

function requireCountContract(meta) {
  if (
    meta?.cohort !== COUNT_COHORT ||
    meta?.command !== COUNT_COMMAND ||
    meta?.source !== COUNT_SOURCE ||
    meta?.provenance !== COUNT_PROVENANCE ||
    meta?.label !== 'marketplace-visible skills' ||
    !Number.isInteger(meta.skills) ||
    !Number.isInteger(meta.plugins)
  ) {
    throw new Error(
      `OG image metadata must identify cohort ${COUNT_COHORT}, source ${COUNT_SOURCE}, ` +
        `and command ${COUNT_COMMAND}. ${REGEN}`,
    );
  }
  return meta;
}

async function checkImage() {
  // Existence alone is NOT enough. A stale, truncated, mis-sized or entirely
  // unrelated PNG would keep this gate green while every page publishes a
  // broken social preview — which is the same failure mode the gate exists to
  // prevent, just one level up. Validate the bytes, not the filename.
  if (!existsSync(OUT)) {
    console.error(
      `MISSING: ${OUT}\n` +
        `Every page emits og:image -> /og-image.png. Without this file every link\n` +
        `preview of the site renders imageless. ${REGEN}`,
    );
    process.exit(1);
  }
  const buf = readFileSync(OUT);
  const size = pngSize(buf);
  if (!size) {
    console.error(`INVALID: ${OUT} is not a readable PNG (bad signature or IHDR). ${REGEN}`);
    process.exit(1);
  }
  if (size.w !== EXPECTED_W || size.h !== EXPECTED_H) {
    console.error(
      `WRONG SIZE: ${OUT} is ${size.w}x${size.h}, expected ${EXPECTED_W}x${EXPECTED_H}.\n` +
        `Off-ratio cards get cropped or rejected by social scrapers. ${REGEN}`,
    );
    process.exit(1);
  }
  if (buf.length < 5 * 1024) {
    console.error(`SUSPECT: ${OUT} is only ${buf.length} bytes — likely truncated. ${REGEN}`);
    process.exit(1);
  }

  const gen = requireCountContract(JSON.parse(readFileSync(META, 'utf8')));
  const now = readIndexStats();

  // Staleness is reported, never fatal. The card prints live counts, and those
  // move every time a skill lands; failing CI on ordinary catalogue growth would
  // make this gate a nuisance, and nuisance gates get deleted. Structural
  // breakage above is what blocks. The count remains meaningful because the
  // sidecar carries its cohort, source, and reproduction command.
  const drift = Math.abs(now.totalSkills - gen.skills) / Math.max(gen.skills, 1);
  if (drift > 0.1) {
    console.warn(
      `  note: card was rendered at ${gen.skills} skills, index now reads ` +
        `${now.totalSkills} (${(drift * 100).toFixed(0)}% drift). ${REGEN}`,
    );
  }

  console.log(`og-image: valid (${size.w}x${size.h}, ${(buf.length / 1024).toFixed(0)} KB)`);
}

export function buildHtml(contract) {
  const fmt = (n) => n.toLocaleString('en-US');
  const headline = `${fmt(contract.skills)} SKILLS FOR<br/>CLAUDE CODE.`;
  const sub = `${fmt(contract.plugins)} plugins · agents · skills — free and open source`;
  const provenance = `${contract.label} · ${contract.source}`;
  const reproduction = contract.command;

  return `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{width:1200px;height:630px;background:oklch(14.574% 0.0043 285.86);
       font-family:'JetBrains Mono',monospace;color:oklch(96.743% 0.0013 286.38);
       padding:72px;display:flex;flex-direction:column;justify-content:space-between}
  .brand{font-size:22px;font-weight:700;letter-spacing:.24em;text-transform:uppercase;
         color:oklch(76.542% 0.1509 47.74)}
  h1{font-size:76px;font-weight:800;line-height:1.04;letter-spacing:-.04em;text-transform:uppercase}
  .sub{font-size:24px;color:oklch(71.181% 0.0129 286.07);margin-top:22px}
  .provenance{font-size:15px;color:oklch(62% 0.0129 286.07);margin-top:13px}
  .cmd{align-self:flex-start;background:oklch(20.904% 0 0);
       border:1px solid oklch(96.743% 0.0013 286.38);
       box-shadow:6px 6px 0 oklch(96.743% 0.0013 286.38);
       padding:20px 28px;font-size:26px;display:flex;gap:14px;align-items:center}
  .prompt{color:oklch(76.542% 0.1509 47.74);font-weight:700}
  .foot{display:flex;justify-content:space-between;align-items:flex-end;
        font-size:20px;color:oklch(55.166% 0.0138 285.94)}
</style></head><body>
  <div class="brand">tonsofskills.com</div>
  <div>
    <h1>${headline}</h1>
    <div class="sub">${sub}</div>
    <div class="provenance">${provenance}</div>
  </div>
  <div class="cmd"><span class="prompt">&gt;</span><span>/plugin marketplace add jeremylongshore/claude-code-plugins</span></div>
  <div class="foot"><span>Open source · MIT</span><span>${reproduction}</span></div>
</body></html>`;
}

// Tokens copied from marketplace/src/styles/tokens.css. Inlined deliberately:
// this renders in a bare browser page with no stylesheet pipeline, and the
// values are the two that matter (canvas + signal), not the whole system.
async function generateImage() {
  const contract = buildCountContract(readIndexStats());
  // Playwright is a devDependency of the `marketplace` workspace, not the root,
  // and this script lives at the root — so a bare `import 'playwright'` fails
  // here regardless of cwd. Resolve it against the workspace that owns it, and
  // fall back to the bare specifier for anyone who has it hoisted. Keep this
  // lazy: CI's structural --check path must not need a browser installation.
  const { createRequire } = await import('node:module');
  const require = createRequire(join(ROOT, 'marketplace', 'package.json'));
  let chromium;
  try {
    ({ chromium } = require('playwright'));
  } catch {
    ({ chromium } = await import('playwright'));
  }
  const browser = await chromium.launch();
  const page = await browser.newPage({
    viewport: { width: 1200, height: 630 },
    deviceScaleFactor: 1,
  });
  await page.setContent(buildHtml(contract), { waitUntil: 'networkidle' });
  // Give the webfont a beat to swap in; otherwise the card can render in the
  // fallback monospace, which is legible but off-brand.
  await page.waitForTimeout(1200);
  mkdirSync(dirname(OUT), { recursive: true });
  const buf = await page.screenshot({ type: 'png' });
  await browser.close();

  // Sidecar records the cohort and command that give the rendered counts their
  // meaning, so --check can verify the contract without reading pixels.
  writeFileSync(
    META,
    JSON.stringify(
      {
        $comment:
          'Generated by scripts/generate-og-image.mjs alongside og-image.png. The cohort, source, and command make embedded counts reproducible.',
        ...contract,
        width: EXPECTED_W,
        height: EXPECTED_H,
      },
      null,
      2,
    ) + '\n',
  );
  writeFileSync(OUT, buf);
  console.log(
    `og-image: wrote ${OUT} (${EXPECTED_W}x${EXPECTED_H}, ${(buf.length / 1024).toFixed(0)} KB; ${contract.cohort})`,
  );
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  try {
    if (process.argv.includes('--check')) await checkImage();
    else await generateImage();
  } catch (error) {
    console.error(`og-image: ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 1;
  }
}
