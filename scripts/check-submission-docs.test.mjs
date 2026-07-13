/**
 * check-submission-docs.test.mjs — corpus for the submission-documents intake gate.
 *
 * Four hard contracts (mirrors the gate's spec in GitHub issue #984):
 *   1. RED    a PR adding a new plugin without its tier's required docs exits 1
 *             and names exactly the missing documents + the templates/skill-docs fix.
 *   2. GREEN  an mnemos-shaped submission (multi-skill pack with filled
 *             PRD/ADR/ONE-PAGER, per templates/skill-docs/examples/mnemos) exits 0.
 *   3. SKIP   a PR adding no new plugin exits 0 via the designed in-script clean
 *             pass (the CI job always reports — never a workflow-level skip).
 *   4. EXEMPT a new external-mirror plugin (dir contains .source.json) exits 0 —
 *             its docs live upstream.
 * Plus: the pure tier classifier and per-tier required-docs matrix.
 *
 * End-to-end tests build a throwaway git repo in os.tmpdir() (no committed
 * fixtures — nested 000-docs/ dirs are gitignored in this repo, so on-disk
 * fixture corpora silently drop; a temp repo sidesteps the trap entirely).
 *
 * Run: node --test scripts/check-submission-docs.test.mjs
 */

import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

import {
  TIER,
  classifyTier,
  requiredDocsForTier,
  inventoryPluginDir,
  checkPlugin,
  newPluginDirsFromDiff,
  findDoc,
} from './check-submission-docs.mjs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '..');
const CLI = path.join(__dirname, 'check-submission-docs.mjs');
const MNEMOS_EXAMPLE = path.join(REPO_ROOT, 'templates', 'skill-docs', 'examples', 'mnemos');

// ─────────────────────────────────────────────────────────────────────────────
// Pure units: tier classification + required-docs matrix
// ─────────────────────────────────────────────────────────────────────────────

test('classifyTier: single skill, no scripts → micro', () => {
  assert.equal(classifyTier({ skills: 1, commands: 0, agents: 0, hasScripts: false }), TIER.MICRO);
});

test('classifyTier: single command, no scripts → micro', () => {
  assert.equal(classifyTier({ skills: 0, commands: 1, agents: 0, hasScripts: false }), TIER.MICRO);
});

test('classifyTier: skill + scripts → standard', () => {
  assert.equal(
    classifyTier({ skills: 1, commands: 0, agents: 0, hasScripts: true }),
    TIER.STANDARD,
  );
});

test('classifyTier: skill + command (multiple components) → standard', () => {
  assert.equal(
    classifyTier({ skills: 1, commands: 1, agents: 0, hasScripts: false }),
    TIER.STANDARD,
  );
});

test('classifyTier: two skills → pack, even without scripts', () => {
  assert.equal(classifyTier({ skills: 2, commands: 0, agents: 0, hasScripts: false }), TIER.PACK);
});

test('requiredDocsForTier matches the templates/skill-docs matrix', () => {
  assert.deepEqual(requiredDocsForTier(TIER.MICRO), ['PRD.md']);
  assert.deepEqual(requiredDocsForTier(TIER.STANDARD), ['PRD.md', 'ADR.md']);
  assert.deepEqual(requiredDocsForTier(TIER.PACK), ['PRD.md', 'ADR.md', 'ONE-PAGER.md']);
});

// ─────────────────────────────────────────────────────────────────────────────
// Fixture builders (throwaway dirs/repos under os.tmpdir())
// ─────────────────────────────────────────────────────────────────────────────

const cleanups = [];
process.on('exit', () => {
  for (const dir of cleanups) {
    try {
      fs.rmSync(dir, { recursive: true, force: true });
    } catch {
      /* best effort */
    }
  }
});

function tmpdir(prefix) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), prefix));
  cleanups.push(dir);
  return dir;
}

function write(root, rel, content = 'placeholder content\n') {
  const abs = path.join(root, rel);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, content);
}

function git(repo, ...args) {
  return execFileSync(
    'git',
    ['-C', repo, '-c', 'user.email=test@example.com', '-c', 'user.name=test', ...args],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] },
  );
}

/** New git repo with one PRE-EXISTING plugin committed as the base. Returns
 *  { repo, baseSha }. New-plugin fixtures are added and committed on top. */
