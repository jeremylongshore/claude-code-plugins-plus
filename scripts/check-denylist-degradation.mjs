#!/usr/bin/env node
/**
 * check-denylist-degradation.mjs — fail-closed degradation for denylist
 * postures a harness cannot enforce (blueprint 727 E4.13).
 *
 * A skill's `disallowed-tools` denylist is enforced by the Claude Code
 * RUNTIME only — the repo validates syntax, and on any other harness the
 * denylist silently does not exist (the register's § 5 finding). This gate
 * makes silent-drop impossible to claim:
 *
 *   1. A first-party skill declaring `disallowed-tools` may not name any
 *      non-claude-code harness in its `compatibility` prose — a portability
 *      claim over a denylist-dependent posture IS the silent-drop bug.
 *   2. If the skill ships a canonical skill-card (`skill-card.yaml`) whose
 *      `adapters` go beyond claude-code, every extra adapter must carry an
 *      `unsupported[]` entry for the denylist capability whose degradation
 *      is `fail-closed` (or omitted — the schema's documented default).
 *      `skip` and `prompt-in-band` are silent-drop for a SAFETY posture and
 *      fail here even though the schema allows them for other capabilities.
 *
 * Zero skill-cards exist at v0, so rule 2 is structural today and becomes
 * live with card adoption — exactly how the adapter-thinness gate landed.
 * Mirror (.source.json) subtrees are upstream-owned and excluded.
 */

import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { KNOWN_HARNESSES } from './check-portability-claims.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');

function trackedSkillFiles() {
  const out = execFileSync('git', ['ls-files', '*SKILL.md'], { cwd: ROOT, encoding: 'utf8' });
  return out.split('\n').filter(Boolean);
}

function isMirror(rel) {
  let dir = dirname(rel);
  while (dir !== '.' && dir !== '/') {
    if (existsSync(resolve(ROOT, dir, '.source.json'))) return true;
    dir = dirname(dir);
  }
  return false;
}

function frontmatterOf(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  return m ? m[1] : null;
}

function fieldValue(fm, name) {
  const m = fm.match(new RegExp(`^${name}:\\s*(.*)$`, 'm'));
  return m ? m[1].trim() : null;
}

export function analyzeSkill(rel, text) {
  const issues = [];
  const fm = frontmatterOf(text);
  if (!fm || !/^disallowed-tools:/m.test(fm)) return { denylist: false, issues };

  const compatibility = fieldValue(fm, 'compatibility') ?? '';
  for (const [name, pattern] of KNOWN_HARNESSES) {
    if (name === 'claude-code') continue;
    if (pattern.test(compatibility)) {
      issues.push(
        `${rel}: declares disallowed-tools but claims '${name}' in compatibility — ` +
          'the denylist silently does not exist there (silent drop). Either drop the ' +
          'claim or ship a skill-card with unsupported[].degradation: fail-closed for it.',
      );
    }
  }

  const cardPath = join(dirname(rel), 'skill-card.yaml');
  if (existsSync(resolve(ROOT, cardPath))) {
    const card = readFileSync(resolve(ROOT, cardPath), 'utf8');
    const adapters = [...card.matchAll(/^\s*-\s*(?:adapter:\s*)?([a-z0-9-]+)\s*$/gm)]
      .map((m) => m[1])
      .filter((a) => a !== 'claude-code');
    for (const adapter of adapters) {
      const failClosed = new RegExp(
        `adapter:\\s*${adapter}[\\s\\S]{0,400}?degradation:\\s*fail-closed`,
      ).test(card);
      const omittedDefault =
        new RegExp(`adapter:\\s*${adapter}`).test(card) &&
        !new RegExp(`adapter:\\s*${adapter}[\\s\\S]{0,400}?degradation:`).test(card);
      if (!failClosed && !omittedDefault) {
        issues.push(
          `${rel}: skill-card adapter '${adapter}' does not degrade the denylist ` +
            "fail-closed — 'skip'/'prompt-in-band' are silent drop for a safety posture.",
        );
      }
    }
  }
  return { denylist: true, issues };
}

function main() {
  let denylistSkills = 0;
  const issues = [];
  for (const rel of trackedSkillFiles()) {
    if (isMirror(rel)) continue;
    const text = readFileSync(resolve(ROOT, rel), 'utf8');
    const result = analyzeSkill(rel, text);
    if (result.denylist) denylistSkills += 1;
    issues.push(...result.issues);
  }
  if (issues.length > 0) {
    for (const issue of issues) console.error(`denylist-degradation: FAIL — ${issue}`);
    process.exit(1);
  }
  console.log(
    `denylist-degradation: OK (${denylistSkills} first-party denylist-bearing skills; ` +
      'no silent-drop claims; card rule armed for adapter growth)',
  );
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main();
}
