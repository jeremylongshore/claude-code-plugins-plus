# Discovery, transports, and serialization

## Discovery

The registered well-known URI is:

```
https://{server_domain}/.well-known/agent-card.json
```

The resource at that URI returns an `AgentCard`. The spec also permits discovery by direct
configuration or by an out-of-band registry — the well-known path is the interoperable default, not
the only route.

`GetExtendedAgentCard` returns a fuller card to an authenticated caller when
`capabilities.extendedAgentCard` is true. An agent without that configured returns
`ExtendedAgentCardNotConfiguredError` (`-32007`); that is a configuration answer, not a permission
denial.

## Interfaces and bindings

`AgentCard.supportedInterfaces` is an **ordered** list. Each `AgentInterface` declares:

| Field | Notes |
| --- | --- |
| `url` | Absolute HTTPS URL for HTTP-family transports; `host:port` for gRPC |
| `protocolBinding` | Open-form string. Officially: `JSONRPC`, `GRPC`, `HTTP+JSON` |
| `protocolVersion` | The A2A version at this URL, e.g. `"0.3"`, `"1.0"` |
| `tenant` | Optional opaque routing token — when set, clients MUST echo it on every request |

The first entry is preferred. Clients may choose any declared binding and should implement fallback
down the list. Speaking a binding the card does not declare is out of contract even when the endpoint
happens to answer.

### Choosing a binding

- **JSON-RPC** — the lowest-friction default. One POST endpoint, method in the body. Best when the
  client is a script, a shell, or an MCP server.
- **gRPC** — real bidirectional streaming and typed stubs. Best inside a service mesh that already
  terminates gRPC. Requires generated code.
- **HTTP+JSON** — REST-shaped resource URLs (`GET /tasks/{id}`, `POST /tasks/{id}:cancel`). Best when an
  existing API gateway must inspect or route on the path.

## Serialization

All JSON serializations use **camelCase**, not the proto `snake_case`:

| Proto | JSON |
| --- | --- |
| `protocol_version` | `protocolVersion` |
| `context_id` | `contextId` |
| `default_input_modes` | `defaultInputModes` |
| `push_notification_config` | `pushNotificationConfig` |

Enums serialize as their proto string names (`TASK_STATE_WORKING`), per ProtoJSON.

A client that hand-rolls JSON from the proto field names will send `context_id` and be silently
ignored by a conformant server, because unknown fields are dropped rather than rejected. This is the
single most common first-integration failure — assert on the response shape, not on a 200.

## Security schemes

`AgentCard.securitySchemes` is a map of scheme name to a `SecurityScheme` `oneof`: API key, HTTP auth,
OAuth2 (authorization-code, client-credentials, implicit, password, device-code flows), OpenID Connect,
or mutual TLS. `securityRequirements` names which schemes and scopes a caller must satisfy.

Per-skill `securityRequirements` **override** the agent-level list. A card that looks open at the top
level can still gate an individual skill.

Credentials satisfying these schemes belong to the operator and are supplied through the MCP server's
environment. Never inline a credential into a message body, an artifact, or a card.
