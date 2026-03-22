---
name: anth-webhooks-events
description: |
  Implement event-driven patterns with Claude API: streaming SSE events,
  Message Batches callbacks, and async processing architectures.
  Use when building real-time Claude integrations or processing batch results.
  Trigger with phrases like "anthropic events", "claude streaming events",
  "anthropic async processing", "claude batch callbacks".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Events & Async Processing

## Overview

The Claude API does not use traditional webhooks. Instead it provides two event-driven patterns: Server-Sent Events (SSE) for real-time streaming and the Message Batches API for async bulk processing. This skill covers both.

## SSE Streaming Events

```python
import anthropic

client = anthropic.Anthropic()

# Process each SSE event type
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Explain microservices."}]
) as stream:
    for event in stream:
        match event.type:
            case "message_start":
                print(f"Started: {event.message.id}")
            case "content_block_start":
                if event.content_block.type == "tool_use":
                    print(f"Tool call: {event.content_block.name}")
            case "content_block_delta":
                if event.delta.type == "text_delta":
                    print(event.delta.text, end="", flush=True)
                elif event.delta.type == "input_json_delta":
                    print(event.delta.partial_json, end="")
            case "message_delta":
                print(f"\nStop: {event.delta.stop_reason}")
                print(f"Output tokens: {event.usage.output_tokens}")
            case "message_stop":
                print("[Complete]")
```

## SSE Event Reference

| Event | When | Key Data |
|-------|------|----------|
| `message_start` | Stream begins | `message.id`, `message.model`, `message.usage.input_tokens` |
| `content_block_start` | New block begins | `content_block.type` (text or tool_use), `index` |
| `content_block_delta` | Incremental content | `delta.text` or `delta.partial_json` |
| `content_block_stop` | Block finishes | `index` |
| `message_delta` | Message-level update | `delta.stop_reason`, `usage.output_tokens` |
| `message_stop` | Stream complete | (empty) |
| `ping` | Keepalive | (empty) |

## Async Batch Processing

```python
# Submit batch (up to 100K requests, 50% cheaper)
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"doc-{i}",
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": f"Summarize: {doc}"}]
            }
        }
        for i, doc in enumerate(documents)
    ]
)

# Poll for completion
import time
while True:
    status = client.messages.batches.retrieve(batch.id)
    if status.processing_status == "ended":
        break
    counts = status.request_counts
    print(f"Processing: {counts.processing} | Done: {counts.succeeded} | Errors: {counts.errored}")
    time.sleep(30)

# Stream results
for result in client.messages.batches.results(batch.id):
    if result.result.type == "succeeded":
        print(f"[{result.custom_id}]: {result.result.message.content[0].text[:100]}")
    else:
        print(f"[{result.custom_id}] ERROR: {result.result.error}")
```

## Event-Driven Architecture Pattern

```python
# Use queues to decouple Claude requests from user-facing endpoints
from redis import Redis
from rq import Queue

redis = Redis()
queue = Queue(connection=redis)

def process_with_claude(prompt: str, callback_url: str):
    """Background job for async Claude processing."""
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    # Notify your system via internal callback
    import requests
    requests.post(callback_url, json={
        "text": msg.content[0].text,
        "usage": {"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}
    })

# Enqueue from your API handler
job = queue.enqueue(process_with_claude, prompt="...", callback_url="https://internal/callback")
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Stream disconnects | Network timeout | Reconnect and re-request (responses are not resumable) |
| Batch `expired` | Not processed in 24h | Resubmit the batch |
| `errored` results | Individual request was invalid | Check `result.error.message` per request |

## Resources

- [Streaming API](https://docs.anthropic.com/en/api/messages-streaming)
- [Message Batches API](https://docs.anthropic.com/en/api/creating-message-batches)

## Next Steps

For performance optimization, see `anth-performance-tuning`.
