/**
 * admin.ts — Operator admin command dispatcher (ccsc-3w0).
 *
 * The convergence point of the CCSC rollout (#167). Admin verbs
 * `!clear` and `!restart` are the most-destructive operator actions
 * the bridge exposes; they were the original story that kicked off
 * the rollout (gog5-ops PR #157, self-closed). This module is the
 * hardened reimplementation specified in the rollout plan + tracking
 * issue #167.
 *
 * Design lineage (all decisions locked in the rollout plan):
 *   - admin.clear / admin.restart are VIRTUAL policy tools — NOT
 *     registered MCP tools. Claude cannot invoke them by tool call;
 *     only operator Slack commands trigger them. This is enforced
 *     by a test asserting no MCP tool name starts with `admin.`.
 *   - The dispatcher routes through gate → parse → policy.evaluate
 *     → journal.write → execute. Same shape as every other tool
 *     call; admin verbs are not a bypass path.
 *   - !restart requires HMAC nonce + cross-channel confirmation
 *     (ccsc-ofn primitives) as a DAY-1 hard requirement. !clear is
 *     reversible and runs without nonce friction.
 *   - argv-mode execFileSync ('tmux', [...]) — no shell interpolation,
 *     no shell-injection surface. Keystrokes are hardcoded constants.
 *   - admin events sign under v2 (ccsc-22l) with policy_attestation
 *     from day 1.
 *
 * Module placement: sibling to policy.ts, journal.ts, etc. Imports
 * those for the dispatch path; FORBIDDEN by depcruise from importing
 * manifest.ts (mirrors the 31-A.4 isolation invariant — admin verbs
 * are authoritative, manifest data is advertising). Sibling module
 * for the same reason policy-dispatch.ts and nonce-hitl.ts are
 * siblings: the test suite imports the production code path directly
 * without triggering server.ts boot-time side effects.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
import type { JournalWriter } from './journal.ts'
import { DEFAULT_MUTE_TTL_MS, type MuteStore, parseSlackMention } from './mute-store.ts'
import type { RateLimitConfig } from './peer-bot-rate-limit.ts'
import type { NonceStore } from './nonce-hitl.ts'
import { verifyNonce } from './nonce-hitl.ts'

const execFileAsync = promisify(execFile)

// ---------------------------------------------------------------------------
// Types — AdminCommand discriminated union
// ---------------------------------------------------------------------------

/** Common fields on every admin command, regardless of verb. The
 *  dispatcher consumes these for journal writes, policy evaluation,
 *  and Slack reaction posting. */
export interface AdminCommandBase {
  /** Slack channel ID where the verb was uttered. The nonce flow
   *  enforces redemption in the same channel; the journal records it. */
  channelId: string
  /** Slack user_id of the operator who issued the verb. Must be on
   *  the channel's adminCommands.allowFrom list. */
  requestedBy: string
  /** Slack thread_ts where the verb appeared. Reactions post here. */
  threadTs: string
  /** Slack message_ts for the reaction target. */
  messageTs: string
}

/** !clear — reversible: clears bridge session state + Claude TUI
 *  conversation in one operation. No nonce required. */
export interface AdminClearCommand extends AdminCommandBase {
  kind: 'clear'
}

/** !restart — destructive: exits the Claude TUI session via tmux
 *  send-keys '/exit'. Requires HMAC nonce + cross-channel confirmation
 *  (ccsc-ofn) from day 1. */
export interface AdminRestartCommand extends AdminCommandBase {
  kind: 'restart'
  /** The nonce the operator supplied. When undefined, the dispatcher
   *  must MINT a fresh nonce and DM it to the operator (challenge
   *  phase). When defined, the dispatcher VERIFIES the nonce
   *  (redemption phase). */
  nonce: string | undefined
}

/** !mute @<bot> — reversible: silences the named peer bot in this
 *  channel for a TTL (default 5 min). No nonce required (reversible,
 *  auto-expiring). Carries the resolved target bot id. */
