/**
 * audit-key-cli.ts — Operator CLI for the audit-signing keypair
 * lifecycle: `ccsc audit-key init` and `ccsc audit-key rotate`
 * (ccsc-l1f).
 *
 * Sibling-module pattern: pure async functions + injectable
 * dependencies. Tests exercise the orchestration logic with mock
 * filesystem and mock subprocess; production wires `node:fs`,
 * `child_process.execFile`, and the real `JournalWriter`.
 *
 * Two commands, per 000-docs/key-management.md:
 *
 *   init  — Generate a fresh Ed25519 keypair, SOPS-encrypt it,
 *           write atomically to the canonical key path. Refuses
 *           to overwrite an existing file (one-shot per state dir;
 *           operator must explicitly `rotate` to replace).
 *
 *   rotate — Load current key, generate new key, write one final
 *           `system.key_rotation` event to the audit log under
 *           the OLD key (carrying both old + new public keys + a
 *           rotation reason). Atomically archive the old encrypted
 *           file and swap in the new one. The verifier picks up
 *           the new key automatically from the rotation event.
 *
 * Operator workflow per 000-docs/key-management.md §94:
 *
 *   1. Run `ccsc audit-key init` (or `rotate`).
 *   2. Copy the printed public key.
 *   3. `pass insert -e intentsolutions/ccsc/audit-pubkey`, paste.
 *   4. Update the external gist with the new public key.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import type { Ed25519KeyPair } from './crypto.ts'
import type { JournalWriter, WriterOptions } from './journal.ts'

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Default purpose string written into the YAML's `purpose:` field. */
export const DEFAULT_PURPOSE = 'claude-code-slack-channel audit-journal v2 signing'

/** Default canonical key path. Matches DEFAULT_AUDIT_KEY_PATH in
 *  audit-key-loader.ts (sibling module — the loader expands `~/`
 *  the same way; here the CLI receives the already-expanded
 *  absolute path from `scripts/audit-key.ts`). */
export const DEFAULT_KEY_BASENAME = 'audit.key.sops.yaml'

/** Default audit log basename — sibling of the key in the state dir. */
export const DEFAULT_JOURNAL_BASENAME = 'audit.log'

/** Valid rotation reasons. The verifier doesn't check these (they
 *  are forensic metadata), but the CLI enforces an enum so future
 *  log readers can rely on a closed vocabulary. */
export const ROTATION_REASONS = [
  'scheduled-90day',
  'compromise-suspected',
  'operator-initiated',
] as const

export type RotationReason = (typeof ROTATION_REASONS)[number]

// ---------------------------------------------------------------------------
// Result type
// ---------------------------------------------------------------------------

/** Structured CLI outcome. Tests assert on this shape; the
 *  production runner translates `code` to `process.exit`. */
export type CliResult =
  | { kind: 'ok'; code: 0; publicKey?: string; archivePath?: string; message: string }
  | { kind: 'error'; code: number; message: string }

// ---------------------------------------------------------------------------
// Dependency injection
// ---------------------------------------------------------------------------

/** All side-effecting operations the CLI performs go through this
 *  interface. Production: wires `node:fs/promises`, `child_process`,
 *  and the real `JournalWriter`. Tests: mock everything; no actual
 *  sops subprocess, no actual filesystem touches outside tmpDir. */
export interface AuditKeyCliDeps {
  // ----- crypto (re-export of crypto.ts; injectable for determinism in tests) -----
  generateKeyPair: () => Ed25519KeyPair
  serializeKeyPairYaml: (kp: Ed25519KeyPair, purpose: string) => string
  parseKeyPairYaml: (text: string) => Ed25519KeyPair

  // ----- filesystem -----
  fileExists: (path: string) => boolean
  /** Writes plaintext content to a path with mode 0o600. Must
   *  fsync before returning so a crash between this and the
   *  sops-encrypt step leaves a flush-consistent plaintext that
   *  the cleanup path can find + unlink. */
  writeTempPlain: (path: string, content: string) => Promise<void>
  /** Run `sops --encrypt --in-place <path>`. Throws on subprocess
   *  failure (missing .sops.yaml config, no recipient configured,
   *  age key not in keyring, etc.). Production uses execFile in
   *  argv mode. */
  encryptInPlace: (path: string) => Promise<void>
  /** Atomic rename. Production: `fs/promises.rename`. */
  renameAtomic: (from: string, to: string) => Promise<void>
  /** Decrypt a SOPS-encrypted file. Production: spawns `sops -d`
   *  via execFile (mirrors audit-key-loader.ts:defaultSopsSpawn). */
  decryptFile: (path: string) => Promise<string>
  /** Unconditional unlink that tolerates ENOENT. Used for cleanup
   *  in the init failure path (a half-written plaintext temp must
   *  not survive). */
  unlinkIfExists: (path: string) => Promise<void>