function makeRepo() {
  const repo = tmpdir('check-submission-docs-');
  git(repo, 'init', '-q');
  write(repo, 'plugins/devops/existing-plugin/.claude-plugin/plugin.json', '{"name":"existing"}\n');
  write(repo, 'plugins/devops/existing-plugin/skills/existing/SKILL.md', '# existing\n');
  write(repo, 'README.md', '# fixture repo\n');
  git(repo, 'add', '-A');
  git(repo, 'commit', '-q', '-m', 'base');
  const baseSha = git(repo, 'rev-parse', 'HEAD').trim();
  return { repo, baseSha };
}

function commitAll(repo, msg) {
  git(repo, 'add', '-A');
  git(repo, 'commit', '-q', '-m', msg);
}

/** Run the CLI; returns { status, out } (stdout+stderr combined). */
function runCli(args) {
  try {
    const out = execFileSync('node', [CLI, ...args], { encoding: 'utf8' });
    return { status: 0, out };
  } catch (err) {
    return { status: err.status, out: `${err.stdout ?? ''}${err.stderr ?? ''}` };
  }
}

/** Standard-tier plugin skeleton (one skill + a script), NO docs. */
function addStandardPluginNoDocs(repo, dir) {
  write(repo, `${dir}/.claude-plugin/plugin.json`, '{"name":"new-standard"}\n');
  write(repo, `${dir}/skills/thing/SKILL.md`, '# thing\n');
  write(repo, `${dir}/scripts/run.sh`, '#!/bin/sh\necho ok\n');
}

// ─────────────────────────────────────────────────────────────────────────────
// Inventory / doc-location units (plain temp dirs, no git needed)
// ─────────────────────────────────────────────────────────────────────────────

test('inventoryPluginDir counts skills/commands/agents and detects scripts + hooks', () => {
  const root = tmpdir('inv-');
  write(root, 'p/skills/a/SKILL.md');
  write(root, 'p/skills/b/SKILL.md');
  write(root, 'p/commands/do-it.md');
  write(root, 'p/agents/helper.md');
  write(root, 'p/scripts/run.sh');
  const inv = inventoryPluginDir(path.join(root, 'p'));
  assert.deepEqual(inv, { skills: 2, commands: 1, agents: 1, hasScripts: true });

  const root2 = tmpdir('inv-hooks-');
  write(root2, 'p/skills/a/SKILL.md');
  write(root2, 'p/hooks/hooks.json', '{"hooks":{}}\n');
  assert.equal(
    inventoryPluginDir(path.join(root2, 'p')).hasScripts,
    true,
    'hooks/ counts as scripts',
  );
});

test('inventoryPluginDir ignores docs/, .claude-plugin/, .forge/ contents', () => {
  const root = tmpdir('inv-excl-');
  write(root, 'p/skills/a/SKILL.md');
  write(root, 'p/docs/PRD.md');
  write(root, 'p/docs/gen.py'); // a code file inside docs/ must not flip hasScripts
  write(root, 'p/.claude-plugin/plugin.json', '{}');
  write(root, 'p/.forge/proofs.md');
  const inv = inventoryPluginDir(path.join(root, 'p'));
  assert.deepEqual(inv, { skills: 1, commands: 0, agents: 0, hasScripts: false });
});

test('findDoc accepts docs/<name> (canonical) and root <name> (mnemos example shape); empty files do not count', () => {
  const root = tmpdir('finddoc-');
  write(root, 'p/docs/PRD.md', 'real content\n');
  write(root, 'p/ADR.md', 'root-level adr\n');
  write(root, 'p/docs/ONE-PAGER.md', ''); // empty → missing
  assert.equal(findDoc(path.join(root, 'p'), 'PRD.md'), path.join('docs', 'PRD.md'));
  assert.equal(findDoc(path.join(root, 'p'), 'ADR.md'), 'ADR.md');
  assert.equal(findDoc(path.join(root, 'p'), 'ONE-PAGER.md'), null);
});

test('checkPlugin exempts a .source.json mirror dir', () => {
  const root = tmpdir('exempt-');
  write(root, 'plugins/community/mirror/.claude-plugin/plugin.json', '{}');
  write(root, 'plugins/community/mirror/.source.json', '{"synced_from":{"repo":"x/y"}}\n');
  write(root, 'plugins/community/mirror/skills/a/SKILL.md');
  const res = checkPlugin(root, 'plugins/community/mirror');
  assert.equal(res.exempt, true);
});

