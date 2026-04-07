---
name: together-core-workflow-b
description: |
  Together AI core workflow b for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together core workflow b".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI — Fine-Tuning & Model Management

## Overview

Create fine-tuning jobs, monitor training runs, and deploy custom models on Together AI's
infrastructure. Use this workflow when you need to customize an open-source model on your
own data, track training metrics, manage model versions, or set up dedicated inference
endpoints for production. This is the secondary workflow — for basic inference and chat
completions, see `together-core-workflow-a`.

## Instructions

### Step 1: Upload Training Data and Create a Fine-Tune Job

```typescript
import Together from 'together-ai';
const client = new Together({ apiKey: process.env.TOGETHER_API_KEY });

const file = await client.files.upload({
  file: fs.createReadStream('training.jsonl'),
  purpose: 'fine-tune',
});

const job = await client.fineTuning.create({
  training_file: file.id,
  model: 'meta-llama/Llama-3.3-70B-Instruct-Turbo',
  n_epochs: 3,
  learning_rate: 1e-5,
  batch_size: 4,
  suffix: 'support-agent-v2',
});
console.log(`Fine-tune job ${job.id} — status: ${job.status}`);
```

### Step 2: Monitor Training Progress

```typescript
let status = await client.fineTuning.retrieve(job.id);
while (!['completed', 'failed', 'cancelled'].includes(status.status)) {
  console.log(`Status: ${status.status} — ${status.training_steps_completed}/${status.total_steps} steps`);
  if (status.metrics) console.log(`  Loss: ${status.metrics.training_loss.toFixed(4)}`);
  await new Promise(r => setTimeout(r, 30_000));
  status = await client.fineTuning.retrieve(job.id);
}
console.log(`Final model: ${status.fine_tuned_model}`);
```

### Step 3: List and Manage Model Versions

```typescript
const models = await client.models.list({ owned_by: 'me' });
models.data.forEach(m =>
  console.log(`${m.id} — created ${m.created_at}, type: ${m.type}`)
);

// Delete an old model version
await client.models.delete('my-org/support-agent-v1');
console.log('Deleted old model version');
```

### Step 4: Deploy to a Dedicated Endpoint

```typescript
const endpoint = await client.endpoints.create({
  model: status.fine_tuned_model,
  instance_type: 'gpu-a100-80gb',
  min_replicas: 1,
  max_replicas: 3,
  autoscale_target_utilization: 0.7,
});
console.log(`Endpoint ${endpoint.id} — URL: ${endpoint.url}`);
console.log(`Status: ${endpoint.status}, replicas: ${endpoint.current_replicas}`);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API key | Regenerate at api.together.xyz/settings |
| `400 Invalid JSONL` | Malformed training file | Each line must be valid JSON with `messages` array |
| `422 Model not fine-tunable` | Model does not support fine-tuning | Check supported models at docs.together.ai |
| `429 Rate limited` | Too many requests per minute | Implement exponential backoff with 1s base |
| Training job failed | Data quality or OOM error | Reduce `batch_size` or check file format |

## Output

A successful workflow uploads training data, monitors a fine-tuning job to completion,
and deploys the custom model to an autoscaling dedicated endpoint for production.

## Resources

- [Together AI Docs](https://docs.together.ai/)
- [Fine-Tuning Guide](https://docs.together.ai/docs/fine-tuning-quickstart)
- [API Reference](https://docs.together.ai/reference/chat-completions-1)

## Next Steps

See `together-sdk-patterns` for client initialization and batch inference helpers.
