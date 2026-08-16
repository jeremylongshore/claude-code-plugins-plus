import { execFileSync } from 'node:child_process';
import { lstatSync, readFileSync, realpathSync } from 'node:fs';
import { dirname, isAbsolute, relative, resolve, sep } from 'node:path';

import { artifactRegistration } from './generated-artifact-registry.mjs';
import { resolvePluginProvenance } from './plugin-provenance.mjs';

export const DEAD_DOMAIN = ['claudecode', 'plugins.io'].join('');
export const LIVE_DOMAIN = 'tonsofskills.com';

export function replaceDeadDomain(value) {
  return String(value).replace(new RegExp(DEAD_DOMAIN.replace('.', '\\.'), 'gi'), LIVE_DOMAIN);
}

export function normalizeDeadDomainValue(value) {
  if (typeof value === 'string') return replaceDeadDomain(value);
  if (Array.isArray(value)) return value.map((item) => normalizeDeadDomainValue(item));
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, normalizeDeadDomainValue(item)]),
    );
  }
  return value;
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

export function isGeneratedDomainProjection(candidate) {
  return artifactRegistration(normalizeDomainPath(candidate))?.kind === 'generated_projection';
}

export function classifyDomainPath(candidate, { root = process.cwd(), content = null } = {}) {
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
      frozenContent ??= readFileSync(resolve(root, path), 'utf8');
    } catch (error) {
      return {
        category: 'refused',
        path,
        reasonCode: 'UNREADABLE_FROZEN_RECORD',
        error: error instanceof Error ? error.message : String(error),
      };
    }
    if (
      !frozenContent.startsWith('<!-- doc-class: frozen -->\n') ||
      !/^> \*\*SUPERSEDED–FROZEN \(/m.test(frozenContent)
    ) {
      return { category: 'refused', path, reasonCode: 'INVALID_FROZEN_RECORD_MARKER' };
    }
    return { category: 'frozen_record', path, reasonCode: 'FROZEN_6767_RECORD' };
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

  const registration = artifactRegistration(path);
  if (registration?.kind === 'historical_snapshot') {
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

export function scanDeadDomainPolicy({ root = process.cwd(), paths } = {}) {
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
  const needle = Buffer.from(DEAD_DOMAIN, 'utf8');
  const rows = [];
  const refused = [];

  for (const entry of candidates) {
    const { path } = entry;
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
    let metadata;
    let content;
    try {
      metadata = lstatSync(target);
      if (metadata.isSymbolicLink() || !metadata.isFile()) {
        refused.push({ path, reasonCode: 'UNREADABLE_TRACKED_PATH' });
        continue;
      }
      content = readFileSync(target);
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
      content: content.toString('utf8'),
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
