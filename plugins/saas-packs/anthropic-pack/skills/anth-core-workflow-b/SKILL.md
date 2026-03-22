---
name: anth-core-workflow-b
description: |
  Build Claude streaming and Message Batches API workflows.
  Use when implementing real-time streaming responses, SSE event handling,
  or processing bulk requests with the 50% cheaper Batches API.
  Trigger with phrases like "claude streaming", "anthropic batch",
  "message batches api", "SSE events anthropic", "stream claude response".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Core Workflow B — Streaming & Batches

## Overview

Two complementary patterns: real-time streaming for interactive UIs (SSE events via `POST /v1/messages` with `stream: true`) and the Message Batches API (`POST /v1/messages/batches`) for processing up to 100,000 requests asynchronously at 50% cost reduction.

## Prerequisites

- Completed `anth-install-auth` setup
- Familiarity with `anth-core-workflow-a` (Messages API basics)
- For batches: understanding of async/polling patterns

## Instructions

### Streaming — Python SDK

```python
import anthropic

client = anthropic.Anthropic()

# Method 1: High-level streaming (recommended)
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Write a short story about a robot."}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

    # After stream completes, access full message
    final_message = stream.get_final_message()
    print(f"\nUsage: {final_message.usage.input_tokens}+{final_message.usage.output_tokens}")

# Method 2: Event-level streaming (for custom event handling)
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": "Explain REST APIs."}]
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="")
        elif event.type == "message_stop":
            print("\n[Stream complete]")
```

### Streaming — TypeScript SDK

```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

// High-level streaming
const stream = client.messages.stream({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 2048,
  messages: [{ role: 'user', content: 'Write a haiku about code.' }],
});

stream.on('text', (text) => process.stdout.write(text));
stream.on('finalMessage', (msg) => {
  console.log(`\nTokens: ${msg.usage.input_tokens}+${msg.usage.output_tokens}`);
});

await stream.finalMessage();
```

### Streaming with Tool Use

```python
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,  # Same tools array from core-workflow-a
    messages=[{"role": "user", "content": "What's the weather?"}]
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "tool_use":
                print(f"Tool call: {event.content_block.name}")
        elif event.type == "content_block_delta":
            if event.delta.type == "input_json_delta":
                print(event.delta.partial_json, end="")  # Tool input arrives incrementally
```

### Message Batches API — Bulk Processing

```python
# Create a batch of up to 100,000 requests (50% cost savings)
batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "req-001",
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Summarize: ...article1..."}]
            }
        },
        {
            "custom_id": "req-002",
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": "Summarize: ...article2..."}]
            }
        },
        # ... up to 100,000 requests
    ]
)

print(f"Batch ID: {batch.id}")          # msgbatch_01HBMt...
print(f"Status: {batch.processing_status}")  # in_progress
print(f"Counts: {batch.request_counts}")     # {processing: 2, succeeded: 0, ...}
```

### Poll for Batch Completion

```python
import time

while True:
    batch_status = client.messages.batches.retrieve(batch.id)
    if batch_status.processing_status == "ended":
        break
    print(f"Processing... {batch_status.request_counts}")
    time.sleep(30)

# Stream results (returns JSONL)
for result in client.messages.batches.results(batch.id):
    if result.result.type == "succeeded":
        text = result.result.message.content[0].text
        print(f"[{result.custom_id}]: {text[:100]}...")
    elif result.result.type == "errored":
        print(f"[{result.custom_id}] ERROR: {result.result.error}")
```

## SSE Event Types Reference

| Event | Description | Key Fields |
|-------|-------------|------------|
| `message_start` | Stream begins | `message.id`, `message.model`, `message.usage` |
| `content_block_start` | New content block | `content_block.type` (text/tool_use) |
| `content_block_delta` | Incremental content | `delta.text` or `delta.partial_json` |
| `content_block_stop` | Block complete | `index` |
| `message_delta` | Message-level update | `delta.stop_reason`, `usage.output_tokens` |
| `message_stop` | Stream complete | (empty) |
| `ping` | Keepalive | (empty) |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Stream disconnects mid-response | Network timeout | Implement reconnection with partial content |
| Batch `expired` status | Not processed within 24h | Resubmit batch |
| `errored` results in batch | Individual request invalid | Check `result.error` for each failed request |
| 429 on batch creation | Too many concurrent batches | Wait; limit is ~100 concurrent batches |

## Resources

- [Streaming Messages](https://docs.anthropic.com/en/api/messages-streaming)
- [Message Batches API](https://docs.anthropic.com/en/api/creating-message-batches)
- [Batch Results](https://docs.anthropic.com/en/api/retrieving-message-batch-results)

## Next Steps

For common errors, see `anth-common-errors`.
