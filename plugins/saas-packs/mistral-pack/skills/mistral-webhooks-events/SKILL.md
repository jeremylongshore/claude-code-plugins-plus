---
name: mistral-webhooks-events
description: |
  Implement Mistral AI async patterns, batch API, agents, and event-driven workflows.
  Use when building async workflows, using the Agents API, batch inference,
  or handling long-running Mistral AI operations.
  Trigger with phrases like "mistral events", "mistral async", "mistral agents",
  "mistral batch", "mistral queue", "mistral background jobs".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, webhooks, workflow]

---
# Mistral AI Events, Agents & Async Patterns

## Overview
Async and event-driven patterns for Mistral AI: the Agents API for stateful multi-turn workflows, Batch API for cost-effective bulk inference (50% cheaper), SSE streaming endpoints, background job queues, and Python async processing. Mistral does not have native webhooks — this skill covers the patterns that replace them.

## Prerequisites
- `@mistralai/mistralai` SDK installed
- `MISTRAL_API_KEY` configured
- For agents: La Plateforme access to create agents
- For batch: JSONL file preparation

## Instructions

### Step 1: Mistral Agents API

Create stateful agents with instructions, tools, and model configuration:

```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

// Create an agent on La Plateforme
const agent = await client.agents.create({
  name: 'Code Reviewer',
  model: 'mistral-large-latest',
  instructions: `You are an expert code reviewer. Analyze code for:
    - Security vulnerabilities
    - Performance issues
    - Best practice violations
    Provide actionable feedback with severity ratings.`,
  description: 'Reviews code for security, performance, and best practices',
  tools: [
    {
      type: 'function',
      function: {
        name: 'search_codebase',
        description: 'Search the codebase for patterns',
        parameters: {
          type: 'object',
          properties: { query: { type: 'string' } },
          required: ['query'],
        },
      },
    },
  ],
});

// Chat with the agent (stateful conversation)
const response = await client.agents.complete({
  agentId: agent.id,
  messages: [
    { role: 'user', content: 'Review this function:\n```\nfunction auth(pwd) { return pwd === "admin123"; }\n```' },
  ],
});

console.log(response.choices?.[0]?.message?.content);
```

### Step 2: Batch API for Bulk Inference

50% cost reduction for non-time-sensitive workloads:

```typescript
// 1. Prepare JSONL input file
const batchRequests = [
  {
    custom_id: 'req-1',
    body: {
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Summarize: ...' }],
      max_tokens: 200,
    },
  },
  {
    custom_id: 'req-2',
    body: {
      model: 'mistral-small-latest',
      messages: [{ role: 'user', content: 'Classify: ...' }],
      max_tokens: 50,
    },
  },
];

// Write to JSONL
import { writeFileSync } from 'fs';
writeFileSync('batch-input.jsonl',
  batchRequests.map(r => JSON.stringify(r)).join('\n')
);

// 2. Upload file and create batch job
const file = await client.files.upload({
  file: { fileName: 'batch-input.jsonl', content: readFileSync('batch-input.jsonl') },
  purpose: 'batch',
});

const batch = await client.batch.jobs.create({
  inputFiles: [file.id],
  endpoint: '/v1/chat/completions',
  model: 'mistral-small-latest',
});

console.log(`Batch job: ${batch.id}, status: ${batch.status}`);

// 3. Poll for completion
async function waitForBatch(jobId: string): Promise<any> {
  while (true) {
    const status = await client.batch.jobs.get({ jobId });
    console.log(`Status: ${status.status}`);

    if (status.status === 'SUCCESS') return status;
    if (status.status === 'FAILED') throw new Error(`Batch failed: ${status.errors}`);

    await new Promise(r => setTimeout(r, 30_000)); // Check every 30s
  }
}
```

### Step 3: Event-Driven Streaming Architecture

