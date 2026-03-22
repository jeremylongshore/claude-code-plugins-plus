---
name: anth-architecture-variants
description: |
  Choose and implement Claude API architecture patterns for different scales:
  serverless, microservice, event-driven, and edge deployment.
  Trigger with phrases like "anthropic architecture", "claude serverless",
  "claude microservice design", "edge claude deployment".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Architecture Variants

## Overview

Four validated architecture patterns for Claude API integrations at different scales and use cases.

## Variant 1: Serverless (AWS Lambda / Cloud Functions)

```python
# Best for: < 100 RPM, event-driven, pay-per-invocation
# lambda_function.py
import anthropic
import json

def handler(event, context):
    client = anthropic.Anthropic()  # Key from Lambda env var

    body = json.loads(event["body"])
    msg = client.messages.create(
        model="claude-haiku-4-20250514",  # Haiku for Lambda speed
        max_tokens=512,
        messages=[{"role": "user", "content": body["prompt"]}]
    )

    return {
        "statusCode": 200,
        "body": json.dumps({
            "text": msg.content[0].text,
            "tokens": msg.usage.input_tokens + msg.usage.output_tokens
        })
    }
```

**Trade-offs:** Cold starts add 1-3s. Lambda timeout (15min) limits long generations. No connection pooling between invocations.

## Variant 2: Streaming Microservice (FastAPI + WebSocket)

```python
# Best for: chatbots, interactive UIs, real-time responses
from fastapi import FastAPI, WebSocket
import anthropic

app = FastAPI()
client = anthropic.Anthropic()

@app.websocket("/chat")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    while True:
        prompt = await websocket.receive_text()
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            for text in stream.text_stream:
                await websocket.send_text(text)
            await websocket.send_text("[DONE]")
```

## Variant 3: Queue-Based Pipeline (Celery / Cloud Tasks)

```python
# Best for: batch processing, async workflows, high volume
from celery import Celery
import anthropic

app = Celery("tasks", broker="redis://localhost")

@app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_document(self, doc_id: str, content: str):
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[{"role": "user", "content": f"Summarize:\n\n{content}"}]
        )
        save_result(doc_id, msg.content[0].text)
    except anthropic.RateLimitError as e:
        self.retry(exc=e, countdown=int(e.response.headers.get("retry-after", 30)))
```

## Variant 4: Multi-Model Orchestrator

```python
# Best for: complex workflows needing different model strengths
class ClaudeOrchestrator:
    def __init__(self):
        self.client = anthropic.Anthropic()

    def classify_then_respond(self, user_input: str) -> str:
        # Step 1: Classify intent with Haiku (fast, cheap)
        classification = self.client.messages.create(
            model="claude-haiku-4-20250514",
            max_tokens=32,
            messages=[{
                "role": "user",
                "content": f"Classify as: question|task|creative|code\nInput: {user_input[:200]}"
            }]
        )
        intent = classification.content[0].text.strip().lower()

        # Step 2: Route to optimal model
        model = {
            "question": "claude-haiku-4-20250514",
            "task": "claude-sonnet-4-20250514",
            "creative": "claude-sonnet-4-20250514",
            "code": "claude-sonnet-4-20250514",
        }.get(intent, "claude-sonnet-4-20250514")

        # Step 3: Generate response
        msg = self.client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": user_input}]
        )
        return msg.content[0].text
```

## Architecture Selection Guide

| Factor | Serverless | Microservice | Queue-Based | Orchestrator |
|--------|-----------|-------------|-------------|-------------|
| Latency | High (cold start) | Low (streaming) | N/A (async) | Medium |
| Volume | Low (<100 RPM) | Medium | High | Medium |
| Cost | Pay-per-use | Fixed infra | Batch savings | Optimized per-task |
| Complexity | Low | Medium | Medium | High |
| Best for | APIs, triggers | Chatbots | ETL, processing | Complex workflows |

## Resources

- [API Getting Started](https://docs.anthropic.com/en/api/getting-started)
- [Streaming](https://docs.anthropic.com/en/api/messages-streaming)
- [Batches](https://docs.anthropic.com/en/api/creating-message-batches)

## Next Steps

For common pitfalls, see `anth-known-pitfalls`.
