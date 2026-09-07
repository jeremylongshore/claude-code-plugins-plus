# ADR: wrap the official A2A SDK behind a fail-closed network boundary

**Date:** 2026-09-01
**Status:** Accepted

## Context

The A2A protocol includes multiple transports, version negotiation, task lifecycle semantics, and
typed error behavior. Reimplementing the wire protocol would duplicate the official SDK and create
silent compatibility risk.

An agent card is also an externally authored manifest. It can contain free text, interface URLs,
security claims, and extension requirements. Treating those claims as local authority would create a
confused-deputy boundary: a remote party could influence destinations or credentials used by the
local agent.

## Decision

Use the exactly pinned `@a2a-js/sdk@1.0.1`, with these constraints:

1. Build a client per tool call. No remote card becomes a durable default.
2. Audit cards as reports. Do not emit a trust score or auto-enable capabilities.
3. Obtain credentials only from operator-controlled environment variables and send them only over
   HTTPS to an exact hostname in `A2A_ALLOWED_HOSTS`. This credential allowlist does not authorize
   cross-origin message delivery.
4. Route all SDK requests through `src/net-guard.ts`. The guard rejects non-HTTP schemes,
   URL-embedded credentials, non-public IP ranges by default, and unsafe redirect hops.
5. Give Undici a custom DNS lookup function. The function validates the complete answer set and
   returns the selected checked address directly to the socket connector, eliminating a second
   unchecked lookup between policy evaluation and connection.
6. Follow redirects manually. Re-evaluate destination and credential scope on each hop, implement
   bodyless `GET` conversion for `303` and `301/302` after `POST`, and preserve request bodies for
   `307/308`.
7. Treat the origin in the caller's `baseUrl` as the default destination authority. A card-selected
   interface or redirect may leave it only when its exact origin is listed separately in
   `A2A_ALLOWED_DESTINATIONS`.
8. Enforce a bounded timeout and decoded response-body size on every guarded request.
9. Do not adopt proxy environment variables. Keep the checked, direct Undici connector as the
   network path unless a separately reviewed proxy-aware pinning design is added.
10. Return tool failures as structured `isError: true` MCP results.
11. Treat `cancel_task` as destructive and default it off. After the operator sets
    `A2A_ALLOW_TASK_CANCELLATION=1`, still require both a host-side `PreToolUse` approval and the exact
    in-band phrase `cancel <taskId>` before calling the remote agent.
12. Bundle the runtime deterministically into a tracked, executable `dist/index.js`. This gives both
    marketplace installs and the npm tarball a real entrypoint without depending on an install hook
    or an unpublished registry package.

## Consequences

- Protocol fidelity follows the official SDK.
- Card claims remain observable without becoming authority.
- SSRF, credential forwarding, redirect, and DNS-rebinding controls share one testable choke point.
- Private/loopback agents require the explicit `A2A_ALLOW_PRIVATE_HOSTS=1` development exception.
- A configured credential does nothing until its destination hostname is allowlisted.
- Cross-origin routing does nothing until its destination origin is independently allowlisted.
- The tracked bundle is larger than source-only publication, but it makes installation behavior
  deterministic. CI rebuilds it and fails when the committed artifact drifts.
- Cancellation is unavailable by default, then needs two further deliberate approvals, and may still
  be refused by the remote agent.

## Verification

Automated tests cover card auditing, IP classification, same-origin authority, redirect method/body
behavior for `Request` inputs, credential stripping and redirect scope, connector-level DNS rebinding
refusal, timeout and response bounds, structured MCP errors, all cancellation gates, an actual built
stdio handshake, and card/message round trips through the official A2A client and server stacks.
