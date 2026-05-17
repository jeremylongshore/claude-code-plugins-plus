/**
 * manifest.ts — Peer-bot manifest schema (Epic 31-A).
 *
 * A manifest is a JSON payload that a peer agent posts in-channel to advertise
 * what it is: name, vendor, version, tools it exposes, channels it opts into,
 * and a contact address. Other bots and humans read manifests as *information*;
 * they are advertisements, never grants (Miller 2006, Robust Composition).
 *
 * This file intentionally has no imports from `policy.ts` or `lib.ts`'s
 * policy-adjacent surface. The symmetric constraint — `policy.ts` does not
 * import from this module — is enforced by the 31-A.4 invariant test in
 * `server.test.ts`. See `000-docs/bot-manifest-protocol.md` §91-109 for the
 * binding invariant and §17-55 for the on-wire schema this file encodes.
 *
 * Scope of this file for ccsc-s53.1:
 *   - The `ManifestV1` Zod schema with magic-header discriminator.
 *   - Inferred TypeScript type.
 *
 * Sibling beads add: size cap (s53.3), the `read_peer_manifests` MCP tool
 * (s53.2), and the 5-minute per-channel read cache (s53.5).
 *
 * SPDX-License-Identifier: MIT
 */

import { z } from 'zod'

// ---------------------------------------------------------------------------
// ManifestV1 — on-channel advertisement schema
// ---------------------------------------------------------------------------

/**
 * SemVer 2.0.0 subset accepted for `version`: `MAJOR.MINOR.PATCH` with an
 * optional pre-release suffix `-<alnum/dot/hyphen>`. Build metadata (`+…`)
 * is deliberately excluded — manifests that want to signal a build should
 * surface it via `description`, not the version field. Keeping the regex
 * narrow means downstream consumers that want to sort manifests can do so
 * without a full SemVer parser.
 */
const SEMVER_RE = /^\d+\.\d+\.\d+(-[A-Za-z0-9.-]+)?$/

/**
 * Slack public-channel ID shape. `C` + uppercase alphanumerics. DM IDs
 * (`D…`) and private-group IDs (`G…`) are deliberately rejected — a
 * manifest advertising participation in a DM or private group would leak
 * non-public information about the bot's reach and is out of scope for
 * the v1 protocol.
 */
const CHANNEL_ID_RE = /^C[A-Z0-9]+$/

/**
 * Zod schema for the v1 manifest payload.
 *
 * The literal `__claude_bot_manifest_v1__: true` property doubles as a
 * version discriminator: future protocol revisions will mint a new key
 * (e.g. `__claude_bot_manifest_v2__`) so consumers that understand only
 * v1 can skip unknown versions without false-matching them. Matches the
 * frozen contract in `000-docs/bot-manifest-protocol.md` §24-41.
 *
 * Validation failures (malformed JSON, missing fields, wrong types, size
 * cap violations, or the magic header missing / not literally `true`) are
 * silently dropped by the consumer — see the protocol doc §81 and bead
 * ccsc-s53.13 ("Drop malformed, invalid, and oversized manifests
 * silently"). This file only encodes the *shape*; the dropping happens in
 * the read tool (ccsc-s53.2) and the size-cap layer (ccsc-s53.3).
 */
/**
 * Optional A2A agent-card subset (Epic 31-B.6, bead ccsc-0qk.6).
 *
 * Shape-aligned with Google's Agent-to-Agent protocol
 * (/.well-known/agent-card.json) so a future HTTP-transport publish
 * path can reuse this field verbatim without a schema migration. The
 * fields here are deliberately a subset — the top-level ManifestV1
 * fields (name, vendor, version, description, tools) already carry
 * the overlap documented in bot-manifest-protocol.md's "Alignment
 * with Google A2A" section; agentCard carries the A2A-specific
 * metadata that has no Slack-side equivalent.
 *
 * Consumer contract: this field is metadata. The Slack read path
 * (extractManifests) accepts it but does nothing with it beyond
 * Zod validation. A peer that signals HTTP capabilities here does
 * not thereby get any additional trust — advertisements are not
 * grants, same as every other manifest field (§91-109).
 *
 * Sizes are conservative so an agentCard-bearing manifest comfortably
 * fits under the 8 KB publish cap.
 */
