/**
 * crypto.ts — Ed25519 audit-signing primitives (ccsc-22l).
 *
 * Journal v2 signs every event with Ed25519 over RFC 8785 JCS canonical
 * bytes. This module owns the keypair shape, key loading from
 * SOPS-encrypted YAML, key generation, and sign/verify primitives.
 *
 * Why Ed25519: RFC 8032 standard, 32-byte private seed, 32-byte public
 * key, 64-byte signature. Bun/Node both support it natively via
 * `node:crypto` — no third-party dependency added.
 *
 * Why a separate module: the journal writer needs the sign primitive but
 * MUST NOT know about key storage. The server's boot path owns the key
 * loading (SOPS decrypt → /dev/shm → into memory → unlink) and passes
 * the resulting keypair to the writer. Tests inject keypairs directly.
 *
 * What this module does NOT do:
 *   - Spawn `sops` as a child process. That lives in server.ts where
 *     boot-path orchestration belongs. This module accepts pre-decrypted
 *     YAML text (or a raw key object) and parses it.
 *   - Persist keys to disk. Key generation returns the keypair; the
 *     caller writes the SOPS-encrypted file.
 *   - Manage rotation. Rotation events are journal-level (system.key_
 *     rotation) — this module just provides the sign/verify primitives.
 *
 * See 000-docs/key-management.md for the operational doc and
 * 000-docs/audit-journal-architecture.md § signed events for the
 * verifier contract.
 */

import { createPrivateKey, createPublicKey, randomBytes, sign as nodeSign, verify as nodeVerify } from 'node:crypto'

// ---------------------------------------------------------------------------
// Ed25519KeyPair — the in-memory key shape
// ---------------------------------------------------------------------------

/** Ed25519 keypair held in memory. The `seed` is the 32-byte private
 *  key material; the `publicKey` is the 32-byte derived public key.
 *  Both are stored as base64-encoded strings to match the SOPS YAML
 *  file format and to make logging accidents less catastrophic (a
 *  base64 leak is no worse than a raw-bytes leak, but it does NOT
 *  inadvertently include bytes that might be confused for ASCII).
 *
 *  Carry these as a unit: anywhere the private key flows, the public
 *  key flows alongside so callers can verify their own writes without
 *  a second round-trip to load the public half.
 */
export interface Ed25519KeyPair {
  /** 32-byte private seed, base64-encoded (44 chars). */
  seed: string
  /** 32-byte public key, base64-encoded (44 chars). */
  publicKey: string
  /** ISO-8601 timestamp from when the keypair was generated. Carried
   *  in the SOPS YAML so the rotation cadence (per key-management.md)
   *  can be checked at any time. */
  createdAt: string
}

// ---------------------------------------------------------------------------
// Key generation
// ---------------------------------------------------------------------------

/** Generate a fresh Ed25519 keypair using a cryptographically secure
 *  random seed. The seed never leaves this function uncovered — the
 *  caller receives a finished `Ed25519KeyPair` with both halves
 *  derived.
 *
 *  Implementation note: we generate the seed ourselves rather than
 *  using `generateKeyPairSync('ed25519')` so the seed is the same shape
 *  the SOPS YAML stores (raw 32 bytes). The Node generator returns
 *  PKCS#8 / SPKI DER blobs which are more cumbersome to round-trip. */
export function generateKeyPair(): Ed25519KeyPair {
  const seed = randomBytes(32)
  const seedB64 = seed.toString('base64')
  const publicKey = derivePublicKey(seedB64)
  return {
    seed: seedB64,
    publicKey,
    createdAt: new Date().toISOString(),
  }
}

// ---------------------------------------------------------------------------
// Key loading / serialization
// ---------------------------------------------------------------------------

/** Parse a SOPS-decrypted YAML text into an `Ed25519KeyPair`. The YAML
 *  contains:
 *
 *    seed: <base64>
 *    public_key: <base64>     # optional — re-derived if absent
 *    created_at: <iso-8601>
 *    purpose: <string>         # informational; not validated
 *
 *  Validates:
 *    - `seed` is exactly 32 bytes when base64-decoded
 *    - `public_key`, if present, matches the seed's derived public key
 *      (mismatch is a tamper signal — refuse to load)
 *    - `created_at` parses as a valid date
 *
 *  Throws on any validation failure. Callers should treat the throw as
 *  a boot-blocking error (the audit log is non-functional without a
 *  valid signing key, unless `--no-audit-signing` was passed). */
