#!/usr/bin/env node

import { execFileSync } from 'node:child_process';
import { lstatSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { artifactRegistration } from './generated-artifact-registry.mjs';
import { normalizeDeadDomainValue } from './dead-domain-policy.mjs';
import { resolvePluginProvenance } from './plugin-provenance.mjs';

function trackedJsonProjections(root) {
  const output = execFileSync('git', ['ls-files', '-z'], {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  return output
    .split('\0')
    .filter(Boolean)
    .filter((path) => path.endsWith('.json'))
    .filter((path) => artifactRegistration(path)?.kind === 'generated_projection')
    .sort();
}

export function normalizeRetiredDomainProjections({ root = process.cwd() } = {}) {
  const repository = resolve(root);
  const changed = [];
  for (const path of trackedJsonProjections(repository)) {
    const provenance = resolvePluginProvenance(dirname(path), { root: repository });
    if (provenance.status === 'refused') {
      throw new Error(`refusing ${path}: ${provenance.reasonCode}`);
    }
    if (provenance.status === 'mirror') continue;
    const target = resolve(repository, path);
    const metadata = lstatSync(target);
    if (metadata.isSymbolicLink() || !metadata.isFile()) {
      throw new Error(`refusing non-regular generated projection: ${path}`);
    }
    const current = readFileSync(target, 'utf8');
    const parsed = JSON.parse(current);
    const normalized = normalizeDeadDomainValue(parsed);
    if (JSON.stringify(normalized) === JSON.stringify(parsed)) continue;
    const next = `${JSON.stringify(normalized, null, 2)}\n`;
    if (next !== current) {
      writeFileSync(target, next);
      changed.push(path);
    }
  }
  return changed;
}

function main() {
  const changed = normalizeRetiredDomainProjections();
  for (const path of changed) console.log(`normalized ${path}`);
  console.log(`retired-domain-projections: ${changed.length} file(s) normalized`);
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch (error) {
    console.error(`retired-domain-projections: ${error.message}`);
    process.exitCode = 1;
  }
}
