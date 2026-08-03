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
 * green while every page publishes a broken preview. Count drift is reported
 * as a note, never a failure: the catalogue grows daily, and a gate that fails
 * on ordinary growth is a gate somebody deletes.
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

if (process.argv.includes('--check')) {
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

  // Staleness is reported, never fatal. The card prints live counts, and those
  // move every time a skill lands; failing CI on ordinary catalogue growth would
  // make this gate a nuisance, and nuisance gates get deleted. Structural
  // breakage above is what blocks.
  try {
    const gen = JSON.parse(readFileSync(META, 'utf8'));
    const now = JSON.parse(readFileSync(INDEX, 'utf8')).stats;
    const drift = Math.abs(now.totalSkills - gen.skills) / Math.max(gen.skills, 1);
    if (drift > 0.1) {
      console.warn(
        `  note: card was rendered at ${gen.skills} skills, index now reads ` +
          `${now.totalSkills} (${(drift * 100).toFixed(0)}% drift). ${REGEN}`,
      );
    }
  } catch {
    /* no sidecar yet, or index unreadable — not a reason to fail the gate */
  }

  console.log(`og-image: valid (${size.w}x${size.h}, ${(buf.length / 1024).toFixed(0)} KB)`);
  process.exit(0);
}

// Live counts, same source the site builds from. Fail soft to a count-free card
// rather than baking a wrong number into an image that is expensive to notice.
let skills = null;
let plugins = null;
try {
  const stats = JSON.parse(readFileSync(INDEX, 'utf8')).stats;
  skills = stats.totalSkills;
  plugins = stats.totalPlugins;
} catch {
  console.error('  search index unreadable — rendering the card without counts');
}

const fmt = (n) => (typeof n === 'number' ? n.toLocaleString('en-US') : null);
const headline = fmt(skills)
  ? `${fmt(skills)} SKILLS FOR<br/>CLAUDE CODE.`
  : 'SKILLS FOR<br/>CLAUDE CODE.';
const sub = fmt(plugins)
  ? `${fmt(plugins)} plugins · agents · skills — free and open source`
  : 'plugins · agents · skills — free and open source';

// Tokens copied from marketplace/src/styles/tokens.css. Inlined deliberately:
// this renders in a bare browser page with no stylesheet pipeline, and the
// values are the two that matter (canvas + signal), not the whole system.
const HTML = `<!doctype html><html><head><meta charset="utf-8">
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
  </div>
  <div class="cmd"><span class="prompt">&gt;</span><span>/plugin marketplace add jeremylongshore/claude-code-plugins</span></div>
  <div class="foot"><span>Claude Code · Codex · Cursor</span><span>Intent Solutions</span></div>
</body></html>`;

// Playwright is a devDependency of the `marketplace` workspace, not the root,
// and this script lives at the root — so a bare `import 'playwright'` fails
// here regardless of cwd. Resolve it against the workspace that owns it, and
// fall back to the bare specifier for anyone who has it hoisted.
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
await page.setContent(HTML, { waitUntil: 'networkidle' });
// Give the webfont a beat to swap in; otherwise the card can render in the
// fallback monospace, which is legible but off-brand.
await page.waitForTimeout(1200);
mkdirSync(dirname(OUT), { recursive: true });
const buf = await page.screenshot({ type: 'png' });
writeFileSync(OUT, buf);
await browser.close();

// Sidecar recording what the card was rendered from, so --check can report
// drift without having to OCR the image.
writeFileSync(
  META,
  JSON.stringify(
    {
      $comment:
        'Generated by scripts/generate-og-image.mjs alongside og-image.png. Lets --check report count drift without reading pixels.',
      skills,
      plugins,
      width: EXPECTED_W,
      height: EXPECTED_H,
    },
    null,
    2,
  ) + '\n',
);
console.log(
  `og-image: wrote ${OUT} (${EXPECTED_W}x${EXPECTED_H}, ${(buf.length / 1024).toFixed(0)} KB)`,
);
