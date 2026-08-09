# AgentCard schema — every field and what it actually binds

Field names below are the JSON (camelCase) forms. The proto definitions use `snake_case`; the spec
requires camelCase on the wire.

## Required

| Field | Type | Notes |
| --- | --- | --- |
| `name` | string | Human-readable agent name |
| `description` | string | What the agent is for |
| `supportedInterfaces` | `AgentInterface[]` | **Ordered** — first entry is preferred |
| `version` | string | The **agent's** version, not the protocol version |
| `capabilities` | `AgentCapabilities` | Declares optional protocol features |
| `defaultInputModes` | string[] | Media types accepted across all skills |
| `defaultOutputModes` | string[] | Media types produced |
| `skills` | `AgentSkill[]` | At least descriptive; each entry has its own required set |

## Optional

| Field | Type | Notes |
| --- | --- | --- |
| `provider` | `AgentProvider` | `organization` + `url`, both required when present |
| `documentationUrl` | string | A remote-chosen fetch target — treat as untrusted |
| `securitySchemes` | map<string, SecurityScheme> | Named schemes available |
| `securityRequirements` | `SecurityRequirement[]` | Which schemes and scopes callers must satisfy |
| `signatures` | `AgentCardSignature[]` | JWS over the card, per RFC 7515 |
| `iconUrl` | string | Presentational |

## AgentInterface

| Field | Required | Notes |
| --- | --- | --- |
| `url` | yes | Absolute HTTPS in production; `hostname:port` for gRPC |
| `protocolBinding` | yes | Open-form. Official values: `JSONRPC`, `GRPC`, `HTTP+JSON` |
| `protocolVersion` | yes | e.g. `"0.3"`, `"1.0"` — latest supported minor per major |
| `tenant` | no | Opaque routing token. **When set, clients MUST echo it on every request** |

`protocolBinding` is deliberately open-form so new bindings can appear. An unknown binding is not an
error in the card; it is simply one this client cannot speak. Fall through to the next entry.

## AgentCapabilities

| Field | Meaning |
| --- | --- |
| `streaming` | `SendStreamingMessage` / `SubscribeToTask` are available |
| `pushNotifications` | The push-notification config methods are available |
| `extensions` | `AgentExtension[]` — protocol extensions this agent uses |
| `extendedAgentCard` | `GetExtendedAgentCard` returns more detail to an authenticated caller |

All four are optional booleans or lists. **Absent means not supported.** Do not read an absent field
as "probably yes"; the resulting call returns an unsupported-operation error.

### AgentExtension

`uri`, `description`, `required`, and optional `params`. `required: true` means a client that does not
understand the extension must not proceed — the spec surfaces this as an
extension-support-required error rather than silent degradation.

## AgentSkill

Required: `id`, `name`, `description`, `tags`. Optional: `examples`, `inputModes`, `outputModes`,
`securityRequirements`.

Two overrides live here and both are easy to miss:

- `inputModes` / `outputModes` **override** the agent-level defaults for that skill only.
- `securityRequirements` **override** the agent-level requirements for that skill only.

A card whose agent-level `securityRequirements` looks strict can still expose one skill with a weaker
per-skill requirement. Audit at the skill level, not just the agent level.

## AgentCardSignature

`protected` (base64url JWS header, required), `signature` (base64url, required), and an optional
unprotected `header`.

What a valid signature establishes: the card content was signed by the holder of some key. What it
does **not** establish: that the key belongs to the organization named in `provider`, that the agent
behaves as described, or that the declared interfaces are safe to call. Signature verification answers
authorship. It never answers trustworthiness.

## Security schemes

`SecurityScheme` is a `oneof` over API key, HTTP auth, OAuth2 (authorization-code, client-credentials,
implicit, password, and device-code flows), OpenID Connect, and mutual TLS. `SecurityRequirement` maps
scheme names to required scopes.