const AgentCard = z.object({
  /** HTTPS endpoints where the agent is also reachable. Optional —
   *  Slack-only bots omit. Capped at 10 entries; each entry is a
   *  fully-qualified URL. */
  endpoints: z.array(z.string().url()).max(10).optional(),

  /** Input/output content types the agent accepts/produces. Maps to
   *  A2A's defaultInputModes / defaultOutputModes. Values are MIME
   *  types (e.g. 'application/json') or schema URIs. */
  schemas: z
    .object({
      input: z.array(z.string().min(1).max(200)).max(20).optional(),
      output: z.array(z.string().min(1).max(200)).max(20).optional(),
    })
    .optional(),

  /** Authentication schemes the HTTPS surface expects. Public or
   *  Slack-only bots omit. Example values: 'bearer', 'apiKey',
   *  'oauth2'. */
  authentication: z
    .object({
      schemes: z.array(z.string().min(1).max(40)).max(10),
    })
    .optional(),

  /** Capability flags — A2A's defaults. Additional flags can land in a
   *  v2 agentCard schema without breaking existing readers (Zod strips
   *  unknown keys by default on z.object). */
  capabilities: z
    .object({
      streaming: z.boolean().optional(),
      pushNotifications: z.boolean().optional(),
    })
    .optional(),
})

export const ManifestV1 = z.object({
  __claude_bot_manifest_v1__: z.literal(true),
  name: z.string().min(1).max(80),
  vendor: z.string().min(1).max(80),
  version: z.string().regex(SEMVER_RE),
  description: z.string().max(1000),
  tools: z
    .array(
      z.object({
        name: z.string().min(1).max(80),
        description: z.string().max(400),
      }),
    )
    .max(50),
  channels: z.array(z.string().regex(CHANNEL_ID_RE)).max(50).optional(),
  contact: z.string().email().optional(),
  publishedAt: z.string().datetime(),
  /** Optional A2A agent-card subset. See `AgentCard` above for the
   *  shape and rationale. A manifest without this field is a
   *  Slack-only bot; a manifest with it advertises additional
   *  HTTP-level surface area for future interop. */
  agentCard: AgentCard.optional(),
})

/** Inferred type for a validated manifest payload. */
export type ManifestV1 = z.infer<typeof ManifestV1>

/**
 * The magic header key. Exported so the read tool (ccsc-s53.2) and any
 * pins.list discriminator can match on the same literal without repeating
 * the string. Consumers MUST check that the key's value is exactly `true`
 * before trusting the payload to be a v1 manifest — presence alone is not
 * enough (a peer could post `{"__claude_bot_manifest_v1__": "yes"}` and
 * that must not match).
 */
export const MANIFEST_V1_MAGIC_KEY = '__claude_bot_manifest_v1__' as const

/**
 * Hard cap on a single manifest's raw body, in bytes after UTF-8 encode
 * (Epic 31-A.3). The doc (§47) phrases the cap as "≤ 40 KB"; we treat
 * "KB" as 1024 bytes, the convention used everywhere else in this
 * codebase for memory-safety constants. Anything over is silently
 * dropped before `JSON.parse` is called — the point of the cap is to
 * bound the cost of the parse step, which can blow up memory
 * super-linearly on deeply-nested or hostile payloads. A peer that can
 * make us allocate 100 MB to parse one pinned message is a cheap DoS
 * otherwise.
 */
export const MAX_MANIFEST_BYTES = 40 * 1024

/**
 * Publish-side cap on the serialized manifest (Epic 31-B.2, bead
 * ccsc-0qk.2). Deliberately stricter than `MAX_MANIFEST_BYTES` by a
 * factor of 5 — Postel's Law: "be conservative in what you send,
 * liberal in what you receive." A publisher writes what it controls;
 * a reader tolerates what the peer happens to post. 8 KB is plenty
 * for a well-formed v1 manifest (the schema caps description at 1000
 * chars, up to 50 tools with ≤ 480 chars each, up to 50 channels) and
 * surfaces operator mistakes (e.g. a pasted API payload that should
 * have been a manifest) loudly at publish time.
 */
