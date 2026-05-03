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
 * Intended to run daily via a GitHub Actions cron; the workflow opens a PR
 * with any diff (since `main` is branch-protected).
 *
 * Usage:
 *   node scripts/fetch-npm-stats.mjs
 *   node scripts/fetch-npm-stats.mjs --dry-run   # print, don't write
 *
 * Exit codes:
 *   0 — success (any count of packages probed cleanly)
 *   1 — one or more registry probes hit persistent rate-limits or server errors,
 *       making the published/unpublished counts unreliable. Surfaces as a red
 *       cron run instead of silently undercounting.
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

// Packages "established" longer than this are considered baseline traffic.
// Newer publishes get a separate aggregate so a bulk-publish event doesn't
// dominate the headline number.
const ESTABLISHED_THRESHOLD_MS = 30 * 24 * 60 * 60 * 1000;

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

// Tagged-result fetcher: caller can tell apart 404 from rate-limit/server-error,
// instead of the previous "any failure → null" collapse that silently hid
// rate-limited packages from the published count.
async function fetchRegistryMetadata(name) {
  const enc = encodeURIComponent(name);
  const url = `https://registry.npmjs.org/${enc}`;
  let lastError = null;
  for (let i = 0; i < 4; i++) {
    let res;
    try {
      res = await fetch(url);
    } catch (err) {
      lastError = err;
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
      continue;
    }
    if (res.status === 404) return { kind: 'not-found' };
    if (res.status === 429) {
      // Backoff. If we exhaust retries we'll fall through to rate-limited.
      await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, i)));
      continue;
    }
    if (res.status >= 500) {
      // Server hiccups; retry too, but keep the status for diagnostics.
      lastError = new Error(`HTTP ${res.status}`);
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
      continue;
    }
    if (!res.ok) {
      // 401/403 etc. — treat as not-ours; surface but don't kill the run.
      return { kind: 'forbidden', status: res.status };
    }
    try {
      const meta = await res.json();
      return { kind: 'found', meta };
    } catch (err) {
      lastError = err;
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
    }
  }
  // Retries exhausted. Distinguish rate-limit from generic server error by
  // whether we ever saw a non-429 status. If lastError is set we saw a 5xx
  // or network/JSON error; otherwise every attempt was 429.
  if (lastError) return { kind: 'server-error', error: lastError.message };
  return { kind: 'rate-limited' };
}

async function fetchDownloadsPoint(name, window) {
  const enc = encodeURIComponent(name);
  const url = `https://api.npmjs.org/downloads/point/${window}/${enc}`;
  let lastError = null;
  for (let i = 0; i < 4; i++) {
    let res;
    try {
      res = await fetch(url);
    } catch (err) {
      lastError = err;
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
      continue;
    }
    if (res.status === 404) return { kind: 'not-found' };
    if (res.status === 429) {
      await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, i)));
      continue;
    }
    if (res.status >= 500) {
      lastError = new Error(`HTTP ${res.status}`);
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
      continue;
    }
    if (!res.ok) return { kind: 'error', status: res.status };
    try {
      return { kind: 'ok', body: await res.json() };
    } catch (err) {
      lastError = err;
      await new Promise((r) => setTimeout(r, 500 * (i + 1)));
    }
  }
  if (lastError) return { kind: 'server-error', error: lastError.message };
  return { kind: 'rate-limited' };
}

// Unscoped names can collide with popular 3rd-party packages (axiom,
// marketplace, etc.). We only count a name as "ours" when our configured
// OWNERS set appears in the package's maintainer list. Scoped names under
// @intentsolutionsio/ are always ours.
const OWNERS = new Set(['jeremylongshore', 'intentsolutionsio']);
const OURS_SCOPES = ['@intentsolutionsio/'];

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

function packageCreatedAt(meta) {
  // npm's `time.created` is the first publish timestamp. Falls back to the
  // earliest version timestamp if `created` is missing on older packages.
  const time = meta?.time || {};
  if (time.created) return new Date(time.created).getTime();
  const versionDates = Object.entries(time)
    .filter(([k]) => k !== 'modified' && k !== 'created')
    .map(([, v]) => new Date(v).getTime())
    .filter((t) => !Number.isNaN(t));
  return versionDates.length ? Math.min(...versionDates) : null;
}

