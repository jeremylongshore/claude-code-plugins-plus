# ADR: a2a-client — wrap the official SDK, and never let a card grant authority

**Author:** Jeremy Longshore
**Date:** 2026-08-09
**Status:** Accepted

## Context

The `agent-comms` skills describe A2A correctly but cannot place a call. Something has to speak the
wire.

Two constraints shape how.

**The protocol is not ours to reimplement.** A2A carries three bindings (JSON-RPC, gRPC, HTTP+JSON),
an ordered interface-preference list with fallback, an opaque `tenant` that must be echoed when
present, camelCase-over-proto serialization, a `oneof` send result, and nine specific error codes with
a canonical mapping across bindings. A hand-rolled client gets the camelCase rule wrong on day one and
is silently ignored by conformant servers, because unknown fields are dropped rather than rejected.

**The discovery document is hostile by construction.** A2A discovery fetches an agent card — a
manifest authored by the remote party. The agent-governance-plane's CISO ruling is explicit that
importing an unsigned external manifest is a governance-bypass / confused-deputy primitive. An agent
card is precisely that: it names interface URLs (any host, including internal ones), a `tenant` the
client must echo, security requirements that can be weaker per skill than at the agent level, required
extensions, and free-text descriptions that reach a model. A client that configures itself from that
document has spent its own authority on the remote party's instructions.

Doing nothing means the skills stay documentation-only.

## Decision

**We wrap the official `@a2a-js/sdk@1.0.1` client and enforce a one-way trust rule: a card informs a
human decision and never widens machine authority.**

Four commitments implement it:

1. **Per-call client construction, nothing cached.** Every tool builds a client from the card at the
   given base URL and discards it. A card cannot install itself as a durable default because no
   default survives the call.
2. **Report, never adopt.** `fetch_agent_card` returns claims labelled `claimed` with a disposition of
   `reported` or `operator-decision-required`, and never writes local configuration. There is
   deliberately **no trust score** — a single number invites automating the decision the ruling puts
   with an operator. A test asserts no `trustScore` / `trusted` / `safe` / `verdict` key is ever
   emitted.
3. **Three-valued signature status.** `absent`, `unverified`, or `verified against <key>`. Since this
   server obtains no independent key, it never reports the third. Collapsing `unverified` into either
   neighbour manufactures confidence that no verification produced.
4. **Operator-held credentials only.** Auth comes from `A2A_BEARER_TOKEN` / `A2A_API_KEY` /
   `A2A_AUTH_HEADER_NAME`. There is no credential discovery and no re-auth negotiation — a `401`/`403`
   surfaces rather than triggering a guessed retry.

The audit logic lives in a **pure module with no I/O** (`servers/card-audit.ts`), imported by the
server and exercised directly by tests. Structure without side effects is what makes "no side effects"
testable.

## Alternatives considered

| Alternative | Why rejected |
| --- | --- |
| Hand-roll the JSON-RPC client | Three bindings, fallback ordering, tenant echo, camelCase-over-proto, a `oneof` result, and nine error codes. The camelCase rule alone fails silently — servers drop unknown fields rather than rejecting them. Reimplementing a spec the maintainers already implement is cost with no upside. |
| Auto-configure from the fetched card — adopt capabilities, use the declared URL | The obvious design, and the confused-deputy primitive the CISO ruling names. It converts a remote-authored document into local authority. |
| Emit a card trust score or overall verdict | Compresses the operator decision into a number, which invites automating it. Enumerated claims plus explicit dispositions keep the human where the ruling puts them. |
| Verify card signatures and report `valid` | Without a key obtained independently of the card, verification is circular — fetching a key from a location the card names lets the card verify itself. `unverified` is the only honest output. |
| Cache resolved clients per base URL for speed | Turns one accepted card into a persistent default and makes revocation invisible. The per-call cost is a page fetch; the correctness gain is that trust never accumulates silently. |
| Expose the push-notification config methods now | A callback is inbound untrusted traffic that needs a receiving endpoint this server does not own. Shipping the registration half without the receiving half invites data loss that looks like success. |
| Follow `documentationUrl` / `iconUrl` to enrich results | An unattended fetch to a host the remote party chose, from inside the caller's network. Reported as strings instead; the auditing agent additionally denies `WebFetch` so it cannot be done at all. |

## Consequences

**Positive:**

- Spec fidelity is inherited from the maintainers, and tracks the spec as the SDK does.
- The trust rule is enforced by structure — pure audit module, no caching, no write tools on the
  auditing agent — rather than by instructions a model may not follow.
- Errors surface verbatim with their codes, so callers can apply the retry policy the spec implies
  (never retry a failed-precondition class unchanged) instead of guessing from prose.
- Verified end-to-end rather than asserted: 22/22 assertions against a reference agent, 29 unit tests.

**Negative / accepted tradeoffs:**

- **Slower and more friction than auto-configuration.** Every integration needs an operator decision
  the first time. That is the intended cost.
- **Per-call card fetch** adds a round trip to every tool call. Accepted so trust never accumulates.
- **Bound to the SDK's release cadence and shape.** The SDK exposes proto-numeric `TaskState` values
  and a `payload.$case` union on stream events; callers see those shapes, and an SDK major will move
  them.
- **Four of eleven A2A methods are unexposed**, so push-notification workflows are out of reach today.
- **`dist/` is gitignored repo-wide**, so installing from a fresh checkout needs a build step. This
  matches all fifteen MCP plugins here rather than special-casing one, but it does mean the plugin is
  not runnable straight out of a clone.

## Tool-permission scope

This is an MCP server rather than a skill, so the relevant scope is what the server itself can reach.

| Capability | Why it's needed |
| --- | --- |
| Outbound HTTPS via the SDK's `fetch` | The only way to reach a remote A2A agent. Wrapped by `createAuthenticatingFetchWithRetry` so operator credentials are injected at one boundary. |
| Read `A2A_BEARER_TOKEN` / `A2A_API_KEY` / `A2A_AUTH_HEADER_NAME` from the environment | Credentials must come from the operator, never from a card. No other environment access is used. |
| stdio | The MCP transport. No HTTP listener, so there is no inbound surface. |

Deliberately absent: **no filesystem access, no shell, no card-named URL resolution.** A tool that
cannot write cannot adopt a claim by accident.
