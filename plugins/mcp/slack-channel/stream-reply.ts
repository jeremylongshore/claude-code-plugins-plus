/**
 * stream-reply.ts — Progressive Slack reply via chat.update (ccsc-ele).
 *
 * Final piece of the CCSC rollout (#167). Collapses perceived-latency
 * for long Claude replies by posting an initial chunk via
 * chat.postMessage and progressively appending via chat.update on the
 * same `ts`. The user sees the message grow in real time, the same UX
 * pattern Anthropic's TTFT-optimised streaming targets.
 *
 * Locked design decisions (rollout plan P0 #9, verification plan #8):
 *   - ONE `gate.outbound.allow` event at stream start carrying the
 *     pre-committed full-text hash. The hash is computed before any
 *     chunk is sent, so a tamper that splices content into a later
 *     chunk would fail at finalize.
 *   - ONE `system.stream_finalize` event at stream end carrying the
 *     chunk count + completion hash. The hash MUST match the
 *     pre-committed value (invariant).
 *   - NO per-chunk journal events — would cause O(n²) canonicalize
 *     cost on the chain AND introduce a finalization race where
 *     events get out of order between writers.
 *   - assertOutboundAllowed runs on EVERY chunk (not just the
 *     initial). The journal records the decision once; the gate
 *     check happens every time. If the channel is removed mid-stream,
 *     subsequent chat.update calls fail at the gate and the stream
 *     finalizes with a `failure_reason`.
 *   - chat.update uses the cached `(channel, ts)` returned by the
 *     initial chat.postMessage. The dispatcher never recomputes the
 *     ts — that's the cached-ts invariant from the audit-journal
 *     architecture doc.
 *
 * Sibling-module pattern (same as acp-adapter.ts, policy-dispatch.ts,
 * nonce-hitl.ts, admin.ts): pure, all side-effectful deps injected,
 * tests import the production code path directly without triggering
 * server.ts boot-time exit paths.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { createHash } from 'node:crypto'
import { chunkText } from './lib.ts'
import type { JournalWriter } from './journal.ts'

// ---------------------------------------------------------------------------
// Defaults
// ---------------------------------------------------------------------------

/** Slack's chat.update rate limit is documented as 1 req/sec per
 *  channel (Tier 4). 1000ms between chunks is the safe floor.
 *  Operator-tunable but the default is conservative. */
export const DEFAULT_STREAM_RATE_LIMIT_MS = 1000

/** Default chunk size — ~500 chars feels like fast incremental reveal
 *  without spamming the rate limit. Slack hard limit on chat.update
 *  text is 40,000 chars; the message stays well under it even on the
 *  longest chains. */
export const DEFAULT_STREAM_CHUNK_SIZE = 500

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Dependencies the streamer needs. Injected so tests can swap mocks
 *  for the side-effectful pieces (Slack API, journal, clock) and
 *  exercise the orchestration without network or filesystem. */
export interface StreamReplyDeps {
  /** Outbound-gate check — throws if (channel, threadTs) is not in
   *  the allowlist + delivered-threads set. Runs on EVERY chunk. */
  assertOutboundAllowed: (channel: string, threadTs: string | undefined) => void
  /** Initial Slack post. Returns the message ts that subsequent
   *  chat.update calls target. The dispatcher caches this ts and
   *  never recomputes it. */
  postMessage: (args: {
    channel: string
    thread_ts?: string
    text: string
  }) => Promise<{ ts: string }>
  /** Slack chat.update. Targets the cached (channel, ts) from
   *  postMessage. The `text` argument carries the FULL running total
   *  up to and including the new chunk — this is Slack's intended
   *  semantics for progressive reveal (the message body is replaced,
   *  not appended-to, on each update). */
  updateMessage: (args: { channel: string; ts: string; text: string }) => Promise<void>
  /** Journal writer — exactly TWO events per stream: one
   *  `gate.outbound.allow` at start + one `system.stream_finalize`
   *  at end. */
  journalWrite: (input: Parameters<JournalWriter['writeEvent']>[0]) => Promise<unknown>
  /** Sleep helper — separates chunks to respect Slack's per-channel
   *  rate limit. Tests inject a no-op or instrumented version to
   *  exercise the rate-limit branch without wall-clock waits. */
  sleep: (ms: number) => Promise<void>
}

/** Configuration for one stream. `channel` + `text` are required;
 *  everything else has a default. */
