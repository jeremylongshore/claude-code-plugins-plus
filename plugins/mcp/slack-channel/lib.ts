/**
 * lib.ts — Pure, testable functions extracted from the Slack Channel MCP server.
 *
 * All functions here are side-effect-free (or accept their dependencies as
 * parameters) so they can be imported by server.test.ts without starting the
 * Slack socket or loading credentials.
 *
 * SPDX-License-Identifier: MIT
 */

import { resolve } from 'path'

// ---------------------------------------------------------------------------
// Constants (re-exported so server.ts and tests share the same values)
// ---------------------------------------------------------------------------

export const MAX_PENDING = 3
export const MAX_PAIRING_REPLIES = 2
export const PAIRING_EXPIRY_MS = 60 * 60 * 1000 // 1 hour

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type DmPolicy = 'pairing' | 'allowlist' | 'disabled'

export interface ChannelPolicy {
  requireMention: boolean
  allowFrom: string[]
}

export interface PendingEntry {
  senderId: string
  chatId: string
  createdAt: number
  expiresAt: number
  replies: number
}

export interface Access {
  dmPolicy: DmPolicy
  allowFrom: string[]
  channels: Record<string, ChannelPolicy>
  pending: Record<string, PendingEntry>
  ackReaction?: string
  textChunkLimit?: number
  chunkMode?: 'length' | 'newline'
}

export type GateAction = 'deliver' | 'drop' | 'pair'

export interface GateResult {
  action: GateAction
  access?: Access
  code?: string
  isResend?: boolean
}

// ---------------------------------------------------------------------------
// Access helpers
// ---------------------------------------------------------------------------

export function defaultAccess(): Access {
  return {
    dmPolicy: 'pairing',
    allowFrom: [],
    channels: {},
    pending: {},
  }
}

export function pruneExpired(access: Access): void {
  const now = Date.now()
  for (const [code, entry] of Object.entries(access.pending)) {
    if (entry.expiresAt <= now) {
      delete access.pending[code]
    }
  }
}

export function generateCode(): string {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789' // No 0/O/1/I confusion
  let code = ''
  for (let i = 0; i < 6; i++) {
    code += chars[Math.floor(Math.random() * chars.length)]
  }
  return code
}

// ---------------------------------------------------------------------------
// Security — assertSendable (file exfiltration guard)
// ---------------------------------------------------------------------------

/**
 * Throws if `filePath` resolves to inside `stateDir` but outside `inboxDir`.
 * Both directory paths should be absolute (already resolved).
 */
export function assertSendable(filePath: string, stateDir: string, inboxDir: string): void {
  const resolved = resolve(filePath)

  if (resolved.startsWith(stateDir) && !resolved.startsWith(inboxDir)) {
    throw new Error(
      `Blocked: cannot send files from state directory (${stateDir}). ` +
        'Only files in inbox/ are sendable.',
    )
  }
}

// ---------------------------------------------------------------------------
// Security — outbound gate
// ---------------------------------------------------------------------------

/**
 * Throws if `chatId` is neither an opted-in channel nor a previously-delivered
 * channel (DM that passed the inbound gate this session).
 */
export function assertOutboundAllowed(
  chatId: string,
  access: Access,
  deliveredChannels: ReadonlySet<string>,
): void {
  if (access.channels[chatId]) return
  if (deliveredChannels.has(chatId)) return
  throw new Error(
    `Outbound gate: channel ${chatId} is not in the allowlist or opted-in channels.`,
  )
}

// ---------------------------------------------------------------------------
// Text chunking
// ---------------------------------------------------------------------------

export function chunkText(text: string, limit: number, mode: 'length' | 'newline'): string[] {
  if (text.length <= limit) return [text]

  const chunks: string[] = []

  if (mode === 'newline') {
    let current = ''
    for (const line of text.split('\n')) {
      if (current.length + line.length + 1 > limit && current.length > 0) {
        chunks.push(current)
        current = ''
      }
      current += (current ? '\n' : '') + line
    }
    if (current) chunks.push(current)
  } else {
    for (let i = 0; i < text.length; i += limit) {
      chunks.push(text.slice(i, i + limit))
    }
  }

  return chunks
}

// ---------------------------------------------------------------------------
// Attachment sanitization
// ---------------------------------------------------------------------------

export function sanitizeFilename(name: string): string {
  return name.replace(/[\[\]\n\r;]/g, '_').replace(/\.\./g, '_')
}

// ---------------------------------------------------------------------------
// Gate function
//
// Accepts access state and a saveAccess callback as parameters rather than
// calling module-level singletons, making it fully testable in isolation.
// ---------------------------------------------------------------------------

export interface GateOptions {
  /** Pre-loaded, pre-pruned access state */
  access: Access
  /** Whether we're in static mode (no persistence writes) */
  staticMode: boolean
  /** Persist the mutated access object (only called when staticMode is false) */
  saveAccess: (access: Access) => void
  /** Current bot user ID for mention detection */
  botUserId: string
}

export async function gate(event: unknown, opts: GateOptions): Promise<GateResult> {
  const ev = event as Record<string, unknown>

  // 1. Drop bot messages immediately
  if (ev['bot_id']) return { action: 'drop' }

  // 2. Drop non-message subtypes (message_changed, message_deleted, etc.)
  if (ev['subtype'] && ev['subtype'] !== 'file_share') return { action: 'drop' }

  // 3. No user ID = drop
  if (!ev['user']) return { action: 'drop' }

  const { access, staticMode, saveAccess, botUserId } = opts

  // 4. DM handling
  if (ev['channel_type'] === 'im') {
    const userId = ev['user'] as string

    if (access.allowFrom.includes(userId)) {
      return { action: 'deliver', access }
    }
    if (access.dmPolicy === 'allowlist' || access.dmPolicy === 'disabled') {
      return { action: 'drop' }
    }

    // Pairing mode — check if there's already a pending code for this user
    for (const [code, entry] of Object.entries(access.pending)) {
      if (entry.senderId === userId) {
        if (entry.replies < MAX_PAIRING_REPLIES) {
          entry.replies++
          if (!staticMode) saveAccess(access)
          return { action: 'pair', code, isResend: true }
        }
        return { action: 'drop' } // Hit reply cap
      }
    }

    // Cap total pending
    if (Object.keys(access.pending).length >= MAX_PENDING) {
      return { action: 'drop' }
    }

    // Generate new pairing code
    const code = generateCode()
    access.pending[code] = {
      senderId: userId,
      chatId: ev['channel'] as string,
      createdAt: Date.now(),
      expiresAt: Date.now() + PAIRING_EXPIRY_MS,
      replies: 1,
    }
    if (!staticMode) saveAccess(access)
    return { action: 'pair', code, isResend: false }
  }

  // 5. Channel handling — opt-in per channel ID
  const channel = ev['channel'] as string
  const policy = access.channels[channel]
  if (!policy) return { action: 'drop' }

  if (policy.allowFrom.length > 0 && !policy.allowFrom.includes(ev['user'] as string)) {
    return { action: 'drop' }
  }

  if (policy.requireMention && !isMentioned(ev, botUserId)) {
    return { action: 'drop' }
  }

  return { action: 'deliver', access }
}

function isMentioned(event: Record<string, unknown>, botUserId: string): boolean {
  if (!botUserId) return false
  const text = (event['text'] as string | undefined) || ''
  return text.includes(`<@${botUserId}>`)
}