export interface AdminMuteCommand extends AdminCommandBase {
  kind: 'mute'
  /** Slack user_id of the bot to mute, resolved from the `@<bot>`
   *  mention argument via parseSlackMention. */
  targetBotId: string
}

/** !unmute @<bot> — reversible: early release for a previously
 *  muted bot. No nonce required. */
export interface AdminUnmuteCommand extends AdminCommandBase {
  kind: 'unmute'
  targetBotId: string
}

/** !mute-status — READ-ONLY (ccsc-yl6k9): list the channel's active peer-bot
 *  mutes + remaining TTL. No arg, no state change. */
export interface AdminMuteStatusCommand extends AdminCommandBase {
  kind: 'mute-status'
}

/** !rate-limit — READ-ONLY (ccsc-yl6k9): show the channel's effective peer-bot
 *  rate limit + circuit-breaker thresholds. No arg, no state change. Tuning the
 *  numbers stays terminal-only (access.json) by design — a Slack message must
 *  never loosen a security limit. */
export interface AdminRateLimitCommand extends AdminCommandBase {
  kind: 'rate-limit'
}

/** !agents — READ-ONLY (ccsc-4e9bf): list the peer bots seen active in this
 *  channel recently. A lightweight "who's online" view; no arg, no state
 *  change. */
export interface AdminAgentsCommand extends AdminCommandBase {
  kind: 'agents'
}

export type AdminCommand =
  | AdminClearCommand
  | AdminRestartCommand
  | AdminMuteCommand
  | AdminUnmuteCommand
  | AdminMuteStatusCommand
  | AdminRateLimitCommand
  | AdminAgentsCommand

// ---------------------------------------------------------------------------
// Parser — text → AdminCommand
// ---------------------------------------------------------------------------

/** Matches the admin-verb shape:
 *    !clear
 *    !restart [<nonce>]
 *    !mute <@U_BOT>
 *    !unmute <@U_BOT>
 *
 *  Anchored — the dispatcher caller is responsible for stripping any
 *  Slack mention prefix to the BRIDGE bot (`<@U_BRIDGE>`) before
 *  passing text in (see `stripBotMention()` in lib.ts). The
 *  ARGUMENT-side mention (the target bot in mute/unmute) is part of
 *  the verb syntax and stays.
 *
 *  Argument capture uses `.+` (not `\S+`) so Slack mentions whose
 *  display-name label contains a space (e.g., `<@U123|Alice Smith>`)
 *  are captured as a single token. Per Gemini review on PR #183 —
 *  legitimate Slack display names regularly contain spaces and the
 *  previous `\S+` would silently refuse to match those. The
 *  downstream `parseSlackMention` accepts spaces inside the
 *  display-name capture (`[^>]*`).
 */
// `mute-status` / `rate-limit` precede `mute` so the longer verb wins the
// alternation; both take no argument (ccsc-yl6k9).
const ADMIN_COMMAND_RE =
  /^!(clear|restart|mute-status|rate-limit|agents|mute|unmute)(?:\s+(.+))?$/

/** Parse a normalized text body into an `AdminCommand`, or `null` if
 *  the text doesn't match an admin verb. Pure function — no side
 *  effects, no policy evaluation, no Slack calls. The dispatcher
 *  composes this with policy + journal + execution.
 *
 *  Input contract:
 *    - `text` MUST already be mention-stripped (e.g., `!clear` not
 *      `<@U_BOT> !clear`).
 *    - The dispatcher caller is responsible for trim + normalize.
 *
 *  Return:
 *    - `AdminClearCommand` for `!clear` (no args permitted)
 *    - `AdminRestartCommand` for `!restart` (nonce arg optional)
 *    - `null` for any non-match — the caller treats this as a normal
 *      inbound message and proceeds with the regular gate.
 */
