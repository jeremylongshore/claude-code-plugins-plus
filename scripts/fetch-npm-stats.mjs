#!/usr/bin/env node
/**
 * fetch-npm-stats.mjs
 *
 * Enumerates every `package.json` in the monorepo, checks which are actually
 * published on npm, fetches day/week/month downloads for each, and emits:
 *   1. marketplace/src/data/npm-stats.json  (consumed by website marquee)
 *   2. README.md bounded block between NPM-STATS:START/END sentinels
 *
 * Covers both `@intentsolutionsio/*` scoped packages and legacy-named ones
 * (claude-cowork, claude-plugin-validator, pr-to-spec, etc.) — anything that
 * resolves to HTTP 200 on the npm registry is counted.
 *
 * Intended to run daily via a GitHub Actions cron; the workflow commits any
 * diff back to main, which triggers a Pages redeploy.
 *
 * Usage:
 *   node scripts/fetch-npm-stats.mjs
 *   node scripts/fetch-npm-stats.mjs --dry-run   # print, don't write
 */

import { existsSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';

const ROOT = resolve(dirname(new URL(import.meta.url).pathname), '..');
const OUT_JSON = join(ROOT, 'marketplace', 'src', 'data', 'npm-stats.json');
const README = join(ROOT, 'README.md');

const START_SENTINEL = '<!-- NPM-STATS:START — do not edit; daily cron updates this -->';
const END_SENTINEL = '<!-- NPM-STATS:END -->';

// Skip build/dependency dirs when walking.
const SKIP_DIRS = new Set(['node_modules', '.git', 'dist', 'build', '.next', '.astro']);

function walkPackageJsons(dir) {
  const out = [];
  let entries;
  try {
    entries = readdirSync(dir, { withFileTypes: true });
  } catch {
    return out;
  }
  for (const ent of entries) {
    const p = join(dir, ent.name);
    if (ent.isDirectory()) {
      if (SKIP_DIRS.has(ent.name)) continue;
      out.push(...walkPackageJsons(p));
    } else if (ent.isFile() && ent.name === 'package.json') {
      out.push(p);
    }
  }
  return out;
}

function readPkg(path) {
  try {
    return JSON.parse(readFileSync(path, 'utf-8'));
  } catch {
    return null;
  }
}

async function fetchJson(url, retries = 4) {
  for (let i = 0; i <= retries; i++) {
    try {
      const res = await fetch(url);
      if (res.status === 404) return { __notFound: true };
      if (res.status === 429) {
        // Back off exponentially on rate-limit; npm's window usually resets in ~1min
        const wait = 1000 * Math.pow(2, i);
        await new Promise((r) => setTimeout(r, wait));
        continue;
      }
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch (err) {
      if (i === retries) throw err;
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
    }
  }
  throw new Error('retries exhausted');
}

// Unscoped names can collide with popular 3rd-party packages (axiom,
// marketplace, etc.). We only count a name as "ours" when our configured
// OWNERS set appears in the package's maintainer list. Scoped names under
// @intentsolutionsio/ are always ours.
const OWNERS = new Set(['jeremylongshore', 'intentsolutionsio']);
const OURS_SCOPES = ['@intentsolutionsio/'];

async function fetchRegistryMetadata(name) {
  const enc = encodeURIComponent(name);
  for (let i = 0; i < 4; i++) {
    const res = await fetch(`https://registry.npmjs.org/${enc}`);
    if (res.status === 404) return null;
    if (res.status === 429) {
      await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, i)));
      continue;
    }
    if (!res.ok) return null;
    try {
      return await res.json();
    } catch {
      return null;
    }
  }
  return null;
}

function isOurs(name, meta) {
  if (OURS_SCOPES.some((s) => name.startsWith(s))) return true;
  if (!meta) return false;
  const maintainers = meta.maintainers || [];
  for (const m of maintainers) {
    const uname = typeof m === 'string' ? m.split('<')[0].trim() : m?.name;
    if (uname && OWNERS.has(uname.toLowerCase())) return true;
  }
  return false;
}

async function statsFor(name) {
  const enc = encodeURIComponent(name);
  const meta = await fetchRegistryMetadata(name);
  if (!meta) return null; // 404 or unreachable
  if (!isOurs(name, meta)) return null; // 3rd-party collision

  // Serial fetch (not Promise.all) to stay under npm's per-IP rate limit.
  const day = await fetchJson(`https://api.npmjs.org/downloads/point/last-day/${enc}`);
  const week = await fetchJson(`https://api.npmjs.org/downloads/point/last-week/${enc}`);
  const month = await fetchJson(`https://api.npmjs.org/downloads/point/last-month/${enc}`);

  // npm returns `{error: "package ... not found"}` for unpublished ones even
  // if registry has a placeholder. Treat missing `downloads` as zero so a
  // scoped reserved-but-unpublished name doesn't poison aggregates.
  const lastDay = day?.downloads ?? 0;
  const lastWeek = week?.downloads ?? 0;
  const lastMonth = month?.downloads ?? 0;

  return { name, lastDay, lastWeek, lastMonth };
}

