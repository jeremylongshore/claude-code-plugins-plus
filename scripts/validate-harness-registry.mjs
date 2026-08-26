#!/usr/bin/env node
/**
 * Validates the model-neutral harness registry.
 *
 * The registry is the single machine-readable source for installation paths
 * and public support claims.  It intentionally distinguishes a portable
 * Agent Skills source from native extension systems such as Omarchy.
 */

import { readFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const REGISTRY = resolve(ROOT, 'config/harness-registry.json');
const SUPPORT = new Set([
  'verified-native',
  'standard-compatible',
  'native-extension',
  'research-required',
  'unsupported',
]);

export function validateRegistry(value) {
  const errors = [];
  if (!value || typeof value !== 'object') return ['registry must be an object'];
  if (value.schemaVersion !== 1) errors.push('schemaVersion must be 1');
  if (!value.portableArtifact || typeof value.portableArtifact !== 'object') {
    errors.push('portableArtifact is required');
  } else {
    for (const field of ['source', 'specification', 'policy']) {
      if (typeof value.portableArtifact[field] !== 'string' || !value.portableArtifact[field]) {
        errors.push(`portableArtifact.${field} must be a non-empty string`);
      }
    }
  }
  if (!Array.isArray(value.harnesses) || value.harnesses.length === 0) {
    errors.push('harnesses must be a non-empty array');
    return errors;
  }

  const ids = new Set();
  for (const harness of value.harnesses) {
    const prefix = `harness ${harness?.id ?? '<unknown>'}`;
    if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(harness?.id ?? '')) errors.push(`${prefix}: invalid id`);
    if (ids.has(harness?.id)) errors.push(`${prefix}: duplicate id`);
    ids.add(harness?.id);
    if (typeof harness?.displayName !== 'string' || !harness.displayName)
      errors.push(`${prefix}: displayName is required`);
    if (!SUPPORT.has(harness?.support)) errors.push(`${prefix}: invalid support tier`);
    if (typeof harness?.publicSupport !== 'boolean')
      errors.push(`${prefix}: publicSupport must be boolean`);
    if (typeof harness?.source !== 'string' || !/^https:\/\//.test(harness.source))
      errors.push(`${prefix}: source must be an HTTPS URL`);
    for (const field of ['projectPath', 'userPath']) {
      if (harness?.[field] !== null && typeof harness?.[field] !== 'string') {
        errors.push(`${prefix}: ${field} must be a string or null`);
      }
    }
    if (harness?.support === 'verified-native' && !harness?.publicSupport) {
      errors.push(`${prefix}: verified-native is the only tier eligible for public support`);
    }
    if (harness?.support !== 'verified-native' && harness?.publicSupport) {
      errors.push(`${prefix}: publicSupport requires verified-native evidence`);
    }
    if (harness?.support === 'native-extension' && (harness?.projectPath || !harness?.userPath)) {
      errors.push(
        `${prefix}: native extensions must not declare a portable project path and need a native user path`,
      );
    }
    if (
      ['verified-native', 'standard-compatible'].includes(harness?.support) &&
      !harness?.projectPath &&
      !harness?.userPath
    ) {
      errors.push(`${prefix}: portable support needs at least one install path`);
    }
  }
  return errors;
}

export function readRegistry(file = REGISTRY) {
  return JSON.parse(readFileSync(file, 'utf8'));
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const errors = validateRegistry(readRegistry());
  if (errors.length) {
    for (const error of errors) console.error(`harness-registry: FAIL — ${error}`);
    process.exit(1);
  }
  console.log('harness-registry: OK');
}
