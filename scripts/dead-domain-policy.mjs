import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { closeSync, constants, fstatSync, openSync, readFileSync, realpathSync } from 'node:fs';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';

import { artifactRegistration } from './generated-artifact-registry.mjs';
import { resolvePluginProvenance } from './plugin-provenance.mjs';

export const DEAD_DOMAIN = ['claudecode', 'plugins.io'].join('');
export const LIVE_DOMAIN = 'tonsofskills.com';

function readRegularFileSync(path, encoding = null) {
  const noFollow = Number.isInteger(constants.O_NOFOLLOW) ? constants.O_NOFOLLOW : 0;
  let descriptor;
  try {
    descriptor = openSync(path, constants.O_RDONLY | noFollow);
    const metadata = fstatSync(descriptor);
    if (!metadata.isFile()) throw new Error('path is not a regular file');
    return readFileSync(descriptor, encoding ?? undefined);
  } finally {
    if (descriptor !== undefined) closeSync(descriptor);
  }
}
export const VERIFIED_CONTACT_EMAIL = 'jeremy@intentsolutions.io';

const APPROVED_RETIRED_MAILBOXES = new Set(['hello', 'jeremy', 'plugins']);
const UNSUPPORTED_CONTACT_DOMAIN = `(?:${DEAD_DOMAIN.replace('.', '\\.')}|${LIVE_DOMAIN.replace('.', '\\.')})`;
const UNSUPPORTED_EMAIL_PATTERN = new RegExp(
  `([a-z0-9._%+-]+)@${UNSUPPORTED_CONTACT_DOMAIN}`,
  'gi',
);

function replacementEmail(localPart) {
  return APPROVED_RETIRED_MAILBOXES.has(localPart.toLowerCase()) ? VERIFIED_CONTACT_EMAIL : null;
}

export function replaceDeadDomain(value) {
  return String(value)
    .replace(
      new RegExp(`\\s*<([a-z0-9._%+-]+)@${UNSUPPORTED_CONTACT_DOMAIN}>`, 'gi'),
      (_match, localPart) => {
        const replacement = replacementEmail(localPart);
        return replacement ? ` <${replacement}>` : '';
      },
    )
    .replace(UNSUPPORTED_EMAIL_PATTERN, (_match, localPart) => {
      return replacementEmail(localPart) ?? '[retired contact]';
    })
    .replace(new RegExp(DEAD_DOMAIN.replace('.', '\\.'), 'gi'), LIVE_DOMAIN);
}

export function normalizeDeadDomainValue(value) {
  if (typeof value === 'string') return replaceDeadDomain(value);
  if (Array.isArray(value)) return value.map((item) => normalizeDeadDomainValue(item));
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).flatMap(([key, item]) => {
        if (key.toLowerCase() === 'email' && typeof item === 'string') {
          UNSUPPORTED_EMAIL_PATTERN.lastIndex = 0;
          const match = UNSUPPORTED_EMAIL_PATTERN.exec(item);
          UNSUPPORTED_EMAIL_PATTERN.lastIndex = 0;
          if (match && match[0].length === item.length) {
            const replacement = replacementEmail(match[1]);
            return replacement ? [[key, replacement]] : [];
          }
        }
        return [[key, normalizeDeadDomainValue(item)]];
      }),
    );
  }
  return value;
}