export function parseKeyPairYaml(yamlText: string): Ed25519KeyPair {
  // Minimal YAML parser sufficient for our flat key:value file. We
  // intentionally do NOT pull in a full YAML library — this file is
  // engineer-authored, never user input, and the SOPS roundtrip
  // produces a stable shape.
  const fields = new Map<string, string>()
  for (const rawLine of yamlText.split('\n')) {
    const line = rawLine.trim()
    if (line === '' || line.startsWith('#')) continue
    const colonIdx = line.indexOf(':')
    if (colonIdx <= 0) continue
    const key = line.slice(0, colonIdx).trim()
    let value = line.slice(colonIdx + 1).trim()
    // Strip trailing inline comments. Defensive — the SOPS round-trip
    // doesn't emit comments, but engineer-edited files sometimes do
    // (e.g., `seed: <base64> # rotation 2026-08-15`) and the comment
    // would otherwise break base64 / date parsing downstream.
    const hashIdx = value.indexOf('#')
    if (hashIdx >= 0) {
      value = value.slice(0, hashIdx).trim()
    }
    value = value.replace(/^["']|["']$/g, '')
    fields.set(key, value)
  }

  const seed = fields.get('seed')
  if (seed === undefined) {
    throw new Error('parseKeyPairYaml: missing required field `seed`')
  }
  const decodedSeed = Buffer.from(seed, 'base64')
  if (decodedSeed.length !== 32) {
    throw new Error(
      `parseKeyPairYaml: seed must be exactly 32 bytes when base64-decoded (got ${decodedSeed.length})`,
    )
  }

  const createdAt = fields.get('created_at') ?? fields.get('createdAt')
  if (createdAt === undefined) {
    throw new Error('parseKeyPairYaml: missing required field `created_at`')
  }
  if (Number.isNaN(Date.parse(createdAt))) {
    throw new Error(`parseKeyPairYaml: created_at is not a valid date (${createdAt})`)
  }

  const derivedPub = derivePublicKey(seed)
  const declaredPub = fields.get('public_key') ?? fields.get('publicKey')
  if (declaredPub !== undefined && declaredPub !== derivedPub) {
    throw new Error(
      'parseKeyPairYaml: declared public_key does not match seed-derived public key — possible key tampering, refusing to load',
    )
  }

  return { seed, publicKey: derivedPub, createdAt }
}

/** Serialize an `Ed25519KeyPair` to YAML for SOPS encryption. The
 *  output deliberately includes the public key (redundant — derivable
 *  from seed) so a partial parse can fail loudly if the two disagree
 *  (tamper detection per `parseKeyPairYaml`). */
export function serializeKeyPairYaml(kp: Ed25519KeyPair, purpose: string): string {
  return [
    `seed: ${kp.seed}`,
    `public_key: ${kp.publicKey}`,
    `created_at: ${kp.createdAt}`,
    `purpose: ${purpose}`,
    '',
  ].join('\n')
}

// ---------------------------------------------------------------------------
// Sign / verify primitives
// ---------------------------------------------------------------------------

/** Sign the given canonical bytes with `kp`'s private key. Returns a
 *  base64-encoded 64-byte Ed25519 signature (88 chars with padding).
 *
 *  Input: arbitrary bytes — typically `Buffer.from(canonicalJson(event), 'utf8')`.
 *  Output: deterministic — Ed25519 signing is deterministic by spec
 *  (RFC 8032 §5.1.6), so the same input + key always produces the same
 *  signature. The journal's hash chain plus deterministic signatures
 *  means a verifier can confirm bit-for-bit that the published file is
 *  exactly what the writer produced. */
export function signBytes(canonicalBytes: Buffer | Uint8Array, kp: Ed25519KeyPair): string {
  const privateKey = createPrivateKey({
    key: buildPkcs8FromSeed(kp.seed),
    format: 'der',
    type: 'pkcs8',
  })
  const sig = nodeSign(null, canonicalBytes, privateKey)
  return sig.toString('base64')
}

/** Verify an Ed25519 signature. Returns `true` only when the signature
 *  was produced by the private key corresponding to `publicKey` over
 *  the given canonical bytes. Returns `false` on any mismatch — never
 *  throws on a bad signature (the caller treats `false` as a tamper
 *  signal, not an error). Throws only on malformed input (non-base64
 *  signature, non-base64 public key, wrong-length public key). */
export function verifySignatureBytes(
  canonicalBytes: Buffer | Uint8Array,
  signatureB64: string,
  publicKeyB64: string,
): boolean {
  const pubBytes = Buffer.from(publicKeyB64, 'base64')
  if (pubBytes.length !== 32) {
    throw new Error(
      `verifySignatureBytes: public key must be exactly 32 bytes when base64-decoded (got ${pubBytes.length})`,
    )
  }
  const sigBytes = Buffer.from(signatureB64, 'base64')
  if (sigBytes.length !== 64) {
    // Wrong-length signature is not a tamper-vs-corruption distinction
    // we can make at this layer. Return false (the verifier's normal
    // "this signature didn't verify" path) rather than throw — keeps
    // verifyJournal's error handling uniform.
    return false
  }

  const publicKey = createPublicKey({
    key: buildSpkiFromPublicKey(publicKeyB64),
    format: 'der',
    type: 'spki',
  })
  return nodeVerify(null, canonicalBytes, publicKey, sigBytes)
}

// ---------------------------------------------------------------------------
// Internal helpers — PKCS#8 / SPKI DER wrapping for Node's crypto
// ---------------------------------------------------------------------------

// Node's `crypto.sign(null, data, key)` requires a KeyObject — it
// cannot consume raw 32-byte Ed25519 material directly. We wrap the
// seed/public bytes in the minimal PKCS#8 / SPKI DER envelopes Node
// expects. These prefixes are spec-fixed (RFC 8410):
//
//   PKCS#8 Ed25519 private key:
//     30 2e 02 01 00 30 05 06 03 2b 65 70 04 22 04 20 <32-byte seed>
//
//   SPKI Ed25519 public key:
//     30 2a 30 05 06 03 2b 65 70 03 21 00 <32-byte public>

const PKCS8_ED25519_PREFIX = Buffer.from('302e020100300506032b657004220420', 'hex')
const SPKI_ED25519_PREFIX = Buffer.from('302a300506032b6570032100', 'hex')

function buildPkcs8FromSeed(seedB64: string): Buffer {
  const seed = Buffer.from(seedB64, 'base64')
  if (seed.length !== 32) {
    throw new Error(`buildPkcs8FromSeed: seed must be exactly 32 bytes (got ${seed.length})`)
  }
  return Buffer.concat([PKCS8_ED25519_PREFIX, seed])
}

function buildSpkiFromPublicKey(publicKeyB64: string): Buffer {
  const pub = Buffer.from(publicKeyB64, 'base64')
  if (pub.length !== 32) {
    throw new Error(
      `buildSpkiFromPublicKey: public key must be exactly 32 bytes (got ${pub.length})`,
    )
  }
  return Buffer.concat([SPKI_ED25519_PREFIX, pub])
}

/** Derive the public-key half of an Ed25519 keypair from its seed.
 *  Used by key generation and by the YAML parser's tamper check. */
export function derivePublicKey(seedB64: string): string {
  const privateKey = createPrivateKey({
    key: buildPkcs8FromSeed(seedB64),
    format: 'der',
    type: 'pkcs8',
  })
  const pubKeyDer = createPublicKey(privateKey).export({ format: 'der', type: 'spki' })
  // SPKI prefix is 12 bytes; strip it to get the raw 32-byte public key.
  // Verify the prefix bytes match the expected Ed25519 SPKI envelope
  // before slicing — guards against future Node crypto API changes
  // that might return a different DER framing. Without this check, a
  // changed framing would silently return wrong bytes that "verify"
  // against signatures produced by the same wrong-bytes path,
  // breaking interop with every other RFC 8032 implementation.
  if (!pubKeyDer.subarray(0, SPKI_ED25519_PREFIX.length).equals(SPKI_ED25519_PREFIX)) {
    throw new Error(
      'derivePublicKey: exported SPKI does not match expected Ed25519 prefix (RFC 8410)',
    )
  }
  const rawPub = pubKeyDer.subarray(SPKI_ED25519_PREFIX.length)
  if (rawPub.length !== 32) {
    throw new Error(
      `derivePublicKey: expected 32-byte public key, got ${rawPub.length} (SPKI parse failed)`,
    )
  }
  return rawPub.toString('base64')
}
