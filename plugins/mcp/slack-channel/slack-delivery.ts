/**
 * slack-delivery.ts — Slack-facing glue for the reply-delivery outbox poller
 * (ccsc-o7x.3).
 *
 * The crash-safety epic (ccsc-o7x) makes a terminal turn's reply loss-proof:
 * the reply is recorded as a durable obligation (ccsc-o7x.2.1), drained by a
 * leased, retrying poller (ccsc-o7x.2.2), and made idempotent so a redelivery
 * after a lost ack never double-posts (ccsc-o7x.2.3). All of THAT logic lives
 * in the vendored `lib.ts` kernel (`makeIdempotentSend`,
 * `deliveryIdempotencyKey`) and `supervisor.ts` (`drainOutbox`).
 *
 * This module is the thin I/O adapter that binds that logic to a real Slack
 * `WebClient` — `findDelivered` (look up our own prior post by its stamped
 * idempotency key) and `post` (send with the key stamped into message
 * metadata). It is deliberately a sibling module, not inline in `server.ts`,
 * so it can be unit-tested against a faked `WebClient` without triggering
 * `server.ts`'s module-load side effects (token load, Socket Mode, `main()`).
 *
 * No Slack-SDK code crosses into `lib.ts`: the kernel stays vendorable by AGP;
 * this Slack glue stays in CCSC.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import type { WebClient } from '@slack/web-api'
import {
  classifyDeliveryError,
  DELIVERY_METADATA_EVENT_TYPE,
  type DeliveryObligation,
  deliveryIdempotencyKey,
  extractSlackErrorCode,
  type IdempotentSendDeps,
} from './lib.ts'
import type { SessionHandle, SessionSupervisor } from './supervisor.ts'

/** Shape of a `conversations.replies` message we care about — just the `ts` and
 *  the message `metadata` (returned when the request sets
 *  `include_all_metadata`). Narrowed locally because the Slack SDK types the
 *  reply union loosely. */
interface ReplyMessage {
  ts?: string
  metadata?: { event_type?: string; event_payload?: Record<string, unknown> }
}

/** Build the production `IdempotentSendDeps` the outbox poller consumes, bound
 *  to a Slack `WebClient`.
 *
 *  - `findDelivered` scans the destination thread (`conversations.replies` with
 *    `include_all_metadata`) for a message we previously posted carrying our
 *    delivery `event_type` and a matching idempotency key. A hit means the reply
 *    already landed (e.g. a prior attempt posted but its ack was lost), so the
 *    redelivery must be a no-op — it returns the existing `ts`. No thread parent
 *    ⇒ `null` (a non-threaded post can't be looked up this way; the in-process
 *    lease still guards the live race, and CCSC sessions are thread-keyed so
 *    obligations carry a thread in practice).
 *  - `post` sends the reply with the idempotency key stamped into Slack message
 *    `metadata`, so a later `findDelivered` can recognise it.
 *
 *  The idempotency *decision* lives in `makeIdempotentSend` (lib.ts); this only
 *  supplies the two Slack calls it composes. */
export function createDeliverySendDeps(client: WebClient): IdempotentSendDeps {
  const replyPoster = createReplyPoster(client)
  return {
    async findDelivered(channel: string, thread: string, key: string): Promise<string | null> {
      if (!thread) return null
      const res = await client.conversations.replies({
        channel,
        ts: thread,
        limit: 200,
        include_all_metadata: true,
      })
      const messages = (res.messages ?? []) as ReplyMessage[]
      for (const m of messages) {
        if (
          m.metadata?.event_type === DELIVERY_METADATA_EVENT_TYPE &&
          m.metadata.event_payload?.idempotency_key === key
        ) {
          return (m.ts as string) || 'delivered'
        }
      }
      return null
    },
    // The poller discards the ts; the inline durable send wants it. Both share
    // one metadata-stamping site (`createReplyPoster`) so the delivery key is
    // written identically on every path.
    async post(obligation, key): Promise<void> {
      await replyPoster(obligation, key)
    },
  }
}

/** Post a reply with the idempotency key stamped into Slack message `metadata`,
 *  returning the resulting `ts`. The single place the delivery metadata is
 *  written — shared by the poller's `post` (which discards the ts) and the
 *  inline durable send via `deliverReplyDurably` (which needs the ts for the
 *  tool result). Bound to a `WebClient`. (ccsc-o7x.3) */
export function createReplyPoster(client: WebClient): ReplyPoster {
  return async (obligation, key) => {
    const res = await client.chat.postMessage({
      channel: obligation.channel,
      text: obligation.payload,
      thread_ts: obligation.thread || undefined,
      unfurl_links: false,
      unfurl_media: false,
      metadata: {
        event_type: DELIVERY_METADATA_EVENT_TYPE,
        event_payload: { idempotency_key: key },
      },
    })
    return (res.ts as string) || undefined
  }
}

// ---------------------------------------------------------------------------
// Durable single-message reply delivery (ccsc-o7x.3 pt2 — ADR-002 addendum)
// ---------------------------------------------------------------------------