  // ----- journal -----
  /** Open a JournalWriter for one event then close. The CLI uses
   *  this exactly twice during rotate (open → writeEvent → close)
   *  and not at all during init. */
  openJournalWriter: (opts: WriterOptions) => Promise<JournalWriter>

  // ----- I/O -----
  /** ISO timestamp source for archive filenames. Default: Date.now. */
  now: () => number
  log: (msg: string) => void
  errLog: (msg: string) => void
}

// ---------------------------------------------------------------------------
// init — generate + encrypt + atomic rename
// ---------------------------------------------------------------------------

export interface AuditKeyInitOpts {
  /** Absolute path to the SOPS-encrypted key file. The temp
   *  plaintext lives at `${keyPath}.tmp` in the same dir so SOPS
   *  picks up the colocated `.sops.yaml` recipient config. */
  keyPath: string
  /** Override the purpose string in the YAML. Defaults to
   *  DEFAULT_PURPOSE. Tests use shorter strings. */
  purpose?: string
}

/** Generate a fresh keypair and write it SOPS-encrypted to keyPath.
 *
 *  Pipeline:
 *    1. Refuse if keyPath already exists (per design doc §98-100).
 *    2. Generate Ed25519 keypair.
 *    3. Serialize to YAML.
 *    4. Write plaintext to `${keyPath}.tmp` (mode 0o600).
 *    5. `sops --encrypt --in-place ${keyPath}.tmp` (file becomes
 *       SOPS-encrypted in place; same path).
 *    6. Atomic rename `${keyPath}.tmp` → `${keyPath}`.
 *    7. Print the public key to the operator for gist + pass.
 *
 *  Failure cleanup: if any step after step 4 throws, the temp
 *  file is unlinked in the finally so plaintext doesn't survive
 *  on disk past the CLI process. Step-3 failure leaves nothing
 *  on disk to clean.
 */
export async function auditKeyInit(
  opts: AuditKeyInitOpts,
  deps: AuditKeyCliDeps,
): Promise<CliResult> {
  const purpose = opts.purpose ?? DEFAULT_PURPOSE
  const tmpPath = `${opts.keyPath}.tmp`

  // Step 1: refuse overwrite. The design doc is explicit — init is
  // one-shot per state dir. Operator must `rotate` to replace.
  if (deps.fileExists(opts.keyPath)) {
    return {
      kind: 'error',
      code: 1,
      message:
        `Refusing to overwrite existing key at ${opts.keyPath}. ` +
        `Run \`ccsc audit-key rotate\` to replace it (preserves audit-log verifiability).`,
    }
  }

  // Defensive: a leftover tmp from an interrupted prior run would
  // confuse the sops-encrypt step. Refuse and ask the operator to
  // resolve manually — a stale tmp might be plaintext key material
  // an operator forgot about, not safe to silently overwrite.
  if (deps.fileExists(tmpPath)) {
    return {
      kind: 'error',
      code: 1,
      message:
        `Found stale temp file at ${tmpPath} from a prior interrupted run. ` +
        `Manually verify its contents and remove it before re-running init.`,
    }
  }

  // Step 2 + 3: generate + serialize.
  const kp = deps.generateKeyPair()
  const yamlText = deps.serializeKeyPairYaml(kp, purpose)

  // Steps 4-6 with cleanup guard.
  try {
    await deps.writeTempPlain(tmpPath, yamlText)
    await deps.encryptInPlace(tmpPath)
    await deps.renameAtomic(tmpPath, opts.keyPath)
  } catch (err) {
    // Cleanup: unlink the temp so plaintext doesn't survive.
    // Failure to unlink is logged but doesn't change the error
    // we report — the operator must resolve manually if cleanup
    // also failed.
    try {
      await deps.unlinkIfExists(tmpPath)
    } catch (cleanupErr) {
      deps.errLog(
        `WARNING: failed to clean up temp file ${tmpPath}: ${cleanupErr instanceof Error ? cleanupErr.message : String(cleanupErr)}. ` +
          `Verify and remove manually — it may contain plaintext key material.`,
      )
    }
    return {
      kind: 'error',
      code: 2,
      message: `audit-key init failed: ${err instanceof Error ? err.message : String(err)}`,
    }
  }

  // Step 7: announce success + print public key.
  deps.log(`Generated audit-signing keypair at ${opts.keyPath}.`)
  deps.log('')
  deps.log('Public key (base64, 44 chars):')
  deps.log(`  ${kp.publicKey}`)
  deps.log('')
  deps.log('Next steps (per 000-docs/key-management.md):')
  deps.log('  1. pass insert -e intentsolutions/ccsc/audit-pubkey   # paste public key above')
  deps.log('  2. Update the external gist with the new public key.')
  deps.log('  3. (Re)start the bridge — boot will pick up the new key automatically.')

  return {
    kind: 'ok',
    code: 0,
    publicKey: kp.publicKey,
    message: `Generated keypair at ${opts.keyPath}`,
  }
}

