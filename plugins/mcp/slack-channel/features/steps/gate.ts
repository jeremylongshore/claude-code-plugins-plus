/**
 * features/steps/gate.ts — Step definitions for inbound_gate.feature.
 *
 * Exercises gate() from lib.ts. Each scenario uses the shared Context to
 * carry the GateOptions and the resulting GateResult between steps.
 *
 * SPDX-License-Identifier: MIT
 */

import { expect } from "bun:test";
import {
	type Access,
	defaultAccess,
	type GateOptions,
	type GateResult,
	gate,
	PERMISSION_REPLY_RE,
} from "../../lib.ts";
import type { Context, StepRegistry } from "../runner.ts";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function makeOpts(overrides: Partial<GateOptions> = {}): GateOptions {
	return {
		access: defaultAccess(),
		staticMode: true,
		saveAccess: () => {},
		botUserId: "U_BOT",
		selfBotId: "B_SELF",
		selfAppId: "A_SELF",
		...overrides,
	};
}

/** Run gate() and store the result in ctx.result. */
async function runGate(
	event: unknown,
	opts: GateOptions,
	ctx: Context,
): Promise<void> {
	const result = await gate(event, opts);
	ctx.result = result;
	ctx.opts = opts;
}

// ---------------------------------------------------------------------------
// Step registrations
// ---------------------------------------------------------------------------

