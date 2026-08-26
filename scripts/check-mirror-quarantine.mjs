#!/usr/bin/env node
/** Assert every external mirror has a non-publishable E8 disposition. */
import fs from 'node:fs';
import path from 'node:path';

import { resolvePluginProvenance } from './plugin-provenance.mjs';

function fail(message) {
  throw new Error(`check-mirror-quarantine: ${message}`);
}

export function checkMirrorQuarantine({ root = process.cwd() } = {}) {
  const ledger = JSON.parse(
    fs.readFileSync(path.join(root, 'freshie/disposition-ledger.json'), 'utf8'),
  );
  if (ledger?.schema_version !== 'disposition-ledger/v1' || !Array.isArray(ledger.artifacts)) {
    fail('disposition ledger is malformed');
  }
  const rows = new Map(ledger.artifacts.map((row) => [row.path, row]));
  const gradePaths = fs
    .readFileSync(path.join(root, 'freshie/grades.csv'), 'utf8')
    .trim()
    .split(/\r?\n/)
    .slice(1)
    .map((line) => `${line.split(',')[0]}/SKILL.md`);
  const mirrors = gradePaths.filter(
    (skill) => resolvePluginProvenance(path.posix.dirname(skill), { root }).status === 'mirror',
  );
  const bad = mirrors.filter(
    (skill) => !['QUARANTINE', 'CERTIFY-UPSTREAM'].includes(rows.get(skill)?.disposition),
  );
  if (bad.length) fail(`mirror without non-publishable disposition: ${bad.join(', ')}`);

  const manifestPath = path.join(root, 'skills/.curated/MANIFEST.json');
  const curated = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const curatedSources = new Set((curated.skills ?? []).map((row) => row.source_path));
  const leaked = mirrors.filter((skill) => curatedSources.has(skill));
  if (leaked.length)
    fail(`quarantined mirror appears in curated publication: ${leaked.join(', ')}`);
  return {
    mirrors: mirrors.length,
    quarantined: mirrors.filter((skill) => rows.get(skill)?.disposition === 'QUARANTINE').length,
  };
}

try {
  const result = checkMirrorQuarantine();
  console.log(`mirror quarantine: OK (${result.quarantined}/${result.mirrors} quarantined)`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
