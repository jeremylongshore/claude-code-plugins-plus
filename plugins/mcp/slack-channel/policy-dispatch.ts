/**
 * policy-dispatch.ts — Side-effect-free dispatcher helpers for policy
 * decisions (ccsc-06s).
 *
 * Lives in its own module so the test suite can import the production
 * code path directly. server.ts has boot-time side effects
 * (process.exit on missing .env) that prevent direct import in the
 * test runner — but these helpers are pure, so a sibling module is
 * the right shape. Mirrors the acp-adapter.ts pattern locked in by
 * PR #173 (Gemini-flagged drift risk on inlined duplicates).
 *
 * Scope of this module:
 *   - buildDenyNotificationParams() — wire-format invariant for the
 *     MCP notification sent to Claude on policy.deny
 *   - recordPolicyDenyToJournal() — two-event journal sequence:
 *     full-detail policy.deny + sanitised policy.deny.context_stripped
 *   - buildPolicyAllowEvent / buildPolicyRequireEvent /
 *     buildPolicyApprovedEvent — pure builders for the remaining policy
 *     journal events the dispatcher writes (ccsc-175). server.ts calls
 *     these to construct what it journals, so a test can import the
 *     production event source directly instead of asserting the inline
 *     server.ts object literals structurally.
 *   - permissionRouteJournalEvents() — the exhaustive route→events
 *     contract (ccsc-175). A `never`-guard makes a new PermissionRoute
 *     variant fail to COMPILE, binding the "every policy decision is
 *     journaled, no silent gaps" invariant (ccsc-1iw.2) to production
 *     code rather than a test-local route→kind map.
 *
 * What this module does NOT do:
 *   - Send the actual MCP notification. server.ts owns the MCP
 *     transport; this module produces the body.
 *   - Choose whether to deny. policy.ts owns evaluate(); this module
 *     handles the side of dispatch that comes AFTER the deny verdict.
 *   - Mutate Claude's conversation history directly. CCSC's MCP-bridge
 *     architecture cannot — Claude Code owns that surface. The
 *     minimisation lives on the notification side: Claude observes a
 *     deny WITH NO retry-aiding metadata. See 000-docs/policy-
 *     evaluation-flow.md § Context-stripping (ccsc-06s) for the
 *     architectural rationale.
 *
 * SPDX-License-Identifier: Apache-2.0
 */

import type { EventKind, JournalWriter, WriteInput } from './journal.ts'
import type { PermissionRoute } from './lib.ts'

// ---------------------------------------------------------------------------
// Wire-format invariant — buildDenyNotificationParams (ccsc-06s)
// ---------------------------------------------------------------------------

/** Shape of the MCP notification body the server sends to Claude on
 *  a policy.deny decision. The literal type on `behavior` pins the
 *  wire-format invariant statically — TypeScript refuses any shape
 *  with extra keys at the call site.
 *
 *  Why `type` (not `interface`): per Gemini review on PR #178, type
 *  aliases with concrete properties are implicitly assignable to
 *  `Record<string, unknown>` because type aliases are closed (no
 *  declaration merging). Interfaces would require an explicit
 *  `[k: string]: unknown` index signature — which would silently
 *  relax the ccsc-06s minimisation by permitting extra keys at the
 *  call site. The `type` form keeps the wire shape EXACTLY two
 *  fields while still satisfying the MCP SDK's
 *  `Record<string, unknown>` parameter type. */
export type DenyNotificationParams = {
  request_id: string
  behavior: 'deny'
}

/** Build the deny-notification body. The ONLY two fields produced at
 *  runtime are `request_id` (so the receiver correlates) and
 *  `behavior: 'deny'`. Rule id, denial reason, and input echo are
 *  intentionally omitted — any of those would seed a retry-rephrase
 *  loop in Claude's next turn.
 *
 *  The helper exists so the wire-format invariant has one obvious
 *  surface to test against. See server.test.ts §"ccsc-06s
 *  buildDenyNotificationParams". */
export function buildDenyNotificationParams(request_id: string): DenyNotificationParams {
  return { request_id, behavior: 'deny' }
}

// ---------------------------------------------------------------------------
// Two-event journal sequence — recordPolicyDenyToJournal (ccsc-06s)
// ---------------------------------------------------------------------------

/** Full detail recorded on the FIRST of the two deny events. The
 *  audit log keeps everything — the minimisation lives on the
 *  notification side, not the journal side. `sessionKey` is optional
 *  to match the dispatcher: a denial can occur on a tool call that
 *  hasn't yet been bound to a session (early-flow rejections), and
 *  the journal schema permits an absent sessionKey on those events. */
export interface PolicyDenyDetail {
  sessionKey?: { channel: string; thread: string }
  toolName: string
  input: Record<string, unknown>
  ruleId: string
  reason: string
}

