#!/usr/bin/env node
// check-safety-ratchet.mjs — the triple-keyed safety ratchet (blueprint 727
// E4.3 + E4.4 + E4.11).
//
// Four frozen debt classes, each pinned by three keys — total count, a
// SHA-256 of the sorted member set, and the validator SCHEMA_VERSION the pin
// was taken under:
//   bare_bash           first-party SKILL.md declaring unscoped `Bash`
//   tier2_tool_safety   bare Bash + Write/WebFetch with no Safety Justification
//   shell_substitution  `[security] YAML field contains shell substitution`
//                       occurrences (file::field) — NEVER waivable: this gate
//                       has no allowlist code path by design
//   agents_only_errors  the --agents-only lane's error lines (the 253-error
//                       corpus baseline), which includes the schema 3.11.0
//                       body-vs-allowlist check
//
// Rules: totals are monotone NON-INCREASING and every member must already be
// in the baseline — a swap (one out, one in) fails even at equal count. A
// shrink passes and instructs a re-pin. `--write` re-pins the baseline from
// current reality (the "bot-written" step: script-generated, reviewed in the
// PR that shrinks the debt). The metrics themselves are computed by the
// canonical validator (`--safety-metrics` / `--agents-only`) so this gate
// owns no classification logic of its own.

import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BASELINE = resolve(ROOT, 'scripts/safety-ratchet-baseline.json');
const WRITE = process.argv.includes('--write');

const sha = (items) => createHash('sha256').update(items.join('\n')).digest('hex');

function collectMetrics() {
  const raw = execFileSync('python3', ['scripts/validate-skills-schema.py', '--safety-metrics'], {
    cwd: ROOT,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  const metrics = JSON.parse(raw);

  let agentsOut = '';
  try {
    agentsOut = execFileSync('python3', ['scripts/validate-skills-schema.py', '--agents-only'], {
      cwd: ROOT,
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
    });
  } catch (error) {
    // Exit 1 with findings is the expected state while the corpus carries debt.
    agentsOut = String(error.stdout || '');
    if (!agentsOut) throw error;
  }
  const agentErrors = agentsOut
    .split('\n')
    .filter((line) => /^\s+ERROR/.test(line))
    .map((line) => line.trim())
    .sort();
  const terminal = agentsOut.match(/Validation FAILED with\s+(\d+) errors/);
  const agentCount = terminal ? Number(terminal[1]) : 0;

  return {
    schema_version: metrics.schema_version,
    classes: {
      bare_bash: metrics.bare_bash,
      tier2_tool_safety: metrics.tier2_tool_safety,
      shell_substitution: metrics.shell_substitution,
      agents_only_errors: agentErrors,
    },
    agents_terminal_error_count: agentCount,
  };
}

export function compare(baseline, current) {
  const failures = [];
  for (const [name, baseEntry] of Object.entries(baseline.classes)) {
    const nowMembers = current.classes[name] ?? [];
    const baseSet = new Set(baseEntry.members);
    if (nowMembers.length > baseEntry.count) {
      failures.push(
        `${name}: count grew ${baseEntry.count} → ${nowMembers.length} (monotone non-increasing)`,
      );
    }
    const newcomers = nowMembers.filter((member) => !baseSet.has(member));
    if (newcomers.length > 0) {
      failures.push(
        `${name}: ${newcomers.length} member(s) not in the baseline (a swap is new debt): ${newcomers
          .slice(0, 5)
          .join(' | ')}`,
      );
    }
  }
  return failures;
}

function shrunk(baseline, current) {
  return Object.entries(baseline.classes).filter(
    ([name, baseEntry]) => (current.classes[name] ?? []).length < baseEntry.count,
  );
}

function main() {
  const current = collectMetrics();
  if (WRITE) {
    const pinned = {
      $comment:
        'Triple-keyed safety-ratchet baseline (E4.3/E4.4/E4.11). Regenerate ONLY via `node scripts/check-safety-ratchet.mjs --write` in the PR that shrinks a class; the gate fails any growth or swap. shell_substitution is never waivable.',
      pinned_at: new Date().toISOString().slice(0, 10),
      schema_version: current.schema_version,
      agents_terminal_error_count: current.agents_terminal_error_count,
      classes: Object.fromEntries(
        Object.entries(current.classes).map(([name, members]) => [
          name,
          { count: members.length, set_sha256: sha(members), members },
        ]),
      ),
    };
    writeFileSync(BASELINE, `${JSON.stringify(pinned, null, 1)}\n`);
    console.log(
      `safety-ratchet: baseline written (${Object.entries(pinned.classes)
        .map(([name, entry]) => `${name}=${entry.count}`)
        .join(' ')})`,
    );
    return;
  }

  const baseline = JSON.parse(readFileSync(BASELINE, 'utf8'));
  const failures = compare(baseline, current);
  if (failures.length > 0) {
    for (const failure of failures) console.error(`safety-ratchet: FAIL — ${failure}`);
    console.error(
      'safety-ratchet: fix the new debt (there is no waiver path); a legitimate shrink re-pins with --write',
    );
    process.exit(1);
  }
  const shrunkClasses = shrunk(baseline, current);
  if (shrunkClasses.length > 0) {
    console.log(
      `safety-ratchet: OK — debt SHRANK (${shrunkClasses
        .map(([name, entry]) => `${name}: ${entry.count} → ${current.classes[name].length}`)
        .join(' | ')}); lock it in: node scripts/check-safety-ratchet.mjs --write`,
    );
    return;
  }
  console.log(
    `safety-ratchet: OK (${Object.entries(baseline.classes)
      .map(([name, entry]) => `${name}=${entry.count}`)
      .join(' ')}; schema ${baseline.schema_version})`,
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