export const MAX_PUBLISH_MANIFEST_BYTES = 8 * 1024

// ---------------------------------------------------------------------------
// extractManifests — pure filter/parse/validate for a batch of message texts
// ---------------------------------------------------------------------------

/**
 * Cheap pre-filter: does a message body syntactically mention the magic
 * header key? Used to short-circuit the parse step for the overwhelming
 * majority of messages that are not manifest payloads. A false positive
 * here (message body that coincidentally contains the key string in
 * prose) is caught by `JSON.parse` or Zod on the next step — this is
 * purely a perf filter, never a trust signal.
 */
function looksLikeManifest(text: string): boolean {
  return text.includes(MANIFEST_V1_MAGIC_KEY)
}

/** UTF-8 byte length of a string. Uses TextEncoder so the count matches
 *  what Slack's servers and the doc mean by "40 KB after UTF-8 encode"
 *  (§47) — `string.length` would count UTF-16 code units and under-
 *  report for multi-byte code points. */
const utf8Encoder = new TextEncoder()
function utf8ByteLength(s: string): number {
  return utf8Encoder.encode(s).length
}

/**
 * Extract every valid v1 manifest from a batch of message texts (Epic
 * 31-A.2, bead ccsc-s53.2). The flow is:
 *
 *   1. skip null / undefined / non-string bodies
 *   2. cheap string-includes filter on the magic header key
 *   3. `JSON.parse` — silent drop on any throw
 *   4. `ManifestV1.safeParse` — silent drop on any Zod error
 *
 * "Silent drop" is the doc's chosen posture (§81, §255) for
 * malformed/invalid manifests: a peer posting garbage must not break the
 * consumer, and there is no caller-visible error channel because this is
 * advertising, not an API. Operators get ground truth via the 30-A
 * journal when the read tool logs the read event — per-message drop
 * details are intentionally not surfaced.
 *
 * The 40 KB raw-body size cap (ccsc-s53.3, §47) is enforced here too —
 * oversized bodies are dropped before `JSON.parse` is called so a
 * hostile pinned message cannot force gigabyte-scale allocation.
 *
 * Returns validated manifests in the order they appeared in the input.
 * Duplicate de-dup is NOT performed here — a channel that has the same
 * peer's manifest pinned AND in the last 50 messages will surface both
 * copies, and the caller (or Claude reading the tool output) decides
 * what to do with the duplication. Keeping this function position-
 * preserving and non-deduping makes it trivially testable.
 */
export function extractManifests(texts: ReadonlyArray<string | null | undefined>): ManifestV1[] {
  return texts.flatMap((text) => {
    if (typeof text !== 'string' || text.length === 0) return []
    if (!looksLikeManifest(text)) return []
    // 40 KB raw-body size cap (ccsc-s53.3). Checked *after* the
    // pre-filter (so we only pay the byte-count walk on candidate
    // payloads) but *before* `JSON.parse` (so the parser can't be
    // weaponised to allocate gigabytes on a hostile pinned message).
    // Oversized drops log a debug line because they are operator-
    // actionable — a peer hitting the cap is either buggy or adversarial.
    // Malformed-JSON and Zod-failure drops stay silent (see §81): common
    // and not a signal.
    const bytes = utf8ByteLength(text)
    if (bytes > MAX_MANIFEST_BYTES) {
      console.debug(`[manifest] silent drop: oversized body ${bytes}B > ${MAX_MANIFEST_BYTES}B cap`)
      return []
    }
    try {
      const parsed: unknown = JSON.parse(text)
      const result = ManifestV1.safeParse(parsed)
      return result.success ? [result.data] : []
    } catch {
      return []
    }
  })
}

// ---------------------------------------------------------------------------
// Per-channel read cache + rate limit (Epic 31-A.5, bead ccsc-s53.5)
// ---------------------------------------------------------------------------

