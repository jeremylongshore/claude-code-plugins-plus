---
name: anth-reference-architecture
description: |
  Implement Claude API reference architectures for common use cases.
  Use when designing a Claude-powered application, choosing between
  direct API vs queue-based, or planning a multi-model architecture.
  Trigger with phrases like "anthropic architecture", "claude system design",
  "anthropic reference architecture", "design claude integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, anthropic]
compatible-with: claude-code
---

# Anthropic Reference Architecture

## Overview

Three validated architecture patterns for Claude API integrations: synchronous API gateway, async queue-based processing, and multi-model routing.

## Architecture 1: Sync API Gateway (Simple)

```
User → API Gateway → Claude Service → Messages API
                                     ↓
                                   Response → User
```

```python
# Best for: chatbots, interactive tools, low-volume (<100 RPM)
from fastapi import FastAPI
import anthropic

app = FastAPI()
client = anthropic.Anthropic(max_retries=3, timeout=60.0)

@app.post("/chat")
async def chat(prompt: str):
    msg = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    return {"text": msg.content[0].text, "tokens": msg.usage.output_tokens}
```

## Architecture 2: Async Queue-Based (Scalable)

```
User → API → Queue (Redis/SQS) → Worker Pool → Messages API
  ↑                                                ↓
  └──────────── Status/Result ←── Result Store ←───┘
```

```python
# Best for: batch processing, high-volume, background tasks
from redis import Redis
from rq import Queue
import anthropic

redis = Redis()
task_queue = Queue("claude-tasks", connection=redis)
result_store = Redis(db=1)

def process_task(task_id: str, prompt: str, model: str):
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )
    result_store.setex(f"result:{task_id}", 3600, msg.content[0].text)

# Enqueue
import uuid
task_id = str(uuid.uuid4())
task_queue.enqueue(process_task, task_id, prompt, "claude-sonnet-4-20250514")
```

## Architecture 3: Multi-Model Router

```
User → Router → Haiku    (classify/extract)
              → Sonnet   (general/code)
              → Opus     (research/complex)
              → Batches  (bulk/offline)
```

```python
class ModelRouter:
    def __init__(self):
        self.client = anthropic.Anthropic()
        self.classifier = anthropic.Anthropic()  # Can be same client

    def route_and_execute(self, prompt: str, context: dict) -> str:
        # Step 1: Classify with Haiku (cheap, fast)
        classification = self.classifier.messages.create(
            model="claude-haiku-4-20250514",
            max_tokens=32,
            messages=[{
                "role": "user",
                "content": f"Classify this request as: simple|moderate|complex|bulk\n\n{prompt[:200]}"
            }]
        )
        complexity = classification.content[0].text.strip().lower()

        # Step 2: Route to appropriate model
        model_map = {
            "simple": "claude-haiku-4-20250514",
            "moderate": "claude-sonnet-4-20250514",
            "complex": "claude-opus-4-20250514",
        }
        model = model_map.get(complexity, "claude-sonnet-4-20250514")

        # Step 3: Execute with selected model
        msg = self.client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
```

## Project Layout

```
my-claude-app/
├── src/
│   ├── main.py              # FastAPI app
│   ├── claude/
│   │   ├── client.py         # Singleton + config
│   │   ├── router.py         # Model routing logic
│   │   ├── tools.py          # Tool definitions
│   │   └── prompts/          # System prompts as files
│   ├── workers/
│   │   └── claude_worker.py  # Queue consumer
│   └── middleware/
│       ├── rate_limiter.py   # App-level rate limiting
│       └── cost_tracker.py   # Spend monitoring
├── tests/
│   ├── unit/                 # Mocked tests
│   └── integration/          # Live API tests
└── config/
    ├── .env.development
    ├── .env.staging
    └── .env.production
```

## Error Handling

| Architecture | Failure Mode | Mitigation |
|-------------|-------------|------------|
| Sync Gateway | 429/5xx blocks user | Circuit breaker + fallback response |
| Queue-Based | Worker crashes | Dead-letter queue + retry policy |
| Multi-Model | Router misclassifies | Default to Sonnet (safest middle) |

## Resources

- [API Overview](https://docs.anthropic.com/en/api/getting-started)
- [Tool Use](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

## Next Steps

For multi-environment setup, see `anth-multi-env-setup`.
