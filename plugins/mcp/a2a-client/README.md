<h1 align="center">a2a-client</h1>

<p align="center">
  An MCP server that makes a Claude Code session a first-class <strong>Agent2Agent (A2A)</strong>
  participant — card discovery, messaging, streaming, and task control against any conformant
  agent.<br>
  Wraps the official <code>@a2a-js/sdk</code>. Conforms to the published A2A specification and
  defines no wire format of its own.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-10b981?style=flat-square" alt="License: MIT">
  <img src="https://img.shields.io/badge/MCP-stdio-8b5cf6?style=flat-square" alt="MCP stdio">
  <img src="https://img.shields.io/badge/A2A-v1.0-0ea5e9?style=flat-square" alt="A2A v1.0">
  <img src="https://img.shields.io/badge/cards-untrusted%20input-f59e0b?style=flat-square" alt="cards are untrusted input">
</p>

---

## Why this server exists

A2A is the surviving open standard for agent-to-agent communication. Its predecessor was archived and
folded into A2A under the Linux Foundation, so there is exactly one standard to conform to. The
protocol has SDKs in seven languages and a published conformance inspector — and, before this server,
no Claude Code layer at all.

That gap is the whole reason this exists. A Claude Code session could talk to tools (MCP) and to
humans, but not to another organization's agent over the one protocol built for it.

**The design constraint that shapes every tool here:** an agent card is an externally-authored
manifest, fetched over the network, describing what a remote party would like the local agent to
believe. Adopting one is a textbook confused-deputy primitive. So every tool **reports** what a card
claims and none of them convert a claim into local authority — no capability is auto-enabled, no
interface URL becomes a default, no card-named URL is resolved on the card's say-so, and there is
deliberately **no trust score**, because a single number invites automating the one decision that has
to stay with an operator.

## Tool surface (7)

| Tool | A2A method | What it does |
|---|---|---|
| `fetch_agent_card` | `GET /.well-known/agent-card.json` | Fetch a remote card and return a structure verdict, an enumerated claims table, and findings. Claims are labelled `claimed`; nothing is adopted. |
| `validate_agent_card` | — (local) | Validate a card (fetched or supplied inline) against the required A2A fields. Returns the verdict, findings, and a count of decisions needing an operator. |
| `send_message` | `SendMessage` | Send a message. Branches the `oneof` response and reports which arm came back — a `Task`, or an inline `Message` from an agent that answered without creating one. |
| `stream_message` | `SendStreamingMessage` | Send and collect streamed events with an event cap. Falls back to non-streaming when the agent does not support it. |
| `get_task` | `GetTask` | Retrieve a task's current status, artifacts, and optional history. |
| `list_tasks` | `ListTasks` | List tasks, optionally scoped to one conversation `contextId`. |
| `cancel_task` | `CancelTask` | Request cancellation. The result carries a note that a cancel is a request, not a kill switch — the task may be uncancelable. |

Push-notification config methods (`Create`/`Get`/`List`/`Delete TaskPushNotificationConfig`) and
`GetExtendedAgentCard` are reachable through the SDK but are not exposed as tools yet: a push
callback is inbound untrusted traffic that needs a receiving endpoint this server does not own.

## Auth — operator-held, never card-derived

Credentials belong to the operator and arrive through the environment. They are never read from an
agent card, never logged, and never echoed in a tool result.

| Env | Effect |
|---|---|
| `A2A_BEARER_TOKEN` | Sends `Authorization: Bearer <token>` |
| `A2A_API_KEY` | Sends the value as-is in the auth header |
| `A2A_AUTH_HEADER_NAME` | Overrides the header name (default `Authorization`) |

There is **no credential discovery and no re-auth negotiation**: a `401`/`403` is surfaced to the
operator rather than answered with a guessed second credential. An agent's declared `securitySchemes`
tell you which credential to set; they never cause one to be fetched.

## Install

### Claude Code (via the marketplace)

```
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install a2a-client
```

### Any `.mcp.json` consumer (stdio)

```json
{
  "mcpServers": {
    "a2a-client": {
      "command": "node",
      "args": ["/abs/path/to/plugins/mcp/a2a-client/dist/servers/a2a-client.js"],
      "env": { "A2A_BEARER_TOKEN": "…" }
    }
  }
}
```

The in-plugin config uses `${CLAUDE_PLUGIN_ROOT}` so no absolute path is needed when installed as a
plugin. Run `pnpm install && pnpm build` once in the plugin directory to produce `dist/` — `dist/` is
gitignored repo-wide, the same as every other MCP plugin here.

## Pairs with

The [`agent-comms`](../../agent-comms/agent-comms) pack is the skill layer over this server:
`a2a-protocol` (the wire surface), `a2a-agent-card` (authoring and auditing cards, plus the
`a2a-card-auditor` agent), `comms-topology`, `topology-safety`, `agent-mailbox`, and
`mas-failure-triage`. The server is the hands; the pack is the judgment.

## Develop

```bash
npm install
npm run typecheck     # tsc --noEmit
npm run test:ci       # vitest run — 29 tests over the pure card-audit module
npm run lint
npm run build         # tsc → dist/ (committed)
```

**Verified end-to-end** against a reference A2A agent built on the official `@a2a-js/sdk` server
module: card fetch and audit, a `SendMessage` round-trip returning a task, a streamed call emitting
`task → statusUpdate → artifactUpdate → statusUpdate`, `GetTask` reaching a terminal `COMPLETED`
state with artifacts, a `CancelTask` on a still-live task returning `CANCELED`, and an unknown task
id surfacing `Task not found` verbatim rather than a fake success — 22 of 22 assertions.

## License

MIT