/**
 * TTL for a cached per-channel manifest list. Doubles as the rate limit
 * on reads: within the TTL window, the consumer returns the cached value
 * and does not hit `pins.list` / `conversations.history` again. Design
 * doc §84. Five minutes is long enough that a chatty operator does not
 * spam Slack, short enough that a peer's manifest edit surfaces within
 * roughly a coffee break.
 */
export const MANIFEST_CACHE_TTL_MS = 5 * 60 * 1000

export interface ManifestCacheEntry {
  readonly cachedAt: number
  readonly manifests: ReadonlyArray<ManifestV1>
}

export interface ManifestCache {
  /** Return the cached manifests if the entry is fresh (age < TTL).
   *  Returns `undefined` on miss — either no entry, or the entry has
   *  expired. Expired entries are lazily evicted on access. Caller
   *  decides what to do on miss (fetch + `set`, typically). */
  get(channelId: string): ReadonlyArray<ManifestV1> | undefined
  /** Store `manifests` for `channelId`, stamped at the cache's `now()`.
   *  If the cache is at `maxEntries`, evicts the single oldest entry
   *  (smallest `cachedAt`) before inserting — soft LRU. */
  set(channelId: string, manifests: ReadonlyArray<ManifestV1>): void
  /** Drop every entry. Exposed for test teardown and for future
   *  operator commands (e.g. a `/manifest:flush` on schema change). */
  clear(): void
  /** Current entry count. Exposed for tests and operator inspection. */
  size(): number
}

export interface ManifestCacheOptions {
  /** Time source. Accept for testability; defaults to `Date.now`.
   *  Must return wall-clock milliseconds since the Unix epoch. */
  now?: () => number
  /** Soft cap on distinct-channel entries. When insertion would exceed
   *  this, the oldest entry is evicted. Default 256 — larger than the
   *  channel count in any realistic workspace, small enough to bound
   *  memory to roughly (maxEntries × 40 KB) worst case when every slot
   *  holds a cap-size manifest list. */
  maxEntries?: number
  /** Entry TTL in ms. Defaults to `MANIFEST_CACHE_TTL_MS`. Exposed for
   *  tests that need to exercise the expiry boundary without waiting
   *  five minutes of wall-clock time. */
  ttlMs?: number
}

/**
 * Create a per-channel manifest cache. Opaque over an internal
 * `Map<channelId, ManifestCacheEntry>` — the cache itself is a plain
 * object with method members, not a class, so there is no `this`
 * binding to worry about when the caller passes the methods around
 * (e.g. into a lambda). Entries are dropped on process exit by design
 * (protocol doc §166 "A restart clears it.") — persistence is out of
 * scope.
 */
export function createManifestCache(opts: ManifestCacheOptions = {}): ManifestCache {
  const now = opts.now ?? Date.now
  const maxEntries = opts.maxEntries ?? 256
  const ttlMs = opts.ttlMs ?? MANIFEST_CACHE_TTL_MS
  const store = new Map<string, ManifestCacheEntry>()

  return {
    get(channelId) {
      const entry = store.get(channelId)
      if (!entry) return undefined
      if (now() - entry.cachedAt >= ttlMs) {
        // Lazy eviction of an expired entry. Avoids a keep-alive bug
        // where an expired entry stays around forever because it's
        // never touched again — each `get` of an expired entry also
        // removes it.
        store.delete(channelId)
        return undefined
      }
      return entry.manifests
    },
    set(channelId, manifests) {
      // Soft LRU-by-age: on an insertion that would breach the cap,
      // drop the single entry with the smallest `cachedAt`. Scanning
      // the map is O(n) but n ≤ maxEntries = 256, so the cost is
      // bounded and negligible compared to the Slack round-trip that
      // populated the value.
      if (store.size >= maxEntries && !store.has(channelId)) {
        let oldestKey: string | undefined
        let oldestAt = Infinity
        for (const [k, v] of store) {
          if (v.cachedAt < oldestAt) {
            oldestAt = v.cachedAt
            oldestKey = k
          }
        }
        if (oldestKey !== undefined) store.delete(oldestKey)
      }
      store.set(channelId, { cachedAt: now(), manifests })
    },
    clear() {
      store.clear()
    },
    size() {
      return store.size
    },
  }
}

