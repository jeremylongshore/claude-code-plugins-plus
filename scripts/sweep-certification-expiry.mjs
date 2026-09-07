#!/usr/bin/env node
/**
 * Derive the rendering-authoritative certification projection from immutable
 * certification evidence. Expired certifications are demoted here; the input
 * report is never rewritten.
 *
 * Usage: node scripts/sweep-certification-expiry.mjs --report certification-report.json
 *        [--out certification-rendering.json] [--now RFC3339]
 */

import fs from 'node:fs';
import { pathToFileURL } from 'node:url';

function fail(message) {
  throw new Error(message);
}

function parseArgs(argv) {
  const values = {};
  for (let i = 0; i < argv.length; i += 1) {
    const flag = argv[i];
    if (!['--report', '--out', '--now'].includes(flag)) fail(`Unknown argument: ${flag}`);
    if (values[flag]) fail(`${flag} may be supplied only once`);
    values[flag] = argv[++i];
    if (!values[flag]) fail(`${flag} requires a value`);
  }
  if (!values['--report']) fail('--report is required');
  return {
    report: values['--report'],
    out: values['--out'] ?? 'certification-rendering.json',
    now: values['--now'],
  };
}

function time(value, label) {
  if (typeof value !== 'string' || Number.isNaN(Date.parse(value)))
    fail(`${label} must be RFC3339`);
  return Date.parse(value);
}

export function sweep(report, now = new Date().toISOString()) {
  if (
    !report ||
    typeof report !== 'object' ||
    Array.isArray(report) ||
    report.schema_version !== 'certification-report/v1'
  ) {
    fail('report must use certification-report/v1');
  }
  if (!Array.isArray(report.artifacts)) fail('report must contain artifacts array');
  const nowMs = time(now, 'now');
  let expired = 0;
  const artifacts = report.artifacts.map((artifact, index) => {
    if (!artifact || typeof artifact !== 'object' || typeof artifact.path !== 'string')
      fail(`artifact ${index} missing path`);
    if (artifact.verdict !== 'CERTIFIED' && artifact.verdict !== 'NOT-CERTIFIED')
      fail(`artifact ${artifact.path} invalid verdict`);
    if (artifact.verdict !== 'CERTIFIED') return { ...artifact };
    const issuedMs = time(artifact.issued_at, `artifact ${artifact.path} issued_at`);
    if (!Number.isInteger(artifact.ttl_hours) || artifact.ttl_hours <= 0)
      fail(`artifact ${artifact.path} ttl_hours must be a positive integer`);
    const expiresAt = new Date(issuedMs + artifact.ttl_hours * 60 * 60 * 1000).toISOString();
    if (Date.parse(expiresAt) <= nowMs) {
      expired += 1;
      return {
        ...artifact,
        verdict: 'NOT-CERTIFIED',
        reason_codes: [...artifact.reason_codes, 'E-CERTIFICATION-EXPIRED'],
        expires_at: expiresAt,
      };
    }
    return { ...artifact, expires_at: expiresAt };
  });
  return {
    schema_version: 'certification-rendering/v1',
    generated_at: now,
    source_schema_version: report.schema_version,
    certified: artifacts.filter((artifact) => artifact.verdict === 'CERTIFIED').length,
    pending: artifacts.filter((artifact) => artifact.verdict !== 'CERTIFIED').length,
    delta: { expired_demoted: expired },
    artifacts,
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const args = parseArgs(process.argv.slice(2));
    const report = JSON.parse(fs.readFileSync(args.report, 'utf8'));
    fs.writeFileSync(args.out, `${JSON.stringify(sweep(report, args.now), null, 2)}\n`);
  } catch (error) {
    console.error(`certification expiry sweep: FAIL: ${error.message}`);
    process.exitCode = 1;
  }
}