```typescript
import { EventEmitter } from 'events';

interface MistralEvents {
  'chat:start': { requestId: string; model: string };
  'chat:chunk': { requestId: string; content: string; index: number };
  'chat:complete': { requestId: string; content: string; usage: any };
  'chat:error': { requestId: string; error: Error };
}

class MistralEventBus extends EventEmitter {
  private client: Mistral;

  constructor() {
    super();
    this.client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });
  }

  async streamChat(requestId: string, messages: any[], model = 'mistral-small-latest') {
    this.emit('chat:start', { requestId, model });

    try {
      const stream = await this.client.chat.stream({ model, messages });
      let full = '';
      let index = 0;

      for await (const event of stream) {
        const content = event.data?.choices?.[0]?.delta?.content;
        if (content) {
          full += content;
          this.emit('chat:chunk', { requestId, content, index: index++ });
        }
      }

      this.emit('chat:complete', { requestId, content: full, usage: { estimatedTokens: Math.ceil(full.length / 4) } });
      return full;
    } catch (error) {
      this.emit('chat:error', { requestId, error: error as Error });
      throw error;
    }
  }
}

// Wire up listeners
const bus = new MistralEventBus();
bus.on('chat:start', ({ requestId, model }) => console.log(`[${requestId}] Starting ${model}`));
bus.on('chat:chunk', ({ content }) => process.stdout.write(content));
bus.on('chat:complete', ({ requestId, usage }) => console.log(`\n[${requestId}] Done`));
bus.on('chat:error', ({ requestId, error }) => console.error(`[${requestId}] Error: ${error.message}`));
```

### Step 4: Background Job Queue with BullMQ

```typescript
import { Queue, Worker } from 'bullmq';
import { Mistral } from '@mistralai/mistralai';

const connection = { host: 'localhost', port: 6379 };
const chatQueue = new Queue('mistral-chat', { connection });

// Worker processes jobs
const worker = new Worker('mistral-chat', async (job) => {
  const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });

  const response = await client.chat.complete({
    model: job.data.model ?? 'mistral-small-latest',
    messages: job.data.messages,
  });

  const result = {
    content: response.choices?.[0]?.message?.content,
    usage: response.usage,
  };

  // Optional: call webhook on completion
  if (job.data.callbackUrl) {
    await fetch(job.data.callbackUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jobId: job.id, ...result }),
    });
  }

  return result;
}, {
  connection,
  concurrency: 5,
  limiter: { max: 10, duration: 1000 }, // 10 jobs/sec max
});

// Enqueue from API
async function enqueueChat(messages: any[], callbackUrl?: string) {
  const job = await chatQueue.add('chat', {
    messages,
    model: 'mistral-small-latest',
    callbackUrl,
  }, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 2000 },
  });

  return { jobId: job.id, status: 'queued' };
}
```

### Step 5: Python Async Batch Processing

```python
import asyncio
import os
from mistralai import Mistral

async def process_batch(prompts: list[str], concurrency: int = 5):
    """Process prompts concurrently with rate limiting."""
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    semaphore = asyncio.Semaphore(concurrency)
    results = []

    async def process_one(prompt: str, idx: int):
        async with semaphore:
            response = await client.chat.complete_async(
                model="mistral-small-latest",
                messages=[{"role": "user", "content": prompt}],
            )
            return {"index": idx, "content": response.choices[0].message.content}

    tasks = [process_one(p, i) for i, p in enumerate(prompts)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results

# Usage
results = asyncio.run(process_batch([
    "Summarize quantum computing",
    "Explain neural networks",
    "What is reinforcement learning",
]))
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Batch job stuck | Processing queue full | Check status, resubmit if FAILED |
| Agent context lost | Session expired | Store conversation in your DB |
| Worker crash | Unhandled exception | BullMQ auto-retries with backoff |
| SSE disconnected | Client/network timeout | Implement reconnection logic |

## Resources
- [Agents API](https://docs.mistral.ai/agents/agents/)
- [Batch Inference](https://docs.mistral.ai/capabilities/batch/)
- [Streaming](https://docs.mistral.ai/capabilities/completion/)
- [BullMQ Docs](https://docs.bullmq.io/)

## Output
- Agents API integration for stateful workflows
- Batch API for 50%-cheaper bulk processing
- Event-driven streaming architecture
- Background job queue with retry/callback
- Python async concurrent processing