// ---------------------------------------------------------------------------
// Publish-size gate (Epic 31-B.2, bead ccsc-0qk.2)
// ---------------------------------------------------------------------------

/**
 * Serialize a validated manifest to its on-wire JSON form and assert
 * the UTF-8 byte count is within the 8 KB publish cap. Throws on
 * violation with a message that names both the actual byte count and
 * the cap, so an operator debugging a rejected publish knows exactly
 * which field to shrink.
 *
 * Returns the serialized string on success so the caller can post it
 * directly. Keeping serialization and size-check in one function
 * guarantees the bytes we measure are the bytes we post — a split
 * signature (`assertPublishSize(manifest)` + separate
 * `JSON.stringify` in the caller) would leave room for formatting
 * differences to silently raise the effective cap.
 *
 * Stricter than the 40 KB read-side cap (Postel's Law — strict on
 * output, liberal on input). See `MAX_PUBLISH_MANIFEST_BYTES` for the
 * reasoning.
 */
// ---------------------------------------------------------------------------
// findOurPriorManifestPins — pure filter for the replace sweep (ccsc-0qk.10)
// ---------------------------------------------------------------------------

/**
 * Shape we need from a pins.list item to decide whether it's a prior
 * manifest we posted. Kept deliberately minimal so the consumer can
 * pass Slack's full item shape via structural typing without a runtime
 * coercion — every field is optional so a file-kind pin (no `.message`)
 * is handled gracefully.
 */
export interface PinItemLike {
  readonly type?: string
  readonly message?: {
    readonly text?: string | null
    readonly bot_id?: string
    readonly user?: string
    readonly ts?: string
  }
}

/** Identity handles needed to recognise our own posts in a pins.list
 *  response. Either field may be empty when bootstrap hasn't finished
 *  populating them; the filter treats empty values as "don't match". */
export interface BotIdentity {
  readonly botId?: string
  readonly botUserId?: string
}

/**
 * Return the message timestamps of pins this bot posted that carry a
 * v1 manifest body (Epic 31-B.10, bead ccsc-0qk.10). Extracted from
 * the publish_manifest handler so the replace-sweep filter can be
 * tested independently of any Slack mock.
 *
 * Filter semantics, each applied as a distinct reject step:
 *
 *   1. type !== 'message' — skip file and file_comment pins.
 *   2. no message or no ts — not actionable.
 *   3. bot_id / user does not match our identity — peer's pin, don't touch.
 *   4. body does not contain the magic header — not a manifest,
 *      leave it alone even if we posted it.
 *
 * Returns ts values in the input's iteration order. Deduplication is
 * NOT performed — the caller (the publish handler) calls pins.remove
 * once per ts, and Slack itself de-dupes repeat removes.
 *
 * If both `selfBotId` and `botUserId` on `identity` are empty strings
 * (bootstrap hasn't populated them yet), the filter returns `[]` —
 * fail-closed: better to skip the replace sweep than to mistakenly
 * unpin a peer's manifest.
 */
export function findOurPriorManifestPins(
  items: ReadonlyArray<PinItemLike>,
  identity: BotIdentity,
): string[] {
  const selfBotId = identity.botId ?? ''
  const botUserId = identity.botUserId ?? ''
  if (!selfBotId && !botUserId) return []
  return items.flatMap((item) => {
    if (item.type !== 'message') return []
    const msg = item.message
    if (!msg?.ts) return []
    const isOurs =
      (!!selfBotId && msg.bot_id === selfBotId) || (!!botUserId && msg.user === botUserId)
    if (!isOurs) return []
    const text = msg.text ?? ''
    if (!text.includes(MANIFEST_V1_MAGIC_KEY)) return []
    return [msg.ts]
  })
}

// ---------------------------------------------------------------------------
// Publish rate limiter (Epic 31-B.4, bead ccsc-0qk.4)
// ---------------------------------------------------------------------------