export function registerGateSteps(registry: StepRegistry): void {
	// -------------------------------------------------------------------------
	// Scenario: Self-echo of a bot's own message is silently dropped
	// -------------------------------------------------------------------------

	registry.register(
		"the bot is running under a known bot_id and app_id",
		(_ctx) => {
			// Just a precondition note — opts are constructed in the When step.
		},
	);

	registry.register(
		"a message event arrives whose bot_id matches the running bot",
		async (ctx) => {
			const opts = makeOpts();
			const event = {
				type: "message",
				bot_id: opts.selfBotId,
				user: "U_OTHER",
				channel: "C_CHAN",
				text: "hello",
				ts: "1000.0001",
			};
			await runGate(event, opts, ctx);
		},
	);

	registry.register("the gate decides to drop the event", (ctx) => {
		const result = ctx.result as GateResult;
		expect(result.action).toBe("drop");
	});

	registry.register("no downstream notification is emitted", (ctx) => {
		// In gate() the 'drop' action IS the mechanism for not emitting.
		const result = ctx.result as GateResult;
		expect(result.action).toBe("drop");
	});

	// -------------------------------------------------------------------------
	// Scenario: A peer bot posting to a channel with no allowBotIds is dropped
	// -------------------------------------------------------------------------

	registry.register(
		"a channel has a policy with an empty allowBotIds list",
		(ctx) => {
			const access: Access = {
				...defaultAccess(),
				channels: {
					C_CHAN: { requireMention: false, allowFrom: [] },
					// allowBotIds absent = empty
				},
			};
			ctx.access = access;
		},
	);

	registry.register(
		"a peer bot posts a message into that channel",
		async (ctx) => {
			const access = ctx.access as Access;
			const opts = makeOpts({ access });
			const event = {
				type: "message",
				bot_id: "B_PEER",
				user: "U_PEER_BOT",
				channel: "C_CHAN",
				text: "peer message",
				ts: "1000.0002",
			};
			await runGate(event, opts, ctx);
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: A peer bot posting to a channel that opts it in by user_id
	// -------------------------------------------------------------------------

	registry.register(
		"a channel policy lists a peer bot's user_id under allowBotIds",
		(ctx) => {
			const access: Access = {
				...defaultAccess(),
				channels: {
					C_CHAN: {
						requireMention: false,
						allowFrom: [],
						allowBotIds: ["U_PEER_BOT"],
					},
				},
			};
			ctx.access = access;
		},
	);

	registry.register(
		"that peer bot posts a non-command message into the channel",
		async (ctx) => {
			const access = ctx.access as Access;
			const opts = makeOpts({ access });
			const event = {
				type: "message",
				bot_id: "B_PEER",
				user: "U_PEER_BOT",
				channel: "C_CHAN",
				text: "status update",
				ts: "1000.0003",
			};
			await runGate(event, opts, ctx);
		},
	);

	registry.register("the gate decides to deliver the event", (ctx) => {
		const result = ctx.result as GateResult;
		expect(result.action).toBe("deliver");
	});

	registry.register(
		"the event is handled by the normal channel pipeline",
		(ctx) => {
			const result = ctx.result as GateResult;
			expect(result.action).toBe("deliver");
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: Peer bot mimics a permission reply — dropped even when opted-in
	// -------------------------------------------------------------------------

	registry.register(
		"that peer bot posts text shaped like an approval reply",
		async (ctx) => {
			const access = ctx.access as Access;
			const opts = makeOpts({ access });
			// 'y abcde' matches PERMISSION_REPLY_RE
			const event = {
				type: "message",
				bot_id: "B_PEER",
				user: "U_PEER_BOT",
				channel: "C_CHAN",
				text: "y abcde",
				ts: "1000.0004",
			};
			await runGate(event, opts, ctx);
		},
	);

	registry.register(
		"the permission reply regex catches the injection attempt",
		(_ctx) => {
			// Verify that the regex itself matches — belt and suspenders.
			expect(PERMISSION_REPLY_RE.test("y abcde")).toBe(true);
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: An event with no user_id is dropped
	// -------------------------------------------------------------------------

	registry.register(
		"a channel-tombstone event carries no user field",
		(ctx) => {
			ctx.tombstoneEvent = {
				type: "message",
				subtype: "message_deleted",
				channel: "C_CHAN",
				ts: "1000.0005",
				// no `user` field
			};
		},
	);

	registry.register("the gate evaluates the event", async (ctx) => {
		const event = ctx.tombstoneEvent as unknown;
		const opts = makeOpts();
		await runGate(event, opts, ctx);
	});

	// -------------------------------------------------------------------------
	// Scenario: A DM from an allowlisted user is delivered
	// -------------------------------------------------------------------------

	registry.register(
		"the access allowFrom list contains a specific user_id",
		(ctx) => {
			const access: Access = {
				...defaultAccess(),
				allowFrom: ["U_ALLOWED"],
			};
			ctx.access = access;
		},
	);

	registry.register("that user direct-messages the bot", async (ctx) => {
		const access = ctx.access as Access;
		const opts = makeOpts({ access });
		const event = {
			type: "message",
			user: "U_ALLOWED",
			channel: "D_DM",
			channel_type: "im",
			text: "hello",
			ts: "1000.0006",
		};
		await runGate(event, opts, ctx);
	});

	registry.register(
		"the DM is routed to the normal handler pipeline",
		(ctx) => {
			const result = ctx.result as GateResult;
			expect(result.action).toBe("deliver");
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: DM from unknown user under pairing policy mints a code
	// -------------------------------------------------------------------------

	registry.register("the access dmPolicy is pairing", (ctx) => {
		const access: Access = {
			...defaultAccess(),
			dmPolicy: "pairing",
			allowFrom: [],
		};
		ctx.access = access;
	});

	registry.register(
		"the access allowFrom list does not contain the sender",
		(_ctx) => {
			// The access object is already set with empty allowFrom — no-op assertion step.
		},
	);

	registry.register(
		"an unknown user direct-messages the bot for the first time",
		async (ctx) => {
			const access = ctx.access as Access;
			const opts = makeOpts({ access });
			const event = {
				type: "message",
				user: "U_STRANGER",
				channel: "D_DM2",
				channel_type: "im",
				text: "hello",
				ts: "1000.0007",
			};
			await runGate(event, opts, ctx);
		},
	);

	registry.register("the gate decides to issue a new pairing code", (ctx) => {
		const result = ctx.result as GateResult;
		expect(result.action).toBe("pair");
	});

	registry.register(
		"the pending map records the code against the sender",
		(ctx) => {
			const result = ctx.result as GateResult;
			expect(result.action).toBe("pair");
			expect(typeof result.code).toBe("string");
			const access = (ctx.opts as GateOptions).access;
			expect(Object.keys(access.pending).length).toBeGreaterThan(0);
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: DM from unknown user under allowlist policy is dropped
	// -------------------------------------------------------------------------

	registry.register("the access dmPolicy is allowlist", (ctx) => {
		const access: Access = {
			...defaultAccess(),
			dmPolicy: "allowlist",
			allowFrom: [],
		};
		ctx.access = access;
	});

	registry.register("an unknown user direct-messages the bot", async (ctx) => {
		const access = ctx.access as Access;
		const opts = makeOpts({ access });
		const event = {
			type: "message",
			user: "U_STRANGER2",
			channel: "D_DM3",
			channel_type: "im",
			text: "hello",
			ts: "1000.0008",
		};
		await runGate(event, opts, ctx);
	});

	// -------------------------------------------------------------------------
	// Scenario: A channel message from a non-opted-in channel is dropped
	// -------------------------------------------------------------------------

	registry.register("the access object has no policy for a channel", (ctx) => {
		const access: Access = {
			...defaultAccess(),
			channels: {}, // C_NEW not present
		};
		ctx.access = access;
	});

	registry.register(
		"a human posts a message into that channel",
		async (ctx) => {
			const access = ctx.access as Access;
			const opts = makeOpts({ access });
			const event = {
				type: "message",
				user: "U_HUMAN",
				channel: "C_NEW",
				text: "hello",
				ts: "1000.0009",
			};
			await runGate(event, opts, ctx);
		},
	);

	// -------------------------------------------------------------------------
	// Scenario: A channel message that fails requireMention is dropped
	// -------------------------------------------------------------------------

	registry.register("a channel policy sets requireMention to true", (ctx) => {
		const access: Access = {
			...defaultAccess(),
			channels: {
				C_CHAN: { requireMention: true, allowFrom: [] },
			},
		};
		ctx.access = access;
	});

	registry.register(
		"a human posts a message that does not mention the bot",
		async (ctx) => {
			const access = ctx.access as Access;
			const opts = makeOpts({ access });
			const event = {
				type: "message",
				user: "U_HUMAN",
				channel: "C_CHAN",
				text: "just a plain message",
				ts: "1000.0010",
			};
			await runGate(event, opts, ctx);
		},
	);
}
