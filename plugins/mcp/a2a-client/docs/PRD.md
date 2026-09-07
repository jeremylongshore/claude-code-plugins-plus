# Product requirements: a2a-client

## Goal

Let a Claude Code session inspect and communicate with conformant A2A agents through MCP without
turning remote card claims into local authority or exposing local credentials/network services.

## Required behavior

- Expose card fetch/validation, message send/stream, task get/list, and confirmation-gated task
  cancellation.
- Accept `validate_agent_card` with either an inline `card` or a remote `baseUrl`; the advertised JSON
  schema and runtime validation must agree.
- Preserve A2A protocol response arms and protocol error codes.
- Return failures as structured MCP tool results instead of transport-level exceptions.
- Refuse non-public destinations by default, recheck redirect destinations, strip caller-supplied
  credentials, and scope configured credentials to HTTPS on an explicit hostname allowlist.
- Keep card-selected interfaces and redirects on the caller-requested origin by default; require a
  separate operator destination-origin allowlist for every cross-origin hop.
- Ensure the DNS answer checked by policy is the address used by the socket connector.
- Bound each HTTP request and response-body bytes with fail-closed operator-configurable limits.
- Keep cancellation disabled by default; when enabled, also require host approval and
  `confirmation: "cancel <taskId>"`.
- Ship a built executable entrypoint at `dist/index.js`; do not reference an unpublished package.
- Pin direct runtime and build dependencies exactly and retain a workspace lockfile.

## Acceptance evidence

- Focused unit tests for card audit, SSRF, destination authority, credential, redirect, request-body,
  timeout, response-size, and DNS-rebinding rules.
- MCP handshake tests over both an in-memory transport and the built stdio entrypoint.
- Local end-to-end card discovery and `send_message` against a reference agent constructed with the
  official A2A server SDK.
- Destructive-policy registry validation and an executable host confirmation hook test.
- Typecheck, lint, package contents inspection, schema/catalog sync, and repository governance gates.

## Explicit non-goals

- Trust scoring or automatic adoption of remote card claims.
- Credential discovery, token exchange, or automatic retry with a different credential.
- Push-notification registration; it requires an inbound callback surface this plugin does not own.
- Claiming that cancellation is a guaranteed remote kill operation.