/** Raised when durable delivery cannot even begin — the session can't be
 *  activated, or it holds no lease — *before* any obligation is recorded or any
 *  send attempted. The caller catches this and falls back to a best-effort
 *  direct send; nothing was persisted, so there is no obligation to redeliver. */
export class DurableUnavailableError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'DurableUnavailableError'
  }
}

/** One logical reply to deliver durably. `id` is the caller-supplied stable
 *  unique key (a fresh UUID per reply call) — it becomes the obligation id and
 *  thus the idempotency key, so a poller redelivery of THIS obligation dedups
 *  exactly. */
export interface DurableReply {
  id: string
  channel: string
  thread: string
  text: string
}

export type DurableDeliveryResult =
  | { status: 'delivered'; ts: string | undefined }
  | { status: 'queued' }

/** Post one reply, stamping the idempotency key into Slack message metadata,
 *  and return the resulting `ts` (the inline attempt wants it for the tool
 *  result). Distinct from `IdempotentSendDeps.post` (which returns `void` for
 *  the poller). The production impl wraps `web.chat.postMessage`. */
export type ReplyPoster = (
  obligation: DeliveryObligation,
  idempotencyKey: string,
) => Promise<string | undefined>

/** Durable single-message reply delivery (ADR-002 addendum, Option A). Records
 *  a `pending` obligation BEFORE the send — so a crash before/at the send leaves
 *  a recoverable record the boot-drain redelivers — then attempts exactly ONE
 *  inline send and resolves:
 *
 *    - **success**        → mark `delivered`, return the Slack `ts`;
 *    - **transient error**→ bump `attempts`, leave `pending`, return `queued`
 *      (the poller redelivers idempotently — the caller must NOT retry, or it
 *      would double-post);
 *    - **non-retryable**  → mark `dead` (error recorded) and rethrow the Slack
 *      error so the caller surfaces the real failure to the agent.
 *
 *  Throws `DurableUnavailableError` *before recording* if the session can't be
 *  activated or holds no lease — the caller falls back to a direct send.
 *
 *  Marking the obligation state is best-effort: if the fenced mark write fails
 *  (lease lost mid-flight), the obligation simply stays as the prior process saw
 *  it and the poller reconciles from disk (a delivered-but-unmarked message is
 *  deduped by `findDelivered`, a still-pending one is redelivered). So a mark
 *  failure never fails the reply. (ccsc-o7x.3) */
export async function deliverReplyDurably(
  deps: { supervisor: SessionSupervisor; post: ReplyPoster },
  reply: DurableReply,
): Promise<DurableDeliveryResult> {
  let handle: SessionHandle
  try {
    handle = await deps.supervisor.activate({ channel: reply.channel, thread: reply.thread })
  } catch (err) {
    throw new DurableUnavailableError(
      `cannot activate session: ${err instanceof Error ? err.message : String(err)}`,
    )
  }
  const lease = handle.lease
  if (lease === null) throw new DurableUnavailableError('session holds no lease')
  const token = lease.token

  // Record the durable obligation BEFORE the send (crash-before-send safe).
  await handle.recordTerminalDelivery(token, {
    id: reply.id,
    channel: reply.channel,
    thread: reply.thread,
    payload: reply.text,
  })
  const obligation: DeliveryObligation = {
    id: reply.id,
    channel: reply.channel,
    thread: reply.thread,
    payload: reply.text,
    attempts: 0,
    state: 'pending',
    createdAt: 0,
  }
  const idemKey = deliveryIdempotencyKey(obligation)

  try {
    const ts = await deps.post(obligation, idemKey)
    await markObligation(handle, token, reply.id, { state: 'delivered', attempts: 1 })
    return { status: 'delivered', ts }
  } catch (err) {
    const code = extractSlackErrorCode(err)
    const lastError = code ?? (err instanceof Error ? err.message : String(err))
    if (classifyDeliveryError(code) === 'non-retryable') {
      await markObligation(handle, token, reply.id, { state: 'dead', attempts: 1, lastError })
      throw err
    }
    // Transient: leave pending (attempts bumped so the poller dedups) + queued.
    await markObligation(handle, token, reply.id, { state: 'pending', attempts: 1, lastError })
    return { status: 'queued' }
  }
}

// ---------------------------------------------------------------------------
// Durable chunked (multi-message) reply delivery (ccsc-o7x.4)
// ---------------------------------------------------------------------------

/** One logical reply that spans multiple Slack messages. `chunks` is the
 *  pre-split payload (the caller runs `chunkText`); each chunk becomes its own
 *  obligation with id `<id>:<i>`, so it carries a distinct idempotency key and a
 *  crash mid-way redelivers only the chunks that did not land. `chunks` must be
 *  non-empty; a single-element array is valid, but the single-message
 *  `deliverReplyDurably` is the lighter path for that case. */
export interface DurableChunkedReply {
  id: string
  channel: string
  thread: string
  chunks: string[]
}