// ---------------------------------------------------------------------------
// rotate — write key_rotation event under OLD key + atomic swap
// ---------------------------------------------------------------------------

export interface AuditKeyRotateOpts {
  /** Path to the CURRENT SOPS-encrypted key file. Will be loaded,
   *  used to sign the rotation event, then archived. */
  keyPath: string
  /** Path to the audit log. The rotation event is appended here
   *  under the OLD key so the verifier can pick up the new key
   *  on its next walk. */
  journalPath: string
  /** Rotation reason — written into the event's input field for
   *  forensic visibility. */
  reason: RotationReason
  /** Operator must explicitly confirm the bridge is stopped. Two
   *  concurrent writers on the audit log would interleave bytes
   *  and corrupt the chain. JournalWriter's `ACTIVE_PATHS` set
   *  only protects against the same process; cross-process
   *  collision needs operator discipline. */
  confirmBridgeStopped: boolean
  /** Override purpose string. Defaults to DEFAULT_PURPOSE. */
  purpose?: string
}

/** Rotate the audit-signing keypair.
 *
 *  Pipeline:
 *    1. Refuse without --confirm-bridge-stopped (cross-process
 *       writer collision protection — see above).
 *    2. Refuse if current keyPath doesn't exist (rotate has
 *       nothing to rotate from; operator should run `init` first).
 *    3. Decrypt current keyPath via SOPS.
 *    4. Parse the YAML → currentKp.
 *    5. Generate new keypair → newKp.
 *    6. Open the existing audit log with currentKp as signingKey
 *       (the rotation event itself signs under the OLD key — the
 *       verifier requires this to confirm the rotation was
 *       authorized by the holder of the old private key).
 *    7. Write ONE event: kind=system.key_rotation, input contains
 *       old_public_key + new_public_key + rotation_reason.
 *    8. Close the writer.
 *    9. Write newKp YAML to ${keyPath}.new.tmp (plaintext, 0o600).
 *   10. sops --encrypt --in-place ${keyPath}.new.tmp.
 *   11. Archive old encrypted file: rename keyPath →
 *       keyPath.<unix-ts>.archived (per design doc §199-201).
 *   12. Atomic rename ${keyPath}.new.tmp → keyPath.
 *   13. Print new public key + archive path for operator.
 *
 *  Critical ordering: the rotation event is written under the OLD
 *  key BEFORE the file swap. If the swap fails partway, the audit
 *  log already records the intent — operator can recover by
 *  manually completing or reverting the swap. If the writeEvent
 *  fails, the swap doesn't happen and the operator is no worse
 *  off than before they started.
 */
