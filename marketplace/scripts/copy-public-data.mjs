#!/usr/bin/env node
/**
 * copy-public-data.mjs — project the large generated data files from their
 * canonical home (`src/data/`) into `public/data/`, where Astro serves them as
 * static assets at runtime (`/data/<file>.json`).
 *
 * Canonical: `marketplace/src/data/*.json` — written by discover-skills.mjs and
 * generate-unified-search.mjs, and read at BUILD time by every generator.
 * Projection: `marketplace/public/data/*.json` — byte-identical copies read only
 * at RUNTIME by the browser (skills/index.astro, explore.astro, BaseLayout.astro).
 *
 * The projection is deliberately NOT tracked in git (see .gitignore): it is
 * regenerated deterministically here, and tracking it duplicated ~28.5 MB of the
 * repository payload while giving a second, silently-divergeable claimant to a
 * fact that `src/data/` already owns.
 *
 * Extracted from build.mjs so `predev` can run it too — without it, a fresh clone
 * running `astro dev` (which serves `public/` as-is, with no build step) 404s on
 * both runtime fetches.
 */
import { copyFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
export const PROJECTED_FILES = ['unified-search-index.json', 'skills-catalog.json'];

const srcDir = resolve(__dirname, '..', 'src', 'data');
const publicDataDir = resolve(__dirname, '..', 'public', 'data');

mkdirSync(publicDataDir, { recursive: true });
for (const file of PROJECTED_FILES) {
  copyFileSync(resolve(srcDir, file), resolve(publicDataDir, file));
  console.log(`[data:copy] ${file} → public/data/${file}`);
}