/**
 * One publish per channel per hour. Prevents pin-spam if an operator
 * (or a misbehaving automation) triggers repeated publishes. Not
 * persisted — a process restart clears the window, which is the
 * accepted tradeoff for keeping this purely in-memory (doc §166 has
 * the same "restart clears" posture for the read cache).
 */
export const PUBLISH_RATE_LIMIT_MS = 60 * 60 * 1000

export interface PublishRateLimiter {
  /**
   * Check whether `channelId` is currently in a cooldown window and,
   * if not, record `now()` as the most-recent publish timestamp. The
   * record happens BEFORE the caller's actual publish — reserving the
   * slot — so a concurrent or retried call sees the cooldown even if
   * the first call's publish is mid-flight or later fails. A rate
   * limiter that rolls back on downstream failure is trivially
   * bypassable (retry until success), which is not what we want here.
   *
   * Throws on a hit with an ID-bearing, time-bearing message naming
   * both the channel and the approximate minutes remaining until the
   * next publish is allowed.
   */
  checkAndRecord(channelId: string): void
  /** Drop every entry. For tests and future operator commands. */
  clear(): void
  /** Current entry count. For tests and operator inspection. */
  size(): number
}

export interface PublishRateLimiterOptions {
  /** Time source. Defaults to `Date.now`. */
  now?: () => number
  /** Window length in ms. Defaults to `PUBLISH_RATE_LIMIT_MS`. */
  windowMs?: number
  /** Soft cap on distinct-channel entries. Default 256 — same bound
   *  as the read cache; larger than any realistic workspace channel
   *  count, small enough to cap memory. */
  maxEntries?: number
}

/**
 * Create an in-memory per-channel publish rate limiter. Symmetric to
 * `createManifestCache` on the read side: plain-object factory, no
 * `this` binding concerns, injected time source for testability,
 * soft-LRU eviction when the entry cap would be breached.
 */
export function createPublishRateLimiter(opts: PublishRateLimiterOptions = {}): PublishRateLimiter {
  const now = opts.now ?? Date.now
  const windowMs = opts.windowMs ?? PUBLISH_RATE_LIMIT_MS
  const maxEntries = opts.maxEntries ?? 256
  const store = new Map<string, number>()

  return {
    checkAndRecord(channelId) {
      const currentMs = now()
      const lastMs = store.get(channelId)
      if (lastMs !== undefined && currentMs - lastMs < windowMs) {
        const remainingMs = windowMs - (currentMs - lastMs)
        const remainingMins = Math.max(1, Math.ceil(remainingMs / 60_000))
        throw new Error(
          `Publish rate limit: channel '${channelId}' was last published ` +
            `${Math.floor((currentMs - lastMs) / 60_000)}m ago; 1-per-hour window. ` +
            `Try again in ~${remainingMins}m.`,
        )
      }
      // Soft-LRU eviction matches the read cache pattern — drop the
      // entry with the smallest timestamp when we'd otherwise breach
      // maxEntries on an insertion for a new channel.
      if (store.size >= maxEntries && !store.has(channelId)) {
        let oldestKey: string | undefined
        let oldestAt = Infinity
        for (const [k, v] of store) {
          if (v < oldestAt) {
            oldestAt = v
            oldestKey = k
          }
        }
        if (oldestKey !== undefined) store.delete(oldestKey)
      }
      store.set(channelId, currentMs)
    },
    clear() {
      store.clear()
    },
    size() {
      return store.size
    },
  }
}

export function assertPublishSizeAndSerialize(manifest: ManifestV1): string {
  const body = JSON.stringify(manifest, null, 2)
  const bytes = utf8ByteLength(body)
  if (bytes > MAX_PUBLISH_MANIFEST_BYTES) {
    throw new Error(
      `Publish size: manifest serializes to ${bytes}B > ${MAX_PUBLISH_MANIFEST_BYTES}B cap. ` +
        `Shrink description, tools[], or channels[] before republishing.`,
    )
  }
  return body
}
