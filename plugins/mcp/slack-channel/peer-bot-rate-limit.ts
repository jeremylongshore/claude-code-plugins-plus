/**
 * peer-bot-rate-limit.ts — Per-(channel, bot_id) sliding-window rate
 * limit to break A→B→A runaway loops (ccsc-gyt).
 *
 * The first piece of the multi-agent epic (ccsc-7xq). When two peer
 * bots are opted into the same channel via `allowBotIds`, A's reply
 * triggers B which triggers A which triggers B — infinite loop unless
 * something breaks it. Existing event-dedup TTL helps but doesn't
 * specifically target the cross-bot case (each bot's message is a
 * legitimately distinct event from Slack's POV).
 *
 * The defense: track per-(channel, sender_bot_id) message timestamps
 * in a sliding window. When the count exceeds the threshold (default
 * 10 msgs in 60s), the inbound gate starts dropping that bot's
 * messages from that channel until the window slides past enough old
 * entries to bring the count back under threshold.
 *
 * Purely defensive — humans can still post freely. The cap only
 * applies to allowlisted PEER BOTS (events where `bot_id` is set).
 * Existing rate limits (event-dedup TTL, MAX_PENDING) stay in place
 * and apply orthogonally.
 *
 * Sibling-module pattern: pure functions + injectable store. Tests
 * import the production code path directly without server.ts boot
 * side effects. Mirrors acp-adapter.ts / policy-dispatch.ts / nonce-
 * hitl.ts / admin.ts / stream-reply.ts.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** Operator-tunable threshold + window. Default values target the
 *  realistic A→B→A loop pattern: two bots replying to each other
 *  every few seconds. 10 msgs in 60s is well above any plausible
 *  legitimate cross-bot conversation rate (humans interleave; loops
 *  don't) but low enough to catch a runaway exchange within seconds. */
export interface RateLimitConfig {
  /** Max messages allowed in the window. */
  count: number
  /** Sliding-window duration in ms. */
  windowMs: number
}

/** Conservative default: 10 messages in 60 seconds. Operators can
 *  tighten or loosen via `ChannelPolicy.peerBotRateLimit`. To opt
 *  OUT of rate limiting entirely (allow unlimited peer-bot messages
 *  in a channel), set `{ count: 0, windowMs: 0 }` — both `check()`
 *  and the gate integration short-circuit on either zero to "always
 *  allow". To deny all peer-bot delivery, use `allowBotIds: []`
 *  instead. (Per Gemini review on PR #182 — single coherent
 *  semantic across the store + gate.) */
export const DEFAULT_PEER_BOT_RATE_LIMIT: RateLimitConfig = {
  count: 10,
  windowMs: 60_000,
}

/** Channel-wide circuit-breaker default: 40 peer-bot messages in 60s summed
 *  across ALL bots in a channel (ccsc-0k7x2). The per-(channel, bot) limit
 *  above only breaks PAIRWISE loops — an A→B→C→A ring keeps every sender under
 *  its own cap, so the ring never trips it. This aggregate counter sits on top
 *  and trips the whole channel's bot traffic when total peer-bot velocity is
 *  runaway-high. Set to ~4× the per-bot default so a legitimate 2–3 bot
 *  exchange interleaved with human work never trips it, but a runaway ring
 *  (which fires as fast as the pipeline allows) does within seconds. Operators
 *  tune via `ChannelPolicy.channelCircuitBreaker`; `{ count: 0, windowMs: 0 }`
 *  disables it. */
export const DEFAULT_CHANNEL_CIRCUIT_BREAKER: RateLimitConfig = {
  count: 40,
  windowMs: 60_000,
}

/** Persistent state for the rate limiter. Carries per-(channel, botId)
 *  timestamp arrays under the longest configured window. Tests can
 *  inject this directly; production wires a single module-level store
 *  in server.ts.
 *
 *  The store is NOT persisted to disk by design. A restart resets all
 *  per-bot counters — same posture as the nonce store (ccsc-ofn): a
 *  fresh process means no leftover state to game. */
