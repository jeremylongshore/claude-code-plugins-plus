# A2A service surface — 11 methods, three bindings

Source: the `A2AService` definition in the A2A specification (`specification/a2a.proto`) and the
method-mapping table in the prose spec. Nothing here is invented; this file is a navigational copy.

## Method mapping

| Functionality | gRPC / JSON-RPC method | REST endpoint |
| --- | --- | --- |
| Send message | `SendMessage` | `POST /message:send` |
| Send streaming message | `SendStreamingMessage` | `POST /message:stream` |
| Get task | `GetTask` | `GET /tasks/{id}` |
| List tasks | `ListTasks` | `GET /tasks` |
| Cancel task | `CancelTask` | `POST /tasks/{id}:cancel` |
| Subscribe to task | `SubscribeToTask` | `POST /tasks/{id}:subscribe` |
| Create push notification config | `CreateTaskPushNotificationConfig` | `POST /tasks/{id}/pushNotificationConfigs` |
| Get push notification config | `GetTaskPushNotificationConfig` | `GET /tasks/{id}/pushNotificationConfigs/{configId}` |
| List push notification configs | `ListTaskPushNotificationConfigs` | `GET /tasks/{id}/pushNotificationConfigs` |
| Delete push notification config | `DeleteTaskPushNotificationConfig` | `DELETE /tasks/{id}/pushNotificationConfigs/{configId}` |
| Get extended agent card | `GetExtendedAgentCard` | `GET /extendedAgentCard` |

Two of the eleven are server-streaming: `SendStreamingMessage` and `SubscribeToTask` both return a
stream of `StreamResponse`. `DeleteTaskPushNotificationConfig` returns `google.protobuf.Empty`.

## Signature notes that bite

- `SendMessage` and `SendStreamingMessage` share one request type, `SendMessageRequest`. The choice of
  streaming is the method, not a flag in the payload.
- `GetTask` and `CancelTask` both return a bare `Task`, not a wrapper.
- `SendMessageResponse` is a `oneof` — it carries **either** a `Task` **or** a `Message`. An agent that
  answers inline without creating a task is spec-legal. Branch on which arm is populated.
- `CreateTaskPushNotificationConfig` takes and returns `TaskPushNotificationConfig` directly.

## Error codes

Standard JSON-RPC codes apply for transport-level faults:

| Code | Name | Meaning |
| --- | --- | --- |
| `-32700` | `JSONParseError` | Invalid JSON payload |
| `-32600` | `InvalidRequestError` | Not a valid Request object |
| `-32601` | `MethodNotFoundError` | Method does not exist or is unavailable |
| `-32602` | `InvalidParamsError` | Method parameters are invalid |
| `-32603` | `InternalError` | Internal server error |

A2A-specific errors occupy `-32001` to `-32099`. The canonical mapping:

| A2A error | JSON-RPC | gRPC status | HTTP |
| --- | --- | --- | --- |
| `TaskNotFoundError` | `-32001` | `NOT_FOUND` | `404` |
| `TaskNotCancelableError` | `-32002` | `FAILED_PRECONDITION` | `400` |
| `PushNotificationNotSupportedError` | `-32003` | `FAILED_PRECONDITION` | `400` |
| `UnsupportedOperationError` | `-32004` | `FAILED_PRECONDITION` | `400` |
| `ContentTypeNotSupportedError` | `-32005` | `INVALID_ARGUMENT` | `400` |
| `InvalidAgentResponseError` | `-32006` | `INTERNAL` | `500` |
| `ExtendedAgentCardNotConfiguredError` | `-32007` | `FAILED_PRECONDITION` | `400` |
| `ExtensionSupportRequiredError` | `-32008` | `FAILED_PRECONDITION` | `400` |
| `VersionNotSupportedError` | `-32009` | `FAILED_PRECONDITION` | `400` |

### Retry policy by class

- `NOT_FOUND` (`-32001`) — the handle is gone. Re-send the work; do not re-poll.
- `FAILED_PRECONDITION` (`-32002/3/4/7/8/9`) — the agent structurally cannot do this. Retrying the same
  request loops forever. Change the request, or route elsewhere.
- `INVALID_ARGUMENT` (`-32005`) — negotiate content type against `defaultInputModes` and the per-skill
  `inputModes` override, then retry once.
- `INTERNAL` (`-32006`) — the only class where blind retry with backoff is defensible.

## Push notification configs

Push notifications invert the direction: the agent calls a URL the client registers. The config carries
`url`, an optional per-task `token`, and `AuthenticationInfo` with an IANA HTTP auth `scheme` plus
`credentials`.

Treat a push-notification callback as **untrusted inbound traffic**. The `token` proves the callback
belongs to a task this client registered; it proves nothing about the payload's contents.