export async function auditKeyRotate(
  opts: AuditKeyRotateOpts,
  deps: AuditKeyCliDeps,
): Promise<CliResult> {
  const purpose = opts.purpose ?? DEFAULT_PURPOSE
  const newTmpPath = `${opts.keyPath}.new.tmp`

  // Step 1: bridge-stopped confirmation.
  if (!opts.confirmBridgeStopped) {
    return {
      kind: 'error',
      code: 1,
      message:
        'Refusing to rotate without --confirm-bridge-stopped. ' +
        'A running bridge holds the audit log open in append mode; rotating concurrently ' +
        'would interleave bytes from two writers and corrupt the hash chain. ' +
        'Stop the bridge process, then re-run with --confirm-bridge-stopped.',
    }
  }

  // Step 2: refuse if no current key.
  if (!deps.fileExists(opts.keyPath)) {
    return {
      kind: 'error',
      code: 1,
      message:
        `No current key at ${opts.keyPath} to rotate. Run \`ccsc audit-key init\` first.`,
    }
  }

  // Cleanup guard: if a stale .new.tmp exists from a prior
  // interrupted rotate, refuse (same reasoning as init).
  if (deps.fileExists(newTmpPath)) {
    return {
      kind: 'error',
      code: 1,
      message:
        `Found stale temp file at ${newTmpPath} from a prior interrupted rotate. ` +
        `Manually verify its contents and remove it before re-running rotate.`,
    }
  }

  // Steps 3-4: decrypt + parse current.
  let currentKp: Ed25519KeyPair
  try {
    const currentYaml = await deps.decryptFile(opts.keyPath)
    currentKp = deps.parseKeyPairYaml(currentYaml)
  } catch (err) {
    return {
      kind: 'error',
      code: 2,
      message: `Failed to load current key: ${err instanceof Error ? err.message : String(err)}`,
    }
  }

  // Step 5: generate new.
  const newKp = deps.generateKeyPair()

  // Steps 6-8: write rotation event under OLD key.
  let writer: JournalWriter
  try {
    writer = await deps.openJournalWriter({
      path: opts.journalPath,
      signingKey: currentKp,
    })
  } catch (err) {
    return {
      kind: 'error',
      code: 2,
      message: `Failed to open audit log at ${opts.journalPath}: ${err instanceof Error ? err.message : String(err)}`,
    }
  }

  try {
    await writer.writeEvent({
      kind: 'system.key_rotation',
      outcome: 'allow',
      input: {
        old_public_key: currentKp.publicKey,
        new_public_key: newKp.publicKey,
        rotation_reason: opts.reason,
      },
    })
  } catch (err) {
    try {
      await writer.close()
    } catch {
      // Already failed; swallow close errors.
    }
    return {
      kind: 'error',
      code: 2,
      message: `Failed to write key_rotation event: ${err instanceof Error ? err.message : String(err)}`,
    }
  }

  try {
    await writer.close()
  } catch (err) {
    // The event already landed (writeEvent fsync'd). A close
    // failure is a resource leak in the calling process but
    // doesn't corrupt the journal. Log + proceed.
    deps.errLog(
      `WARNING: journal writer close failed (event was written successfully): ${err instanceof Error ? err.message : String(err)}`,
    )
  }

  // Steps 9-10: write new keypair to temp + encrypt.
  const newYaml = deps.serializeKeyPairYaml(newKp, purpose)
  try {
    await deps.writeTempPlain(newTmpPath, newYaml)
    await deps.encryptInPlace(newTmpPath)
  } catch (err) {
    try {
      await deps.unlinkIfExists(newTmpPath)
    } catch (cleanupErr) {
      deps.errLog(
        `WARNING: failed to clean up temp file ${newTmpPath}: ${cleanupErr instanceof Error ? cleanupErr.message : String(cleanupErr)}. ` +
          `Verify and remove manually — it may contain plaintext key material.`,
      )
    }
    return {
      kind: 'error',
      code: 3,
      message:
        `Rotation event WAS written to the audit log under the OLD key, but new-key ` +
        `encrypt failed: ${err instanceof Error ? err.message : String(err)}. ` +
        `The audit log now expects events under the NEW public key (${newKp.publicKey}) ` +
        `but the new key file was not written. Manual recovery required: either ` +
        `(a) re-run rotate with the same NEW seed to materialize the key file, or ` +
        `(b) accept that subsequent events cannot be signed and start a new chain ` +
        `(see 000-docs/key-management.md § Lost-key recovery).`,
    }
  }

  // Step 11: archive old.
  const archivePath = `${opts.keyPath}.${deps.now()}.archived`
  try {
    await deps.renameAtomic(opts.keyPath, archivePath)
  } catch (err) {
    try {
      await deps.unlinkIfExists(newTmpPath)
    } catch {
      // Cleanup attempt; we've already failed the primary op.
    }
    return {
      kind: 'error',
      code: 3,
      message: `Failed to archive old key file: ${err instanceof Error ? err.message : String(err)}`,
    }
  }

  // Step 12: swap in new.
  try {
    await deps.renameAtomic(newTmpPath, opts.keyPath)
  } catch (err) {
    // Roll back the archive step so the operator isn't left
    // with NO key file at all (we just successfully archived
    // the old one and now the new-key install failed).
    try {
      await deps.renameAtomic(archivePath, opts.keyPath)
    } catch {
      // Best-effort revert; the original error is what we report.
    }
    return {
      kind: 'error',
      code: 3,
      message:
        `Failed to install new key file: ${err instanceof Error ? err.message : String(err)}. ` +
        `Attempted to revert by restoring archive → keyPath.`,
    }
  }

  // Step 13: announce success.
  deps.log('Rotation complete.')
  deps.log('')
  deps.log(`  Reason:           ${opts.reason}`)
  deps.log(`  Old public key:   ${currentKp.publicKey}`)
  deps.log(`  New public key:   ${newKp.publicKey}`)
  deps.log(`  Old key archived: ${archivePath}`)
  deps.log('')
  deps.log('Audit log now expects events under the NEW key. The rotation event itself was')
  deps.log('signed under the OLD key — third-party verifiers will pick up the new key')
  deps.log('automatically when they encounter the system.key_rotation event.')
  deps.log('')
  deps.log('Next steps (per 000-docs/key-management.md):')
  deps.log('  1. pass insert -e intentsolutions/ccsc/audit-pubkey   # paste NEW public key')
  deps.log('  2. Update the external gist (add row to History table; update Current key).')
  deps.log('  3. Restart the bridge — boot will load the new key automatically.')

  return {
    kind: 'ok',
    code: 0,
    publicKey: newKp.publicKey,
    archivePath,
    message: `Rotated keypair at ${opts.keyPath}, archived at ${archivePath}`,
  }
}