// Per-package outcome: {status, ...payload}. status is one of:
//   'published'    — counted with downloads
//   'unpublished'  — registry returned 404
//   'foreign'      — registry has it but it's not ours (3rd-party collision)
//   'rate-limited' — propagates upward as a hard failure
//   'error'        — generic transient/network/server error
async function statsFor(name) {
  const metaResult = await fetchRegistryMetadata(name);
  if (metaResult.kind === 'not-found') return { name, status: 'unpublished' };
  if (metaResult.kind === 'rate-limited') return { name, status: 'rate-limited' };
  if (metaResult.kind === 'server-error') {
    return { name, status: 'error', detail: metaResult.error };
  }
  if (metaResult.kind === 'forbidden') {
    return { name, status: 'error', detail: `HTTP ${metaResult.status}` };
  }

  const { meta } = metaResult;
  if (!isOurs(name, meta)) return { name, status: 'foreign' };

  // Serial fetch (not Promise.all) to stay under npm's per-IP rate limit.
  const day = await fetchDownloadsPoint(name, 'last-day');
  const week = await fetchDownloadsPoint(name, 'last-week');
  const month = await fetchDownloadsPoint(name, 'last-month');

  for (const r of [day, week, month]) {
    if (r.kind === 'rate-limited') return { name, status: 'rate-limited' };
    if (r.kind === 'server-error') return { name, status: 'error', detail: r.error };
  }

  // npm returns `{error: "package ... not found"}` for unpublished ones even
  // if registry has a placeholder. Treat missing `downloads` as zero so a
  // scoped reserved-but-unpublished name doesn't poison aggregates.
  const lastDay = day.kind === 'ok' ? (day.body?.downloads ?? 0) : 0;
  const lastWeek = week.kind === 'ok' ? (week.body?.downloads ?? 0) : 0;
  const lastMonth = month.kind === 'ok' ? (month.body?.downloads ?? 0) : 0;
  const createdAt = packageCreatedAt(meta);
  const latestVersion = meta?.['dist-tags']?.latest ?? null;

  return {
    name,
    status: 'published',
    lastDay,
    lastWeek,
    lastMonth,
    createdAt,
    latestVersion,
  };
}

