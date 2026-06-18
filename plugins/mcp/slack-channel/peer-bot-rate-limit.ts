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
  /** Sweep entries with all-expired timestamps. Called periodically
   *  by the reaper (similar to nonce-store pruneExpired). */
  prune(now: number, maxWindowMs: number): number
  /** Diagnostic — number of distinct (channel, bot) pairs tracked. */
  size(): number
}

// ---------------------------------------------------------------------------
// In-memory store
// ---------------------------------------------------------------------------

/** Build a fresh in-memory rate-limit store. */
export function createPeerBotRateLimitStore(): PeerBotRateLimitStore {
  // Map<`${channelId}\0${botId}`, number[]>. NUL separator is safe
  // because Slack IDs are alphanumeric (no embedded NULs).
  const buckets = new Map<string, number[]>()

  function keyOf(channelId: string, botId: string): string {
    return `${channelId}\0${botId}`
  }

  return {
    check(channelId, botId, now, config) {
      // Operator opt-out: { count: 0, windowMs: 0 } (or either zero)
      // means "disable the rate limit for this call". Always allow,
      // do NOT record a timestamp. This matches the ChannelPolicy
      // contract documented in lib.ts and the gate-integration
      // short-circuit. Per Gemini review on PR #182 — single
      // coherent semantic across the store + gate.
      if (config.count === 0 || config.windowMs === 0) return true

      const key = keyOf(channelId, botId)
      const arr = buckets.get(key) ?? []
      // Drop stale timestamps before evaluating. In-place filter to
      // keep memory bounded.
      const cutoff = now - config.windowMs
      let writeIdx = 0
      for (let i = 0; i < arr.length; i++) {
        if (arr[i]! > cutoff) {
          arr[writeIdx++] = arr[i]!
        }
      }
      arr.length = writeIdx

      if (arr.length >= config.count) {
        // Over threshold — DO NOT append. The next call after enough
        // old entries age out will succeed naturally.
        if (arr.length === 0) buckets.delete(key)
        else buckets.set(key, arr)
        return false
      }

      arr.push(now)
      buckets.set(key, arr)
      return true
    },
    prune(now, maxWindowMs) {
      let removed = 0
      const cutoff = now - maxWindowMs
      for (const [key, arr] of buckets) {
        // Filter in-place; drop the whole entry if no live timestamps.
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
    },
    size() {
      return buckets.size
    },
  }
}
