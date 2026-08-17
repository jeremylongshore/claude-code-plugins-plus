#!/usr/bin/env node
/**
 * check-generated-artifacts.mjs — assert that deterministically-regenerated
 * projections are NOT tracked in git.
 *
 * A generated file that is also committed has two claimants to one fact: the
 * generator and the tree. They diverge silently, because nothing compares them —
 * exactly how `marketplace/public/data/*.json` came to duplicate ~28.5 MB of
 * `marketplace/src/data/*.json` byte-for-byte (identical blob SHAs), and how the
 * kobiton binary reached `skills/.curated/` (bead claude-5awj.2 / .1).
 *
 * This gate is the RECURRENCE PREVENTION for that class: re-adding such a file
 * fails CI with the regeneration command in the message. It deliberately checks
 * TRACKING, not content — content equality is the generator's job, and a gate
 * that regenerated to compare would be slow and would mask a broken generator.
 *
 * Exit 0 = clean. Exit 1 = a projection is tracked (each one named).
 */
import { execFileSync, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { basename, isAbsolute, join } from 'node:path';
import { pathToFileURL } from 'node:url';

import { artifactRegistrationsByTracking } from './generated-artifact-registry.mjs';

// `:(top)` pathspecs in the shared registry stay repo-root-relative. Without
// that prefix, invoking this gate from a subdirectory silently matches nothing.
const BUF = { maxBuffer: 64 * 1024 * 1024 };

function normalizeRepositoryPath(candidate) {
  const path = String(candidate).replaceAll('\\', '/').replace(/^\.\//, '');
  if (
    path.length === 0 ||
    path.includes('\0') ||
    /[\r\n]/.test(path) ||
    isAbsolute(path) ||
    path.startsWith(':') ||
    path === '..' ||
    path.startsWith('../') ||
    path.split('/').includes('..')
  ) {
    throw new Error(`generated-artifact path escapes repository: ${candidate}`);
  }
  return path;
}

export function readIndexedArtifact(candidate, { root = process.cwd() } = {}) {
  const path = normalizeRepositoryPath(candidate);
  const indexed = spawnSync('git', ['ls-files', '--stage', '--', path], {
    cwd: root,
    encoding: 'utf8',
  });
  if (indexed.error || indexed.status !== 0) {
    throw new Error(`unable to inspect generated artifact index entry: ${path}`);
  }
  const rows = indexed.stdout.trim().split('\n').filter(Boolean);
  const match = rows.length === 1 ? rows[0].match(/^(100644|100755) [0-9a-f]+ 0\t(.+)$/) : null;
  if (!match || match[2] !== path) {
    throw new Error(`generated content check requires one regular stage-0 index entry: ${path}`);
  }
  const content = spawnSync('git', ['show', `:${path}`], {
    cwd: root,
    encoding: null,
    maxBuffer: BUF.maxBuffer,
  });
  if (content.error || content.status !== 0) {
    throw new Error(`unable to read generated artifact from Git index: ${path}`);
  }
  return content.stdout;
}

/**
 * Compare rendered candidate bytes to the Git index without touching the
 * working tree. `git diff --no-index --quiet` supplies the exact byte-level
 * regenerate-and-diff contract while temporary files keep author changes safe.
 */
export function assertGeneratedContentCurrent(candidates, { root = process.cwd() } = {}) {
  if (!Array.isArray(candidates) || candidates.length === 0) {
    throw new Error('generated content check requires at least one candidate');
  }
  const seen = new Set();
  const failures = [];
  const scratch = mkdtempSync(join(tmpdir(), 'generated-content-drift-'));
  try {
    for (const candidate of candidates) {
      const path = normalizeRepositoryPath(candidate?.path);
      if (seen.has(path)) throw new Error(`duplicate generated content candidate: ${path}`);
      seen.add(path);
      if (typeof candidate?.contents !== 'string' && !Buffer.isBuffer(candidate?.contents)) {
        throw new Error(`generated content candidate has no bytes: ${path}`);
      }
      const expected = readIndexedArtifact(path, { root });
      const safeName = `${seen.size}-${basename(path)}`;
      const expectedPath = join(scratch, `${safeName}.indexed`);
      const candidatePath = join(scratch, `${safeName}.rendered`);
      writeFileSync(expectedPath, expected);
      writeFileSync(candidatePath, candidate.contents);
      const diff = spawnSync(
        'git',
        ['diff', '--no-index', '--quiet', '--', expectedPath, candidatePath],
        {
          cwd: root,
          encoding: 'utf8',
        },
      );
      if (diff.error || diff.status === null || diff.status > 1) {
        throw new Error(
          `unable to compare regenerated artifact ${path}: ${diff.error?.message ?? diff.stderr ?? 'git diff failed'}`,
        );
      }
      if (diff.status === 1) failures.push(path);
    }
  } finally {
    rmSync(scratch, { recursive: true, force: true });
  }
  if (failures.length > 0) {
    throw new Error(
      `generated content drift (${failures.length}): ${failures.join(', ')}; run the named generator and stage its outputs`,
    );
  }
  return [...seen].sort();
}

export function checkUntrackedProjections({ root = process.cwd() } = {}) {
  const projections = artifactRegistrationsByTracking('untracked');
  let failures = 0;
  for (const p of projections) {
    let tracked = '';
    try {
      tracked = execFileSync('git', ['ls-files', '--', p.pathspec], {
        ...BUF,
        cwd: root,
      })
        .toString()
        .trim();
    } catch (error) {
      throw new Error(
        `unable to enumerate tracked files matching ${p.glob}; generated-artifacts refuses to pass without Git evidence: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
    const files = tracked ? tracked.split('\n') : [];
    if (files.length) {
      failures += files.length;
      console.error(
        `\n✗ ${files.length} tracked file(s) matching ${p.glob} — this is a GENERATED projection.`,
      );
      console.error(`    canonical:  ${p.canonical}`);
      console.error(`    why:        ${p.why}`);
      console.error(`    regenerate: ${p.regenerate}`);
      console.error(
        `    fix:        git rm --cached <file>   (it is already ignored; do not commit it)`,
      );
      for (const f of files.slice(0, 10)) console.error(`      ${f}`);
      if (files.length > 10) console.error(`      … and ${files.length - 10} more`);
    }
  }
  if (failures) {
    throw new Error(
      `${failures} tracked projection file(s); a generated file must have exactly one claimant — its generator`,
    );
  }
  return projections.length;
}

function main() {
  try {
    const count = checkUntrackedProjections();
    console.log(`generated-artifacts: OK (${count} projection globs, 0 tracked)`);
  } catch (error) {
    console.error(
      `\ngenerated-artifacts: ${error instanceof Error ? error.message : String(error)}`,
    );
    process.exitCode = 1;
  }
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) main();
