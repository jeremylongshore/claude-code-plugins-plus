/**
 * audit-key-loader.ts — Boot-time loader for the Ed25519 audit-
 * signing keypair (ccsc-uge).
 *
 * Bridges the gap between the crypto.ts primitives (Ed25519 sign/
 * verify, SOPS YAML parse) shipped in the v0.10 rollout (#167) and
 * the production server.ts boot path. Spawns the operator's local
 * `sops` binary to decrypt the SOPS-encrypted key file, pipes the
 * plaintext YAML through `parseKeyPairYaml`, and returns the
 * resulting `Ed25519KeyPair` for `JournalWriter.open({ signingKey })`.
 *
 * Trust model: the decrypted YAML lives in this process's memory
 * only. We never write the plaintext to disk (no `/dev/shm` tmpfs,
 * no temp file) — the SOPS subprocess pipes directly to stdout
 * which we consume in-memory. A core dump or memory inspection of
 * this process leaks the key; same posture as every other secret
 * the bridge already holds (tokens in .env).
 *
 * Failure semantics (per 000-docs/key-management.md):
 *   - SOPS file absent + --no-audit-signing flag set → return null
 *     (caller falls back to v1 mode).
 *   - SOPS file absent + no flag → return loud error (caller
 *     exits non-zero with instructive message).
 *   - SOPS file present but malformed (sops decryption fails, YAML
 *     parse fails, tamper-checked public_key mismatches seed) →
 *     return loud error (caller exits non-zero).
 *   - Key older than 90 days → return with a `staleWarning` flag
 *     set; caller logs but does not block boot.
 *
 * Sibling-module pattern: pure async function + injectable spawn,
 * tests use a mock spawn that returns canned stdout.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { execFile } from 'node:child_process'
import { existsSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { promisify } from 'node:util'
import { type Ed25519KeyPair, parseKeyPairYaml } from './crypto.ts'

const execFileAsync = promisify(execFile)

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Default SOPS key file location per 000-docs/key-management.md. */
export const DEFAULT_AUDIT_KEY_PATH = '~/.claude/channels/slack/audit.key.sops.yaml'

/** Stale-warning threshold in ms — 90 days per the rotation cadence
 *  documented in key-management.md. The loader warns when the key's
 *  `createdAt` is older than this; an operator can choose to defer
 *  rotation. NOT a hard failure. */
export const STALE_KEY_THRESHOLD_MS = 90 * 24 * 60 * 60 * 1000

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Outcome of `loadSigningKey`. Three terminal states:
 *
 *   - `loaded` — key decrypted successfully. `staleWarning` is true
 *     when createdAt is older than 90 days.
 *   - `disabled` — no SOPS file AND --no-audit-signing flag set.
 *     Caller falls back to v1 mode (writer emits unsigned events).
 *   - `error` — SOPS file missing without the flag, decrypt failed,
 *     YAML malformed, or public-key tamper check rejected. Caller
 *     exits non-zero with the message.
 */
export type AuditSigningResolution =
  | { kind: 'loaded'; keypair: Ed25519KeyPair; staleWarning: boolean; source: string }
  | { kind: 'disabled'; reason: 'no-audit-signing-flag' }
  | { kind: 'error'; reason: string }

/** Options for `loadSigningKey`. Tests inject a custom `spawn` to
 *  exercise the SOPS-subprocess paths without actually running
 *  sops. Production passes nothing — defaults kick in. */
export interface LoadSigningKeyOptions {
  /** Absolute path (or `~`-prefixed) to the SOPS-encrypted YAML.
   *  Defaults to DEFAULT_AUDIT_KEY_PATH. */
  path?: string
  /** True iff the operator passed `--no-audit-signing` on the CLI.
   *  When the file is absent, this is the difference between graceful
   *  v1 fallback (true) and loud refusal (false). */
  noAuditSigning?: boolean
  /** Override the SOPS subprocess runner. Tests inject a function
   *  that returns the canned plaintext (or throws to simulate a
   *  decrypt failure). Production uses execFile('sops', ...). */
  spawn?: (path: string) => Promise<string>
  /** Clock for stale-key calculation. Defaults to Date.now. */
  now?: () => number
}

// ---------------------------------------------------------------------------
// CLI flag parser
// ---------------------------------------------------------------------------

/** Parse the `--no-audit-signing` flag out of argv (Slack-bridge's
 *  CLI flag style). Returns true iff the flag is present. Doesn't
 *  validate other args — server.ts's main argv parsing owns that. */
export function parseNoAuditSigningFlag(argv: readonly string[]): boolean {
  return argv.includes('--no-audit-signing')
}

