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
  {
    lstat = fs.lstatSync,
    open = fs.openSync,
    fstat = fs.fstatSync,
    readFile = fs.readFileSync,
    close = fs.closeSync,
    allowAbsent = false,
  } = {},
) {
  let raw;
  let descriptor;
  try {
    const noFollow = Number.isInteger(fs.constants.O_NOFOLLOW) ? fs.constants.O_NOFOLLOW : 0;
    descriptor = open(recordPath, fs.constants.O_RDONLY | noFollow);
    const openedMetadata = fstat(descriptor);
    const pathMetadata = lstat(recordPath);
    if (pathMetadata.isSymbolicLink()) {
      return { status: 'refused', reasonCode: 'SOURCE_RECORD_SYMLINK', markerPath: recordPath };
    }
    if (!pathMetadata.isFile() || !openedMetadata.isFile()) {
      return { status: 'refused', reasonCode: 'SOURCE_RECORD_NOT_REGULAR', markerPath: recordPath };
    }
    if (pathMetadata.dev !== openedMetadata.dev || pathMetadata.ino !== openedMetadata.ino) {
      throw new Error('source record changed while it was being opened');
    }
    raw = readFile(descriptor, 'utf8');
  } catch (error) {
    if (error && typeof error === 'object' && error.code === 'ELOOP') {
      return { status: 'refused', reasonCode: 'SOURCE_RECORD_SYMLINK', markerPath: recordPath };
    }
    // Absence is authoritative only when the initial open failed. Once a
    // descriptor exists, any path lookup/read ENOENT is a concurrent mutation
    // and must fail closed.
    if (
      error &&
      typeof error === 'object' &&
      error.code === 'ENOENT' &&
      allowAbsent &&
      descriptor === undefined
    ) {
      try {
        const pathMetadata = lstat(recordPath);
        if (pathMetadata.isSymbolicLink()) {
          return { status: 'refused', reasonCode: 'SOURCE_RECORD_SYMLINK', markerPath: recordPath };
        }
        return {
          status: 'refused',
          reasonCode: 'UNREADABLE_SOURCE_RECORD',
          markerPath: recordPath,
          error: 'source record appeared after the open attempt',
        };
      } catch (metadataError) {
        if (metadataError && typeof metadataError === 'object' && metadataError.code === 'ENOENT') {
          return { status: 'absent', reasonCode: 'NO_SOURCE_RECORD_AT_PATH' };
        }
        return {
          status: 'refused',
          reasonCode: 'UNREADABLE_SOURCE_RECORD',
          markerPath: recordPath,
          error: metadataError instanceof Error ? metadataError.message : String(metadataError),
        };
      }
    }
    return {
      status: 'refused',
      reasonCode: 'UNREADABLE_SOURCE_RECORD',
      markerPath: recordPath,
      error: error instanceof Error ? error.message : String(error),
    };
  } finally {
    if (descriptor !== undefined) close(descriptor);
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
    // Open first, then distinguish genuine absence from a dangling symlink.
    // This avoids metadata-check/file-use races while ensuring every
    // marker-shaped entry reaches fail-closed parsing.
    const provenance = parseSourceRecord(markerPath, { allowAbsent: true });
    if (provenance.status !== 'absent') return provenance;
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
