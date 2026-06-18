/**
 * features/steps/admin.ts — Step definitions for admin_commands.feature.
 *
 * Exercises dispatchAdminCommand() in admin.ts. Context carries the
 * dispatch dependencies (recording observers for journal, tmux,
 * reactions, quiesce flag), the result of dispatch, and the
 * configurable behavior of isAllowed and verifyChallenge per scenario.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { expect } from 'bun:test'
import {
  type AdminCommand,
  type DispatchDeps,
  type DispatchOutcome,
  dispatchAdminCommand,
} from '../../admin.ts'
import type { StepRegistry } from '../runner.ts'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

interface AdminContext {
  envelope: {
    channelId: string
    requestedBy: string
    threadTs: string
    messageTs: string
  }
  journal: Array<Record<string, unknown>>
  tmuxCalls: Array<readonly string[]>
  reactions: string[]
  quiesceCalled: boolean
  order: string[]
  isAllowed: boolean
  verifyResult: ReturnType<DispatchDeps['verifyChallenge']>
  verifyCalled: boolean
  journalThrows: boolean
  outcome: DispatchOutcome | null
  mintedNonce: string
}

function freshContext(ctx: Record<string, unknown>): AdminContext {
  const c: AdminContext = {
    envelope: {
      channelId: 'C_OPS',
      requestedBy: 'U_ALICE',
      threadTs: '1700000000.000100',
      messageTs: '1700000000.000100',
    },
    journal: [],
    tmuxCalls: [],
    reactions: [],
    quiesceCalled: false,
    order: [],
    isAllowed: true,
    verifyResult: {
      ok: true,
      challenge: {
        nonce: 'a1b2c3d4e5f6g7h8',
        userId: 'U_ALICE',
        channelId: 'C_OPS',
        expiresAt: 1_000_060,
        consumed: true,
      },
    } as ReturnType<DispatchDeps['verifyChallenge']>,
    verifyCalled: false,
    journalThrows: false,
    outcome: null,
    mintedNonce: 'a1b2c3d4e5f6g7h8',
  }
  ctx.adminCtx = c
  return c
}

function getCtx(ctx: Record<string, unknown>): AdminContext {
  return ctx.adminCtx as AdminContext
}

function buildDeps(c: AdminContext): DispatchDeps {
  return {
    isAllowed: () => c.isAllowed,
    journalWrite: async (input) => {
      if (c.journalThrows) {
        c.order.push('journal-throw')
        throw new Error('disk full')
      }
      c.order.push('journal')
      c.journal.push(input as Record<string, unknown>)
      return undefined
    },
    quiesceAndDeactivate: async () => {
      c.order.push('quiesce')
      c.quiesceCalled = true
    },
    sendTmuxKeys: async (keys) => {
      c.order.push('tmux')
      c.tmuxCalls.push([...keys])
    },
    issueChallenge: async () => {
      c.order.push('challenge')
      return { nonce: c.mintedNonce, expiresAt: 1_000_060 }
    },
    verifyChallenge: (nonce, presentedBy) => {
      c.verifyCalled = true
      // Honor the test's configured verifyResult — but if ok, echo the
      // presented nonce/user/channel so the challenge field is
      // self-consistent.
      if (c.verifyResult.ok) {
        return {
          ok: true,
          challenge: {
            ...c.verifyResult.challenge,
            nonce,
            userId: presentedBy.userId,
            channelId: presentedBy.channelId,
          },
        }
      }
      return c.verifyResult
    },
    postReaction: async (emoji) => {
      c.order.push('react')
      c.reactions.push(emoji)
    },
  }
}

// ---------------------------------------------------------------------------
// Registration
// ---------------------------------------------------------------------------

export function registerAdminSteps(registry: StepRegistry): void {
  // Background
  registry.register('an admin command dispatcher with recording dependencies', (ctx) => {
    freshContext(ctx)
  })

  // Allowlist setup
  registry.register("the requester is on the channel's adminCommands.allowFrom list", (ctx) => {
    getCtx(ctx).isAllowed = true
  })
  registry.register("the requester is NOT on the channel's adminCommands.allowFrom list", (ctx) => {
    getCtx(ctx).isAllowed = false
  })

  // Verify result setup
  registry.register('the verifier will return ok for the presented nonce', (ctx) => {
    const c = getCtx(ctx)
    c.verifyResult = {
      ok: true,
      challenge: {
        nonce: 'a1b2c3d4e5f6g7h8',
        userId: c.envelope.requestedBy,
        channelId: c.envelope.channelId,
        expiresAt: 1_000_060,
        consumed: true,
      },
    } as ReturnType<DispatchDeps['verifyChallenge']>
  })
  registry.register(
    /^the verifier will return (expired|replay|wrong-channel|wrong-user|unknown) for the presented nonce$/,
    (ctx, m) => {
      const c = getCtx(ctx)
      c.verifyResult = {
        ok: false,
        reason: m[1] as 'expired' | 'replay' | 'wrong-channel' | 'wrong-user' | 'unknown',
      }
    },
  )

  // Journal failure mode
  registry.register('the journal writer will throw on every write', (ctx) => {
    getCtx(ctx).journalThrows = true
  })

  // Dispatch actions
  registry.register('the operator dispatches !clear', async (ctx) => {
    const c = getCtx(ctx)
    const cmd: AdminCommand = { kind: 'clear', ...c.envelope }
    c.outcome = await dispatchAdminCommand(cmd, buildDeps(c))
  })

  registry.register('the operator dispatches !restart without a nonce', async (ctx) => {
    const c = getCtx(ctx)
    const cmd: AdminCommand = { kind: 'restart', nonce: undefined, ...c.envelope }
    c.outcome = await dispatchAdminCommand(cmd, buildDeps(c))
  })

  registry.register('the operator dispatches !restart with a nonce', async (ctx) => {
    const c = getCtx(ctx)
    const cmd: AdminCommand = { kind: 'restart', nonce: 'a1b2c3d4e5f6g7h8', ...c.envelope }
    c.outcome = await dispatchAdminCommand(cmd, buildDeps(c))
  })

  // Assertions — journal
  registry.register(
    /^the journal records (admin\.[a-z._]+) with outcome (allow|deny)$/,
    (ctx, m) => {
      const c = getCtx(ctx)
      const kind = m[1]
      const outcome = m[2]
      const found = c.journal.find((j) => j.kind === kind)
      expect(found).toBeDefined()
      expect(found!.outcome).toBe(outcome)
    },
  )
  registry.register(/^the journal records (admin\.[a-z._]+)$/, (ctx, m) => {
    const c = getCtx(ctx)
    const found = c.journal.find((j) => j.kind === m[1])
    expect(found).toBeDefined()
  })
  registry.register('the journal event does NOT contain the minted nonce', (ctx) => {
    const c = getCtx(ctx)
    // No event in the journal carries the literal nonce value
    for (const ev of c.journal) {
      expect(JSON.stringify(ev)).not.toContain(c.mintedNonce)
    }
  })
  registry.register('the journal write was observed before the tmux send-keys', (ctx) => {
    const c = getCtx(ctx)
    const journalIdx = c.order.indexOf('journal')
    const tmuxIdx = c.order.indexOf('tmux')
    expect(journalIdx).toBeGreaterThanOrEqual(0)
    expect(tmuxIdx).toBeGreaterThan(journalIdx)
  })

  // Assertions — side effects
  registry.register('supervisor.quiesceAndDeactivate was called', (ctx) => {
    expect(getCtx(ctx).quiesceCalled).toBe(true)
  })
  registry.register(/^tmux received keys "([^"]+)" "([^"]+)"$/, (ctx, m) => {
    const c = getCtx(ctx)
    expect(c.tmuxCalls).toEqual([[m[1]!, m[2]!]])
  })
  registry.register('no tmux keys were sent', (ctx) => {
    expect(getCtx(ctx).tmuxCalls).toEqual([])
  })
  registry.register(/^a (recycle|arrows_counterclockwise) reaction was posted$/, (ctx, m) => {
    expect(getCtx(ctx).reactions).toEqual([m[1]!])
  })
  registry.register(/^an (recycle|arrows_counterclockwise) reaction was posted$/, (ctx, m) => {
    expect(getCtx(ctx).reactions).toEqual([m[1]!])
  })

  // Assertions — outcome
  registry.register('the dispatcher returns a challenge_issued outcome', (ctx) => {
    const o = getCtx(ctx).outcome
    expect(o?.kind).toBe('challenge_issued')
  })
  registry.register('the dispatcher returns a denied outcome', (ctx) => {
    const o = getCtx(ctx).outcome
    expect(o?.kind).toBe('denied')
  })
  registry.register(
    /^the dispatcher returns a denied outcome with reason containing "([^"]+)"$/,
    (ctx, m) => {
      const o = getCtx(ctx).outcome
      expect(o?.kind).toBe('denied')
      if (o?.kind === 'denied') {
        expect(o.reason).toContain(m[1]!)
      }
    },
  )
  registry.register('the dispatcher returns an executed outcome', (ctx) => {
    const o = getCtx(ctx).outcome
    expect(o?.kind).toBe('executed')
  })
  registry.register('the verifier was NOT called', (ctx) => {
    expect(getCtx(ctx).verifyCalled).toBe(false)
  })
}
