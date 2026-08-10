# PRD: a2a-client

**Author:** Jeremy Longshore
**Date:** 2026-08-09
**Status:** Active

## Problem

A Claude Code session can call tools (MCP) and talk to humans, but it cannot talk to another
organization's agent over the protocol built for exactly that.

Agent2Agent (A2A) is the settled standard for agent-to-agent communication — 25,261 stars, Linux
Foundation, official SDKs in seven languages, and a published conformance inspector. Its predecessor
ACP is archived and its README redirects to A2A's migration guide, so there is one standard rather
than a contested field.

As of 2026-08-09, GitHub searches for "a2a claude code skill", "agent2agent claude code", and "a2a
agent card claude" returned **zero results** each, and `a2a-mcp` was unpublished on npm. The
documentation half of the gap is addressable with skills; the calling half needs a real client that
speaks the wire.

There is a second, sharper problem hiding inside the first. A2A discovery works by fetching an
**agent card** — a manifest authored by the remote party, describing what they would like the local
agent to believe: which URLs to send traffic to, which capabilities exist, which security requirements
apply. A client that configures itself from that document has handed a remote party its own authority.
That is a confused-deputy primitive, and the obvious implementation walks straight into it.

## Target users

| User | Context | Primary need |
| --- | --- | --- |
| Integrator | A partner published an A2A agent; the card is theirs, the blast radius is ours | Complete a real round-trip, and see what the card claims without the client acting on it |
| Skill author | Building on the `agent-comms` pack; needs the live-call path behind the protocol skills | Typed, spec-faithful tools that surface protocol errors verbatim |
| Operator debugging an integration | A task stalled, a stream died, or a cancel did nothing | Verbatim status and error codes rather than a paraphrase that loses the code |

## Success criteria

1. A full A2A flow completes against a conformant agent — card fetch, `SendMessage` round-trip,
   streamed call, `GetTask` to a terminal state, `CancelTask` on a live task — with an unknown task id
   producing a verbatim error rather than a fake success. **Met: 22/22 assertions against a reference
   agent built on the official `@a2a-js/sdk` server module.**
2. No tool converts a card claim into local configuration, and no output contains a trust score.
   Asserted by test, not by convention. **Met: 67 unit tests over the pure audit and guard modules.**
   The wire honours the same rule: private, loopback, link-local, and metadata destinations are
   refused by default whether the caller or a remote card named them.
3. `.mcp.json` uses `${CLAUDE_PLUGIN_ROOT}`, and the built server completes an MCP handshake and
   lists all seven tools. **Met.**
4. Credentials are only ever read from the environment — never from a card, never logged, never echoed
   in a tool result — and are sent only to a host the operator nominated in `A2A_ALLOWED_HOSTS`. With
   no allowlist configured, no credential leaves the process. **Met, asserted by test.**

## Functional requirements

- **FR-1:** Resolve an agent card from `/.well-known/agent-card.json` (or an explicit path) and return
  a structure verdict, an enumerated claims table, and findings — labelled `reported` or
  `operator-decision-required`.
- **FR-2:** Flag interface URLs pointing at loopback or private ranges, non-HTTPS interface URLs,
  card-required extensions, and per-skill `securityRequirements` that drop an agent-level scheme.
- **FR-3:** Send messages and branch the `SendMessageResult` `oneof`, reporting whether a `Task` or an
  inline `Message` came back — a spec-legal agent may answer without creating a task.
- **FR-4:** Stream events with a caller-set cap, reporting truncation explicitly rather than silently.
- **FR-5:** Get, list, and cancel tasks, with the cancel result stating that a cancel is a request the
  agent may decline.
- **FR-6:** Refuse every outbound request to a private, loopback, link-local, or carrier-grade-NAT
  destination unless explicitly opted in, and attach an operator credential only to an allowlisted
  host — enforced at a single fetch-level choke point so it covers card resolution, protocol calls,
  and SDK-internal requests alike.

## Out of scope

- **Defining or extending a protocol.** This wraps the official SDK and conforms to the published
  spec. No format, version, or registry of its own; no conformance-certification claim.
- **Push-notification callback receipt.** The four `TaskPushNotificationConfig` methods and
  `GetExtendedAgentCard` are reachable through the SDK but are not exposed as tools — an inbound
  callback is untrusted traffic needing a receiving endpoint this server does not own.
- **Signature verification.** Without a key obtained independently of the card, `unverified` is the
  only honest answer, and reporting the stronger claim would be a false assurance.
- **Credential discovery or re-auth negotiation.** A `401`/`403` is surfaced, not answered with a
  guessed second credential.
- **Caching cards across calls.** Deliberate: a card must not be able to install itself as a durable
  default.
