/**
 * ACP boundary adapter — ccsc-21x.
 *
 * The Agent Client Protocol (ACP) is the converging cross-ecosystem JSON-RPC
 * 2.0 standard for agent control (Zed adoption; open issues for the same
 * primitive in google/adk-python#2425 and zed-industries/zed#50592). This
 * module is the ONLY place in the codebase where ACP terminology appears.
 * The supervisor's existing vocabulary (activate / quiesce / deactivate /
 * quarantine) does not change — see 000-docs/session-state-machine.md §
 * ACP-mapping for the contract this adapter honours.
 *
 * Extracted from server.ts so both the production import and the test suite
 * can use the same code path. server.ts has top-level bootstrap side-effects
 * (process.exit on missing tokens) that make direct import from a test
 * runner unsafe — this module has none, so server.test.ts imports it
 * directly instead of inlining a duplicate. Eliminates the drift risk
 * Gemini flagged on PR #172.
 *
 * Additive only. Internal vocabulary is unchanged; existing tests + audit
 * log files keep their meanings.
 */

import { z } from 'zod'
import type { SessionKey } from './lib.ts'
import type { SessionSupervisor } from './supervisor.ts'

export const AcpSessionCancelRequestSchema = z.object({
  jsonrpc: z.literal('2.0'),
  id: z.union([z.string(), z.number()]),
  method: z.literal('session/cancel'),
  params: z.object({
    // ACP session IDs are opaque strings to the protocol. Our local convention
    // is "<channel>:<thread>" — Slack channel and thread IDs contain only
    // alphanumerics and a dot, so ':' is an unambiguous delimiter.
    sessionId: z.string().min(3).max(128),
  }),
})

/** ACP request envelope for `session/cancel`. JSON-RPC 2.0 shape. */
export type AcpSessionCancelRequest = z.infer<typeof AcpSessionCancelRequestSchema>

/** ACP response envelope returned by {@link mapAcpSessionCancel}. JSON-RPC 2.0.
 *
 *  `id` is `string | number | null` per JSON-RPC 2.0 §5.1: when an error
 *  occurs detecting the id (i.e. the request itself failed to parse), the
 *  response MUST set `id` to `null`. The success branch only carries
 *  `string | number` because a successful response always echoes the
 *  client's id verbatim. */
export type AcpResponse =
  | { jsonrpc: '2.0'; id: string | number; result: { stopReason: 'cancelled' } }
  | {
      jsonrpc: '2.0'
      id: string | number | null
      error: { code: number; message: string; data?: unknown }
    }

/** Map an ACP `session/cancel` request onto the supervisor's existing
 *  `quiesce(key)` method.
 *
 *  Returns an ACP-shaped response envelope. Never throws — protocol errors
 *  are returned as JSON-RPC error objects:
 *    - `-32600` Invalid Request: request shape doesn't validate against
 *               {@link AcpSessionCancelRequestSchema}.
 *    - `-32602` Invalid params: `sessionId` does not parse into a
 *               `(channel, thread)` pair.
 *    - `-32603` Internal error: `supervisor.quiesce()` rejected
 *               (quarantined session, save failure, etc.).
 *
 *  On success returns `{ result: { stopReason: 'cancelled' } }` per the ACP
 *  prompt-turn contract — quiesce is a cooperative interrupt, and the
 *  supervisor's promise resolves only after every in-flight save settles,
 *  matching ACP's "agent acknowledges with `cancelled` stop reason" shape.
 *
 *  This function is the only ACP-aware site in the codebase. Internal
 *  terminology (quiesce, SessionKey, SessionHandle) is unchanged. The
 *  adapter exists so that the day Anthropic ships external-message
 *  injection (anthropics/claude-code#53049) and ACP becomes the wire
 *  format, the migration is a single function edit, not a vocabulary
 *  rename. */
export async function mapAcpSessionCancel(
  req: unknown,
  sup: SessionSupervisor,
): Promise<AcpResponse> {
  const parsed = AcpSessionCancelRequestSchema.safeParse(req)
  if (!parsed.success) {
    // JSON-RPC 2.0 §5.1: when the request object is invalid the id may be
    // unknown. We surface the id when one was provided (string|number) and
    // fall back to `null` (the spec-defined sentinel) otherwise.
    const candidateId =
      typeof req === 'object' && req !== null ? (req as Record<string, unknown>).id : undefined
    const fallbackId =
      typeof candidateId === 'string' || typeof candidateId === 'number' ? candidateId : null
    return {
      jsonrpc: '2.0',
      id: fallbackId,
      error: {
        code: -32600,
        message: 'Invalid Request',
        data: { issues: parsed.error.issues },
      },
    }
  }
  const { id, params } = parsed.data

  // Parse "channel:thread" into a SessionKey. Slack IDs do not contain ':',
  // so a single split is unambiguous. The supervisor's realpath-guarded
  // sessionPath() rejects malformed values downstream regardless, but
  // surfacing -32602 here gives the caller a precise error code rather than
  // -32603 from a downstream failure.
  const sep = params.sessionId.indexOf(':')
  if (sep <= 0 || sep === params.sessionId.length - 1) {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32602,
        message: 'Invalid params: sessionId must be "<channel>:<thread>"',
        data: { sessionId: params.sessionId },
      },
    }
  }
  const key: SessionKey = {
    channel: params.sessionId.slice(0, sep),
    thread: params.sessionId.slice(sep + 1),
  }

  try {
    await sup.quiesce(key)
  } catch (err) {
    return {
      jsonrpc: '2.0',
      id,
      error: {
        code: -32603,
        message: 'Internal error: supervisor.quiesce failed',
        data: { reason: err instanceof Error ? err.message : String(err) },
      },
    }
  }

  return { jsonrpc: '2.0', id, result: { stopReason: 'cancelled' } }
}