export function parseAdminCommand(
  text: string,
  envelope: AdminCommandBase,
): AdminCommand | null {
  const match = ADMIN_COMMAND_RE.exec(text.trim())
  if (match === null) return null
  const verb = match[1] as
    | 'clear'
    | 'restart'
    | 'mute'
    | 'unmute'
    | 'mute-status'
    | 'rate-limit'
    | 'agents'
  const arg = match[2]

  if (verb === 'clear') {
    // !clear takes NO arguments. If an arg was provided, refuse to
    // match — the operator likely typo'd. Falling through to null
    // means the message is treated as normal chat (the gate may still
    // refuse it for other reasons). This is the conservative choice.
    if (arg !== undefined) return null
    return { kind: 'clear', ...envelope }
  }

  // !mute-status / !rate-limit / !agents — read-only, no argument (ccsc-yl6k9,
  // ccsc-4e9bf). Same conservative rule as !clear: a stray arg falls through to
  // normal chat.
  if (verb === 'mute-status' || verb === 'rate-limit' || verb === 'agents') {
    if (arg !== undefined) return null
    return { kind: verb, ...envelope }
  }

  if (verb === 'restart') {
    return { kind: 'restart', nonce: arg, ...envelope }
  }

  // verb === 'mute' or 'unmute' — argument MUST be a Slack mention
  // that resolves to a bot user_id. Failure to resolve falls through
  // to null (treated as normal chat).
  if (arg === undefined) return null
  const targetBotId = parseSlackMention(arg)
  if (targetBotId === null) return null
  if (verb === 'mute') return { kind: 'mute', targetBotId, ...envelope }
  return { kind: 'unmute', targetBotId, ...envelope }
}

// ---------------------------------------------------------------------------
// Dispatcher — orchestrate policy + journal + execute
// ---------------------------------------------------------------------------

/** Outcome of `dispatchAdminCommand`. The dispatcher never throws —
 *  every failure path returns a structured outcome so the caller can
 *  react (e.g., post a Slack message explaining why a verb was
 *  rejected). */
export type DispatchOutcome =
  | { kind: 'executed'; verb: 'clear' | 'restart' | 'mute' | 'unmute' }
  | { kind: 'challenge_issued'; nonce: string; expiresAt: number }
  | { kind: 'denied'; reason: string }
  /** Read-only verb result (ccsc-yl6k9). The dispatcher built a status
   *  message; the caller posts it to the channel. No state changed. */
  | { kind: 'status'; verb: 'mute-status' | 'rate-limit' | 'agents'; message: string }

/** Dependencies the dispatcher needs. Injected so tests can swap
 *  mocks for the side-effectful pieces (tmux, journal, Slack, nonce
 *  store) and exercise the orchestration in isolation. */
