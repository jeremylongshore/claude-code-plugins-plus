# Groq Event Patterns — Worked Examples

End-to-end examples that exercise the endpoints and functions defined in `SKILL.md`
and `references/implementation.md`. Each assumes the server is running locally and
`GROQ_API_KEY` is set.

## Example 1: Consume the SSE streaming endpoint

Call the `/api/chat/stream` endpoint from Step 1 with `curl` and watch tokens arrive
as they are generated. `-N` disables buffering so events print live.

```bash
curl -N -X POST http://localhost:3000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Explain SSE in one sentence."}]}'
```

Expected event stream (one `data:` line per token, terminated by a `done` event):

```
data: {"content":"Server","type":"token"}
data: {"content":"-Sent","type":"token"}
data: {"content":" Events","type":"token"}
data: {"type":"done"}
```

## Example 2: Submit a batch and receive callbacks

Enqueue three prompts with `submitBatch` (Step 2). Each completed item POSTs a
`groq.batch.item_completed` event to the callback URL.

```typescript
const batchId = await submitBatch(
  ["Summarize doc A", "Summarize doc B", "Summarize doc C"],
  "https://myapp.example.com/hooks/groq",
  "llama-3.1-8b-instant"
);
console.log(`Batch ${batchId} enqueued — 3 items`);
```

Each callback body:

```json
{
  "event": "groq.batch.item_completed",
  "data": {
    "batchId": "3f9c…",
    "index": 0,
    "total": 3,
    "content": "…",
    "model": "llama-3.1-8b-instant",
    "usage": { "prompt_tokens": 12, "completion_tokens": 48 }
  }
}
```

## Example 3: Classify an inbound webhook

Send a raw event to the `/webhook` receiver (Step 3). The endpoint acknowledges with
`202` immediately, then classifies the event with the 8B model in the background.

```bash
curl -X POST http://localhost:3000/webhook \
  -H "Content-Type: application/json" \
  -d '{"source":"stripe","type":"charge.failed","amount":4999}'
```

The receiver returns `{"received": true}` right away; the async classification
produces, for example, `{"type":"payment","priority":"high","summary":"Charge
failed for $49.99","action":"notify_billing"}`, which triggers the Slack alert.
