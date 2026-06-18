/**
 * features/steps/outbound.ts — Step definitions for outbound_reply_filter.feature.
 *
 * Exercises assertOutboundAllowed() and deliveredThreadKey() from lib.ts.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { expect } from 'bun:test'
import { type Access, assertOutboundAllowed, defaultAccess, deliveredThreadKey } from '../../lib.ts'
import type { Context, StepRegistry } from '../runner.ts'

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Call assertOutboundAllowed and catch any error into ctx.outboundError */
function tryOutbound(
  chatId: string,
  threadTs: string | undefined,
  access: Access,
  deliveredThreads: Set<string>,
  ctx: Context,
): void {
  try {
    assertOutboundAllowed(chatId, threadTs, access, deliveredThreads)
    ctx.outboundError = null
  } catch (e) {
    ctx.outboundError = e as Error
  }
}

// ---------------------------------------------------------------------------
// Step registrations
// ---------------------------------------------------------------------------

export function registerOutboundSteps(registry: StepRegistry): void {
  // -------------------------------------------------------------------------
  // Scenario: A reply into an opted-in channel succeeds
  // -------------------------------------------------------------------------

  registry.register('an access object opts the channel into the allowlist', (ctx) => {
    const access: Access = {
      ...defaultAccess(),
      channels: {
        C_OPT: { requireMention: false, allowFrom: [] },
      },
    }
    ctx.access = access
    ctx.chatId = 'C_OPT'
    ctx.threadTs = undefined
    ctx.deliveredThreads = new Set<string>()
  })

  registry.register('the server attempts a reply at the top of that channel', (ctx) => {
    const { access, chatId, threadTs, deliveredThreads } = ctx as {
      access: Access
      chatId: string
      threadTs: string | undefined
      deliveredThreads: Set<string>
    }
    tryOutbound(chatId, threadTs, access, deliveredThreads, ctx)
  })

  registry.register('the gate allows the outbound message', (ctx) => {
    expect(ctx.outboundError).toBeNull()
  })

  registry.register(
    'the channel-level opt-in supersedes any thread-level delivery check',
    (ctx) => {
      // Confirm that even with an empty deliveredThreads set, the opt-in channel passes.
      expect(ctx.outboundError).toBeNull()
    },
  )

  // -------------------------------------------------------------------------
  // Scenario: A reply into a thread that has previously delivered inbound
  // -------------------------------------------------------------------------

  registry.register(
    'a delivered-threads set records a prior inbound in a specific thread',
    (ctx) => {
      const channel = 'C_UNOPT'
      const thread = '1234.0001'
      const deliveredThreads = new Set<string>([deliveredThreadKey(channel, thread)])
      ctx.access = defaultAccess()
      ctx.chatId = channel
      ctx.threadTs = thread
      ctx.deliveredThreads = deliveredThreads
    },
  )

  registry.register('the server attempts a reply into that same thread', (ctx) => {
    const { access, chatId, threadTs, deliveredThreads } = ctx as {
      access: Access
      chatId: string
      threadTs: string
      deliveredThreads: Set<string>
    }
    tryOutbound(chatId, threadTs, access, deliveredThreads, ctx)
  })

  registry.register('the composite key matches the delivered entry', (ctx) => {
    expect(ctx.outboundError).toBeNull()
  })

  // -------------------------------------------------------------------------
  // Scenario: A reply into a thread with no prior inbound in an unopted channel
  // -------------------------------------------------------------------------

  registry.register('the channel is not in the access allowlist', (ctx) => {
    ctx.access = defaultAccess() // no channels
    ctx.chatId = 'C_UNOPT'
    ctx.threadTs = '9999.0001'
  })

  registry.register('the delivered-threads set is empty for this thread', (ctx) => {
    ctx.deliveredThreads = new Set<string>()
  })

  registry.register('the server attempts a reply into that thread', (ctx) => {
    const { access, chatId, threadTs, deliveredThreads } = ctx as {
      access: Access
      chatId: string
      threadTs: string | undefined
      deliveredThreads: Set<string>
    }
    tryOutbound(chatId, threadTs, access, deliveredThreads, ctx)
  })

  registry.register('the gate throws an outbound-gate error', (ctx) => {
    expect(ctx.outboundError).not.toBeNull()
    expect((ctx.outboundError as Error).message).toContain('Outbound gate')
  })

  registry.register('the error identifies the channel and thread that failed the check', (ctx) => {
    const err = ctx.outboundError as Error
    expect(err.message).toContain('C_UNOPT')
  })

  // -------------------------------------------------------------------------
  // Scenario: A reply into thread B on behalf of thread A's session is rejected
  // -------------------------------------------------------------------------

  registry.register('a delivered-threads set records thread A in an unopted channel', (ctx) => {
    const channel = 'C_UNOPT2'
    const threadA = '1111.0001'
    const deliveredThreads = new Set<string>([deliveredThreadKey(channel, threadA)])
    ctx.access = defaultAccess()
    ctx.chatId = channel
    ctx.threadA = threadA
    ctx.threadB = '2222.0002'
    ctx.deliveredThreads = deliveredThreads
  })

  registry.register('the server attempts a reply into thread B of the same channel', (ctx) => {
    const { access, chatId, threadB, deliveredThreads } = ctx as {
      access: Access
      chatId: string
      threadB: string
      deliveredThreads: Set<string>
    }
    tryOutbound(chatId, threadB, access, deliveredThreads, ctx)
  })

  registry.register('cross-thread authority is denied', (ctx) => {
    expect(ctx.outboundError).not.toBeNull()
  })

  // -------------------------------------------------------------------------
  // Scenario: A top-level post into a channel with only threaded deliveries
  // -------------------------------------------------------------------------

  registry.register('a delivered-threads set records a thread but no top-level delivery', (ctx) => {
    const channel = 'C_THREAD_ONLY'
    const thread = '5555.0001'
    // Only the threaded key — not the top-level (undefined) key
    const deliveredThreads = new Set<string>([deliveredThreadKey(channel, thread)])
    ctx.access = defaultAccess()
    ctx.chatId = channel
    ctx.threadTs = undefined // top-level post
    ctx.deliveredThreads = deliveredThreads
  })

  registry.register('the server attempts a top-level post into that channel', (ctx) => {
    const { access, chatId, threadTs, deliveredThreads } = ctx as {
      access: Access
      chatId: string
      threadTs: string | undefined
      deliveredThreads: Set<string>
    }
    tryOutbound(chatId, threadTs, access, deliveredThreads, ctx)
  })

  registry.register('the top-level slot is distinct from any threaded slot', (ctx) => {
    expect(ctx.outboundError).not.toBeNull()
  })
}