export interface DispatchDeps {
  /** Evaluate the channel's adminCommands.allowFrom rule. Returns
   *  true if the requester is allowed to issue admin verbs in this
   *  channel; false otherwise. The caller is responsible for
   *  channel-policy lookup. */
  isAllowed: (channelId: string, userId: string) => boolean
  /** Journal writer for admin events. Awaited so the durable record
   *  exists BEFORE Slack reactions / tmux execution happen. */
  journalWrite: (input: Parameters<JournalWriter['writeEvent']>[0]) => Promise<unknown>
  /** Quiesce + deactivate the operator's bridge-side session state
   *  (called by !clear). Provided by SessionSupervisor. */
  quiesceAndDeactivate: () => Promise<void>
  /** Send a literal keystroke sequence to the tmux session that hosts
   *  Claude Code. argv-mode by construction — the dispatcher passes
   *  the keys array verbatim; the implementation must use
   *  `execFile('tmux', ['send-keys', ...args])` with no shell
   *  interpolation. Returns a Promise so the dispatcher does not
   *  block the event loop on synchronous process execution (Gemini
   *  review on PR #180). Tests inject a Promise-returning no-op. */
  sendTmuxKeys: (keys: readonly string[]) => Promise<void>
  /** Mint a fresh HMAC nonce + DM it to the operator. Returns the
   *  challenge so the dispatcher can journal the issuance. */
  issueChallenge: (
    userId: string,
    channelId: string,
  ) => Promise<{ nonce: string; expiresAt: number }>
  /** Verify a presented nonce against the store. Returns the
   *  ccsc-ofn VerifyResult. */
  verifyChallenge: (
    nonce: string,
    presentedBy: { userId: string; channelId: string },
  ) => ReturnType<typeof verifyNonce>
  /** Post a Slack reaction to the originating message. ♻️ for !clear,
   *  🔄 for !restart, 🔇 for !mute, 🔊 for !unmute. */
  postReaction: (emoji: string) => Promise<void>
  /** Mute store (ccsc-gjm). Required when dispatching `!mute` /
   *  `!unmute`; injected so tests can swap mock stores. */
  muteStore?: MuteStore
  /** Clock for mute TTL math. Defaults to `Date.now`. Tests inject
   *  for deterministic expiry assertions. */
  now?: () => number
  /** Resolve the channel's EFFECTIVE peer-bot rate-limit + circuit-breaker
   *  config (policy override or the built-in default) for the read-only
   *  `!rate-limit` verb (ccsc-yl6k9). The server computes this from
   *  access.json + the DEFAULT_* constants. Absent → `!rate-limit` reports
   *  that the limits view is unavailable. */
  getChannelRateLimits?: (channelId: string) => {
    peerBot: RateLimitConfig
    channel: RateLimitConfig
  }
  /** List peer-bot user IDs seen active in the channel recently, for the
   *  read-only `!agents` verb (ccsc-4e9bf). The server derives this from the
   *  peer-bot rate-limit store's per-channel activity. Absent → `!agents`
   *  reports the view is unavailable. */
  getActiveAgents?: (channelId: string, now: number) => string[]
}

/** Dispatch an admin command through the full pipeline:
 *
 *   1. Allowlist check (channel's `adminCommands.allowFrom`).
 *      → fail: `denied` with reason; journal `policy.deny` (caller's
 *        responsibility via the existing deny dispatcher).
 *   2. For !restart with no nonce: issue challenge.
 *      Mint nonce + journal `admin.restart.challenge` + return
 *      `challenge_issued` for the caller to DM.
 *   3. For !restart with nonce: verify.
 *      → fail: `denied` with reason ('expired' / 'replay' /
 *        'wrong-channel' / 'wrong-user' / 'unknown'); journal
 *        `admin.restart.denied`.
 *      → ok: proceed to execute.
 *   4. For !clear: skip challenge phase entirely.
 *   5. Execute:
 *      - !clear: journal `admin.clear` → quiesceAndDeactivate →
 *        sendTmuxKeys(['send-keys', '-t', '<SESSION>', '/clear', 'Enter'])
 *        → react ♻️
 *      - !restart: journal `admin.restart` → sendTmuxKeys(['send-keys',
 *        '-t', '<SESSION>', '/exit', 'Enter']) → react 🔄
 *
 *  Ordering invariant: journal write completes BEFORE
 *  quiesceAndDeactivate / sendTmuxKeys / postReaction. If the journal
 *  is wedged the dispatcher logs to stderr and continues — admin
 *  verbs are authoritative even on a broken journal. Same posture as
 *  policy-dispatch's resilience contract. */
