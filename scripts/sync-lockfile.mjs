/**
 * sync-lockfile.mjs — content-pinning lockfile for the external plugin sync.
 *
 * THREAT MODEL: sources.yaml pins nothing — scripts/sync-external.mjs mirrors
 * each upstream's live default branch every Monday. A source vetted once at
 * listing silently absorbs every later upstream push, so a compromised or
 * rogue upstream author's next commit rides straight into the marketplace and
 * executes in users' agents.
 *
 * MITIGATION: sources.lock.json (repo root) records, per source, the upstream
 * commit the sync resolved plus a sha256 digest of every mirrored file. On
 * each sync run the engine diffs the freshly-cloned upstream content against
 * the lock BEFORE writing anything:
 *
 *   - new-source  → first sync of a human-listed source: mirror + record the
 *                   baseline (vetting-at-listing is the existing human gate).
 *   - unchanged   → mirror as today (no-op diffs).
 *   - drifted     → QUARANTINE: the source is skipped this run and the run is
 *                   flagged like a partial sync. The lock only advances via an
 *                   explicit --relock=<source> / --relock-all after a human
 *                   reviews the upstream diff.
 *
 * The lock file is deterministic (sorted keys, stable entry shape) so its git
 * diff IS the security review surface.
 *
 * This module is pure and testable: no I/O beyond reading/writing the lock
 * file at the path the caller passes. The sync engine (sync-external.mjs)
 * owns all cloning/mirroring; the one-time baseline bootstrap is documented
 * in the PR that introduced this file.
 *
 * Tests: node --test scripts/sync-lockfile.test.mjs
 */

import fs from 'fs';
import crypto from 'crypto';

export const LOCK_VERSION = 1;

export const LOCK_COMMENT =
  'Content-pinning lockfile for the sources.yaml mirrors (scripts/sync-external.mjs). ' +
  'Each entry pins one upstream source: the resolved upstream commit and a sha256 per mirrored file. ' +
  'The diff of this file is the security review surface — a drifted source is quarantined by the sync ' +
  'and only re-baselined via an explicit --relock=<source> / --relock-all after human review. ' +
  'Managed by scripts/sync-lockfile.mjs; do not hand-edit digests.';

/**
 * Digest a file's exact bytes. Returns "sha256:<hex>".
 */
export function computeFileDigest(buffer) {
  if (!Buffer.isBuffer(buffer)) {
    throw new TypeError('computeFileDigest expects a Buffer (exact bytes, not a decoded string)');
  }
  return `sha256:${crypto.createHash('sha256').update(buffer).digest('hex')}`;
}

/**
 * Build a lock entry for one source from its current upstream state.
 *
 * @param {{repo: string}} source        sources.yaml entry (only .repo is read)
 * @param {string|null} resolvedRef      upstream HEAD sha the sync resolved (null if unknown)
 * @param {Array<{path: string, sha256: string}>} currentFiles
 * @param {string} lockedAt              ISO timestamp of the baseline approval
 */
export function buildLockEntry(source, resolvedRef, currentFiles, lockedAt) {
  const files = {};
  for (const f of [...currentFiles].sort((a, b) => a.path.localeCompare(b.path))) {
    files[f.path] = f.sha256;
  }
  return {
    repo: source.repo,
    resolved_ref: resolvedRef ?? null,
    locked_at: lockedAt,
    files,
  };
}

/**
 * Load the lock file. A missing file yields an empty lock (every source then
 * classifies as new-source — the backward-compatible bootstrap path). A file
 * that EXISTS but cannot be parsed throws: fail closed rather than silently
 * treating a corrupted lock as "nothing is pinned".
 */