// ─────────────────────────────────────────────────────────────────────────────
// Contract 1 — RED: new plugin missing required docs fails, naming each doc
// ─────────────────────────────────────────────────────────────────────────────

test('RED: new standard-tier plugin with no docs → exit 1, lists PRD.md + ADR.md, points at templates', () => {
  const { repo, baseSha } = makeRepo();
  addStandardPluginNoDocs(repo, 'plugins/devops/new-standard');
  commitAll(repo, 'add new plugin without docs');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 1);
  assert.match(out, /new-standard.*tier: standard/);
  assert.match(out, /MISSING required document: plugins\/devops\/new-standard\/docs\/PRD\.md/);
  assert.match(out, /MISSING required document: plugins\/devops\/new-standard\/docs\/ADR\.md/);
  assert.match(out, /templates\/skill-docs\//, 'failure message must point at the templates dir');
});

test('RED: pack tier with only PRD present → exit 1, lists exactly ADR.md + ONE-PAGER.md', () => {
  const { repo, baseSha } = makeRepo();
  const dir = 'plugins/ai-ml/new-pack';
  write(repo, `${dir}/.claude-plugin/plugin.json`, '{"name":"new-pack"}\n');
  write(repo, `${dir}/skills/one/SKILL.md`, '# one\n');
  write(repo, `${dir}/skills/two/SKILL.md`, '# two\n');
  write(repo, `${dir}/docs/PRD.md`, '# PRD: new-pack\nreal content\n');
  commitAll(repo, 'add pack missing ADR + ONE-PAGER');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 1);
  assert.match(out, /new-pack.*tier: pack/);
  assert.doesNotMatch(out, /MISSING required document: plugins\/ai-ml\/new-pack\/docs\/PRD\.md/);
  assert.match(out, /MISSING required document: plugins\/ai-ml\/new-pack\/docs\/ADR\.md/);
  assert.match(out, /MISSING required document: plugins\/ai-ml\/new-pack\/docs\/ONE-PAGER\.md/);
});

test('RED: micro tier (single skill, no scripts) missing PRD → exit 1, lists only PRD.md', () => {
  const { repo, baseSha } = makeRepo();
  const dir = 'plugins/productivity/new-micro';
  write(repo, `${dir}/.claude-plugin/plugin.json`, '{"name":"new-micro"}\n');
  write(repo, `${dir}/skills/solo/SKILL.md`, '# solo\n');
  commitAll(repo, 'add micro without PRD');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 1);
  assert.match(out, /new-micro.*tier: micro/);
  assert.match(out, /MISSING required document: plugins\/productivity\/new-micro\/docs\/PRD\.md/);
  assert.doesNotMatch(out, /MISSING required document: .*ADR\.md/);
  assert.doesNotMatch(out, /MISSING required document: .*ONE-PAGER\.md/);
});

// ─────────────────────────────────────────────────────────────────────────────
// Contract 2 — GREEN: an mnemos-shaped submission passes
// ─────────────────────────────────────────────────────────────────────────────

test('GREEN: mnemos-shaped submission (pack with the worked-example PRD/ADR/ONE-PAGER) → exit 0', () => {
  const { repo, baseSha } = makeRepo();
  const dir = 'plugins/ai-ml/mnemos-shaped';
  write(repo, `${dir}/.claude-plugin/plugin.json`, '{"name":"mnemos-shaped"}\n');
  write(repo, `${dir}/skills/memory/SKILL.md`, '# memory\n');
  write(repo, `${dir}/skills/recall/SKILL.md`, '# recall\n');
  // The real worked-example documents from templates/skill-docs/examples/mnemos/.
  for (const doc of ['PRD.md', 'ADR.md', 'ONE-PAGER.md']) {
    fs.mkdirSync(path.join(repo, dir, 'docs'), { recursive: true });
    fs.copyFileSync(path.join(MNEMOS_EXAMPLE, doc), path.join(repo, dir, 'docs', doc));
  }
  commitAll(repo, 'add compliant mnemos-shaped pack');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 0, out);
  assert.match(out, /mnemos-shaped.*tier: pack.*all required docs present/);
  assert.match(out, /Submission-documents gate passed/);
});