export async function dispatchAdminCommand(
  cmd: AdminCommand,
  deps: DispatchDeps,
): Promise<DispatchOutcome> {
  // Read-only verbs (ccsc-yl6k9): allowlist-gated like every admin verb, but
  // NOT journaled — they change no state, and the journal records decisions,
  // not queries. Handled before the generic gate below so they never reach
  // journalAttempt, whose kindMap only covers state-changing verbs.
  if (cmd.kind === 'mute-status' || cmd.kind === 'rate-limit' || cmd.kind === 'agents') {
    if (!deps.isAllowed(cmd.channelId, cmd.requestedBy)) {
      return {
        kind: 'denied',
        reason: 'requester not authorized for admin commands in this channel',
      }
    }
    const now = deps.now !== undefined ? deps.now() : Date.now()
    let message: string
    if (cmd.kind === 'mute-status') {
      message = formatMuteStatus(deps.muteStore, cmd.channelId, now)
    } else if (cmd.kind === 'rate-limit') {
      message = formatRateLimit(deps.getChannelRateLimits, cmd.channelId)
    } else {
      message = formatAgents(deps.getActiveAgents, cmd.channelId, now)
    }
    return { kind: 'status', verb: cmd.kind, message }
  }

  // Allowlist gate — same shape regardless of verb.
  if (!deps.isAllowed(cmd.channelId, cmd.requestedBy)) {
    await journalAttempt(deps, cmd, 'denied', 'requester not on adminCommands.allowFrom')
    return { kind: 'denied', reason: 'requester not authorized for admin commands in this channel' }
  }

  if (cmd.kind === 'clear') {
    await journalAttempt(deps, cmd, 'allow')
    await deps.quiesceAndDeactivate()
    // Argv-mode by contract on the dep — no shell interpolation. We
    // emit the keystrokes in two steps (literal /clear, then Enter)
    // because tmux send-keys takes each token as a separate argv.
    await deps.sendTmuxKeys(['/clear', 'Enter'])
    await deps.postReaction('recycle')
    return { kind: 'executed', verb: 'clear' }
  }

  if (cmd.kind === 'mute' || cmd.kind === 'unmute') {
    // ccsc-gjm — both verbs are reversible and auto-expiring (or
    // operator-reversible via the counterpart). No nonce required.
    // Allowlist gate already passed above.
    if (deps.muteStore === undefined) {
      // Caller bug — wired the verb parser but didn't wire a store.
      // Fail loud, don't silently no-op.
      await journalAttempt(deps, cmd, 'denied', 'mute store not configured')
      return { kind: 'denied', reason: 'mute store not configured' }
    }
    const now = deps.now !== undefined ? deps.now() : Date.now()
    if (cmd.kind === 'mute') {
      const expiresAt = now + DEFAULT_MUTE_TTL_MS
      deps.muteStore.mute(cmd.channelId, cmd.targetBotId, expiresAt, cmd.requestedBy, now)
      await journalAttempt(deps, cmd, 'allow')
      await deps.postReaction('mute')
      return { kind: 'executed', verb: 'mute' }
    }
    // !unmute — early release. The store reports whether any entry
    // was actually cleared; we journal regardless (the operator
    // expressed the intent) but the audit reader can see whether
    // it landed via the input field if we extend it later.
    deps.muteStore.unmute(cmd.channelId, cmd.targetBotId)
    await journalAttempt(deps, cmd, 'allow')
    await deps.postReaction('loud_sound')
    return { kind: 'executed', verb: 'unmute' }
  }

  // cmd.kind === 'restart' — only kind remaining

  // Challenge phase: no nonce → mint + DM + journal.
  if (cmd.nonce === undefined) {
    const challenge = await deps.issueChallenge(cmd.requestedBy, cmd.channelId)
    await deps.journalWrite({
      kind: 'admin.restart.challenge',
      outcome: 'n/a',
      actor: 'session_owner',
      // Intentionally NOT recording the nonce itself in the journal —
      // a journal-read attacker would otherwise have a free
      // replay credential. The expiry timestamp is recorded so an
      // investigator can correlate challenge timing with subsequent
      // verifications. ccsc-ofn invariant.
      input: { expires_at: challenge.expiresAt },
      sessionKey: { channel: cmd.channelId, thread: cmd.threadTs },
    })
    return { kind: 'challenge_issued', nonce: challenge.nonce, expiresAt: challenge.expiresAt }
  }

  // Verification phase: nonce supplied → verify.
  const verifyResult = deps.verifyChallenge(cmd.nonce, {
    userId: cmd.requestedBy,
    channelId: cmd.channelId,
  })
  if (!verifyResult.ok) {
    await journalAttempt(deps, cmd, 'denied', `nonce verification failed: ${verifyResult.reason}`)
    return { kind: 'denied', reason: `nonce ${verifyResult.reason}` }
  }

  // Execute restart.
  await journalAttempt(deps, cmd, 'allow')
  // /exit closes the Claude Code session. tmux respawn-pane (operator's
  // existing automation) brings it back; the dispatcher doesn't manage
  // the respawn.
  await deps.sendTmuxKeys(['/exit', 'Enter'])
  await deps.postReaction('arrows_counterclockwise')
  return { kind: 'executed', verb: 'restart' }
}