/** Write the two-event sequence the ccsc-06s dispatcher requires:
 *
 *    1. `policy.deny` with FULL detail (forensic record)
 *    2. `policy.deny.context_stripped` with NO retry-aiding fields
 *
 *  Both are awaited so that on return, the JournalWriter's serial
 *  queue has drained at least these two events past the recovery
 *  point. The caller can then send the minimal MCP notification
 *  knowing the journal record is durable.
 *
 *  Order is enforced by `await` — there is no path through which the
 *  second event is written before the first. Tested directly in
 *  server.test.ts §"ccsc-06s recordPolicyDenyToJournal".
 *
 *  Defensive on each write: a broken audit log MUST NOT interrupt
 *  the denial — the policy decision is authoritative even if the
 *  journal is wedged. Errors are surfaced to stderr but never thrown,
 *  AND the second write is attempted whether or not the first
 *  succeeded (audit-resilience invariant). */
export async function recordPolicyDenyToJournal(
  writeEvent: (input: Parameters<JournalWriter['writeEvent']>[0]) => Promise<unknown>,
  detail: PolicyDenyDetail,
): Promise<void> {
  try {
    await writeEvent({
      kind: 'policy.deny',
      outcome: 'deny',
      actor: 'claude_process',
      sessionKey: detail.sessionKey,
      toolName: detail.toolName,
      input: detail.input,
      ruleId: detail.ruleId,
      reason: detail.reason,
    })
  } catch (err) {
    console.error('[slack] journal.writeEvent failed (policy.deny)', {
      error: err instanceof Error ? err.message : String(err),
    })
  }
  try {
    await writeEvent({
      kind: 'policy.deny.context_stripped',
      outcome: 'n/a',
      actor: 'system',
      sessionKey: detail.sessionKey,
      toolName: detail.toolName,
      // Intentionally NO input / ruleId / reason here. The preceding
      // policy.deny event carries those. Recording them again would
      // defeat the audit-purpose distinction between the two events.
    })
  } catch (err) {
    console.error('[slack] journal.writeEvent failed (policy.deny.context_stripped)', {
      error: err instanceof Error ? err.message : String(err),
    })
  }
}

// ---------------------------------------------------------------------------
// Policy journal-event builders — allow / require / approved (ccsc-175)
//
// server.ts used to write these three events as inline object literals at
// the dispatch site. Because server.ts runs main() and constructs Slack
// clients at module top level, a test cannot import it to drive the real
// write — the no-gaps invariant (ccsc-1iw.2) therefore bound a test-local
// route→kind map, not production code. Extracting the builders here (the
// same shape as recordPolicyDenyToJournal above) makes the production
// event source importable: a test drives the builder and asserts the exact
// EventKind written. The deny pair stays in recordPolicyDenyToJournal — it
// carries the awaited-before-notify + resilient-write semantics the deny
// branch needs and must not regress.
// ---------------------------------------------------------------------------

/** Fields recorded on a `policy.allow` event (auto_approve match). */
export interface PolicyAllowDetail {
  sessionKey?: { channel: string; thread: string }
  toolName: string
  input: Record<string, unknown>
  ruleId: string
  /** Audit-receipt correlation id, when a receipt was posted. */
  correlationId?: string
}

/** Build the `policy.allow` journal event for an auto-approved call. */
export function buildPolicyAllowEvent(detail: PolicyAllowDetail): WriteInput {
  return {
    kind: 'policy.allow',
    outcome: 'allow',
    actor: 'claude_process',
    sessionKey: detail.sessionKey,
    toolName: detail.toolName,
    input: detail.input,
    ruleId: detail.ruleId,
    correlationId: detail.correlationId,
  }
}

/** Fields recorded on a `policy.require` event (require_approval match). */
export interface PolicyRequireDetail {
  sessionKey?: { channel: string; thread: string }
  toolName: string
  /** Base input echo (tool, channel, thread_ts). `approversNeeded` is
   *  merged on by the builder so the trace records the quorum size. */
  input: Record<string, unknown>
  ruleId: string
  approversNeeded: number
}

/** Build the `policy.require` trace event for a human-approval dispatch. */
export function buildPolicyRequireEvent(detail: PolicyRequireDetail): WriteInput {
  return {
    kind: 'policy.require',
    outcome: 'require',
    actor: 'claude_process',
    sessionKey: detail.sessionKey,
    toolName: detail.toolName,
    input: { ...detail.input, approversNeeded: detail.approversNeeded },
    ruleId: detail.ruleId,
  }
}

/** Fields recorded on a `policy.approved` event (quorum reached). Unlike
 *  the other three, this is NOT a `decidePermissionRoute` outcome — it is
 *  emitted later, when a human-approver quorum votes Allow on a pending
 *  require_approval request (server.ts processApprovalVote). */
export interface PolicyApprovedDetail {
  sessionKey: { channel: string; thread: string }
  toolName: string
  ruleId: string
  approversNeeded: number
  /** Verified Slack user_ids that voted Allow (NEVER display names). */
  approvers: readonly string[]
}