async function collectStats(pkgNames, concurrency = 4) {
  const counts = {
    candidates: pkgNames.length,
    probed: 0,
    published: 0,
    unpublished: 0,
    foreign: 0,
    rateLimited: 0,
    errors: 0,
  };
  const published = [];
  const rateLimitedNames = [];
  const errorDetails = [];
  let i = 0;

  async function worker() {
    while (i < pkgNames.length) {
      const idx = i++;
      const name = pkgNames[idx];
      let result;
      try {
        result = await statsFor(name);
      } catch (err) {
        counts.probed += 1;
        counts.errors += 1;
        errorDetails.push({ name, detail: err.message });
        continue;
      }
      counts.probed += 1;
      switch (result.status) {
        case 'published':
          counts.published += 1;
          published.push(result);
          break;
        case 'unpublished':
          counts.unpublished += 1;
          break;
        case 'foreign':
          counts.foreign += 1;
          break;
        case 'rate-limited':
          counts.rateLimited += 1;
          rateLimitedNames.push(name);
          break;
        case 'error':
          counts.errors += 1;
          errorDetails.push({ name, detail: result.detail });
          break;
      }
    }
  }

  const workers = Array.from({ length: concurrency }, () => worker());
  await Promise.all(workers);
  return { counts, published, rateLimitedNames, errorDetails };
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
    '| Window | All packages | Established (>30d) |',
    '|--------|-------------:|-------------------:|',
    `| Last 24 hours | ${fmt(agg.totalDay)} | ${fmt(agg.establishedDay)} |`,
    `| Last 7 days | ${fmt(agg.totalWeek)} | ${fmt(agg.establishedWeek)} |`,
    `| Last 30 days | ${fmt(agg.totalMonth)} | ${fmt(agg.establishedMonth)} |`,
    '',
    `<sub>"Established" excludes packages first published within the last 30 days, so a bulk-publish event doesn't dominate the headline.</sub>`,
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
      `README.md missing NPM-STATS sentinels. Add:\n${START_SENTINEL}\n${END_SENTINEL}\nwhere the stats block belongs.`,
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

  // 2. Probe each name. Tagged-result fetchers distinguish 404 from
  //    rate-limit / server-error so we can surface drops loudly instead of
  //    silently undercounting.
  console.log('Fetching npm registry metadata + download stats...');
  const { counts, published, rateLimitedNames, errorDetails } = await collectStats(names, 4);

  // 3. Aggregate
  const now = Date.now();
  const established = published.filter(
    (p) => p.createdAt && now - p.createdAt > ESTABLISHED_THRESHOLD_MS,
  );
  const totalDay = published.reduce((s, p) => s + p.lastDay, 0);
  const totalWeek = published.reduce((s, p) => s + p.lastWeek, 0);
  const totalMonth = published.reduce((s, p) => s + p.lastMonth, 0);
  const establishedDay = established.reduce((s, p) => s + p.lastDay, 0);
  const establishedWeek = established.reduce((s, p) => s + p.lastWeek, 0);
  const establishedMonth = established.reduce((s, p) => s + p.lastMonth, 0);
  const top = [...published].sort((a, b) => b.lastMonth - a.lastMonth);

  const agg = {
    generatedAt: new Date().toISOString(),
    publishedCount: published.length,
    establishedCount: established.length,
    candidateCount: names.length,
    totalDay,
    totalWeek,
    totalMonth,
    establishedDay,
    establishedWeek,
    establishedMonth,
    top,
    telemetry: counts,
  };

  // 4. Telemetry — single-line summary plus drop-list if anything got skipped.
  console.log('');
  console.log(
    `Telemetry: candidates=${counts.candidates} probed=${counts.probed} ` +
      `published=${counts.published} unpublished=${counts.unpublished} ` +
      `foreign=${counts.foreign} rate-limited=${counts.rateLimited} errors=${counts.errors}`,
  );
  if (rateLimitedNames.length) {
    console.warn(`\n⚠ Rate-limited (${rateLimitedNames.length}):`);
    for (const n of rateLimitedNames) console.warn(`    ${n}`);
  }
  if (errorDetails.length) {
    console.warn(`\n⚠ Errors (${errorDetails.length}):`);
    for (const e of errorDetails) console.warn(`    ${e.name}: ${e.detail}`);
  }

  console.log('\nTotals (all published):');
  console.log(`  day=${fmt(totalDay)}  week=${fmt(totalWeek)}  month=${fmt(totalMonth)}`);
  console.log(`Totals (established >30d, ${established.length} pkgs):`);
  console.log(
    `  day=${fmt(establishedDay)}  week=${fmt(establishedWeek)}  month=${fmt(establishedMonth)}`,
  );
  console.log('\nTop 10:');
  for (const [i, p] of top.slice(0, 10).entries()) {
    console.log(`  ${i + 1}. ${p.name.padEnd(50)}  ${fmt(p.lastMonth)}`);
  }

  if (dryRun) {
    console.log('\n(--dry-run: no files written)');
  } else {
    // 5. Write JSON + README block
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

  // 6. Exit non-zero if rate-limits or server-errors happened — the published
  //    count is unreliable and the cron should turn red so we notice instead
  //    of silently shipping stale data.
  if (counts.rateLimited > 0 || counts.errors > 0) {
    console.error(
      `\n✗ ${counts.rateLimited} rate-limited, ${counts.errors} errored — counts unreliable.`,
    );
    process.exit(1);
  }
}

main().catch((err) => {
  console.error('fetch-npm-stats failed:', err);
  process.exit(1);
});
