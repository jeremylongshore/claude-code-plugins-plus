#!/usr/bin/env node
// check-mcp-destructive-policy.mjs — the E4.10 gate (blueprint 727).
//
// Every tracked plugins/mcp/* plugin must declare its destructive-operation
// policy in plugins/mcp/destructive-policies.json (which lives BESIDE the
// plugin dirs so .source.json mirrors stay untouched). The gate:
//   1. requires exactly one entry per tracked plugin dir (missing and orphan
//      entries both fail);
//   2. validates policy ∈ {refuse, recommend-only, permit-with-confirmation,
//      permit} and that every named artifact path exists;
//   3. for refuse/recommend-only declarations, requires a refusal_test and
//      EXECUTES it (python3 -m unittest), failing on a non-zero exit — a
//      declaration is only as good as its passing test.
//
// "Tracked" means the dir contains at least one git-tracked file. Untracked
// build-output dirs are invisible to CI checkouts and therefore are not gated.

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REGISTRY = 'plugins/mcp/destructive-policies.json';
const VALID = new Set(['refuse', 'recommend-only', 'permit-with-confirmation', 'permit']);
const NEEDS_TEST = new Set(['refuse', 'recommend-only']);

export function trackedPluginDirs() {
  const out = execFileSync('git', ['ls-files', 'plugins/mcp/'], {
    cwd: ROOT,
    encoding: 'utf8',
  });
  const dirs = new Set();
  for (const line of out.split('\n')) {
    const m = line.match(/^plugins\/mcp\/([^/]+)\//);
    // Dot-dirs (.greptile etc.) are repo tooling, not MCP plugins.
    if (m && !m[1].startsWith('.')) dirs.add(m[1]);
  }
  return dirs;
}

export function analyzeRegistry(registry, dirs) {
  const issues = [];
  const policies = registry.policies ?? {};
  for (const dir of dirs) {
    if (!(dir in policies)) issues.push({ code: 'UNDECLARED_PLUGIN', plugin: dir });
  }
  for (const [name, entry] of Object.entries(policies)) {
    if (!dirs.has(name)) issues.push({ code: 'ORPHAN_ENTRY', plugin: name });
    if (!VALID.has(entry.policy)) {
      issues.push({ code: 'INVALID_POLICY', plugin: name, policy: entry.policy });
    }
    if (!entry.rationale) issues.push({ code: 'MISSING_RATIONALE', plugin: name });
    if (!entry.enforcing_artifact || !existsSync(resolve(ROOT, entry.enforcing_artifact))) {
      issues.push({ code: 'MISSING_ARTIFACT', plugin: name, path: entry.enforcing_artifact });
    }
    if (NEEDS_TEST.has(entry.policy)) {
      if (!entry.refusal_test || !existsSync(resolve(ROOT, entry.refusal_test))) {
        issues.push({ code: 'MISSING_REFUSAL_TEST', plugin: name, path: entry.refusal_test });
      }
    }
  }
  return issues;
}

function runRefusalTests(registry) {
  const modules = new Set();
  for (const entry of Object.values(registry.policies ?? {})) {
    if (NEEDS_TEST.has(entry.policy) && entry.refusal_test) {
      modules.add(entry.refusal_test.replace(/\.py$/, '').replace(/\//g, '.'));
    }
  }
  const failures = [];
  for (const module of modules) {
    try {
      execFileSync('python3', ['-m', 'unittest', module], {
        cwd: ROOT,
        stdio: ['ignore', 'pipe', 'pipe'],
        timeout: 120_000,
      });
      console.log(`mcp-destructive-policy: refusal test PASS — ${module}`);
    } catch (error) {
      failures.push({ module, detail: String(error.stderr || error.message).slice(-800) });
    }
  }
  return failures;
}

function main() {
  const registry = JSON.parse(readFileSync(resolve(ROOT, REGISTRY), 'utf8'));
  const dirs = trackedPluginDirs();
  const issues = analyzeRegistry(registry, dirs);
  if (issues.length > 0) {
    for (const issue of issues) {
      console.error(
        `mcp-destructive-policy: ${issue.code} — ${issue.plugin}${issue.path ? ` (${issue.path})` : ''}`,
      );
    }
    process.exit(1);
  }
  const failures = runRefusalTests(registry);
  if (failures.length > 0) {
    for (const failure of failures) {
      console.error(
        `mcp-destructive-policy: REFUSAL TEST FAILED — ${failure.module}\n${failure.detail}`,
      );
    }
    process.exit(1);
  }
  const tally = {};
  for (const entry of Object.values(registry.policies)) {
    tally[entry.policy] = (tally[entry.policy] ?? 0) + 1;
  }
  console.log(
    `mcp-destructive-policy: OK (${dirs.size} tracked MCP plugins declared: ${Object.entries(tally)
      .map(([policy, count]) => `${policy}=${count}`)
      .join(' ')})`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
