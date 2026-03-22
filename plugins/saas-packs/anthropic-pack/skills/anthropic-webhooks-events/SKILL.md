---
name: anthropic-webhooks-events
description: |
  Use Anthropic Message Batches for async bulk processing and event handling.
  Trigger with "anthropic batches", "claude batch api", "anthropic async",
  "bulk claude processing", "anthropic webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, batches, async]
---

# Anthropic Message Batches & Async Processing

## Overview
Anthropic doesn't have traditional webhooks. Instead, use **Message Batches** for async bulk processing — up to 10,000 requests per batch at 50% off, with a 24-hour processing SLA.

## Prerequisites
- Completed `anthropic-webhooks-install-auth` setup
- Valid API credentials configured

## Instructions

### Step 1: Create a Batch
```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic();

const batch = await client.messages.batches.create({
  requests: documents.map((doc, i) => ({
    custom_id: `doc-${i}`,
    params: {
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1024,
      messages: [{ role: 'user', content: `Summarize: ${doc.text}` }],
    },
  })),
});

console.log(`Batch ${batch.id} created — ${batch.request_counts.processing} processing`);
```

### Step 2: Poll for Completion
```typescript
async function waitForBatch(batchId: string): Promise<Anthropic.Messages.MessageBatch> {
  while (true) {
    const batch = await client.messages.batches.retrieve(batchId);

    if (batch.processing_status === 'ended') {
      console.log(`Batch complete:
        Succeeded: ${batch.request_counts.succeeded}
        Errored: ${batch.request_counts.errored}
        Expired: ${batch.request_counts.expired}`);
      return batch;
    }

    console.log(`Processing... ${batch.request_counts.processing} remaining`);
    await new Promise(r => setTimeout(r, 30_000)); // Check every 30s
  }
}
```

### Step 3: Retrieve Results
```typescript
const results = await client.messages.batches.results(batch.id);

for await (const result of results) {
  if (result.result.type === 'succeeded') {
    const text = result.result.message.content[0].text;
    console.log(`${result.custom_id}: ${text.substring(0, 100)}...`);
  } else {
    console.error(`${result.custom_id}: ${result.result.type} — ${result.result.error?.message}`);
  }
}
```

## Python Example
```python
import anthropic
import time

client = anthropic.Anthropic()

batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"doc-{i}",
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": f"Summarize: {doc}"}],
            },
        }
        for i, doc in enumerate(documents)
    ]
)

# Poll
while batch.processing_status != "ended":
    time.sleep(30)
    batch = client.messages.batches.retrieve(batch.id)

# Get results
for result in client.messages.batches.results(batch.id):
    if result.result.type == "succeeded":
        print(result.custom_id, result.result.message.content[0].text[:100])
```

## Batch Limits
| Limit | Value |
|-------|-------|
| Max requests per batch | 10,000 |
| Max concurrent batches | 100 |
| Processing SLA | 24 hours |
| Pricing | 50% of standard per-token pricing |
| Result availability | 29 days after creation |

## Output
- Successful operation confirmed
- Results logged to console

## Error Handling
| Result Type | Meaning | Action |
|-------------|---------|--------|
| `succeeded` | Normal response | Process `result.message` |
| `errored` | API error | Check `result.error` — retry failed items in new batch |
| `expired` | Not processed within 24h | Resubmit in new batch |
| `canceled` | Batch was canceled | Resubmit if needed |

## Examples
See code blocks above for complete examples.

## Resources
- [Message Batches API](https://docs.anthropic.com/en/api/creating-message-batches)
- [Batch Pricing](https://www.anthropic.com/pricing) — 50% off standard

## Next Steps
See `anthropic-ci-integration` for using batches in CI pipelines.
