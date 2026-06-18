/**
 * features/steps/sendable.ts — Step definitions for file_exfiltration_guard.feature.
 *
 * Exercises assertSendable() from lib.ts. Uses a real tmp directory created
 * per-feature-file run. The Context carries `inboxDir`, `stateRoot`,
 * `allowlistRoots`, and `targetPath` across steps.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { expect } from 'bun:test'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { assertSendable } from '../../lib.ts'
import type { StepRegistry } from '../runner.ts'

// ---------------------------------------------------------------------------
// Fixture management — one tmp tree shared across all scenarios in this file.
// We set it up once, tear down in a cleanup function registered from the
// runner.test.ts afterAll.
// ---------------------------------------------------------------------------

export interface SendableFixtures {
  root: string
  inboxDir: string
  stateRoot: string
  allowlistRoot: string
  cleanup: () => void
}

export function createSendableFixtures(): SendableFixtures {
  const root = mkdtempSync(join(tmpdir(), 'feat-sendable-'))
  const inboxDir = join(root, 'inbox')
  const stateRoot = join(root, 'state')
  const allowlistRoot = join(root, 'allowed')

  mkdirSync(inboxDir, { recursive: true })
  mkdirSync(stateRoot, { recursive: true })
  mkdirSync(allowlistRoot, { recursive: true })

  // Files inside the inbox (sendable)
  writeFileSync(join(inboxDir, 'photo.png'), 'png-data')

  // A state-dir file outside the inbox (blocked by S1)
  writeFileSync(join(stateRoot, 'access.json'), '{}')

  // A credential file under the allowlist root (blocked by basename denylist)
  const credDir = join(allowlistRoot, 'creds')
  mkdirSync(credDir, { recursive: true })
  writeFileSync(join(credDir, 'credentials'), 'creds-data')

  // A normal file under allowlist root (sendable)
  writeFileSync(join(allowlistRoot, 'report.csv'), 'csv-data')

  // A sensitive single-component directory inside allowlist root
  const sshDir = join(allowlistRoot, '.ssh')
  mkdirSync(sshDir, { recursive: true })
  writeFileSync(join(sshDir, 'id_rsa'), 'ssh-key')

  // A sensitive adjacent-pair directory inside allowlist root
  const configGcloudDir = join(allowlistRoot, '.config', 'gcloud')
  mkdirSync(configGcloudDir, { recursive: true })
  writeFileSync(join(configGcloudDir, 'credentials'), 'gcloud-creds')

  // A file outside every root
  const outsideDir = join(root, 'outside')
  mkdirSync(outsideDir, { recursive: true })
  writeFileSync(join(outsideDir, 'secret.txt'), 'secret')

  return {
    root,
    inboxDir,
    stateRoot,
    allowlistRoot,
    cleanup: () => rmSync(root, { recursive: true, force: true }),
  }
}

// ---------------------------------------------------------------------------
// Step registrations
// ---------------------------------------------------------------------------

export function registerSendableSteps(registry: StepRegistry, fixtures: SendableFixtures): void {
  const { inboxDir, stateRoot, allowlistRoot } = fixtures

  // -------------------------------------------------------------------------
  // Background steps
  // -------------------------------------------------------------------------

  registry.register('an inbox directory exists at a known location', (ctx) => {
    ctx.inboxDir = inboxDir
  })

  registry.register('the allowlisted sendable roots are configured explicitly', (ctx) => {
    ctx.allowlistRoots = [allowlistRoot]
  })

  registry.register('the state root contains credential files that are never sendable', (ctx) => {
    ctx.stateRoot = stateRoot
  })

  // -------------------------------------------------------------------------
  // Scenario: Traversal path with a parent-directory component is rejected
  // -------------------------------------------------------------------------

  registry.register(
    'a caller requests a file path that contains a parent-component token',
    (ctx) => {
      // Raw traversal string — assertSendable checks before resolving
      ctx.targetPath = join(inboxDir, '..', 'outside', 'secret.txt')
    },
  )

  registry.register('the guard throws before consulting the filesystem', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    expect(() => assertSendable(targetPath, inbox, allowlistRoots, sr)).toThrow('Blocked')
  })

  registry.register('the error message names the traversal check', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    let caught: Error | undefined
    try {
      assertSendable(targetPath, inbox, allowlistRoots, sr)
    } catch (e) {
      caught = e as Error
    }
    expect(caught).toBeDefined()
    expect(caught!.message).toContain('..')
  })

  // -------------------------------------------------------------------------
  // Scenario: A path that does not resolve on the filesystem is rejected
  // -------------------------------------------------------------------------

  registry.register('a caller requests a path that realpath cannot resolve', (ctx) => {
    ctx.targetPath = join(inboxDir, 'does-not-exist.png')
  })

  registry.register('the guard throws with an access error', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    expect(() => assertSendable(targetPath, inbox, allowlistRoots, sr)).toThrow('Blocked')
  })

  registry.register('no symlink is followed against the allowlist', (_ctx) => {
    // The throw happens before any symlink traversal — covered by the prior step.
  })

  // -------------------------------------------------------------------------
  // Scenario: A file inside the state directory but outside the inbox is rejected
  // -------------------------------------------------------------------------

  registry.register('a caller requests a path that resolves under the state root', (ctx) => {
    ctx.targetPath = join(stateRoot, 'access.json')
  })

  registry.register('the guard throws because the state root is blanket-denied', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    // Even if stateRoot were an allowlisted root, the S1 check should block it.
    expect(() => assertSendable(targetPath, inbox, [...allowlistRoots, sr], sr)).toThrow('Blocked')
  })

  registry.register('the inbox carve-out does not apply', (ctx) => {
    // The file is in stateRoot/access.json, NOT in the inbox. Verify.
    const path = ctx.targetPath as string
    expect(path).toContain('state')
    expect(path).not.toContain('inbox')
  })

  // -------------------------------------------------------------------------
  // Scenario: A file inside the inbox under the state root is accepted
  // -------------------------------------------------------------------------

  registry.register('a caller requests a path that resolves under the inbox directory', (ctx) => {
    ctx.targetPath = join(inboxDir, 'photo.png')
  })

  registry.register('the guard allows the upload', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    expect(() => assertSendable(targetPath, inbox, allowlistRoots, sr)).not.toThrow()
  })

  registry.register('the inbox carve-out supersedes the state-root block', (ctx) => {
    // Inbox IS under stateRoot-equivalent (we put it in a different root here,
    // but the semantics are the same: inbox is always an exempted subdir).
    // Re-run with stateRoot = parent of inbox to verify carve-out.
    const inbox = ctx.inboxDir as string
    const allowlistRoots = ctx.allowlistRoots as string[]
    const targetPath = join(inbox, 'photo.png')
    // Here the stateRoot wraps the inbox — carve-out must still allow it.
    const rootParent = fixtures.root
    expect(() => assertSendable(targetPath, inbox, allowlistRoots, rootParent)).not.toThrow()
  })

  // -------------------------------------------------------------------------
  // Scenario: A credential file matched by basename is rejected
  // -------------------------------------------------------------------------

  registry.register('a credential file lives under an allowlisted root', (ctx) => {
    ctx.targetPath = join(allowlistRoot, 'creds', 'credentials')
  })

  registry.register('a caller requests that credential file by path', (_ctx) => {
    // targetPath already set in the Given step
  })

  registry.register(
    'the guard throws because the basename matches the credential denylist',
    (ctx) => {
      const {
        targetPath,
        inboxDir: inbox,
        allowlistRoots,
        stateRoot: sr,
      } = ctx as {
        targetPath: string
        inboxDir: string
        allowlistRoots: string[]
        stateRoot: string
      }
      expect(() => assertSendable(targetPath, inbox, allowlistRoots, sr)).toThrow('Blocked')
    },
  )

  // -------------------------------------------------------------------------
  // Scenario: A path descending through a sensitive single-component directory
  // -------------------------------------------------------------------------

  registry.register(
    'a caller requests a file whose parent chain includes a sensitive directory name',
    (ctx) => {
      ctx.targetPath = join(allowlistRoot, '.ssh', 'id_rsa')
    },
  )

  registry.register('the guard throws because the component denylist applies', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    expect(() => assertSendable(targetPath, inbox, allowlistRoots, sr)).toThrow('Blocked')
  })

  // -------------------------------------------------------------------------
  // Scenario: A path descending through a sensitive adjacent-pair directory
  // -------------------------------------------------------------------------

  registry.register(
    'a caller requests a file whose parent chain matches a pair denylist entry',
    (ctx) => {
      ctx.targetPath = join(allowlistRoot, '.config', 'gcloud', 'credentials')
    },
  )

  registry.register('the guard throws because an adjacent-pair match applies', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    expect(() => assertSendable(targetPath, inbox, allowlistRoots, sr)).toThrow('Blocked')
  })

  // -------------------------------------------------------------------------
  // Scenario: A path outside every allowlisted root is rejected
  // -------------------------------------------------------------------------

  registry.register(
    'a caller requests a path that resolves outside the configured roots',
    (ctx) => {
      ctx.targetPath = join(fixtures.root, 'outside', 'secret.txt')
    },
  )

  registry.register('the guard throws because the allowlist does not cover the location', (ctx) => {
    const {
      targetPath,
      inboxDir: inbox,
      allowlistRoots,
      stateRoot: sr,
    } = ctx as {
      targetPath: string
      inboxDir: string
      allowlistRoots: string[]
      stateRoot: string
    }
    expect(() => assertSendable(targetPath, inbox, allowlistRoots, sr)).toThrow('Blocked')
  })
}