/** Build the `policy.approved` journal event for a quorum grant. */
export function buildPolicyApprovedEvent(detail: PolicyApprovedDetail): WriteInput {
  return {
    kind: 'policy.approved',
    outcome: 'allow',
    actor: 'human_approver',
    sessionKey: detail.sessionKey,
    toolName: detail.toolName,
    input: {
      tool: detail.toolName,
      approversNeeded: detail.approversNeeded,
      approvers: [...detail.approvers],
    },
    ruleId: detail.ruleId,
  }
}

// ---------------------------------------------------------------------------
// Exhaustive route→events contract — permissionRouteJournalEvents (ccsc-175)
// ---------------------------------------------------------------------------

/** Context the exhaustive route→events mapping needs to build each event.
 *  Every field is optional except the always-present ones, because a
 *  single ctx serves all four routes; the relevant subset is consumed per
 *  route. `reason` is deny-only, `correlationId` allow-only,
 *  `approversNeeded` require-only. */
export interface PermissionRouteJournalContext {
  sessionKey?: { channel: string; thread: string }
  toolName: string
  /** Base input echo: { tool, channel, thread_ts }. */
  input: Record<string, unknown>
  /** Audit-receipt correlation id — attached to `policy.allow`. */
  correlationId?: string
  /** Quorum size — attached to `policy.require`. */
  approversNeeded?: number
  /** Denial reason — attached to the first `policy.deny` event. */
  reason?: string
}

/** The ordered journal events a resolved permission route must produce.
 *
 *  This is the single production source of the "no silent gaps" invariant
 *  (ccsc-1iw.2): every `PermissionRoute` variant maps here to the exact
 *  EventKind(s) journaled for it, or to `[]` for the deliberately-silent
 *  `default_human` route. The `never`-guard in the `default` arm makes a
 *  newly-added route variant fail to COMPILE until its audit record is
 *  declared — and because server.ts calls this function, that compile
 *  error surfaces in the production build, not only in a test.
 *
 *  Execution split (intentional): server.ts writes the returned events
 *  directly for `auto_allow` / `require_human` / `default_human`. For
 *  `deny` it routes through `recordPolicyDenyToJournal` instead — that
 *  helper awaits each write before the MCP deny notification and attempts
 *  the second event even if the first throws (ccsc-06s resilience). The
 *  `deny` arm here returns the identical two-event pair so the contract is
 *  complete and exhaustive; a consistency test pins the two paths together
 *  (server.test.ts §"permissionRouteJournalEvents deny matches helper"). */
export function permissionRouteJournalEvents(
  route: PermissionRoute,
  ctx: PermissionRouteJournalContext,
): readonly WriteInput[] {
  switch (route.type) {
    case 'auto_allow':
      return [
        buildPolicyAllowEvent({
          sessionKey: ctx.sessionKey,
          toolName: ctx.toolName,
          input: ctx.input,
          ruleId: route.ruleId,
          correlationId: ctx.correlationId,
        }),
      ]
    case 'require_human':
      return [
        buildPolicyRequireEvent({
          sessionKey: ctx.sessionKey,
          toolName: ctx.toolName,
          input: ctx.input,
          ruleId: route.ruleId,
          approversNeeded: ctx.approversNeeded ?? 0,
        }),
      ]
    case 'deny':
      return [
        {
          kind: 'policy.deny',
          outcome: 'deny',
          actor: 'claude_process',
          sessionKey: ctx.sessionKey,
          toolName: ctx.toolName,
          input: ctx.input,
          ruleId: route.ruleId,
          reason: route.reason,
        },
        {
          kind: 'policy.deny.context_stripped',
          outcome: 'n/a',
          actor: 'system',
          sessionKey: ctx.sessionKey,
          toolName: ctx.toolName,
        },
      ]
    case 'default_human':
      // Deliberately silent — the evaluator has no opinion. Tracing the
      // no-rule-match case would 10x the journal on a busy channel.
      return []
    default: {
      // Exhaustiveness guard: a new PermissionRoute variant that forgets
      // to declare its journal record fails to compile here (ccsc-175).
      const _exhaustive: never = route
      return _exhaustive
    }
  }
}

/** The EventKind(s) a route journals, derived from the contract above.
 *  Convenience surface for the no-gaps test and any caller that wants the
 *  kinds without building full events. Kept in lock-step with
 *  permissionRouteJournalEvents by construction (it maps over the same
 *  output), so there is no second switch to drift. */
export function permissionRouteJournalKinds(
  routeType: PermissionRoute['type'],
): readonly EventKind[] {
  // Build with a minimal ctx; only `.kind` is read. `route` is
  // reconstructed with placeholder fields the kind-mapping ignores.
  const route: PermissionRoute =
    routeType === 'auto_allow'
      ? { type: 'auto_allow', ruleId: '' }
      : routeType === 'require_human'
        ? { type: 'require_human', ruleId: '' }
        : routeType === 'deny'
          ? { type: 'deny', ruleId: '', reason: '' }
          : { type: 'default_human' }
  return permissionRouteJournalEvents(route, { toolName: '', input: {} }).map((e) => e.kind)
}
