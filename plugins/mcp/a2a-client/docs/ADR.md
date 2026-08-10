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
4. **Operator-held credentials, scoped to nominated hosts.** Auth comes from `A2A_BEARER_TOKEN` /
   `A2A_API_KEY` / `A2A_AUTH_HEADER_NAME`, and is attached **only** to a host listed in
   `A2A_ALLOWED_HOSTS`. With no allowlist, no credential ever leaves the process. There is no
   credential discovery and no re-auth negotiation — a `401`/`403` surfaces rather than triggering a
   guessed retry.
5. **A single outbound choke point** (`servers/net-guard.ts`). Every request — card resolution,
   protocol calls, anything the SDK does internally — passes a destination check that refuses private,
   loopback, link-local, and carrier-grade-NAT addresses unless `A2A_ALLOW_PRIVATE_HOSTS=1`. Hostnames
   are resolved and *every* returned address is checked, so a public name pointing inward is refused.

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
| Enforce the trust rule in the audit output only (the first cut) | Review caught this correctly: the audit *reported* a card pointing at `10.0.0.7`, and the protocol client then called it anyway, while the operator's credential went to whatever host the caller named. The posture held in the report and failed in the socket. A guard at the fetch seam is the only placement that covers card resolution, interface calls, and SDK-internal requests together. |
| Block private hosts with no escape hatch | Makes local development against a reference agent impossible, which is exactly how this plugin is tested. `A2A_ALLOW_PRIVATE_HOSTS=1` is an explicit, documented, off-by-default opt-in. |
| Attach credentials to any host, and rely on the caller to pass the right `baseUrl` | The caller may be a model acting on injected content. Requiring the operator to nominate destinations moves the decision to the only party that can make it. |

## Consequences

**Positive:**

- Spec fidelity is inherited from the maintainers, and tracks the spec as the SDK does.
- The credential-egress and SSRF classes are closed at one auditable place rather than at each call
  site, and both fail closed: no allowlist means no credential, and private destinations are refused
  by default.
- The trust rule is enforced by structure — pure audit module, no caching, no write tools on the
  auditing agent — rather than by instructions a model may not follow.
- Errors surface verbatim with their codes, so callers can apply the retry policy the spec implies
  (never retry a failed-precondition class unchanged) instead of guessing from prose.
- Exercised end-to-end rather than asserted: 22/22 assertions against a reference agent, 67 unit
  tests, and a fail-closed guard check refusing `127.0.0.1`, `localhost`, and `169.254.169.254`.

**Negative / accepted tradeoffs:**

- **Slower and more friction than auto-configuration.** Every integration needs an operator decision
  the first time. That is the intended cost.
- **Per-call card fetch** adds a round trip to every tool call. Accepted so trust never accumulates.
- **Bound to the SDK's release cadence and shape.** The SDK exposes proto-numeric `TaskState` values
  and a `payload.$case` union on stream events; callers see those shapes, and an SDK major will move
  them.
- **Four of eleven A2A methods are unexposed**, so push-notification workflows are out of reach today.
- **`dist/` is gitignored repo-wide**, so a fresh checkout has no entrypoint. Rather than special-case
  one plugin against the repo convention, the package carries a `prepare` script, so `pnpm install`
  builds it. A consumer who copies only the launcher without installing still gets `MODULE_NOT_FOUND`.
- **Fail-closed credentials are a usability cost.** Setting `A2A_BEARER_TOKEN` alone does nothing
  until `A2A_ALLOWED_HOSTS` names a destination. That will read as a bug to someone who has not read
  the auth section, and it is the correct default anyway.
- **DNS rebinding is not covered.** The address check runs before the request; a name whose resolution
  changes between check and connect defeats it. Closing that needs a pinned-IP dialer the SDK's
  `fetch` seam does not expose. Stated in the module header and the README rather than left implicit.

## Tool-permission scope

This is an MCP server rather than a skill, so the relevant scope is what the server itself can reach.

| Capability | Why it's needed |
| --- | --- |
| Outbound HTTPS via the SDK's `fetch` | The only way to reach a remote A2A agent. Wrapped by `createGuardedFetch` so the destination check and credential scoping apply at one boundary. |
| DNS resolution (`node:dns/promises`) | Needed to refuse a public hostname that resolves to a private address. Read-only. |
| Read `A2A_ALLOWED_HOSTS` / `A2A_BEARER_TOKEN` / `A2A_API_KEY` / `A2A_AUTH_HEADER_NAME` / `A2A_ALLOW_PRIVATE_HOSTS` from the environment | Credentials and destination policy must come from the operator, never from a card. No other environment access is used. |
| stdio | The MCP transport. No HTTP listener, so there is no inbound surface. |

Deliberately absent: **no filesystem access, no shell, no card-named URL resolution.** A tool that
cannot write cannot adopt a claim by accident.