export interface StreamReplyOptions {
  channel: string
  threadTs?: string
  text: string
  chunkSize?: number
  rateLimitMs?: number
}

/** Outcome of `streamReply`. Two terminal states + one mid-stream
 *  failure path. All carry the cached `ts` so the caller can locate
 *  the (possibly partially-updated) Slack message for diagnostics. */
export type StreamReplyResult =
  | {
      kind: 'completed'
      ts: string
      chunksSent: number
      committedHash: string
    }
  | {
      kind: 'failed_mid_stream'
      ts: string
      chunksSent: number
      committedHash: string
      reason: string
    }
  | {
      kind: 'gate_rejected_at_start'
      reason: string
    }

// ---------------------------------------------------------------------------
// streamReply — the orchestrator
// ---------------------------------------------------------------------------

/** Stream a Slack reply progressively via chat.update.
 *
 *  Pipeline:
 *
 *    1. assertOutboundAllowed(channel, threadTs)
 *       → on throw: return `gate_rejected_at_start`, no journal event
 *    2. Compute full-text SHA-256 (the pre-commit hash)
 *    3. Chunk via lib.ts:chunkText(text, chunkSize, 'length')
 *    4. journalWrite({ kind: 'gate.outbound.allow', body: { full_text_hash, expected_chunks } })
 *    5. postMessage({ channel, thread_ts, text: chunks[0] })
 *       → cache the returned ts
 *    6. For each subsequent chunk:
 *       a. sleep(rateLimitMs)
 *       b. assertOutboundAllowed (channel removal mid-stream → failure path)
 *       c. updateMessage({ channel, ts, text: cumulative })
 *       → on assertOutboundAllowed throw OR updateMessage reject:
 *          journalWrite({ kind: 'system.stream_finalize', outcome: 'deny', reason })
 *          return `failed_mid_stream`
 *    7. journalWrite({ kind: 'system.stream_finalize', outcome: 'allow', chunks_sent })
 *    8. return `completed`
 *
 *  No per-chunk journal events. The pre-commit hash + finalize-with-
 *  matching-hash invariant means a journal reader can verify the
 *  full message content without needing to replay every intermediate
 *  state.
 *
 *  Returns a structured result for normal completion + mid-stream
 *  failures. **Re-throws on init failures**: if
 *  `journalWrite(gate.outbound.allow)` throws OR `postMessage` throws
 *  before any chunks land, the exception propagates. Rationale: a
 *  failure at init means either the audit log is broken (refuse to
 *  post bytes that can't be journaled) or Slack itself is unreachable
 *  (caller decides whether to retry). In both cases, no Slack
 *  content was delivered. On `postMessage` throw the dispatcher
 *  writes a defensive `system.stream_finalize` with deny outcome
 *  before re-throwing, so the "one allow + one finalize" invariant
 *  holds even on early failure (per Gemini review on PR #181). All
 *  other paths (mid-stream gate rejection, mid-stream Slack error,
 *  finalize-write failure) return a structured result.
 */
