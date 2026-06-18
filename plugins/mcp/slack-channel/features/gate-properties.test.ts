/**
 * Property-based tests for gate() — the primary inbound security boundary.
 *
 * Complements server.test.ts (example-based) and the Gherkin runner
 * (scenario-based) with fast-check generators that exercise the full input
 * space. Catches edge-case drift during the ccsc-u41 gate() refactor that
 * specific test cases cannot.
 *
 * Every property asserts an invariant that MUST hold for ALL inputs in the
 * specified shape — not just the examples in server.test.ts. If a refactor
 * breaks any invariant, fast-check shrinks to a minimal counterexample.
 */

import { describe, expect, test } from 'bun:test'
import fc from 'fast-check'
import { type Access, defaultAccess, type GateOptions, gate, PERMISSION_REPLY_RE } from '../lib.ts'

function makeAccess(overrides: Partial<Access> = {}): Access {
  return { ...defaultAccess(), ...overrides }
}

function makeOpts(overrides: Partial<GateOptions> = {}): GateOptions {
  return {
    access: makeAccess(),
    staticMode: true, // pure — no saveAccess side-effects in properties
    saveAccess: () => {},
    botUserId: 'U_BOT',
    selfBotId: 'B_BOT',
    selfAppId: 'A_BOT',
    ...overrides,
  }
}

// Arbitrary Slack user ID (U + 10 alnum chars — Slack's actual format is wider
// but this is enough entropy to avoid collisions with fixtures like 'U_BOT')
const userIdArb = fc
  .string({
    minLength: 6,
    maxLength: 10,
    unit: fc.constantFrom(...'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
  })
  .map((s) => `U${s}`)

const channelIdArb = fc
  .string({
    minLength: 6,
    maxLength: 10,
    unit: fc.constantFrom(...'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
  })
  .map((s) => `C${s}`)

const botIdArb = fc
  .string({
    minLength: 6,
    maxLength: 10,
    unit: fc.constantFrom(...'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
  })
  .map((s) => `B${s}`)

const appIdArb = fc
  .string({
    minLength: 6,
    maxLength: 10,
    unit: fc.constantFrom(...'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'),
  })
  .map((s) => `A${s}`)

describe('gate() properties — self-echo invariants', () => {
  test('any event whose bot_id matches selfBotId ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(
        channelIdArb,
        userIdArb,
        fc.string({ maxLength: 200 }),
        async (channel, user, text) => {
          const opts = makeOpts({ selfBotId: 'B_SELF' })
          const result = await gate(
            { bot_id: 'B_SELF', channel, channel_type: 'channel', user, text },
            opts,
          )
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })

  test('any event whose bot_profile.app_id matches selfAppId ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(channelIdArb, botIdArb, userIdArb, async (channel, bot_id, user) => {
        const opts = makeOpts({ selfAppId: 'A_SELF' })
        const result = await gate(
          {
            bot_id,
            bot_profile: { app_id: 'A_SELF' },
            channel,
            channel_type: 'channel',
            user,
          },
          opts,
        )
        expect(result.action).toBe('drop')
      }),
      { numRuns: 200 },
    )
  })

  test('any event whose user matches botUserId ⇒ drop (even with bot_id set)', async () => {
    await fc.assert(
      fc.asyncProperty(channelIdArb, botIdArb, async (channel, bot_id) => {
        const opts = makeOpts({ botUserId: 'U_SELF' })
        const result = await gate(
          { bot_id, channel, channel_type: 'channel', user: 'U_SELF' },
          opts,
        )
        expect(result.action).toBe('drop')
      }),
      { numRuns: 200 },
    )
  })
})