async function collectStats(pkgNames, concurrency = 8) {
  const results = [];
  let i = 0;
  async function worker() {
    while (i < pkgNames.length) {
      const idx = i++;
      const name = pkgNames[idx];
      try {
        const s = await statsFor(name);
        if (s) results.push(s);
      } catch (err) {
        // Transient failures shouldn't poison the run
        console.warn(`  ⚠ ${name}: ${err.message}`);
      }
    }
  }
  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);
  return results;
}

function fmt(n) {
  return Number(n || 0).toLocaleString('en-US');
}

function buildReadmeBlock(agg) {
  const lines = [
    START_SENTINEL,
    '',
    '### 📦 Live npm Downloads',
    '',
    `Across **${agg.publishedCount} published packages** in the `,
    `[claude-code-plugins](https://www.npmjs.com/~jeremylongshore) namespace. Updated daily by GitHub Actions.`,
    '',
    '| Window | Downloads |',
    '|--------|----------:|',
    `| Last 24 hours | ${fmt(agg.totalDay)} |`,
    `| Last 7 days | ${fmt(agg.totalWeek)} |`,
    `| Last 30 days | ${fmt(agg.totalMonth)} |`,
    '',
    '**Top 10 by last 30 days:**',
    '',
    '| # | Package | Last 30d |',
    '|---|---------|---------:|',
    ...agg.top.slice(0, 10).map((p, i) => {
      const url = `https://www.npmjs.com/package/${p.name}`;
      return `| ${i + 1} | [\`${p.name}\`](${url}) | ${fmt(p.lastMonth)} |`;
    }),
    '',
    `<sub>Last refreshed ${agg.generatedAt}.</sub>`,
    '',
    END_SENTINEL,
  ];
  return lines.join('\n');
}

function updateReadme(block) {
  const readme = readFileSync(README, 'utf-8');
  const s = readme.indexOf(START_SENTINEL);
  const e = readme.indexOf(END_SENTINEL);
  if (s === -1 || e === -1) {
    throw new Error(
      `README.md missing NPM-STATS sentinels. Add:\n${START_SENTINEL}\n${END_SENTINEL}\nwhere the stats block belongs.`
    );
  }
  return readme.slice(0, s) + block + readme.slice(e + END_SENTINEL.length);
}

async function main() {
  const dryRun = process.argv.includes('--dry-run');

  // 1. Enumerate every package.json in the monorepo
  console.log('Enumerating package.json files...');
  const pkgFiles = walkPackageJsons(ROOT);
  const candidates = new Set();
  for (const f of pkgFiles) {
    const p = readPkg(f);
    if (!p) continue;
    if (p.private) continue;
    if (!p.name) continue;
    candidates.add(p.name);
  }
  const names = Array.from(candidates).sort();
  console.log(`  candidates: ${names.length}`);

  // 2. Fetch stats for each (publishes that haven't happened yet → HTTP 404 → skipped)
  console.log('Fetching npm download stats...');
  const stats = await collectStats(names, 4);
  console.log(`  published: ${stats.length}`);

  // 3. Aggregate
  const totalDay = stats.reduce((s, p) => s + p.lastDay, 0);
  const totalWeek = stats.reduce((s, p) => s + p.lastWeek, 0);
  const totalMonth = stats.reduce((s, p) => s + p.lastMonth, 0);
  const top = [...stats].sort((a, b) => b.lastMonth - a.lastMonth);

  const agg = {
    generatedAt: new Date().toISOString(),
    publishedCount: stats.length,
    candidateCount: names.length,
    totalDay,
    totalWeek,
    totalMonth,
    top,
  };

  console.log('\nTotals:');
  console.log(`  day=${fmt(totalDay)}  week=${fmt(totalWeek)}  month=${fmt(totalMonth)}`);
  console.log('\nTop 10:');
  for (const [i, p] of top.slice(0, 10).entries()) {
    console.log(`  ${i + 1}. ${p.name.padEnd(50)}  ${fmt(p.lastMonth)}`);
  }

  if (dryRun) {
    console.log('\n(--dry-run: no files written)');
    return;
  }

  // 4. Write JSON + README block
  writeFileSync(OUT_JSON, JSON.stringify(agg, null, 2) + '\n');
  console.log(`\nWrote ${OUT_JSON}`);

  try {
    const updated = updateReadme(buildReadmeBlock(agg));
    const current = readFileSync(README, 'utf-8');
    if (updated !== current) {
      writeFileSync(README, updated);
      console.log('Updated README NPM-STATS block');
    } else {
      console.log('README NPM-STATS block already current');
    }
  } catch (err) {
    console.warn(`⚠ README update skipped: ${err.message}`);
  }
}

main().catch((err) => {
  console.error('fetch-npm-stats failed:', err);
  process.exit(1);
});
