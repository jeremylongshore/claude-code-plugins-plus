# Task lifecycle — states, events, and the mistakes each one causes

A `Task` is the unit of action in A2A. It is created by the server, identified by a server-generated
`id`, and grouped with sibling tasks by `contextId`.

## The state enum

| State | Class | Meaning |
| --- | --- | --- |
| `TASK_STATE_SUBMITTED` | live | Accepted and acknowledged, not started |
| `TASK_STATE_WORKING` | live | Actively being processed |
| `TASK_STATE_COMPLETED` | terminal | Finished successfully |
| `TASK_STATE_FAILED` | terminal | Finished with an error |
| `TASK_STATE_CANCELED` | terminal | Canceled before completion |
| `TASK_STATE_REJECTED` | terminal | The agent declined to perform the work |
| `TASK_STATE_INPUT_REQUIRED` | interrupted | Waiting on more input |
| `TASK_STATE_AUTH_REQUIRED` | interrupted | Waiting on authentication |
| `TASK_STATE_UNSPECIFIED` | unknown | Indeterminate — treat as a protocol fault |

JSON serialization uses the ProtoJSON convention, so these arrive as the SCREAMING_SNAKE_CASE names
above, not as integers and not as camelCase.

## Three classes, three behaviours

**Terminal** states end the task. Stop polling, close the stream, release the handle. The distinction
that matters here is `FAILED` versus `REJECTED`: `FAILED` means the agent tried and could not;
`REJECTED` means it chose not to. Retrying a `REJECTED` task with the same content is a loop. Retrying
a `FAILED` one may be reasonable.

**Interrupted** states look terminal on a status poll but are not. The task is alive and blocked on the
client. Send a new `Message` carrying the same `taskId` to unblock it. Code that treats `INPUT_REQUIRED`
as an end state silently abandons live work on the remote side — a leak, not just a bug.

**Live** states mean keep waiting. Prefer a stream over a poll loop when `capabilities.streaming` is
true; poll with backoff otherwise.

## Streaming events

`SendStreamingMessage` and `SubscribeToTask` return a stream of `StreamResponse`, a `oneof` over:

- `Task` — the initial full task object
- `Message` — an inline reply
- `TaskStatusUpdateEvent` — a status transition, carrying a `final` marker
- `TaskArtifactUpdateEvent` — an artifact chunk, carrying `append` and `lastChunk` markers

Two invariants worth asserting in client code:

1. **`TaskArtifactUpdateEvent.append` is a splice instruction, not a hint.** When `append` is true the
   payload extends the named artifact; when false it replaces. Ignoring it corrupts multi-chunk output.
2. **A stream can end without a `final` status event** if the transport drops. A stream that closes
   without a terminal state is an incomplete read, not a completed task — re-attach with
   `SubscribeToTask` and re-read the state.

## Context versus task

`contextId` groups tasks into one logical conversation; `taskId` identifies one unit of work. A
follow-up that logically continues a finished task is a **new task with the same `contextId`**, not a
message to the terminal task. Sending to a terminal `taskId` is what produces the
`TaskNotFoundError`-after-success confusion.

## Artifacts

`Task.artifacts` holds output; `Task.history` holds the interaction record. Artifacts carry `Part`
values — a `oneof` over `text`, raw `bytes` (base64 in JSON), or a `url` pointing at file content.

A `url` part is a **fetch instruction from a remote agent**. Resolving it reaches out to a host the
remote party chose. Treat it with the same suspicion as any other untrusted redirect: surface the URL,
do not silently fetch it.
