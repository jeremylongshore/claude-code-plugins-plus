import fs from 'node:fs';
import path from 'node:path';

const SOURCE_FILE = '.source.json';

function inside(root, candidate) {
  const relative = path.relative(root, candidate);
  return (
    relative === '' ||
    (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative))
  );
}

export function parseSourceRecord(
  recordPath,
  { lstat = fs.lstatSync, readFile = fs.readFileSync } = {},
) {
  let metadata;
  try {
    metadata = lstat(recordPath);
  } catch (error) {
    return {
      status: 'refused',
      reasonCode: 'UNREADABLE_SOURCE_RECORD',
      markerPath: recordPath,
      error: error instanceof Error ? error.message : String(error),
    };
  }
  if (metadata.isSymbolicLink()) {
    return { status: 'refused', reasonCode: 'SOURCE_RECORD_SYMLINK', markerPath: recordPath };
  }
  if (!metadata.isFile()) {
    return { status: 'refused', reasonCode: 'SOURCE_RECORD_NOT_REGULAR', markerPath: recordPath };
  }

  let raw;
  try {
    raw = readFile(recordPath, 'utf8');
  } catch (error) {
    return {
      status: 'refused',
      reasonCode: 'UNREADABLE_SOURCE_RECORD',
      markerPath: recordPath,
      error: error instanceof Error ? error.message : String(error),
    };
  }

  let value;
  try {
    value = JSON.parse(raw);
  } catch (error) {
    return {
      status: 'refused',
      reasonCode: 'MALFORMED_SOURCE_RECORD',
      markerPath: recordPath,
      error: error instanceof Error ? error.message : String(error),
    };
  }

  const upstream = value?.synced_from;
  if (
    !upstream ||
    typeof upstream !== 'object' ||
    typeof upstream.repo !== 'string' ||
    upstream.repo.length === 0 ||
    typeof upstream.path !== 'string' ||
    upstream.path.length === 0
  ) {
    return {
      status: 'refused',
      reasonCode: 'CONTRADICTORY_SOURCE_RECORD',
      markerPath: recordPath,
    };
  }

  return {
    status: 'mirror',
    reasonCode: 'UPSTREAM_SOURCE_RECORD',
    markerPath: recordPath,
    upstream: {
      repo: upstream.repo,
      path: upstream.path,
      branch: typeof upstream.branch === 'string' ? upstream.branch : null,
    },
  };
}

/**
 * Resolve provenance by walking the candidate directory and its real
 * filesystem ancestors. A source record is an exclusion boundary; it is not
 * inferred from names, package scopes, or directory categories.
 */
export function resolvePluginProvenance(candidateDir, { root = process.cwd() } = {}) {
  const rootPath = fs.realpathSync(path.resolve(root));
  const candidateAbsolute = path.resolve(rootPath, candidateDir);
  if (!inside(rootPath, candidateAbsolute)) {
    return { status: 'refused', reasonCode: 'PATH_TRAVERSAL', candidateDir: String(candidateDir) };
  }
  let candidatePath;
  try {
    candidatePath = fs.realpathSync(candidateAbsolute);
  } catch (error) {
    return {
      status: 'refused',
      reasonCode: 'UNREADABLE_CANDIDATE_PATH',
      candidateDir: String(candidateDir),
      error: error instanceof Error ? error.message : String(error),
    };
  }
  if (!inside(rootPath, candidatePath)) {
    return { status: 'refused', reasonCode: 'PATH_TRAVERSAL', candidateDir: String(candidateDir) };
  }

  let current = candidatePath;
  while (inside(rootPath, current)) {
    const markerPath = path.join(current, SOURCE_FILE);
    if (fs.existsSync(markerPath)) return parseSourceRecord(markerPath);
    if (current === rootPath) break;
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }

  return { status: 'first-party', reasonCode: 'NO_UPSTREAM_SOURCE_RECORD' };
}

export function isPathInside(root, candidate) {
  return inside(path.resolve(root), path.resolve(candidate));
}
