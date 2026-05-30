#!/usr/bin/env node
/**
 * Audits live GitHub issue + PR bodies for broken repo-relative links.
 *
 * Why this exists: lychee/markdown-link-check scan files committed to the repo.
 * They cannot catch the failure mode that bit us on 2026-05-30, where an issue
 * body cited a repo path (`plugins/saas-packs/databricks-pack/000-docs/013-AT-ADEC-epic1-mcp-scope-adjustment.md`)
 * that was gitignored — the linked path did not exist in the public tree, so
 * the `github.com/.../blob/main/...` URL returned 404. No repo-side checker
 * scans issue bodies; this script does.
 *
 * Logic:
 *   1. Fetch all open issues + PRs via `gh` CLI.
 *   2. Extract every markdown-style and bare URL from each body.
 *   3. Categorize each URL:
 *      - GitHub blob/tree pointing into this repo → verify the path is tracked
 *        by `git ls-files`. If not tracked, it's broken (gitignored / deleted).
 *      - Repo-rooted (`/plugins/...`) or relative (`./...`) → same check.
 *      - External (non-github) URLs → out of scope (use lychee/repo workflow).
 *      - Anchor-only (`#section`) → out of scope.
 *   4. Report broken repo-path references grouped by container (issue/PR).
 *   5. Exit 1 if any broken; 0 otherwise.
 *
 * Local usage:
 *   node scripts/check-issue-body-links.mjs
 *   node scripts/check-issue-body-links.mjs --max 1000   # widen the cap
 *   node scripts/check-issue-body-links.mjs --closed    # include closed too
 *
 * CI usage:
 *   See .github/workflows/check-issue-body-links.yml.
 */

import { execSync } from 'child_process';

const REPO_OWNER = 'jeremylongshore';
const REPO_NAME = 'claude-code-plugins-plus-skills';
const REPO_SLUG = `${REPO_OWNER}/${REPO_NAME}`;

const args = process.argv.slice(2);
const MAX_ITEMS = (() => {
  const i = args.indexOf('--max');
  return i >= 0 ? Number(args[i + 1]) : 500;
})();
const INCLUDE_CLOSED = args.includes('--closed');
const STATE = INCLUDE_CLOSED ? 'all' : 'open';

function ghJson(cmd) {
  return JSON.parse(execSync(cmd, { encoding: 'utf-8', maxBuffer: 200 * 1024 * 1024 }));
}

function gitTrackedFiles() {
  return new Set(
    execSync('git ls-files', { encoding: 'utf-8', maxBuffer: 200 * 1024 * 1024 })
      .split('\n')
      .filter(Boolean),
  );
}

process.stderr.write(`Fetching ${STATE} issues from ${REPO_SLUG}...\n`);
const issues = ghJson(
  `gh issue list --repo ${REPO_SLUG} --state ${STATE} --limit ${MAX_ITEMS} --json number,title,body,url`,
);
process.stderr.write(`  ${issues.length} issues\n`);

process.stderr.write(`Fetching ${STATE} PRs from ${REPO_SLUG}...\n`);
const prs = ghJson(
  `gh pr list --repo ${REPO_SLUG} --state ${STATE} --limit ${MAX_ITEMS} --json number,title,body,url`,
);
process.stderr.write(`  ${prs.length} PRs\n`);

const tracked = gitTrackedFiles();
process.stderr.write(`Git tree: ${tracked.size} tracked files\n\n`);

// Match markdown links: [text](url) — capture the url
const MD_LINK_RE = /\[(?:[^\]]*)\]\(([^)]+)\)/g;
// Match bare URLs in prose (but not URLs already captured by MD_LINK_RE since
// they're inside parens — the negative lookbehind excludes them).
const BARE_URL_RE = /(?<![([\w])https?:\/\/[^\s<>"'`)]+/g;

function extractLinks(body) {
  const out = new Set();
  if (!body) return out;
  for (const m of body.matchAll(MD_LINK_RE)) out.add(m[1]);
  for (const m of body.matchAll(BARE_URL_RE)) out.add(m[0]);
  return out;
}

const GH_BLOB_RE = new RegExp(
  `^https?://github\\.com/${REPO_OWNER}/${REPO_NAME}/(?:blob|tree|raw)/[^/]+/(.+)$`,
  'i',
);

function categorize(url) {
  const cleaned = url.trim().replace(/[.,;]$/, '');
  if (cleaned.startsWith('#')) return { kind: 'anchor' };

  if (/^https?:\/\//i.test(cleaned)) {
    const m = cleaned.match(GH_BLOB_RE);
    if (m) {
      // Strip query/fragment from the path
      const path = m[1].replace(/[#?].*$/, '');
      return { kind: 'github-blob', path, original: cleaned };
    }
    return { kind: 'external', url: cleaned };
  }

  if (cleaned.startsWith('/')) {
    return {
      kind: 'repo-rooted',
      path: cleaned.slice(1).replace(/[#?].*$/, ''),
      original: cleaned,
    };
  }

  if (cleaned.startsWith('./') || cleaned.startsWith('../')) {
    return { kind: 'relative', original: cleaned };
  }

  // Bare schemes like mailto:, irc:, etc.
  if (cleaned.match(/^[a-z]+:/i)) return { kind: 'other-scheme', original: cleaned };

  return { kind: 'unknown', original: cleaned };
}

const broken = [];

for (const list of [
  { kind: 'issue', items: issues },
  { kind: 'pr', items: prs },
]) {
  for (const item of list.items) {
    const urls = extractLinks(item.body);
    for (const url of urls) {
      const cat = categorize(url);
      if (cat.kind === 'github-blob' || cat.kind === 'repo-rooted') {
        if (!tracked.has(cat.path)) {
          broken.push({
            container: `${list.kind} #${item.number}`,
            title: item.title,
            itemUrl: item.url,
            link: cat.original,
            reason: `path "${cat.path}" not in git tree (gitignored or deleted)`,
          });
        }
      }
    }
  }
}

process.stderr.write(
  `Found ${broken.length} broken repo-path references across ${issues.length + prs.length} items.\n\n`,
);

if (broken.length === 0) {
  console.log('# Live issue / PR body link audit\n');
  console.log(
    `All repo-path references across **${issues.length} ${STATE} issues** and ` +
      `**${prs.length} ${STATE} PRs** resolve to tracked files in the current main tree.`,
  );
  process.exit(0);
}

// Group by container for the report
const byContainer = new Map();
for (const b of broken) {
  if (!byContainer.has(b.container)) {
    byContainer.set(b.container, {
      title: b.title,
      itemUrl: b.itemUrl,
      items: [],
    });
  }
  byContainer.get(b.container).items.push(b);
}

console.log('# Live issue / PR body link audit — broken repo paths\n');
console.log(`Scanned ${issues.length} issues + ${prs.length} PRs (state: ${STATE}).`);
console.log(
  `Found **${broken.length} broken repo-path references** across ${byContainer.size} containers.\n`,
);
console.log('Repo paths here are checked against `git ls-files` on the current main tree. ');
console.log('A "broken" link means the cited path is gitignored, deleted, or never existed.\n');
console.log('---\n');

for (const [container, info] of byContainer) {
  console.log(`## ${container}: ${info.title}\n`);
  console.log(`Source: ${info.itemUrl}\n`);
  for (const b of info.items) {
    console.log(`- \`${b.link}\``);
    console.log(`  - ${b.reason}`);
  }
  console.log('');
}

process.exit(1);