// ---------------------------------------------------------------------------
// argv parser
// ---------------------------------------------------------------------------

export type ParsedAuditKeyCommand =
  | { command: 'init'; keyPath?: string; purpose?: string }
  | {
      command: 'rotate'
      keyPath?: string
      journalPath?: string
      reason?: RotationReason
      confirmBridgeStopped: boolean
      purpose?: string
    }
  | { command: 'help' }
  | { command: 'error'; message: string }

/** Parse argv for the audit-key CLI. Accepts subcommand-style
 *  invocation: `audit-key init [--key <path>]` or
 *  `audit-key rotate --reason=<...> --journal <path> [--key <path>] [--confirm-bridge-stopped]`.
 *
 *  Returns a discriminated union — callers (the runner) check
 *  `command` and dispatch. `error` is returned for malformed
 *  argv (unknown subcommand, missing required flag, invalid
 *  reason enum value).
 *
 *  The first arg should be the subcommand (init / rotate / help).
 *  Production callers pass `process.argv.slice(3)` after slicing
 *  off node/bun + script + the `audit-key` discriminator. */
export function parseAuditKeyArgv(argv: readonly string[]): ParsedAuditKeyCommand {
  if (argv.length === 0) return { command: 'help' }
  const sub = argv[0]
  if (sub === 'help' || sub === '--help' || sub === '-h') return { command: 'help' }

  if (sub === 'init') {
    const rest = argv.slice(1)
    let keyPath: string | undefined
    let purpose: string | undefined
    for (let i = 0; i < rest.length; i++) {
      const a = rest[i]!
      if (a === '--key') {
        keyPath = rest[++i]
      } else if (a.startsWith('--key=')) {
        keyPath = a.slice('--key='.length)
      } else if (a === '--purpose') {
        purpose = rest[++i]
      } else if (a.startsWith('--purpose=')) {
        purpose = a.slice('--purpose='.length)
      } else {
        return { command: 'error', message: `init: unknown argument ${a}` }
      }
    }
    return { command: 'init', keyPath, purpose }
  }

  if (sub === 'rotate') {
    const rest = argv.slice(1)
    let keyPath: string | undefined
    let journalPath: string | undefined
    let reason: RotationReason | undefined
    let purpose: string | undefined
    let confirmBridgeStopped = false
    for (let i = 0; i < rest.length; i++) {
      const a = rest[i]!
      if (a === '--key') {
        keyPath = rest[++i]
      } else if (a.startsWith('--key=')) {
        keyPath = a.slice('--key='.length)
      } else if (a === '--journal') {
        journalPath = rest[++i]
      } else if (a.startsWith('--journal=')) {
        journalPath = a.slice('--journal='.length)
      } else if (a === '--reason') {
        const value = rest[++i]
        if (value === undefined || !ROTATION_REASONS.includes(value as RotationReason)) {
          return {
            command: 'error',
            message: `rotate: --reason must be one of ${ROTATION_REASONS.join(', ')} (got ${value ?? 'undefined'})`,
          }
        }
        reason = value as RotationReason
      } else if (a.startsWith('--reason=')) {
        const value = a.slice('--reason='.length)
        if (!ROTATION_REASONS.includes(value as RotationReason)) {
          return {
            command: 'error',
            message: `rotate: --reason must be one of ${ROTATION_REASONS.join(', ')} (got ${value})`,
          }
        }
        reason = value as RotationReason
      } else if (a === '--confirm-bridge-stopped') {
        confirmBridgeStopped = true
      } else if (a === '--purpose') {
        purpose = rest[++i]
      } else if (a.startsWith('--purpose=')) {
        purpose = a.slice('--purpose='.length)
      } else {
        return { command: 'error', message: `rotate: unknown argument ${a}` }
      }
    }
    if (reason === undefined) {
      return {
        command: 'error',
        message: `rotate: --reason is required (one of ${ROTATION_REASONS.join(', ')})`,
      }
    }
    return { command: 'rotate', keyPath, journalPath, reason, confirmBridgeStopped, purpose }
  }

  return { command: 'error', message: `Unknown subcommand: ${sub}` }
}