// ---------------------------------------------------------------------------
// SOPS subprocess invocation (production)
// ---------------------------------------------------------------------------

/** Default SOPS runner — spawns `sops -d -- <path>` via execFile and
 *  returns stdout. Throws if SOPS exits non-zero (decrypt failure,
 *  missing age key, malformed input).
 *
 *  Argv-mode by construction (no shell). The `--` separator stops
 *  argument parsing before the path — defense-in-depth against a
 *  pathological path that begins with a hyphen and could otherwise
 *  be interpreted as a flag (per Gemini security review on PR #185).
 *  In practice the path comes from operator configuration, not user
 *  input, but the `--` is one extra character for non-zero benefit. */
async function defaultSopsSpawn(path: string): Promise<string> {
  const { stdout } = await execFileAsync('sops', ['-d', '--', path], {
    encoding: 'utf8',
    // Modest size cap — a 32-byte seed YAML is < 1 KiB. Anything
    // larger is suspicious. 16 KiB headroom for future extensions.
    maxBuffer: 16 * 1024,
  })
  return stdout
}

// ---------------------------------------------------------------------------
// Path expansion — handle ~/ prefix
// ---------------------------------------------------------------------------

/** Expand a leading `~/` to the OS-reported home directory.
 *  Uses `os.homedir()` + `path.join()` (per Gemini review on PR
 *  #185) — more portable than `process.env.HOME` + string
 *  concatenation, and handles environments where HOME is unset
 *  (Windows, certain containerized setups). */
function expandTilde(p: string): string {
  if (!p.startsWith('~/')) return p
  return join(homedir(), p.slice(2))
}

// ---------------------------------------------------------------------------
// loadSigningKey — the orchestrator
// ---------------------------------------------------------------------------

/** Load the Ed25519 signing keypair at boot. Returns a structured
 *  `AuditSigningResolution` for the caller (server.ts) to act on:
 *  pass `loaded.keypair` into `JournalWriter.open({ signingKey })`,
 *  fall back to v1 mode on `disabled`, exit non-zero on `error`.
 *
 *  Pipeline:
 *    1. Resolve path (expand `~`).
 *    2. Check file exists.
 *       - Missing + noAuditSigning → return { kind: 'disabled' }
 *       - Missing + no flag → return { kind: 'error' } with
 *         instructive message pointing at key-management.md
 *    3. Spawn `sops -d` (or the injected mock).
 *       - SOPS throws → return { kind: 'error' } wrapping the
 *         underlying message
 *    4. Parse via crypto.ts:parseKeyPairYaml.
 *       - Parse throws (malformed YAML, wrong-length seed,
 *         declared public_key mismatch) → return { kind: 'error' }
 *    5. Check createdAt against staleness threshold.
 *    6. Return { kind: 'loaded', keypair, staleWarning, source }.
 *
 *  Defensive: never throws. Every failure path returns a structured
 *  result. The caller decides whether to log + continue or exit. */
export async function loadSigningKey(
  opts: LoadSigningKeyOptions = {},
): Promise<AuditSigningResolution> {
  const path = expandTilde(opts.path ?? DEFAULT_AUDIT_KEY_PATH)
  const noAuditSigning = opts.noAuditSigning ?? false
  const spawn = opts.spawn ?? defaultSopsSpawn
  const now = opts.now ?? ((): number => Date.now())

  // Step 2: existence check.
  if (!existsSync(path)) {
    if (noAuditSigning) {
      return { kind: 'disabled', reason: 'no-audit-signing-flag' }
    }
    return {
      kind: 'error',
      reason:
        `Audit-signing key not found at ${path}. ` +
        `Run \`ccsc audit-key init\` to generate one, or pass --no-audit-signing to ` +
        `start in unsigned-relaxed mode (NOT recommended for production). See ` +
        `000-docs/key-management.md.`,
    }
  }

  // Step 3: SOPS decrypt.
  let yamlText: string
  try {
    yamlText = await spawn(path)
  } catch (err) {
    return {
      kind: 'error',
      reason: `SOPS decrypt failed for ${path}: ${err instanceof Error ? err.message : String(err)}`,
    }
  }

  // Step 4: parse + tamper-check.
  let keypair: Ed25519KeyPair
  try {
    keypair = parseKeyPairYaml(yamlText)
  } catch (err) {
    return {
      kind: 'error',
      reason: `audit key parse failed: ${err instanceof Error ? err.message : String(err)}`,
    }
  }

  // Step 5: staleness check (non-blocking).
  const ageMs = now() - Date.parse(keypair.createdAt)
  const staleWarning = ageMs > STALE_KEY_THRESHOLD_MS

  return { kind: 'loaded', keypair, staleWarning, source: path }
}
