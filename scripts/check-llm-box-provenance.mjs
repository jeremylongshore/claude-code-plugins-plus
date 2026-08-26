#!/usr/bin/env node
import fs from 'node:fs';
import yaml from 'js-yaml';

const root = process.cwd();
const source = yaml
  .load(fs.readFileSync(`${root}/sources.yaml`, 'utf8'))
  .sources.find((x) => x.name === 'llm-box');
const marker = JSON.parse(
  fs.readFileSync(`${root}/plugins/community/llm-box/.source.json`, 'utf8'),
);
const pkg = JSON.parse(fs.readFileSync(`${root}/plugins/community/llm-box/package.json`, 'utf8'));
const catalog = JSON.parse(
  fs.readFileSync(`${root}/.claude-plugin/marketplace.extended.json`, 'utf8'),
).plugins.find((x) => x.name === 'llm-box');
const failures = [];
if (
  ![source?.license, marker?.license, pkg?.license, catalog?.license].every((x) => x === 'AGPL-3.0')
)
  failures.push('license projections must all equal AGPL-3.0');
if (marker?.synced_from?.source_commit !== '0b4cbae76fbf86825076b230a342735bdfd2a0fc')
  failures.push('source marker must pin the reviewed upstream commit');
if (
  source?.copyleft_disposition?.status !== 'quarantined' ||
  !Array.isArray(source?.copyleft_disposition?.channels) ||
  source.copyleft_disposition.channels.length
)
  failures.push('source must record a quarantined no-channel copyleft disposition');
if (
  catalog?.publication !== 'quarantined' ||
  pkg?.private !== true ||
  pkg?.publishConfig?.access !== 'restricted'
)
  failures.push('catalog/package must retain explicit non-publishable posture');
if (failures.length) {
  console.error(failures.join('\n'));
  process.exit(1);
}
console.log('llm-box provenance: OK (AGPL-3.0, pinned, quarantined)');