describe('gate() properties — bot message opt-in invariants', () => {
  test('bot message to channel with NO allowBotIds ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(channelIdArb, botIdArb, userIdArb, async (channel, bot_id, user) => {
        // Channel policy exists but has no allowBotIds
        const opts = makeOpts({
          access: makeAccess({
            channels: { [channel]: { allowFrom: [], requireMention: false } },
          }),
        })
        const result = await gate({ bot_id, channel, channel_type: 'channel', user }, opts)
        expect(result.action).toBe('drop')
      }),
      { numRuns: 200 },
    )
  })

  test('bot message to channel where allowBotIds does NOT contain bot user ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(
        channelIdArb,
        botIdArb,
        userIdArb,
        userIdArb,
        async (channel, bot_id, botUser, allowedBotUser) => {
          fc.pre(botUser !== allowedBotUser)
          const opts = makeOpts({
            access: makeAccess({
              channels: {
                [channel]: {
                  allowFrom: [],
                  requireMention: false,
                  allowBotIds: [allowedBotUser],
                },
              },
            }),
          })
          const result = await gate(
            { bot_id, channel, channel_type: 'channel', user: botUser },
            opts,
          )
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })

  test('bot message matching PERMISSION_REPLY_RE ⇒ drop (even with allowBotIds)', async () => {
    // Permission reply shape: ^\s*(y|yes|n|no)\s+[a-km-z]{5}\s*$
    const permissionReplyArb = fc
      .tuple(
        fc.constantFrom('y', 'yes', 'n', 'no', 'Y', 'YES', 'N', 'NO'),
        fc.string({
          minLength: 5,
          maxLength: 5,
          unit: fc.constantFrom(...'abcdefghijkmnopqrstuvwxyz'),
        }),
      )
      .map(([verb, code]) => `${verb} ${code}`)

    await fc.assert(
      fc.asyncProperty(
        channelIdArb,
        botIdArb,
        userIdArb,
        permissionReplyArb,
        async (channel, bot_id, botUser, text) => {
          // Sanity: our generator actually produces the regex's shape
          fc.pre(PERMISSION_REPLY_RE.test(text))

          const opts = makeOpts({
            access: makeAccess({
              channels: {
                [channel]: {
                  allowFrom: [],
                  requireMention: false,
                  allowBotIds: [botUser], // Opted in!
                },
              },
            }),
          })
          const result = await gate(
            { bot_id, channel, channel_type: 'channel', user: botUser, text },
            opts,
          )
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })
})

describe('gate() properties — no-user-field invariant', () => {
  test('non-bot event without a user field ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(
        channelIdArb,
        fc.constantFrom('im', 'channel', 'group'),
        fc.option(fc.constantFrom('message_changed', 'message_deleted', 'channel_join'), {
          nil: undefined,
        }),
        async (channel, channel_type, subtype) => {
          // subtype === 'file_share' would fall through; we exclude it above
          const opts = makeOpts()
          const ev: Record<string, unknown> = { channel, channel_type }
          if (subtype) ev.subtype = subtype
          const result = await gate(ev, opts)
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })
})

describe('gate() properties — non-message-subtype invariant', () => {
  test('event with subtype other than undefined or "file_share" ⇒ drop', async () => {
    const disallowedSubtypeArb = fc.constantFrom(
      'message_changed',
      'message_deleted',
      'channel_join',
      'channel_leave',
      'bot_message',
      'me_message',
      'thread_broadcast',
    )

    await fc.assert(
      fc.asyncProperty(
        channelIdArb,
        userIdArb,
        disallowedSubtypeArb,
        async (channel, user, subtype) => {
          const opts = makeOpts()
          const result = await gate({ channel, channel_type: 'channel', user, subtype }, opts)
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })
})

describe('gate() properties — DM allowlist invariant', () => {
  test('DM from user NOT in allowFrom with dmPolicy=allowlist ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(
        userIdArb,
        fc.array(userIdArb, { minLength: 0, maxLength: 5 }),
        channelIdArb,
        async (sender, allowFromList, channel) => {
          fc.pre(!allowFromList.includes(sender))
          const opts = makeOpts({
            access: makeAccess({ dmPolicy: 'allowlist', allowFrom: allowFromList }),
          })
          const result = await gate({ channel, channel_type: 'im', user: sender }, opts)
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })

  test('DM from user IN allowFrom ⇒ deliver (regardless of dmPolicy)', async () => {
    await fc.assert(
      fc.asyncProperty(
        userIdArb,
        fc.constantFrom('allowlist', 'pairing', 'disabled'),
        channelIdArb,
        async (sender, dmPolicy, channel) => {
          const opts = makeOpts({
            access: makeAccess({
              dmPolicy: dmPolicy as Access['dmPolicy'],
              allowFrom: [sender],
            }),
          })
          const result = await gate({ channel, channel_type: 'im', user: sender }, opts)
          expect(result.action).toBe('deliver')
        },
      ),
      { numRuns: 200 },
    )
  })
})

describe('gate() properties — channel gate invariants', () => {
  test('channel message to channel with NO policy in access.channels ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(channelIdArb, userIdArb, async (channel, user) => {
        const opts = makeOpts() // empty channels map
        const result = await gate({ channel, channel_type: 'channel', user }, opts)
        expect(result.action).toBe('drop')
      }),
      { numRuns: 200 },
    )
  })

  test('channel message from user NOT in policy.allowFrom (non-empty) ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(
        channelIdArb,
        userIdArb,
        fc.array(userIdArb, { minLength: 1, maxLength: 5 }),
        async (channel, sender, allowFromList) => {
          fc.pre(!allowFromList.includes(sender))
          const opts = makeOpts({
            access: makeAccess({
              channels: {
                [channel]: { allowFrom: allowFromList, requireMention: false },
              },
            }),
          })
          const result = await gate({ channel, channel_type: 'channel', user: sender }, opts)
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })

  test('channel message without @bot-mention when requireMention=true ⇒ drop', async () => {
    await fc.assert(
      fc.asyncProperty(
        channelIdArb,
        userIdArb,
        // Any text that does NOT contain <@U_BOT>
        fc.string({ maxLength: 200 }).filter((s) => !s.includes('<@U_BOT>')),
        async (channel, user, text) => {
          const opts = makeOpts({
            access: makeAccess({
              channels: {
                [channel]: { allowFrom: [], requireMention: true },
              },
            }),
          })
          const result = await gate({ channel, channel_type: 'channel', user, text }, opts)
          expect(result.action).toBe('drop')
        },
      ),
      { numRuns: 200 },
    )
  })
})
