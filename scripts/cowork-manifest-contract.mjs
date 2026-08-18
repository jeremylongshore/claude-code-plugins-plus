import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';

/**
 * Verify the checksum contract emitted by build-cowork-zips.mjs.
 * The producer's field is deliberately named `checksum`; accepting aliases
 * would allow a schema drift to make verification a no-op.
 */
export function verifyCoworkChecksum(filePath, entry, label = 'artifact') {
  if (!entry || typeof entry.checksum !== 'string' || !/^[0-9a-f]{64}$/.test(entry.checksum)) {
    return { ok: false, reason: `${label} is missing a valid checksum` };
  }
  const actual = createHash('sha256').update(readFileSync(filePath)).digest('hex');
  return actual === entry.checksum
    ? { ok: true, actual }
    : { ok: false, reason: `${label} checksum mismatch`, actual };
}