export function loadLock(lockPath) {
  if (!fs.existsSync(lockPath)) {
    return { $comment: LOCK_COMMENT, version: LOCK_VERSION, sources: {} };
  }
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(lockPath, 'utf8'));
  } catch (err) {
    throw new Error(
      `sources lock at ${lockPath} exists but is not valid JSON (${err.message}) — ` +
        'refusing to treat a corrupt lock as "unpinned". Fix or restore it from git.',
    );
  }
  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error(`sources lock at ${lockPath} must be a JSON object`);
  }
  // A present `sources` field that is not a JSON object (array, string, null)
  // must fail closed. Silently defaulting to `{}` would classify every pinned
  // source as new-source and re-baseline the whole lock — exactly the drift
  // quarantine bypass this file exists to prevent. An ABSENT `sources` field is
  // still fine (the empty-lock bootstrap path).
  if (
    parsed.sources !== undefined &&
    (parsed.sources === null || typeof parsed.sources !== 'object' || Array.isArray(parsed.sources))
  ) {
    throw new Error(
      `sources lock at ${lockPath} has an invalid "sources" field (must be a JSON object) — ` +
        'refusing to silently re-baseline every source. Fix or restore it from git.',
    );
  }
  return {
    $comment: typeof parsed.$comment === 'string' ? parsed.$comment : LOCK_COMMENT,
    version: typeof parsed.version === 'number' ? parsed.version : LOCK_VERSION,
    sources: parsed.sources ?? {},
  };
}

/**
 * Serialize a lock object deterministically: fixed top-level key order,
 * source names sorted, per-entry key order fixed (repo, resolved_ref,
 * locked_at, files), file paths sorted. Insertion order never leaks into the
 * output, so the git diff of the file is stable and reviewable.
 */
export function serializeLock(lock) {
  const out = {
    $comment: lock.$comment ?? LOCK_COMMENT,
    version: lock.version ?? LOCK_VERSION,
    sources: {},
  };
  const sources = lock.sources || {};
  for (const name of Object.keys(sources).sort()) {
    const e = sources[name] || {};
    const files = {};
    for (const p of Object.keys(e.files || {}).sort()) {
      files[p] = e.files[p];
    }
    out.sources[name] = {
      repo: e.repo,
      resolved_ref: e.resolved_ref ?? null,
      locked_at: e.locked_at,
      files,
    };
  }
  return JSON.stringify(out, null, 2) + '\n';
}

/**
 * Write the lock file (deterministic serialization). Skips the write when the
 * on-disk bytes are already identical, so an all-unchanged sync run does not
 * touch the file's mtime.
 */
export function saveLock(lockPath, lock) {
  const serialized = serializeLock(lock);
  if (fs.existsSync(lockPath)) {
    const existing = fs.readFileSync(lockPath, 'utf8');
    if (existing === serialized) return false;
  }
  fs.writeFileSync(lockPath, serialized);
  return true;
}

/**
 * Classify a source's freshly-fetched upstream content against the lock.
 *
 * @param {object} lock                  loaded lock object
 * @param {string} sourceName            sources.yaml `name`
 * @param {Array<{path: string, sha256: string}>} currentFiles
 * @returns {{status: 'unchanged'|'new-source'|'drifted', added: string[], removed: string[], changed: string[]}}
 */
export function diffSource(lock, sourceName, currentFiles) {
  const current = new Map(currentFiles.map((f) => [f.path, f.sha256]));
  const hasEntry =
    lock?.sources != null && Object.prototype.hasOwnProperty.call(lock.sources, sourceName);
  const entry = hasEntry ? lock.sources[sourceName] : null;

  // Only a genuinely ABSENT source is new. A source that is present in the lock
  // but whose entry is corrupt (missing/invalid `files`) must fail closed — not
  // be silently treated as new-source, which would re-baseline it and skip the
  // drift quarantine.
  if (!hasEntry) {
    return {
      status: 'new-source',
      added: [...current.keys()].sort(),
      removed: [],
      changed: [],
    };
  }

  if (!entry || !entry.files || typeof entry.files !== 'object' || Array.isArray(entry.files)) {
    throw new Error(
      `lock entry for source "${sourceName}" is corrupt or malformed (missing/invalid "files") — ` +
        'refusing to silently re-baseline it as a new source.',
    );
  }

  const locked = entry.files;
  const added = [];
  const removed = [];
  const changed = [];

  for (const [p, digest] of current) {
    if (!(p in locked)) {
      added.push(p);
    } else if (locked[p] !== digest) {
      changed.push(p);
    }
  }
  for (const p of Object.keys(locked)) {
    if (!current.has(p)) removed.push(p);
  }

  added.sort();
  removed.sort();
  changed.sort();

  const status = added.length + removed.length + changed.length === 0 ? 'unchanged' : 'drifted';
  return { status, added, removed, changed };
}