// ---------------------------------------------------------------------------
// Help text
// ---------------------------------------------------------------------------

export const HELP_TEXT = `Usage:
  ccsc audit-key init [--key <path>] [--purpose <string>]
  ccsc audit-key rotate --reason <scheduled-90day|compromise-suspected|operator-initiated>
                       --confirm-bridge-stopped
                       [--key <path>] [--journal <path>] [--purpose <string>]

Commands:
  init     Generate a fresh Ed25519 keypair, SOPS-encrypt it, and write to the
           canonical key path. Refuses to overwrite an existing file. Print the
           public key for external pinning (pass + gist).

  rotate   Load current keypair, generate a new one, write one final
           system.key_rotation event to the audit log under the OLD key, then
           atomically archive the old encrypted file and swap in the new one.
           The verifier picks up the new key automatically on its next walk.

Defaults:
  --key      ~/.claude/channels/slack/audit.key.sops.yaml
  --journal  ~/.claude/channels/slack/audit.log
  --purpose  "${DEFAULT_PURPOSE}"

Bridge-stopped requirement:
  Rotate refuses without --confirm-bridge-stopped. A running bridge holds the
  audit log open in append mode; rotating concurrently would interleave bytes
  from two writers and corrupt the hash chain. Stop the bridge first.

Operator workflow (after either command):
  1. Copy the printed public key.
  2. pass insert -e intentsolutions/ccsc/audit-pubkey
  3. Update the external gist with the new public key.
  4. (Re)start the bridge.

See 000-docs/key-management.md for the full lifecycle, backup posture, and
lost-key recovery procedure.
`

// ---------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------

/** Top-level CLI runner. Parses argv, dispatches to init / rotate /
 *  help / error. Callers translate the returned CliResult.code to
 *  process.exit. Tests assert on the result shape directly. */
export async function runAuditKeyCli(
  argv: readonly string[],
  deps: AuditKeyCliDeps,
  defaults: { keyPath: string; journalPath: string },
): Promise<CliResult> {
  const parsed = parseAuditKeyArgv(argv)

  switch (parsed.command) {
    case 'help':
      deps.log(HELP_TEXT)
      return { kind: 'ok', code: 0, message: 'help displayed' }

    case 'error':
      deps.errLog(`Error: ${parsed.message}`)
      deps.errLog('')
      deps.errLog(HELP_TEXT)
      return { kind: 'error', code: 64, message: parsed.message }

    case 'init':
      return auditKeyInit(
        { keyPath: parsed.keyPath ?? defaults.keyPath, purpose: parsed.purpose },
        deps,
      )

    case 'rotate':
      return auditKeyRotate(
        {
          keyPath: parsed.keyPath ?? defaults.keyPath,
          journalPath: parsed.journalPath ?? defaults.journalPath,
          reason: parsed.reason!,
          confirmBridgeStopped: parsed.confirmBridgeStopped,
          purpose: parsed.purpose,
        },
        deps,
      )
  }
}
