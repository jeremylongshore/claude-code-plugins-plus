/**
 * mute-store.ts — Operator-initiated peer-bot mute store (ccsc-gjm).
 *
 * Second piece of the multi-agent epic (ccsc-7xq). The per-bot rate
 * limit (ccsc-gyt) catches automated A→B→A loops once they exceed
 * the threshold, but an operator who sees a loop forming wants a
 * faster manual escape valve. `!mute @CodexBot` in a channel adds
 * (channel, bot_id) to this store with a TTL; the inbound gate
 * consults the store and drops that bot's messages until the mute
 * expires (or the operator types `!unmute @CodexBot` for early
 * release).
 *
 * The store is in-memory only — same posture as the nonce store
 * (ccsc-ofn) and the peer-bot rate limit (ccsc-gyt). A restart
 * resets all mutes, which is the conservative posture (operator
 * sees a fresh channel after restart, not a hidden silent bot).
 *
 * Sibling-module pattern. Pure functions + injectable store.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Default mute TTL: 5 minutes. Long enough for the operator to
 *  diagnose what triggered the loop and adjust policy / talk to the
 *  bot's owner. Short enough that a forgotten mute auto-clears (no
 *  silent permanent state). Tunable per-call via `mute(..., ttlMs)`. */
export const DEFAULT_MUTE_TTL_MS = 5 * 60 * 1000

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

/** One active mute. Tracked per (channel, bot_id) — the same bot
 *  muted in one channel does NOT affect their delivery in other
 *  channels. */
export interface MuteEntry {
  channelId: string
  botId: string
  /** Wall-clock ms timestamp after which the mute auto-clears. */
  expiresAt: number
  /** Slack user_id of the operator who muted (for audit). */
  mutedBy: string
  /** When the mute was applied (for audit + diagnostics). */
  mutedAt: number
}

export interface MuteStore {
  /** Apply a mute. Overwrites any existing mute for the same
   *  (channel, bot_id) — the most-recent mute wins. */
  mute(channelId: string, botId: string, expiresAt: number, mutedBy: string, now: number): void
  /** Is (channel, bot_id) currently muted? Auto-prunes the entry
   *  if it has expired. Returns true when a live (unexpired) mute
   *  exists for the pair. */
  isMuted(channelId: string, botId: string, now: number): boolean
  /** Early release. No-op if the pair is not currently muted. */
  unmute(channelId: string, botId: string): boolean
  /** Diagnostic — list live mutes for a channel. Used by audit
   *  projection and operator-facing status commands. */
  list(channelId: string, now: number): readonly MuteEntry[]
  /** Sweep all expired entries across all channels. Returns the removed
   *  entries (ccsc-yl6k9) so the reaper can post a "mute expired" notice for
   *  each — operators aren't surprised when a bot silently un-mutes. Called
   *  periodically by the reaper. */
  prune(now: number): readonly MuteEntry[]
  /** Diagnostic — total live entries across all channels. */
  size(): number
}

// ---------------------------------------------------------------------------
// In-memory store
// ---------------------------------------------------------------------------

/** Build a fresh in-memory mute store. */
export function createMuteStore(): MuteStore {
  // Map keyed by `${channelId}\0${botId}` (NUL separator is safe —
  // Slack IDs are alphanumeric).
  const entries = new Map<string, MuteEntry>()

  function keyOf(channelId: string, botId: string): string {
    return `${channelId}\0${botId}`
  }

  return {
    mute(channelId, botId, expiresAt, mutedBy, now) {
      entries.set(keyOf(channelId, botId), {
        channelId,
        botId,
        expiresAt,
        mutedBy,
        mutedAt: now,
      })
    },
    isMuted(channelId, botId, now) {
      const entry = entries.get(keyOf(channelId, botId))
      if (entry === undefined) return false
      if (entry.expiresAt <= now) {
        // Auto-prune the stale entry. The gate's check shouldn't
        // pay the cost of a separate sweep just to filter out
        // ancient entries.
        entries.delete(keyOf(channelId, botId))
        return false
      }
      return true
    },
    unmute(channelId, botId) {
      return entries.delete(keyOf(channelId, botId))
    },
    list(channelId, now) {
      const result: MuteEntry[] = []
      for (const entry of entries.values()) {
        if (entry.channelId !== channelId) continue
        if (entry.expiresAt <= now) continue
        result.push(entry)
      }
      return result
    },
    prune(now) {
      const expired: MuteEntry[] = []
      for (const [key, entry] of entries) {
        if (entry.expiresAt <= now) {
          entries.delete(key)
          expired.push(entry)
        }
      }
      return expired
    },
    size() {
      return entries.size
    },
  }
}

// ---------------------------------------------------------------------------
// Slack-mention parsing — `<@U_BOT>` → bot id
// ---------------------------------------------------------------------------

/** Extract the user_id from a Slack mention token. Returns null if
 *  the input isn't a well-formed mention. Slack's mention shape is
 *  `<@U_USERID>` (or `<@U_USERID|display>` when a display name is
 *  cached). This parser tolerates both forms.
 *
 *  Used by the !mute / !unmute admin verbs to resolve the
 *  argument-side mention into a bot user_id that the store keys on
 *  AND that the gate's `allowBotIds` check uses. The same id space
 *  on both sides means an operator who can see the bot in the
 *  channel can mention it. */
export function parseSlackMention(token: string): string | null {
  // Match <@U_xxx> or <@U_xxx|display>. Slack user ids start with U
  // (humans) or B (bot tokens) or W (enterprise) — we accept any
  // identifier shape Slack issues and let the gate's allowBotIds
  // check authoritative.
  const match = /^<@([A-Z][A-Z0-9_]+)(?:\|[^>]*)?>$/.exec(token)
  return match === null ? null : match[1]!
}
