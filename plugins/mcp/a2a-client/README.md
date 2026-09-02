# a2a-client

`a2a-client` is a stdio MCP server for discovering and calling Agent2Agent (A2A) agents through the
official `@a2a-js/sdk`. It exposes seven tools while treating every remote agent card as untrusted
input: claims are reported for operator review and never become persistent local authority.

## Tools

| Tool                  | Behavior                                                                           |
| --------------------- | ---------------------------------------------------------------------------------- |
| `fetch_agent_card`    | Fetch and audit a remote card without adopting its claims                          |
| `validate_agent_card` | Audit either an inline card or a card fetched from `baseUrl`                       |
| `send_message`        | Send a message and distinguish task responses from inline messages                 |
| `stream_message`      | Collect a bounded number of streamed events                                        |
| `get_task`            | Read task status, artifacts, and optional history                                  |
| `list_tasks`          | List tasks, optionally by conversation context                                     |
| `cancel_task`         | Request cancellation behind operator opt-in, host approval, and exact-phrase gates |

All tool failures are returned as MCP tool results with `isError: true` and a JSON body containing
`error.code` and `error.message`. Protocol error codes are preserved when the A2A SDK provides them.

## Security boundary

Every card and protocol request uses one guarded fetch path.

- Only HTTP and HTTPS are accepted. URL-embedded credentials are refused.
- Public destinations are the default. Loopback, private, link-local, carrier-grade NAT, multicast,
  and reserved IP ranges are refused unless `A2A_ALLOW_PRIVATE_HOSTS=1` is set for deliberate local
  development.
- Hostnames are checked on the DNS lookup used by Undici's socket connector. The validated address
  is passed directly to the connection, so there is no separate unchecked lookup for a DNS rebinding
  attacker to win.
- Agent-card fetches, card-selected interfaces, and redirects stay on the origin named by `baseUrl`
  by default. Cross-origin traffic requires the exact destination origin in the separate
  `A2A_ALLOWED_DESTINATIONS` operator allowlist; the credential allowlist never grants message-routing
  authority.
- Redirects are followed manually, capped at five, and rechecked on every hop. `303` and `301/302`
  after `POST` switch to a bodyless `GET`; `307/308` preserve method and body.
- `Authorization`, `Proxy-Authorization`, and `Cookie` supplied by a caller are stripped. A configured
  credential is attached only over HTTPS and when the destination host is in `A2A_ALLOWED_HOSTS`;
  both conditions are rechecked after every redirect.
- Each HTTP request has a 30-second default timeout, and each HTTP response is limited to 2 MiB by
  default, including streamed bodies. Both limits are operator-configurable within hard safety caps.
- Proxy environment variables are not used. The pinned direct connector is part of the SSRF
  boundary; proxy support would require a separate guard-aware connector design.

`A2A_ALLOW_PRIVATE_HOSTS=1` deliberately disables the IP-range restriction. Use it only for a local
agent you control; it is not a production bypass.

### Authentication environment

| Variable                      | Effect                                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `A2A_ALLOWED_HOSTS`           | Comma-separated exact hostnames allowed to receive the configured credential over HTTPS; empty means none                 |
| `A2A_ALLOWED_DESTINATIONS`    | Comma-separated exact HTTP(S) origins allowed for cross-origin card interfaces or redirects; empty means same-origin only |
| `A2A_BEARER_TOKEN`            | Sends `Authorization: Bearer <token>` to allowlisted hosts                                                                |
| `A2A_API_KEY`                 | Raw credential value used when no bearer token is set                                                                     |
| `A2A_AUTH_HEADER_NAME`        | Credential header name; defaults to `Authorization`                                                                       |
| `A2A_ALLOW_PRIVATE_HOSTS`     | Exact value `1` permits non-public destinations for local development                                                     |
| `A2A_ALLOW_TASK_CANCELLATION` | Exact value `1` enables the otherwise-disabled `cancel_task` path; confirmation gates still apply                         |
| `A2A_REQUEST_TIMEOUT_MS`      | Per-request timeout in milliseconds; defaults to `30000`, maximum `300000`                                                |
| `A2A_MAX_RESPONSE_BYTES`      | Maximum decoded response-body bytes; defaults to `2097152`, maximum `67108864`                                            |

There is no credential discovery or re-authentication fallback. A remote card's security declarations
do not cause this process to fetch or select a credential.

## Cancellation policy

`cancel_task` has three independent gates:

1. The server refuses every cancellation unless the operator sets `A2A_ALLOW_TASK_CANCELLATION=1`.
2. `hooks/hooks.json` registers a `PreToolUse` hook that asks the Claude Code host for approval in
   both direct-MCP and plugin-namespaced installations.
3. The MCP server refuses the call unless `confirmation` exactly equals `cancel <taskId>`.

Cancellation remains a remote request, not a kill guarantee. Inspect the returned task state.

The host-approval hook is specific to marketplace installations in Claude Code. The standalone npm
binary cannot install a Claude host hook; it retains the server-side default-off environment gate and
exact task-bound confirmation phrase. Standalone operators should add an equivalent approval policy in
their MCP host before enabling cancellation.

## Install and run

From the Tons of Skills marketplace:

```text
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install a2a-client
```

The plugin ships a built, executable `dist/index.js`; `.mcp.json` launches that file directly and
does not depend on an unpublished registry package.

After the npm package is published, it can also be installed as a standalone binary:

```bash
npm install --global @intentsolutionsio/a2a-client@0.1.0
a2a-client
```

Example MCP configuration for a checked-out plugin:

```json
{
  "mcpServers": {
    "a2a-client": {
      "command": "node",
      "args": ["/absolute/path/to/plugins/mcp/a2a-client/dist/index.js"],
      "env": {
        "A2A_ALLOWED_HOSTS": "agents.partner.example.com",
        "A2A_BEARER_TOKEN": "<set-outside-source-control>",
        "A2A_ALLOW_TASK_CANCELLATION": ""
      }
    }
  }
}
```

## Develop

From the repository root:

```bash
pnpm install --frozen-lockfile
pnpm --filter @intentsolutionsio/a2a-client typecheck
pnpm --filter @intentsolutionsio/a2a-client lint
pnpm --filter @intentsolutionsio/a2a-client test:ci
```

`test:ci` rebuilds the bundled entrypoint, enforces the configured 80% coverage thresholds, then runs
unit, policy, MCP handshake, and local A2A end-to-end tests. The end-to-end fixture uses the official
A2A server stack on loopback and explicitly
enables the local-development exception.

## License

MIT
