#!/usr/bin/env node
/**
 * Produce the generated launch-readiness record from ordered machine facts.
 * A later condition can never offset an earlier legal/safety/provenance fact.
 *
 * Usage:
 *   node scripts/evaluate-launch-readiness.mjs --conditions conditions.json \
 *     [--out launch-readiness.json]
 */

import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

const ORDER = Object.freeze([
  'legal',
  'safety',
  'provenance',
  'evidence',
  'certification_independence',
  'quality',
  'owner_attestation',
]);

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const values = {};
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    if (!['--conditions', '--out'].includes(flag)) fail(`Unknown argument: ${flag}`);
    if (values[flag]) fail(`${flag} may be supplied only once`);
    values[flag] = argv[++i];
    if (!values[flag]) fail(`${flag} requires a path`);
  }
  if (!values['--conditions']) fail('--conditions is required');
  return { conditions: values['--conditions'], out: values['--out'] ?? 'launch-readiness.json' };
}

export function evaluate(payload, now = new Date().toISOString()) {
  if (!payload || typeof payload !== 'object' || Array.isArray(payload))
    fail('conditions must be an object');
  if (payload.schema_version !== 'launch-conditions/v1') {
    fail('conditions schema_version must be launch-conditions/v1');
  }
  if (
    !payload.conditions ||
    typeof payload.conditions !== 'object' ||
    Array.isArray(payload.conditions)
  ) {
    fail('conditions must contain a conditions object');
  }
  const provided = Object.keys(payload.conditions).sort();
  if (provided.join(',') !== [...ORDER].sort().join(',')) {
    fail(`conditions must contain exactly: ${ORDER.join(', ')}`);
  }
  const breakdown = [];
  for (const id of ORDER) {
    const condition = payload.conditions[id];
    if (!condition || typeof condition !== 'object' || Array.isArray(condition)) {
      fail(`condition ${id} must be an object`);
    }
    if (typeof condition.passed !== 'boolean' || !Array.isArray(condition.reason_codes)) {
      fail(`condition ${id} requires boolean passed and reason_codes array`);
    }
    if (!condition.reason_codes.every((code) => typeof code === 'string' && code.length > 0)) {
      fail(`condition ${id} has invalid reason_codes`);
    }
    if (!condition.passed && condition.reason_codes.length === 0) {
      fail(`failed condition ${id} requires a machine reason code`);
    }
    breakdown.push({ id, passed: condition.passed, reason_codes: [...condition.reason_codes] });
  }
  return {
    schema_version: 'launch-readiness/v1',
    generated_at: now,
    ready: breakdown.every((condition) => condition.passed),
    decision_hierarchy: [...ORDER],
    conditions: breakdown,
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const payload = JSON.parse(fs.readFileSync(args.conditions, 'utf8'));
  fs.writeFileSync(args.out, `${JSON.stringify(evaluate(payload), null, 2)}\n`);
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main();
  } catch (error) {
    console.error(`launch readiness: FAIL: ${error.message}`);
    process.exitCode = 1;
  }
}