export async function streamReply(
  opts: StreamReplyOptions,
  deps: StreamReplyDeps,
): Promise<StreamReplyResult> {
  const chunkSize = opts.chunkSize ?? DEFAULT_STREAM_CHUNK_SIZE
  const rateLimitMs = opts.rateLimitMs ?? DEFAULT_STREAM_RATE_LIMIT_MS

  // Step 1: gate check at start. Failure here is a clean reject —
  // no Slack post, no journal event, the caller knows the channel
  // never received any content.
  try {
    deps.assertOutboundAllowed(opts.channel, opts.threadTs)
  } catch (err) {
    return {
      kind: 'gate_rejected_at_start',
      reason: err instanceof Error ? err.message : String(err),
    }
  }

  // Guard against empty input (per Gemini review on PR #181). Empty
  // text would either crash at `chunks[0]!` (if chunkText returned
  // [], depending on implementation details) OR send an empty
  // message to Slack (today chunkText returns [""] which is just as
  // bad — empty Slack post). Caller has a bug if they're streaming
  // nothing; reject loudly. The check uses opts.text directly so a
  // future chunkText refactor doesn't reopen the gap.
  if (opts.text.length === 0) {
    return { kind: 'gate_rejected_at_start', reason: 'empty text — nothing to stream' }
  }

  // Step 2: pre-commit hash.
  const committedHash = createHash('sha256').update(opts.text, 'utf8').digest('hex')

  // Step 3: chunk.
  const chunks = chunkText(opts.text, chunkSize, 'length')

  // Step 4: journal the allow with pre-committed hash. The chain
  // commits to the full content at stream START — any later attempt
  // to splice different content would break the finalize-hash check.
  await deps.journalWrite({
    kind: 'gate.outbound.allow',
    outcome: 'allow',
    actor: 'claude_process',
    sessionKey: opts.threadTs !== undefined
      ? { channel: opts.channel, thread: opts.threadTs }
      : undefined,
    input: {
      stream: true,
      full_text_hash: committedHash,
      expected_chunks: chunks.length,
    },
  })

  // Step 5: initial post. The returned ts is the cached id for
  // every subsequent chat.update.
  //
  // Wrap in try/catch so a postMessage failure between the
  // gate.outbound.allow journal write and any chunks landing still
  // produces a matching system.stream_finalize event (per Gemini
  // review on PR #181 — the "exactly TWO journal events per stream"
  // invariant must hold even on early failure). The exception
  // re-throws after the finalize is written; caller treats this
  // exactly like the journal-allow-write failure path.
  let initial: { ts: string }
  try {
    initial = await deps.postMessage({
      channel: opts.channel,
      thread_ts: opts.threadTs,
      text: chunks[0]!,
    })
  } catch (err) {
    const reason = `postMessage failed: ${err instanceof Error ? err.message : String(err)}`
    // No ts to report — postMessage threw before returning one.
    // Use empty string as a placeholder; the chunks_sent: 0 in the
    // finalize event tells the story.
    await finalizeJournal(deps, opts, '', 0, committedHash, 'deny', reason)
    throw err
  }
  const ts = initial.ts
  let chunksSent = 1
  let cumulative = chunks[0]!

  // Step 6: progressive update. Each update carries the running
  // total — Slack's chat.update semantic is "replace the message
  // body" so we always send everything-so-far.
  for (let i = 1; i < chunks.length; i++) {
    cumulative += chunks[i]!
    try {
      await deps.sleep(rateLimitMs)
      // Gate check every chunk. If the channel is removed from
      // access mid-stream, this throws and we finalize with the
      // failure reason recorded.
      deps.assertOutboundAllowed(opts.channel, opts.threadTs)
      await deps.updateMessage({ channel: opts.channel, ts, text: cumulative })
      chunksSent += 1
    } catch (err) {
      const reason = err instanceof Error ? err.message : String(err)
      await finalizeJournal(deps, opts, ts, chunksSent, committedHash, 'deny', reason)
      return { kind: 'failed_mid_stream', ts, chunksSent, committedHash, reason }
    }
  }

  // Step 7: stream finalized cleanly. Recompute the hash on the
  // cumulative text and verify it matches the pre-committed value —
  // a defensive identity check (catches a buggy chunker that
  // dropped/duplicated content).
  const finalHash = createHash('sha256').update(cumulative, 'utf8').digest('hex')
  if (finalHash !== committedHash) {
    const reason = `pre-commit hash ${committedHash} does not match finalize hash ${finalHash}`
    await finalizeJournal(deps, opts, ts, chunksSent, committedHash, 'deny', reason)
    return { kind: 'failed_mid_stream', ts, chunksSent, committedHash, reason }
  }

  await finalizeJournal(deps, opts, ts, chunksSent, committedHash, 'allow')
  return { kind: 'completed', ts, chunksSent, committedHash }
}

/** Common path for the terminal system.stream_finalize event.
 *  Defensive on throw — a broken journal does NOT change the stream
 *  outcome, just logs to stderr. */
async function finalizeJournal(
  deps: StreamReplyDeps,
  opts: StreamReplyOptions,
  ts: string,
  chunksSent: number,
  committedHash: string,
  outcome: 'allow' | 'deny',
  reason?: string,
): Promise<void> {
  try {
    await deps.journalWrite({
      kind: 'system.stream_finalize',
      outcome: outcome === 'allow' ? 'allow' : 'deny',
      actor: 'claude_process',
      sessionKey:
        opts.threadTs !== undefined
          ? { channel: opts.channel, thread: opts.threadTs }
          : undefined,
      input: {
        ts,
        chunks_sent: chunksSent,
        committed_hash: committedHash,
      },
      ...(reason !== undefined ? { reason } : {}),
    })
  } catch (err) {
    console.error('[slack] journal.writeEvent failed (system.stream_finalize)', {
      error: err instanceof Error ? err.message : String(err),
    })
  }
}
