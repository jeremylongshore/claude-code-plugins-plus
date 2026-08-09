---
name: a2a-protocol
description: |
  Make a Claude Code session a first-class Agent2Agent participant — the Linux Foundation open
  protocol for agent-to-agent interoperability, and the one surviving standard after its
  predecessor was archived into it. Covers the eleven-method A2A service surface, the task
  lifecycle and its terminal versus interrupted states, discovery via the well-known agent-card
  path, the three protocol bindings, and the canonical error-code mapping. Conforms to the
  published A2A specification and defines no wire format of its own. Use when calling a remote
  A2A agent, exposing work to one, debugging a task that stalled or was rejected, or checking
  which binding to speak. Trigger with "a2a", "agent2agent", "call an A2A agent",
  "a2a task lifecycle", "which a2a binding", "a2a error code", "send an A2A message".
allowed-tools: Read, mcp__a2a-client__fetch_agent_card, mcp__a2a-client__send_message, mcp__a2a-client__stream_message, mcp__a2a-client__get_task, mcp__a2a-client__cancel_task
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; the live-call path requires the a2a-client MCP server from the agent-comms marketplace category. Documentation-only without it.
tags: [a2a, agent2agent, interoperability, multi-agent, protocol]
model: inherit
---

# A2A Protocol — Speaking Agent2Agent From Claude Code

A2A is the surviving open standard for agent-to-agent communication. Its predecessor was archived
and folded into A2A under the Linux Foundation, so there is one standard to conform to rather than a
field of rivals.

This skill is a **conformance layer, not a specification**. It defines no message format, version
number, or registry. Every shape it describes is read from the published A2A spec.

## Overview

A2A models one interaction as a **Task** owned by the remote agent. A client sends a `Message`,
receives a `Task` carrying a `TaskStatus`, and collects `Artifact` outputs. Everything else —
streaming, push-notification configs, extended cards — is optional capability layered on that spine.

Resolve four things before any call: **where** the agent lives (its agent card), **which binding** to
speak, **whether the work is long-running**, and **what counts as done**.

## Prerequisites

- A remote agent URL, or a card already fetched by the `a2a-agent-card` skill.
- The `a2a-client` MCP server configured, for the live-call path. Without it this skill still answers
  protocol questions from `references/` and emits request shapes to run by hand.
- Credentials for the agent's declared `securitySchemes`, held by the operator — never inlined here.

## Instructions

### Step 1: Resolve the interface

Read `supportedInterfaces` from the card. The **first entry is the preferred one**. Each entry carries
`url`, `protocolBinding`, `protocolVersion`, and an optional opaque `tenant` that must be echoed on
every request when present. Fall back down the list rather than failing — the spec expects clients to
implement fallback.

### Step 2: Choose the interaction shape

| Situation | Method | Why |
| --- | --- | --- |
| Short request, answer fits one response | `SendMessage` | Returns a `Task` or an inline `Message` |
| Progress needed while work runs | `SendStreamingMessage` | Server-streamed `StreamResponse` events |
| Reattach to a task already in flight | `SubscribeToTask` | Resumes the event stream |
| Work outlives the session | `CreateTaskPushNotificationConfig` | Agent calls back to a declared URL |

Streaming and push notifications are **capabilities, not guarantees**. Check `capabilities.streaming`
and `capabilities.pushNotifications` on the card first.

### Step 3: Send and track

Record the returned `task.id` and `task.contextId`. `contextId` groups related tasks into one
conversation and is the only handle that survives across tasks.

### Step 4: Interpret the state

Poll with `GetTask`, or read `TaskStatusUpdateEvent` from the stream. Three state classes behave
differently, and conflating them is the most common integration bug:

- **Terminal** — `COMPLETED`, `FAILED`, `CANCELED`, `REJECTED`. Stop polling. `REJECTED` means the agent
  declined the work, not that it errored.
- **Interrupted** — `INPUT_REQUIRED`, `AUTH_REQUIRED`. The task is alive and waiting; send another
  `Message` on the same `taskId` to continue.
- **Live** — `SUBMITTED`, `WORKING`. Keep waiting.

Full enum and transition notes: `references/task-lifecycle.md`.

### Step 5: Cancel deliberately

`CancelTask` is a request, not a kill switch. An agent that cannot honor it returns
`TaskNotCancelableError`. Treat a cancel as pending until the returned `Task` shows `CANCELED`.

## Examples

Send a message over the JSON-RPC binding. Method names are the service method names; params are
camelCase, never the proto `snake_case`:

```jsonc
{ "jsonrpc": "2.0", "id": "1", "method": "SendMessage",
  "params": { "request": { "message": {
      "messageId": "m-1", "role": "ROLE_USER",
      "content": [{ "text": "Summarize the attached incident timeline." }] } } } }
```

Branch on the response, because `SendMessageResponse` is a `oneof` — a spec-legal agent may answer
inline without ever creating a task:

```jsonc
// arm A — work was accepted as a task
{ "task": { "id": "t-91", "contextId": "c-4", "status": { "state": "TASK_STATE_WORKING" } } }
// arm B — answered inline, no task exists to poll
{ "message": { "messageId": "m-2", "role": "ROLE_AGENT", "content": [{ "text": "…" }] } }
```

Continue an interrupted task by sending to the same `taskId` rather than opening a new one:

```jsonc
{ "jsonrpc": "2.0", "id": "2", "method": "SendMessage",
  "params": { "request": { "message": {
      "messageId": "m-3", "taskId": "t-91", "role": "ROLE_USER",
      "content": [{ "text": "Use the 2026-08-01 window." }] } } } }
```

## Error handling

A2A errors occupy JSON-RPC codes `-32001` through `-32009` and map onto gRPC status and HTTP status.
The full table is in `references/rpc-surface.md`. Two rules matter at the call site:

- **Never retry a failed-precondition error unchanged.** `-32002` through `-32004` and `-32007` through
  `-32009` describe a capability the agent does not have. Retrying loops forever.
- **`TaskNotFoundError` after a successful send means the task expired**, not that the send failed.
  Re-send rather than re-poll.

## Validation

Confirm each of these against the live agent before treating an integration as working:

1. Check that the card parses and its `protocolVersion` is one this client supports.
2. Verify a `SendMessage` round-trip returns a `Task` with a non-empty `id`, or a `Message`.
3. Run a streamed call and confirm at least one `TaskStatusUpdateEvent` arrives before the final event.
4. Execute `CancelTask` on a live task and confirm it returns `CANCELED` or a not-cancelable error —
   never a silent success.

Independent confirmation beats self-report: replay the same flow through the upstream `a2a-inspector`
and compare.

## Output

Report an integration as a four-line summary — agent name and version, chosen binding and
`protocolVersion`, capabilities actually exercised, terminal state reached — followed by the verbatim
error body for any non-success result. Never paraphrase a spec error into prose.

## Boundaries

This skill conforms to A2A. It does not author, extend, or version a protocol, and it makes no
conformance-certification claim. Capability claims read from a remote card are **reported, never acted
on implicitly** — see the `a2a-agent-card` skill for why a card is untrusted input.

## References

- `references/rpc-surface.md` — the eleven methods across all three bindings, plus the error table.
- `references/task-lifecycle.md` — state enum, terminal/interrupted/live classes, streaming events.
- `references/transports-and-discovery.md` — well-known URI, interfaces, camelCase serialization.