test('GREEN: micro plugin with a root-level PRD.md (worked-example shape) → exit 0', () => {
  const { repo, baseSha } = makeRepo();
  const dir = 'plugins/productivity/tiny';
  write(repo, `${dir}/.claude-plugin/plugin.json`, '{"name":"tiny"}\n');
  write(repo, `${dir}/commands/tiny.md`, '# tiny command\n');
  write(repo, `${dir}/PRD.md`, '# PRD: tiny\nreal content\n');
  commitAll(repo, 'add compliant micro plugin');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 0, out);
  assert.match(out, /tiny.*tier: micro.*all required docs present/);
});

// ─────────────────────────────────────────────────────────────────────────────
// Contract 3 — SKIP: no new plugin in the diff → designed clean pass
// ─────────────────────────────────────────────────────────────────────────────

test('SKIP: PR that only edits an existing plugin → exit 0 with the designed no-new-plugins log line', () => {
  const { repo, baseSha } = makeRepo();
  write(repo, 'plugins/devops/existing-plugin/skills/existing/SKILL.md', '# existing (edited)\n');
  write(repo, 'plugins/devops/existing-plugin/scripts/new-helper.sh', 'echo hi\n'); // added file, but NOT a new plugin.json
  commitAll(repo, 'edit existing plugin');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 0, out);
  assert.match(out, /No new plugin directories in this diff — nothing to check/);
});

test('newPluginDirsFromDiff: only ADDED plugin.json manifests under plugins/ count', () => {
  const { repo, baseSha } = makeRepo();
  addStandardPluginNoDocs(repo, 'plugins/devops/brand-new');
  write(repo, 'skills/root-level/SKILL.md', '# not a plugin\n'); // root skills/ is out of scope
  write(repo, 'plugins/devops/existing-plugin/README.md', 'added file in EXISTING plugin\n');
  commitAll(repo, 'mixed changes');

  assert.deepEqual(newPluginDirsFromDiff(repo, baseSha), ['plugins/devops/brand-new']);
});

// ─────────────────────────────────────────────────────────────────────────────
// Contract 4 — EXEMPT: external mirror (.source.json) passes without docs
// ─────────────────────────────────────────────────────────────────────────────

test('EXEMPT: new mirror plugin carrying .source.json, no docs → exit 0, logged as exempt', () => {
  const { repo, baseSha } = makeRepo();
  const dir = 'plugins/community/synced-mirror';
  write(repo, `${dir}/.claude-plugin/plugin.json`, '{"name":"synced-mirror"}\n');
  write(repo, `${dir}/.source.json`, '{"synced_from":{"repo":"someone/upstream"}}\n');
  write(repo, `${dir}/skills/a/SKILL.md`, '# a\n');
  write(repo, `${dir}/skills/b/SKILL.md`, '# b\n');
  write(repo, `${dir}/scripts/setup.sh`, 'echo setup\n');
  commitAll(repo, 'sync new mirror plugin');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 0, out);
  assert.match(out, /synced-mirror — external mirror \(\.source\.json\): exempt/);
});

// Mixed PR: one exempt mirror + one non-compliant first-party plugin still fails.
test('MIXED: exempt mirror + docs-less first-party plugin in the same PR → exit 1', () => {
  const { repo, baseSha } = makeRepo();
  const mirror = 'plugins/community/mirror-ok';
  write(repo, `${mirror}/.claude-plugin/plugin.json`, '{"name":"mirror-ok"}\n');
  write(repo, `${mirror}/.source.json`, '{"synced_from":{"repo":"x/y"}}\n');
  addStandardPluginNoDocs(repo, 'plugins/devops/docsless');
  commitAll(repo, 'mixed intake');

  const { status, out } = runCli(['--root', repo, '--changed-only', '--base', baseSha]);
  assert.equal(status, 1);
  assert.match(out, /mirror-ok — external mirror/);
  assert.match(out, /MISSING required document: plugins\/devops\/docsless\/docs\/PRD\.md/);
});

// Explicit-path mode (author self-check, no git required).
test('explicit path mode: checking a compliant dir directly → exit 0', () => {
  const root = tmpdir('explicit-');
  const dir = 'plugins/devops/self-check';
  write(root, `${dir}/.claude-plugin/plugin.json`, '{"name":"self-check"}\n');
  write(root, `${dir}/skills/s/SKILL.md`, '# s\n');
  write(root, `${dir}/docs/PRD.md`, '# PRD\ncontent\n');
  const { status, out } = runCli(['--root', root, dir]);
  assert.equal(status, 0, out);
});
