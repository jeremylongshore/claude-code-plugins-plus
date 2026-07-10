#!/usr/bin/env node
/**
 * census-watch.mjs — local watcher for the 2026-07-08 whole-catalog quality census.
 *
 * WHY THIS EXISTS (and why it runs locally, not as a cloud routine):
 *   The 2026-07-08 census graded 27 marketplace source-entries D/F and put them on a
 *   delist clock (deadline 2026-07-22 — see the `# census 2026-07-08 … deadline 2026-07-22`
 *   comments in sources.yaml and bead claude-ss50.8). Those sources live in cross-owner
 *   upstream repos (datopian/*, wondelai/*, numman-ali/*, …). A previous cloud routine
 *   tried to watch them but its sandboxed GitHub-App session was scoped to a single owner
 *   (jeremylongshore), so every cross-owner read was blocked (add_repo cross-tier rejected,
 *   raw api.github.com intercepted). This script runs on the dev box where `gh` has
 *   unrestricted cross-owner read access, so it can actually do the job.
 *
 * WHAT IT DOES:
 *   1. Parses sources.yaml, selecting the entries carrying the census delist-deadline marker.
 *   2. Collapses them to unique upstream repos (n-skills / wondelai are monorepos → many
 *      source-entries share one repo).
 *   3. For each upstream, reads the default-branch HEAD (sha + commit date) via `gh api`.
 *   4. Classifies each: GONE (repo deleted/archived → auto-delist), MOVED (pushed since the
 *      census date → the maintainer MAY have landed the fix → re-grade candidate), or
 *      DORMANT (no activity since census → delist candidate on the deadline).
 *   5. Diffs against the previous run's state so subsequent runs surface *new* movement,
 *      and rewrites the state file. First run initializes the baseline.
 *
 * OUTPUT: a human report to stdout + a machine state file. A cron wrapper can diff the
 *   printed summary or read the state JSON to decide whether to ping Slack.
 *
 * Zero runtime deps (no js-yaml) on purpose: a local cron must run without `npm install`.
 * sources.yaml has a stable 2-space list indent, so raw block parsing is reliable.
 *
 * Usage:  node scripts/census-watch.mjs [--json]
 */

import fs from 'fs';
import path from 'path';
import os from 'os';
import { fileURLToPath } from 'url';
import { execFileSync } from 'child_process';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SOURCES_FILE = path.join(__dirname, '..', 'sources.yaml');
const STATE_DIR = path.join(os.homedir(), '.local', 'state', 'census-watch');
const STATE_FILE = path.join(STATE_DIR, 'state.json');

const CENSUS_DATE = '2026-07-08'; // the whole-catalog census that set the clock
const DEADLINE = '2026-07-22'; // delist deadline for sources still failing
const DEADLINE_MARKER = `deadline ${DEADLINE}`; // stable comment string in sources.yaml
const JSON_OUT = process.argv.includes('--json');

/** Parse sources.yaml by raw 2-space list blocks; return the census-marked entries. */
function onClockSources() {
  const raw = fs.readFileSync(SOURCES_FILE, 'utf8');
  // Split on the top-level list-item delimiter. slice(1) drops the file header.
  const blocks = raw.split(/\n {2}- name:/).slice(1);
  const out = [];
  for (const b of blocks) {
    if (!b.includes(DEADLINE_MARKER)) continue;
    const name = (b.match(/^\s*(\S.*)$/m)?.[1] || '(unknown)').trim();
    const repoM = b.match(/\n\s*repo:\s*(\S+)/);
    if (!repoM) continue;
    out.push({ name, repo: repoM[1].trim() });
  }
  return out;
}

/** Read the default-branch HEAD of an upstream repo via gh. Returns null on 404/gone. */
function upstreamHead(repo) {
  let meta;
  try {
    meta = JSON.parse(
      execFileSync(
        'gh',
        ['api', `repos/${repo}`, '--jq', '{default_branch, archived, pushed_at}'],
        { encoding: 'utf8' },
      ),
    );
  } catch {
    return { gone: true };
  }
  if (meta.archived) return { gone: true, archived: true, pushedAt: meta.pushed_at };
  let head;
  try {
    const line = execFileSync(
      'gh',
      [
        'api',
        `repos/${repo}/commits/${meta.default_branch}`,
        '--jq',
        '.sha + "|" + .commit.committer.date',
      ],
      { encoding: 'utf8' },
    ).trim();
    const [sha, date] = line.split('|');
    head = { sha: sha.slice(0, 12), date };
  } catch {
    head = { sha: null, date: meta.pushed_at };
  }
  return {
    gone: false,
    defaultBranch: meta.default_branch,
    headSha: head.sha,
    headDate: head.date,
  };
}

