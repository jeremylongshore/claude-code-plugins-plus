#!/usr/bin/env node
/**
 * Fail closed when a certification signer is also the PR author or artifact
 * producer. This check consumes identity facts extracted from verified signed
 * evidence bundles; it never treats a reviewer assertion as a signer fact.
 *
 * Usage:
 *   node scripts/check-certification-separation.mjs --records identities.json
 *
 * Input contract (certification-identities/v1):
 * {
 *   "schema_version": "certification-identities/v1",
 *   "records": [{
 *     "artifact_path": "plugins/example/skills/example/SKILL.md",
 *     "signing_identity": "https://github.com/org/repo/.github/workflows/certify.yml@refs/heads/main",
 *     "pr_author_identity": "octocat",
 *     "producing_identity": "ci://evaluation-runner"
 *   }]
 * }
 */

import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const SCHEMA_VERSION = 'certification-identities/v1';

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  if (argv.length !== 2 || argv[0] !== '--records') {
    fail('Usage: node scripts/check-certification-separation.mjs --records identities.json');
  }
  return argv[1];
}

function nonEmptyString(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

export function validateRecords(payload) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload)) {
    fail('identity records must be an object');
  }
  if (payload.schema_version !== SCHEMA_VERSION) {
    fail(`identity records schema_version must be ${SCHEMA_VERSION}`);
  }
  if (!Array.isArray(payload.records)) {
    fail('identity records must contain a records array');
  }

  const paths = new Set();
  const failures = [];
  for (const [index, record] of payload.records.entries()) {
    if (!record || typeof record !== 'object' || Array.isArray(record)) {
      fail(`record ${index} must be an object`);
    }
    const fields = [
      'artifact_path',
      'signing_identity',
      'pr_author_identity',
      'producing_identity',
    ];
    for (const field of fields) {
      if (!nonEmptyString(record[field])) fail(`record ${index} missing ${field}`);
    }
    if (paths.has(record.artifact_path)) {
      fail(`duplicate artifact_path: ${record.artifact_path}`);
    }
    paths.add(record.artifact_path);

    if (record.signing_identity === record.pr_author_identity) {
      failures.push(`${record.artifact_path}: E-CERTIFIER-IS-PR-AUTHOR`);
    }
    if (record.signing_identity === record.producing_identity) {
      failures.push(`${record.artifact_path}: E-CERTIFIER-IS-PRODUCER`);
    }
  }
  return failures;
}

function main() {
  const recordsPath = path.resolve(parseArgs(process.argv.slice(2)));
  let payload;
  try {
    payload = JSON.parse(fs.readFileSync(recordsPath, 'utf8'));
  } catch (error) {
    fail(`unable to read identity records: ${error.message}`);
  }
  const failures = validateRecords(payload);
  if (failures.length > 0) {
    for (const failure of failures) console.error(failure);
    process.exitCode = 1;
    return;
  }
  console.log(`certification separation: OK (${payload.records.length} record(s))`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch (error) {
    console.error(`certification separation: FAIL: ${error.message}`);
    process.exitCode = 1;
  }
}
