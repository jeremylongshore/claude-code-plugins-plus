#!/usr/bin/env node
/**
 * Fail closed when a configured external mirror lacks an explicit license
 * include or when its checked-in artifact lacks the corresponding root file.
 *
 * `sources.yaml` is the sync contract; `.source.json` identifies artifacts
 * that have actually been mirrored. Checking both prevents a future source
 * from silently dropping license text and catches an incomplete sync before
 * that artifact can be published or indexed.
 */

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import yaml from 'js-yaml';

import { hasRootLicenseInclude, isRootLicenseFile } from './sync-lockfile.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const SOURCES_PATH = path.join(ROOT, 'sources.yaml');

const config = yaml.load(fs.readFileSync(SOURCES_PATH, 'utf8'));
const sources = Array.isArray(config?.sources) ? config.sources : null;
if (!sources?.length) {
  throw new Error('sources.yaml must define a non-empty sources list');
}

const failures = [];
for (const source of sources) {
  if (!source?.name || !source?.target_path) {
    failures.push('source entry is missing name or target_path');
    continue;
  }
  if (!hasRootLicenseInclude(source.include)) {
    failures.push(`${source.name}: include[] lacks an explicit root LICENSE/COPYING entry`);
  }
}

const mirrorMarkers = [];
function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const absolute = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(absolute);
    if (entry.isFile() && entry.name === '.source.json') mirrorMarkers.push(absolute);
  }
}
walk(path.join(ROOT, 'plugins'));

for (const marker of mirrorMarkers) {
  const mirror = path.dirname(marker);
  const hasLicense = fs
    .readdirSync(mirror, { withFileTypes: true })
    .some((entry) => entry.isFile() && isRootLicenseFile(entry.name));
  if (!hasLicense) failures.push(`${path.relative(ROOT, mirror)}: no root LICENSE/COPYING file`);
}

if (failures.length) {
  console.error('Mirror license policy failed:');
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(
  `✓ mirror license policy: ${sources.length}/${sources.length} configured sources and ${mirrorMarkers.length}/${mirrorMarkers.length} mirrored artifacts carry license coverage`,
);