export const RETAINED_DOMAIN_EVIDENCE = new Map([
  [
    '000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md',
    '5edfe778767f68423eaae3160dde3afce36a21c87991624b2940339eefa2b682',
  ],
  [
    '000-docs/6767-c-DR-STND-claude-code-extensions-standard.md',
    'f44ce14c2d0a71da1abcf84eb71ccd1089a9df5e5f1bf16d0aca8f41faec3131',
  ],
  [
    '000-docs/6767-d-AT-APIS-claude-code-extensions-schema.md',
    'bf0740c5902cdd8e92c01d974926d31660c79158eff5099e9358b865383f2075',
  ],
  [
    '000-docs/6767-e-WA-WFLW-extensions-validation-ci-gates.md',
    '18a3da015e85f9b37175f3ef851cf159a1c1fb50958ee14da6d068abc4a678cc',
  ],
  [
    '000-docs/6767-h-SPEC-DR-STND-claude-code-extensions-master.md',
    'd84ef7449d6d852c9b9506fc2bd649bbc15e59a050606ede341d40da866df36e',
  ],
  [
    'tests/fixtures/prose-anchors/expected-output.json',
    '1e8d83065d3767b83850eeaa739c4c25d54a108fe2994c584f7b43123a49ee78',
  ],
  [
    'freshie/exports/run-1/csv-exports/field_registry.csv',
    '91d49c058b1cc8ab9702da57060252c7927a5222e0ad640615875c5ef609e9bc',
  ],
  [
    'freshie/exports/run-1/csv-exports/frontmatter_fields.csv',
    '57187a7a3437fc990f1c7291eebd9f0f8695144b0e990f7f95cc4ad2929b8804',
  ],
  [
    'freshie/exports/run-1/csv-exports/frontmatter_values.csv',
    '8bd190047208687bb2bb49f6f3d31c4713f548116e9161537ce9f1ed4cd2403c',
  ],
  [
    'freshie/exports/run-1/csv-exports/plugin_fields.csv',
    'ac810307f7c17c1c711583e198a42ab67252cf1aa0996b015891c7609982c817',
  ],
  [
    'freshie/exports/run-1/csv-exports/plugin_values.csv',
    'b46d6b7ee8327873cb91d138d3423e6b0647152f3817e0a27e12180924c19251',
  ],
  [
    'freshie/exports/run-1/frontmatter_fields.json',
    '7e7876a83e7f15b05a8d987b8bf0e4733626bc6b6c5d9e39f6b2fab8d01d3d3a',
  ],
  [
    'freshie/exports/run-1/frontmatter_values.json',
    '36348da9fe9ccc931f621728376e98d946a6d7613057d9ccdfef05e97ac5adf0',
  ],
  [
    'freshie/exports/run-1/plugin_fields.json',
    'e2137e241ff07d780aeeedd85e425286d40ba8176ee945bb7389e2aaee8ae76b',
  ],
  [
    'freshie/exports/run-1/plugin_values.json',
    '784271b6a16c42a4e7c95dcc1001e1e2e2ca2dabd01fd0c5de6be133766da9c3',
  ],
]);

function contentSha256(content) {
  return createHash('sha256').update(content).digest('hex');
}

const FROZEN_DOMAIN_RECORDS = new Set([
  '000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md',
  '000-docs/6767-c-DR-STND-claude-code-extensions-standard.md',
  '000-docs/6767-d-AT-APIS-claude-code-extensions-schema.md',
  '000-docs/6767-e-WA-WFLW-extensions-validation-ci-gates.md',
  '000-docs/6767-h-SPEC-DR-STND-claude-code-extensions-master.md',
]);

function compareText(a, b) {
  return a < b ? -1 : a > b ? 1 : 0;
}

function inside(root, candidate) {
  const candidateRelative = relative(root, candidate);
  return (
    candidateRelative === '' ||
    (!candidateRelative.startsWith(`..${sep}`) &&
      candidateRelative !== '..' &&
      !isAbsolute(candidateRelative))
  );
}

