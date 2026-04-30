---
name: together-webhooks-events
description: 'Together AI webhooks events for inference, fine-tuning, and model deployment.

  Use when working with Together AI''s OpenAI-compatible API.

  Trigger: "together webhooks events".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- ai
- inference
- together
compatibility: Designed for Claude Code
---
# Together AI Webhooks & Events

## Overview
Together AI delivers webhook callbacks for asynchronous operations including fine-tuning jobs, batch inference, and model lifecycle events. Subscribe to events for fine-tune completion, job failures, model deprecation notices, and batch processing status to build automated ML pipelines without polling the jobs API.

## Webhook Registration
```typescript
const response = await fetch("https://api.together.xyz/v1/webhooks", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.TOGETHER_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://yourapp.com/webhooks/together",
    events: ["fine_tune.completed", "fine_tune.failed", "model.deprecated", "batch.done"],
    secret: process.env.TOGETHER_WEBHOOK_SECRET,
  }),
});
```

## Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyTogetherSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-together-signature"] as string;
  const expected = crypto.createHmac("sha256", process.env.TOGETHER_WEBHOOK_SECRET!)
    .update(req.body).digest("hex");
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(401).json({ error: "Invalid signature" });
  }
  next();
}
```

## Event Handler
```typescript
import express from "express";
const app = express();

app.post("/webhooks/together", express.raw({ type: "application/json" }), verifyTogetherSignature, (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

  switch (event.type) {
    case "fine_tune.completed":
      deployModel(event.data.fine_tune_id, event.data.model_name); break;
    case "fine_tune.failed":
      alertTeam(event.data.fine_tune_id, event.data.error_message); break;
    case "model.deprecated":
      migratePipelines(event.data.model_id, event.data.replacement_model); break;
    case "batch.done":
      collectResults(event.data.batch_id, event.data.output_url); break;
  }
});
```

## Event Types
| Event | Payload Fields | Use Case |
|-------|---------------|----------|
| `fine_tune.completed` | `fine_tune_id`, `model_name`, `eval_loss` | Auto-deploy fine-tuned model |
| `fine_tune.failed` | `fine_tune_id`, `error_message`, `step` | Alert team and retry with adjusted params |
| `model.deprecated` | `model_id`, `replacement_model`, `sunset_date` | Migrate inference pipelines proactively |
| `batch.done` | `batch_id`, `output_url`, `total_tokens` | Download batch results and update billing |
| `fine_tune.checkpoint` | `fine_tune_id`, `step`, `loss` | Monitor training progress in real time |

## Retry & Idempotency
```typescript
const processed = new Set<string>();

async function handleIdempotent(event: { id: string; type: string; data: any }) {
  if (processed.has(event.id)) return;
  await routeEvent(event);
  processed.add(event.id);
  if (processed.size > 10_000) {
    const entries = Array.from(processed);
    entries.slice(0, entries.length - 10_000).forEach((id) => processed.delete(id));
  }
}
```

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Rotate key at api.together.xyz |
| Fine-tune stuck | Training data format issues | Validate JSONL before submission |
| Batch timeout | Large batch exceeds time limit | Split into smaller batches |
| Model not found | Deprecated without migration | Check `model.deprecated` events proactively |

## Resources
- [Together AI Docs](https://docs.together.ai/)
- [Fine-tuning Guide](https://docs.together.ai/docs/fine-tuning)

## Next Steps
See `together-security-basics`.