export type DurableChunkedDeliveryResult =
  | { status: 'delivered'; ts: string | undefined; sent: number }
  | { status: 'queued'; delivered: number; pending: number }

/** Durable multi-message reply delivery (ccsc-o7x.4) — the chunked sibling of
 *  `deliverReplyDurably`. One reply → N chunks → N obligations, each with id
 *  `<reply.id>:<i>` (a distinct idempotency key per chunk).
 *
 *  Records ALL N obligations in ONE atomic write BEFORE any send
 *  (`recordTerminalDeliveries`) — so a crash before/at any send leaves a
 *  recoverable, all-or-nothing record the boot-drain redelivers. Then posts the
 *  chunks IN ORDER, each under its own idempotency key:
 *
 *    - every chunk posts            → all `delivered`, return the FIRST chunk's
 *      `ts`;
 *    - a transient error on chunk i → mark i `pending` and STOP (do NOT post
 *      i+1…): the poller redelivers i…N-1 in order, so chunks never land out of
 *      order. Return `queued` (the caller must NOT retry — that would double-post
 *      the already-sent prefix);
 *    - a non-retryable error on chunk i → mark i `dead` and rethrow so the agent
 *      sees the real failure. Chunks 0…i-1 already landed (a partial reply — the
 *      honest outcome); i+1…N stay pending and the poller attempts/dead-letters
 *      them (a channel-wide non-retryable error dead-letters them the same way).
 *
 *  Throws `DurableUnavailableError` BEFORE recording if the session can't be
 *  activated or holds no lease — the caller falls back to a direct send.
 *
 *  Order guarantee: per-chunk obligations append in order and the poller drains a
 *  session's outbox in array order (`pendingDeliveries` + `drainOutbox`); the
 *  inline path posts in order and stops at the first transient gap. So a chunk
 *  never lands ahead of an earlier one — inline or via the poller. (ccsc-o7x.4) */
export async function deliverChunkedReplyDurably(
  deps: { supervisor: SessionSupervisor; post: ReplyPoster },
  reply: DurableChunkedReply,
): Promise<DurableChunkedDeliveryResult> {
  let handle: SessionHandle
  try {
    handle = await deps.supervisor.activate({ channel: reply.channel, thread: reply.thread })
  } catch (err) {
    throw new DurableUnavailableError(
      `cannot activate session: ${err instanceof Error ? err.message : String(err)}`,
    )
  }
  const lease = handle.lease
  if (lease === null) throw new DurableUnavailableError('session holds no lease')
  const token = lease.token

  // One obligation per chunk; the id folds in the chunk index so each carries a
  // distinct idempotency key (`ccsc-reply:<reply.id>:<i>`).
  const records = reply.chunks.map((payload, i) => ({
    id: `${reply.id}:${i}`,
    channel: reply.channel,
    thread: reply.thread,
    payload,
  }))

  // Record ALL N before ANY send (crash-before-send safe, all-or-nothing).
  await handle.recordTerminalDeliveries(token, records)

  let firstTs: string | undefined
  let delivered = 0
  for (const record of records) {
    const obligation: DeliveryObligation = { ...record, attempts: 0, state: 'pending', createdAt: 0 }
    const idemKey = deliveryIdempotencyKey(obligation)
    try {
      const ts = await deps.post(obligation, idemKey)
      if (delivered === 0) firstTs = ts
      await markObligation(handle, token, obligation.id, { state: 'delivered', attempts: 1 })
      delivered++
    } catch (err) {
      const code = extractSlackErrorCode(err)
      const lastError = code ?? (err instanceof Error ? err.message : String(err))
      if (classifyDeliveryError(code) === 'non-retryable') {
        await markObligation(handle, token, obligation.id, { state: 'dead', attempts: 1, lastError })
        throw err
      }
      // Transient: leave this chunk (and every later one) pending and STOP — the
      // poller redelivers the tail in order. Posting later chunks inline now
      // would land them ahead of this one once it retries.
      await markObligation(handle, token, obligation.id, {
        state: 'pending',
        attempts: 1,
        lastError,
      })
      return { status: 'queued', delivered, pending: records.length - delivered }
    }
  }
  return { status: 'delivered', ts: firstTs, sent: delivered }
}

/** Best-effort fenced patch of one obligation's state. Never throws: a fenced /
 *  save failure leaves the obligation as-is for the poller to reconcile (see
 *  `deliverReplyDurably`). */
async function markObligation(
  handle: SessionHandle,
  token: number,
  id: string,
  patch: { state: DeliveryObligation['state']; attempts: number; lastError?: string },
): Promise<void> {
  try {
    await handle.update(
      (prev) => ({
        ...prev,
        outbox: (prev.outbox ?? []).map((o) =>
          o.id === id
            ? {
                ...o,
                state: patch.state,
                attempts: patch.attempts,
                ...(patch.lastError !== undefined ? { lastError: patch.lastError } : {}),
              }
            : o,
        ),
      }),
      token,
    )
  } catch {
    // Swallow — the poller reconciles obligation state from disk.
  }
}