export interface PeerBotRateLimitStore {
  /** Record a message and return whether it's within the rate limit.
   *
   *  Semantics:
   *    - Return `true` (allow) when the count after adding this
   *      message is at or below `config.count`. The timestamp is
   *      appended.
   *    - Return `false` (drop) when adding this message would push
   *      the count above `config.count`. The timestamp is NOT
   *      appended — otherwise the array would grow unboundedly
   *      during the drop window and ages would skew.
   *
   *  Old timestamps (outside the window) are pruned on every call.
   *  This keeps memory bounded without a separate sweep task. */
  check(channelId: string, botId: string, now: number, config: RateLimitConfig): boolean
  /** Record a peer-bot message toward the CHANNEL-WIDE aggregate and return
   *  whether the channel is still under its circuit-breaker threshold
   *  (ccsc-0k7x2). Same sliding-window semantics as `check()` but keyed by
   *  channel alone, so it counts every allowlisted bot's traffic together —
   *  catching N-cycle (A→B→C→A) rings that stay under the per-bot cap. */
  checkChannel(channelId: string, now: number, config: RateLimitConfig): boolean
  /** List the bot IDs that posted in `channelId` within `windowMs` of `now`
   *  (ccsc-4e9bf) — a lightweight "agents online" view derived from the
   *  per-(channel, bot) activity already tracked. Read-only, no mutation. */
  activeBots(channelId: string, now: number, windowMs: number): string[]
  /** Sweep entries with all-expired timestamps. Called periodically
   *  by the reaper (similar to nonce-store pruneExpired). */
  prune(now: number, maxWindowMs: number): number
  /** Diagnostic — number of distinct (channel, bot) pairs tracked. */
  size(): number
}

// ---------------------------------------------------------------------------
// In-memory store
// ---------------------------------------------------------------------------

/** Shared sliding-window decision used by both the per-(channel, bot) limit and
 *  the per-channel aggregate breaker. Prunes stale timestamps for `key`, then
 *  ALLOWS (append + true) when under `config.count`, or DROPS (no append +
 *  false) at/over it. `{ count: 0 }` / `{ windowMs: 0 }` disables → always
 *  allow (and never records). Not appending on a drop keeps the array from
 *  growing during the drop window. */
function slidingWindowAllow(
  buckets: Map<string, number[]>,
  key: string,
  now: number,
  config: RateLimitConfig,
): boolean {
  // Operator opt-out: { count: 0, windowMs: 0 } disables the limit for this
  // call — always allow, record nothing. `<= 0` (not `=== 0`) so a negative
  // misconfiguration also disables rather than producing surprising behavior.
  // Single coherent semantic across the store + gate (per Gemini reviews on
  // PRs #182 and #246).
  if (config.count <= 0 || config.windowMs <= 0) return true

  const arr = buckets.get(key) ?? []
  // Drop stale timestamps before evaluating. In-place filter, memory bounded.
  const cutoff = now - config.windowMs
  let writeIdx = 0
  for (let i = 0; i < arr.length; i++) {
    if (arr[i]! > cutoff) {
      arr[writeIdx++] = arr[i]!
    }
  }
  arr.length = writeIdx

  if (arr.length >= config.count) {
    // Over threshold — DO NOT append. The next call after enough old entries
    // age out will succeed naturally. `arr` is necessarily non-empty here
    // (config.count >= 1 after the guard above, and arr.length >= config.count).
    buckets.set(key, arr)
    return false
  }

  arr.push(now)
  buckets.set(key, arr)
  return true
}

/** Sweep a bucket map of entries whose timestamps are all older than the
 *  window; returns the number of (key) entries removed. */
function pruneBuckets(buckets: Map<string, number[]>, now: number, maxWindowMs: number): number {
  let removed = 0
  const cutoff = now - maxWindowMs
  for (const [key, arr] of buckets) {
    let writeIdx = 0
    for (let i = 0; i < arr.length; i++) {
      if (arr[i]! > cutoff) {
        arr[writeIdx++] = arr[i]!
      }
    }
    if (writeIdx === 0) {
      buckets.delete(key)
      removed += 1
    } else {
      arr.length = writeIdx
    }
  }
  return removed
}

/** Build a fresh in-memory rate-limit store. */
export function createPeerBotRateLimitStore(): PeerBotRateLimitStore {
  // Per-(channel, bot) buckets, keyed `${channelId}\0${botId}`. NUL separator
  // is safe because Slack IDs are alphanumeric (no embedded NULs).
  const buckets = new Map<string, number[]>()
  // Per-channel aggregate buckets for the circuit breaker (ccsc-0k7x2), keyed
  // by channelId alone — a separate map so the two windows never collide.
  const channelBuckets = new Map<string, number[]>()

  return {
    check(channelId, botId, now, config) {
      return slidingWindowAllow(buckets, `${channelId}\0${botId}`, now, config)
    },
    checkChannel(channelId, now, config) {
      return slidingWindowAllow(channelBuckets, channelId, now, config)
    },
    activeBots(channelId, now, windowMs) {
      const prefix = `${channelId}\0`
      const cutoff = now - windowMs
      const result: string[] = []
      for (const [key, arr] of buckets) {
        if (!key.startsWith(prefix)) continue
        if (arr.some((ts) => ts > cutoff)) result.push(key.slice(prefix.length))
      }
      return result
    },
    prune(now, maxWindowMs) {
      return pruneBuckets(buckets, now, maxWindowMs) + pruneBuckets(channelBuckets, now, maxWindowMs)
    },
    size() {
      return buckets.size
    },
  }
}
