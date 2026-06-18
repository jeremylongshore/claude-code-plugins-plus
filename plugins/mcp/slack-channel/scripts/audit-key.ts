#!/usr/bin/env bun
/**
 * scripts/audit-key.ts — Production runner for the audit-key CLI
 * (ccsc-l1f). Thin wrapper: wires production dependencies for
 * audit-key-cli.ts and translates the result to process.exit.
 *
 * Invocation:
 *   bun scripts/audit-key.ts init
 *   bun scripts/audit-key.ts rotate --reason=scheduled-90day --confirm-bridge-stopped
 *   bun scripts/audit-key.ts help
 *
 * See `audit-key-cli.ts:HELP_TEXT` for the full CLI surface.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { execFile } from 'node:child_process'
import { existsSync } from 'node:fs'
import { rename, unlink, writeFile } from 'node:fs/promises'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { promisify } from 'node:util'

import { type AuditKeyCliDeps, runAuditKeyCli } from '../audit-key-cli.ts'
import { generateKeyPair, parseKeyPairYaml, serializeKeyPairYaml } from '../crypto.ts'
import { JournalWriter } from '../journal.ts'

const execFileAsync = promisify(execFile)

/** Expand a leading `~/` to the OS-reported home directory.
 *  Mirrors audit-key-loader.ts:expandTilde. Pulled inline to
 *  keep this runner self-contained (no cross-module coupling
 *  beyond the CLI itself). */
function expandTilde(p: string): string {
  if (!p.startsWith('~/')) return p
  return join(homedir(), p.slice(2))
}

const DEFAULT_KEY_PATH = expandTilde('~/.claude/channels/slack/audit.key.sops.yaml')
const DEFAULT_JOURNAL_PATH = expandTilde('~/.claude/channels/slack/audit.log')

/** Production deps: real subprocess, real fs, real JournalWriter.
 *  Tests inject mocks at the runAuditKeyCli boundary. */
const prodDeps: AuditKeyCliDeps = {
  generateKeyPair,
  serializeKeyPairYaml,
  parseKeyPairYaml,
  fileExists: existsSync,
  writeTempPlain: async (path, content) => {
    // Atomic-write semantic: mode 0o600 from the start (don't
    // create-then-chmod, that's a TOCTOU window for the file
    // briefly being world-readable on some filesystems). The
    // fs/promises.writeFile spec accepts a mode option that's
    // applied via open(O_CREAT, ..., mode).
    await writeFile(path, content, { mode: 0o600, encoding: 'utf8' })
  },
  encryptInPlace: async (path) => {
    // argv-mode invocation with `--` separator (per Gemini #185
    // pattern adopted in audit-key-loader.ts). SOPS picks up the
    // recipient from the colocated `.sops.yaml` config file.
    await execFileAsync('sops', ['--encrypt', '--in-place', '--', path], {
      // Modest buffer cap; SOPS doesn't emit much on success.
      maxBuffer: 64 * 1024,
    })
  },
  renameAtomic: rename,
  decryptFile: async (path) => {
    const { stdout } = await execFileAsync('sops', ['-d', '--', path], {
      encoding: 'utf8',
      maxBuffer: 16 * 1024,
    })
    return stdout
  },
  unlinkIfExists: async (path) => {
    try {
      await unlink(path)
    } catch (err: any) {
      if (err?.code === 'ENOENT') return
      throw err
    }
  },
  openJournalWriter: (opts) => JournalWriter.open(opts),
  now: Date.now,
  log: (msg) => {
    // Use the fd directly via process.stdout.write rather than
    // console.log so the output goes to stdout (operator pipe-able)
    // without console's added formatting.
    process.stdout.write(`${msg}\n`)
  },
  errLog: (msg) => {
    process.stderr.write(`${msg}\n`)
  },
}

async function main(): Promise<void> {
  // process.argv: [bun, scripts/audit-key.ts, ...userArgs]
  const userArgs = process.argv.slice(2)

  const result = await runAuditKeyCli(userArgs, prodDeps, {
    keyPath: DEFAULT_KEY_PATH,
    journalPath: DEFAULT_JOURNAL_PATH,
  })

  if (result.kind === 'error') {
    process.stderr.write(`${result.message}\n`)
  }
  process.exit(result.code)
}

// CLI entrypoint: process exits inside main(); the void cast
// suppresses the floating-promise lint at the top level.
void main()
