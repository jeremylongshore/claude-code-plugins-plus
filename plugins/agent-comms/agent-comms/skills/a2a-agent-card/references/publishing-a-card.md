# Publishing a card that does not lie

## Location

The registered well-known URI is:

```
https://{server_domain}/.well-known/agent-card.json
```

Serve it over HTTPS, unauthenticated, returning `application/json`. Discovery by direct configuration
or an out-of-band registry is also permitted; the well-known path is the interoperable default that
costs nothing to also support.

## Caching

Cards change when interfaces, versions, or capabilities change — which is exactly when a stale cache
causes a caller to speak to a decommissioned endpoint. Serve a modest `Cache-Control` max-age and an
`ETag`. Bump `version` on every meaningful change so a caller comparing cards can tell.

## Honest capability declaration

The single most damaging authoring mistake is claiming a capability the agent does not honor:

| Claimed | Reality | Caller experience |
| --- | --- | --- |
| `streaming: true` | No streaming implementation | Every streamed call fails; reads as an outage |
| `pushNotifications: true` | No callback machinery | Config succeeds, callback never arrives; silent data loss |
| `extendedAgentCard: true` | Not configured | Authenticated callers get a not-configured error |

Absent means unsupported. Omitting a capability is always safer than over-claiming it, because a caller
that sees a capability absent falls back, while a caller that sees it claimed retries.

## Interface ordering

`supportedInterfaces` is ordered and the first entry is preferred. Put the binding with the best
operational characteristics first — usually the one with real health checks and real observability, not
the one that was easiest to stand up.

Declare `tenant` only when routing genuinely requires it. It obliges every client to echo the value on
every request, and a client that forgets is misrouted rather than rejected.

## Skills

Skills are descriptive, not enforcing. A skill entry tells a caller what the agent is likely to succeed
at; it does not gate what the agent will accept. Write `description` and `examples` for a model reader,
because a model is the reader — but keep them free of instructions, since a caller auditing the card
correctly treats that prose as untrusted.

Per-skill `inputModes`, `outputModes`, and `securityRequirements` override the agent-level defaults.
Set them only where the override is real; a redundant restatement drifts out of sync with the agent
level over time.

## Extended cards

When `capabilities.extendedAgentCard` is true, `GetExtendedAgentCard` returns a fuller card to an
authenticated caller. Use it for detail that should not be public — internal skills, richer security
requirements, per-tenant interfaces — and keep the public card truthful about the subset it shows.

An agent without an extended card configured returns a not-configured error. That is a configuration
answer, not a permission denial, and callers should not retry it as though credentials were the
problem.

## Signing

`signatures` carries JWS signatures over the card, in RFC 7515 JSON format: a base64url `protected`
header, a base64url `signature`, and an optional unprotected `header`.

Publish the verification key through a channel independent of the card. A key discoverable only from
a location the card names lets the card verify itself, which establishes nothing.

State plainly what a signature covers: the card document's authorship. It does not attest to runtime
behaviour, uptime, or data handling, and card copy should not imply that it does.