// ---------------------------------------------------------------------------
// Read-only verb formatters (ccsc-yl6k9) — pure, no side effects
// ---------------------------------------------------------------------------

/** "4m 12s" / "45s" from a millisecond duration (floored at 0). */
function formatRemaining(ms: number): string {
  const totalSec = Math.max(0, Math.floor(ms / 1000))
  const m = Math.floor(totalSec / 60)
  const s = totalSec % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

/** "10 msgs / 60s" or "disabled" for a rate-limit config. Defensive against a
 *  missing/malformed cfg from a hand-edited access.json (Gemini, PR #249). */
function describeLimit(cfg: RateLimitConfig | undefined | null): string {
  if (!cfg || cfg.count <= 0 || cfg.windowMs <= 0) return 'disabled'
  return `${cfg.count} msgs / ${Math.round(cfg.windowMs / 1000)}s`
}

/** Build the `!mute-status` message — the channel's active peer-bot mutes with
 *  remaining TTL. Read-only; never mutates the store. */
function formatMuteStatus(store: MuteStore | undefined, channelId: string, now: number): string {
  if (store === undefined) return ':mute: Mute status is unavailable (no mute store configured).'
  const mutes = store.list(channelId, now)
  if (mutes.length === 0) return ':mute: No active peer-bot mutes in this channel.'
  const lines = mutes.map(
    (m) => `• <@${m.botId}> — ${formatRemaining(m.expiresAt - now)} left (muted by <@${m.mutedBy}>)`,
  )
  return `:mute: *Active peer-bot mutes:*\n${lines.join('\n')}`
}

/** Build the `!agents` message — peer bots seen active in the channel recently
 *  (ccsc-4e9bf). Read-only "who's online" view. */
function formatAgents(
  resolve: DispatchDeps['getActiveAgents'],
  channelId: string,
  now: number,
): string {
  if (resolve === undefined) return ':satellite_antenna: Agent activity view is unavailable.'
  const bots = resolve(channelId, now)
  if (bots.length === 0) return ':satellite_antenna: No peer agents active in this channel recently.'
  const lines = bots.map((b) => `• <@${b}>`)
  return `:satellite_antenna: *Peer agents active recently:*\n${lines.join('\n')}`
}

/** Build the `!rate-limit` message — the channel's effective per-bot limit and
 *  channel-wide circuit breaker. Read-only; tuning stays terminal-only. */
function formatRateLimit(
  resolve: DispatchDeps['getChannelRateLimits'],
  channelId: string,
): string {
  if (resolve === undefined) return ':bar_chart: Rate-limit view is unavailable.'
  const limits = resolve(channelId)
  if (limits === undefined || limits === null) {
    return ':bar_chart: Rate-limit view is unavailable.'
  }
  const { peerBot, channel } = limits
  return [
    ':bar_chart: *Effective peer-bot limits for this channel:*',
    `• Per-bot: ${describeLimit(peerBot)}`,
    `• Channel breaker: ${describeLimit(channel)}`,
    '_Tuning is terminal-only — edit the channel policy via `/slack-channel:access`._',
  ].join('\n')
}

/** Common journal-write path for admin events. Records verb +
 *  outcome + requester + channel. Defensive on throw — admin
 *  decision is authoritative even on a broken journal. Status verbs
 *  (mute-status / rate-limit) are read-only and never reach here. */
async function journalAttempt(
  deps: DispatchDeps,
  cmd: Exclude<AdminCommand, AdminMuteStatusCommand | AdminRateLimitCommand | AdminAgentsCommand>,
  outcome: 'allow' | 'denied',
  reason?: string,
): Promise<void> {
  const kindMap = {
    clear: outcome === 'allow' ? 'admin.clear' : 'admin.clear.denied',
    restart: outcome === 'allow' ? 'admin.restart' : 'admin.restart.denied',
    mute: outcome === 'allow' ? 'admin.mute' : 'admin.mute.denied',
    unmute: outcome === 'allow' ? 'admin.unmute' : 'admin.unmute.denied',
  } as const
  const kind = kindMap[cmd.kind]
  try {
    // mute/unmute events carry the target bot in input so audit
    // readers can correlate who-muted-whom without parsing the
    // text. Other verbs don't carry a target.
    const input: Record<string, unknown> = {}
    if (cmd.kind === 'mute' || cmd.kind === 'unmute') {
      input.target_bot_id = cmd.targetBotId
    }
    await deps.journalWrite({
      kind,
      outcome: outcome === 'allow' ? 'allow' : 'deny',
      actor: 'session_owner',
      sessionKey: { channel: cmd.channelId, thread: cmd.threadTs },
      ...(Object.keys(input).length > 0 ? { input } : {}),
      ...(reason !== undefined ? { reason } : {}),
    })
  } catch (err) {
    console.error('[slack] journal.writeEvent failed (admin event)', {
      kind,
      error: err instanceof Error ? err.message : String(err),
    })
  }
}

// ---------------------------------------------------------------------------
// tmux send-keys — argv-mode helper (production)
// ---------------------------------------------------------------------------

/** Production implementation of `DispatchDeps.sendTmuxKeys`. Executes
 *  `tmux send-keys -t <session> <keys...>` via argv-mode async
 *  `execFile` (promisified) — NO shell interpolation, NO opportunity
 *  for command injection via SESSION or keys, AND does not block the
 *  Node event loop while tmux runs. Keys are passed verbatim as
 *  separate argv elements; tmux parses literal keystroke names
 *  (e.g., 'Enter') and text strings.
 *
 *  Refuses to construct if `sessionName` is empty — a missing
 *  SLACK_TMUX_SESSION env var must be a loud boot-time error, not a
 *  silent no-op at admin-verb time.
 *
 *  OpenClaw 2026 security analysis attack classes addressed:
 *    - Shell-quoting bypass: N/A — no shell involved
 *    - Line-continuation: N/A — argv elements are literal
 *    - Busybox multiplexing: N/A — direct execFile of `tmux`
 *    - GNU option abbreviation: tmux uses its own option parser; our
 *      argv shape uses `-t <session>` which is unambiguous
 */
export function createTmuxSendKeys(
  sessionName: string,
): (keys: readonly string[]) => Promise<void> {
  if (sessionName.length === 0) {
    throw new Error(
      'createTmuxSendKeys: sessionName is empty — refuse to construct a sendKeys that would target the default session. Set SLACK_TMUX_SESSION before enabling admin commands.',
    )
  }
  return async (keys) => {
    // Argv: ['send-keys', '-t', sessionName, ...keys]. No shell.
    // execFileAsync returns { stdout, stderr } — we discard both; the
    // tmux send-keys exit code surfaces as a rejection.
    await execFileAsync('tmux', ['send-keys', '-t', sessionName, ...keys])
  }
}

/** Test-only no-op sendKeys. Records calls into the provided array so
 *  tests can assert the argv that would have been sent. Production
 *  code must use `createTmuxSendKeys`. Returns a resolved Promise so
 *  the dispatcher's await pattern works uniformly. */
export function createRecordingSendKeys(
  recorder: Array<readonly string[]>,
): (keys: readonly string[]) => Promise<void> {
  return async (keys) => {
    recorder.push([...keys])
  }
}