function classify(info) {
  if (info.gone) return info.archived ? 'GONE-ARCHIVED' : 'GONE-DELETED';
  if (!info.headDate) return 'DORMANT';
  return new Date(info.headDate) > new Date(`${CENSUS_DATE}T00:00:00Z`) ? 'MOVED' : 'DORMANT';
}

function main() {
  const sources = onClockSources();
  // repo -> [source names]
  const byRepo = new Map();
  for (const s of sources) {
    if (!byRepo.has(s.repo)) byRepo.set(s.repo, []);
    byRepo.get(s.repo).push(s.name);
  }

  const prev = fs.existsSync(STATE_FILE)
    ? JSON.parse(fs.readFileSync(STATE_FILE, 'utf8'))
    : { repos: {} };
  const firstRun = !fs.existsSync(STATE_FILE);

  const now = new Date();
  const daysLeft = Math.ceil((new Date(`${DEADLINE}T23:59:59Z`) - now) / 86_400_000);

  const results = [];
  for (const [repo, names] of [...byRepo.entries()].sort()) {
    const info = upstreamHead(repo);
    const cls = classify(info);
    const before = prev.repos[repo];
    let delta;
    if (firstRun || !before) delta = 'init';
    else if (before.headSha !== info.headSha) delta = 'CHANGED-since-last-run';
    else delta = 'same';
    results.push({
      repo,
      sources: names,
      class: cls,
      headSha: info.headSha || null,
      headDate: info.headDate || null,
      delta,
    });
  }

  const state = {
    generatedAt: now.toISOString(),
    censusDate: CENSUS_DATE,
    deadline: DEADLINE,
    daysLeft,
    repos: Object.fromEntries(
      results.map((r) => [r.repo, { headSha: r.headSha, headDate: r.headDate, class: r.class }]),
    ),
  };
  fs.mkdirSync(STATE_DIR, { recursive: true });
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2) + '\n');

  if (JSON_OUT) {
    console.log(JSON.stringify({ ...state, results }, null, 2));
    return;
  }

  const moved = results.filter((r) => r.class === 'MOVED');
  const dormant = results.filter((r) => r.class === 'DORMANT');
  const gone = results.filter((r) => r.class.startsWith('GONE'));
  const changed = results.filter((r) => r.delta === 'CHANGED-since-last-run');

  const sourceCount = sources.length;
  console.log(
    `\n  Census watch — ${CENSUS_DATE} D/F cohort · delist deadline ${DEADLINE} (${daysLeft} days left)`,
  );
  console.log(`  ${sourceCount} source-entries on the clock across ${byRepo.size} upstream repos`);
  console.log(`  state: ${STATE_FILE}${firstRun ? '  (initialized this run)' : ''}\n`);

  const pad = (s, n) => String(s).padEnd(n);
  console.log(
    `  ${pad('UPSTREAM REPO', 34)}${pad('CLASS', 15)}${pad('HEAD DATE', 22)}${pad('Δ', 10)}SOURCES`,
  );
  console.log(`  ${'-'.repeat(96)}`);
  for (const r of results) {
    console.log(
      `  ${pad(r.repo, 34)}${pad(r.class, 15)}${pad((r.headDate || '—').slice(0, 19), 22)}${pad(r.delta === 'init' ? 'init' : r.delta === 'same' ? '·' : '⚑ NEW', 10)}${r.sources.join(', ')}`,
    );
  }

  console.log(`\n  SUMMARY`);
  console.log(
    `   • ${moved.length} upstream(s) MOVED since ${CENSUS_DATE} → RE-GRADE candidates (a fix may have landed):`,
  );
  moved.forEach((r) =>
    console.log(`       ${r.repo}  (${r.sources.length} skill(s): ${r.sources.join(', ')})`),
  );
  console.log(
    `   • ${dormant.length} upstream(s) DORMANT → DELIST candidates on ${DEADLINE} unless re-graded:`,
  );
  dormant.forEach((r) =>
    console.log(`       ${r.repo}  (${r.sources.length} skill(s): ${r.sources.join(', ')})`),
  );
  if (gone.length) {
    console.log(`   • ${gone.length} upstream(s) GONE → auto-delist:`);
    gone.forEach((r) => console.log(`       ${r.repo}  [${r.class}]`));
  }
  if (!firstRun && changed.length) {
    console.log(`   • ${changed.length} upstream(s) CHANGED since last watch → re-grade now:`);
    changed.forEach((r) => console.log(`       ${r.repo}`));
  }
  console.log(
    `\n  Next: re-grade the MOVED upstreams (validator), flip verified:true on any that now pass,`,
  );
  console.log(
    `  and on ${DEADLINE} delist whatever is still DORMANT/failing (bead claude-ss50.8).\n`,
  );
}

main();