export function normalizeDomainPath(candidate) {
  const value = String(candidate).replaceAll('\\', '/');
  if (
    value.length === 0 ||
    value.includes('\0') ||
    isAbsolute(value) ||
    value === '..' ||
    value.startsWith('../') ||
    value.split('/').includes('..')
  ) {
    throw new Error(`domain-policy path escapes repository: ${candidate}`);
  }
  return value.replace(/^\.\//, '');
}

export function isFrozenDomainRecord(candidate) {
  return FROZEN_DOMAIN_RECORDS.has(normalizeDomainPath(candidate));
}

function isFrozenDomainEvidence(candidate) {
  const path = normalizeDomainPath(candidate);
  return isFrozenDomainRecord(path) || artifactRegistration(path)?.kind === 'frozen_projection';
}

export function isGeneratedDomainProjection(candidate) {
  return artifactRegistration(normalizeDomainPath(candidate))?.kind === 'generated_projection';
}

export function classifyDomainPath(
  candidate,
  { root = process.cwd(), content = null, retainedEvidence = RETAINED_DOMAIN_EVIDENCE } = {},
) {
  let path;
  try {
    path = normalizeDomainPath(candidate);
  } catch (error) {
    return {
      category: 'refused',
      path: String(candidate),
      reasonCode: 'PATH_TRAVERSAL',
      error: error instanceof Error ? error.message : String(error),
    };
  }

  if (isFrozenDomainRecord(path)) {
    let frozenContent = content;
    try {
      frozenContent ??= readRegularFileSync(resolve(root, path), 'utf8');
    } catch (error) {
      return {
        category: 'refused',
        path,
        reasonCode: 'UNREADABLE_FROZEN_RECORD',
        error: error instanceof Error ? error.message : String(error),
      };
    }
    const frozenText = Buffer.isBuffer(frozenContent)
      ? frozenContent.toString('utf8')
      : String(frozenContent);
    if (
      !frozenText.startsWith('<!-- doc-class: frozen -->\n') ||
      !/^> \*\*SUPERSEDED–FROZEN \(/m.test(frozenText)
    ) {
      return { category: 'refused', path, reasonCode: 'INVALID_FROZEN_RECORD_MARKER' };
    }
    const expected = retainedEvidence.get(path);
    if (!expected || contentSha256(frozenContent) !== expected) {
      return { category: 'refused', path, reasonCode: 'FROZEN_RECORD_BYTE_DRIFT' };
    }
    return { category: 'frozen_record', path, reasonCode: 'FROZEN_6767_RECORD' };
  }

  const registration = artifactRegistration(path);
  if (registration?.kind === 'frozen_projection') {
    let projectionContent = content;
    try {
      projectionContent ??= readRegularFileSync(resolve(root, path));
    } catch (error) {
      return {
        category: 'refused',
        path,
        reasonCode: 'UNREADABLE_FROZEN_PROJECTION',
        error: error instanceof Error ? error.message : String(error),
      };
    }
    const expected = retainedEvidence.get(path);
    if (!expected || contentSha256(projectionContent) !== expected) {
      return { category: 'refused', path, reasonCode: 'FROZEN_RECORD_BYTE_DRIFT' };
    }
    return {
      category: 'frozen_record',
      path,
      reasonCode: 'FROZEN_6767_PROJECTION',
      registrationId: registration.id,
    };
  }

  const provenance = resolvePluginProvenance(dirname(path), { root });
  if (provenance.status === 'refused') {
    return {
      category: 'refused',
      path,
      reasonCode: provenance.reasonCode,
      markerPath: provenance.markerPath ?? null,
      error: provenance.error ?? null,
    };
  }
  if (provenance.status === 'mirror') {
    return {
      category: 'provenance_mirror',
      path,
      reasonCode: provenance.reasonCode,
      markerPath: provenance.markerPath,
    };
  }

  if (registration?.kind === 'historical_snapshot') {
    const expected = retainedEvidence.get(path);
    if (!expected) {
      return { category: 'refused', path, reasonCode: 'UNREGISTERED_HISTORICAL_SNAPSHOT' };
    }
    let historicalContent = content;
    try {
      historicalContent ??= readRegularFileSync(resolve(root, path));
    } catch (error) {
      return {
        category: 'refused',
        path,
        reasonCode: 'UNREADABLE_HISTORICAL_SNAPSHOT',
        error: error instanceof Error ? error.message : String(error),
      };
    }
    if (contentSha256(historicalContent) !== expected) {
      return { category: 'refused', path, reasonCode: 'HISTORICAL_SNAPSHOT_BYTE_DRIFT' };
    }
    return {
      category: 'historical_snapshot',
      path,
      reasonCode: 'RETAINED_POINT_IN_TIME_EVIDENCE',
      registrationId: registration.id,
    };
  }
  if (registration?.kind === 'generated_projection') {
    return {
      category: 'generated_projection',
      path,
      reasonCode: 'GENERATED_PROJECTION',
      registrationId: registration.id,
    };
  }
  return { category: 'first_party_source', path, reasonCode: 'FIRST_PARTY_SOURCE' };
}

function countNeedle(buffer, needle) {
  const haystack = buffer.toString('utf8').toLowerCase();
  const normalizedNeedle = needle.toString('utf8').toLowerCase();
  let count = 0;
  let offset = 0;
  while ((offset = haystack.indexOf(normalizedNeedle, offset)) !== -1) {
    count += 1;
    offset += normalizedNeedle.length;
  }
  return count;
}

function trackedEntries(root) {
  let output;
  try {
    output = execFileSync('git', ['ls-files', '--stage', '-z'], {
      cwd: root,
      encoding: 'buffer',
      maxBuffer: 64 * 1024 * 1024,
    });
  } catch (error) {
    throw new Error(`domain-policy cannot enumerate tracked files: ${error.message}`);
  }
  return output
    .toString('utf8')
    .split('\0')
    .filter(Boolean)
    .map((record) => {
      const separator = record.indexOf('\t');
      const metadata = separator === -1 ? '' : record.slice(0, separator);
      const path = separator === -1 ? record : record.slice(separator + 1);
      const match = metadata.match(/^(\d{6}) [0-9a-f]{40,64} ([0-3])$/);
      if (!match) throw new Error(`domain-policy malformed Git index entry for ${path}`);
      return { mode: match[1], path: normalizeDomainPath(path), stage: Number(match[2]) };
    })
    .sort((a, b) => compareText(a.path, b.path));
}

function summary(rows) {
  return {
    files: rows.length,
    occurrences: rows.reduce((sum, row) => sum + row.occurrences, 0),
    paths: rows.map((row) => row.path),
  };
}

export function scanDeadDomainPolicy({
  root = process.cwd(),
  paths,
  retainedEvidence = RETAINED_DOMAIN_EVIDENCE,
} = {}) {
  const repository = realpathSync(resolve(root));
  const supplied = paths?.map((entry) =>
    typeof entry === 'string'
      ? { mode: null, path: normalizeDomainPath(entry), stage: 0 }
      : { ...entry, path: normalizeDomainPath(entry.path) },
  );
  const entries = supplied ?? trackedEntries(repository);
  const candidates = [...new Map(entries.map((entry) => [entry.path, entry])).values()].sort(
    (a, b) => compareText(a.path, b.path),
  );
  const candidatePaths = new Set(candidates.map((entry) => entry.path));
  const needle = Buffer.from(DEAD_DOMAIN, 'utf8');
  const rows = [];
  const refused = [];
  const invalidRetainedPaths = new Set();

  for (const [path, expectedHash] of retainedEvidence) {
    if (supplied && !candidatePaths.has(path)) continue;
    if (!candidatePaths.has(path)) {
      refused.push({ path, reasonCode: 'RETAINED_EVIDENCE_NOT_TRACKED' });
      invalidRetainedPaths.add(path);
      continue;
    }
    try {
      const target = resolve(repository, path);
      if (contentSha256(readRegularFileSync(target)) !== expectedHash) {
        refused.push({
          path,
          reasonCode: isFrozenDomainEvidence(path)
            ? 'FROZEN_RECORD_BYTE_DRIFT'
            : 'HISTORICAL_SNAPSHOT_BYTE_DRIFT',
        });
        invalidRetainedPaths.add(path);
      }
    } catch (error) {
      refused.push({
        path,
        reasonCode: 'UNREADABLE_RETAINED_EVIDENCE',
        error: error instanceof Error ? error.message : String(error),
      });
      invalidRetainedPaths.add(path);
    }
  }

  for (const entry of candidates) {
    const { path } = entry;
    if (invalidRetainedPaths.has(path)) continue;
    if (entry.stage !== 0) {
      refused.push({ path, reasonCode: 'UNRESOLVED_INDEX_ENTRY' });
      continue;
    }
    if (entry.mode === '120000') {
      refused.push({ path, reasonCode: 'TRACKED_SYMLINK' });
      continue;
    }
    if (entry.mode !== null && !['100644', '100755'].includes(entry.mode)) {
      refused.push({ path, reasonCode: 'UNSUPPORTED_INDEX_MODE' });
      continue;
    }

    const target = resolve(repository, path);
    if (!inside(repository, target)) {
      refused.push({ path, reasonCode: 'PATH_TRAVERSAL' });
      continue;
    }
    let content;
    try {
      content = readRegularFileSync(target);
    } catch (error) {
      refused.push({
        path,
        reasonCode: 'UNREADABLE_TRACKED_PATH',
        error: error instanceof Error ? error.message : String(error),
      });
      continue;
    }

    const occurrences = countNeedle(content, needle);
    if (occurrences === 0) continue;
    const classification = classifyDomainPath(path, {
      root: repository,
      content,
      retainedEvidence,
    });
    if (classification.category === 'refused') {
      refused.push(classification);
      continue;
    }
    rows.push({ ...classification, occurrences });
  }

  rows.sort((a, b) => compareText(a.path, b.path));
  refused.sort((a, b) => compareText(a.path, b.path));
  const select = (category) => rows.filter((row) => row.category === category);
  const firstParty = select('first_party_source');
  const generated = select('generated_projection');
  const frozen = select('frozen_record');
  const historical = select('historical_snapshot');
  const mirrors = select('provenance_mirror');
  const actionable = [...firstParty, ...generated].sort((a, b) => compareText(a.path, b.path));
  const retained = [...frozen, ...historical, ...mirrors].sort((a, b) =>
    compareText(a.path, b.path),
  );

  return {
    actionable: summary(actionable),
    all_policy_surface: summary(rows),
    first_party_source: summary(firstParty),
    frozen_record: summary(frozen),
    generated_projection: summary(generated),
    historical_snapshot: summary(historical),
    provenance_mirror: summary(mirrors),
    refused,
    retained: summary(retained),
    target_actionable_occurrences: 0,
  };
}

export function domainPolicyAllows(report) {
  return report.refused.length === 0 && report.actionable.occurrences === 0;
}
