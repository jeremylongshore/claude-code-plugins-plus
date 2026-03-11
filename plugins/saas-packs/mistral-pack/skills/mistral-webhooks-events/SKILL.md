---
name: mistral-webhooks-events
description: |
  Implement event handling patterns for Mistral AI integrations.
  Use when building async workflows, implementing queues,
  or handling long-running Mistral AI operations.
  Trigger with phrases like "mistral events", "mistral async",
  "mistral queue", "mistral background jobs", "mistral webhook".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Events & Async Patterns

## Overview
Implement async patterns and event handling for Mistral AI integrations. Note: Mistral AI does not have native webhooks, so this skill covers async patterns and event-driven architectures.

## Prerequisites
- Mistral AI SDK installed
- Queue system (Redis, SQS, etc.) for async processing
- Event emitter or pub/sub for notifications
- Background job processor (BullMQ, etc.)

## Instructions

### Step 1: Event-Driven Chat Architecture

```typescript
import { EventEmitter } from 'events';
import Mistral from '@mistralai/mistralai';

// Custom event types
interface MistralEvents {
  'chat:start': { requestId: string; model: string; timestamp: Date };
  'chat:chunk': { requestId: string; content: string; index: number };
  'chat:complete': { requestId: string; fullResponse: string; usage: any };
  'chat:error': { requestId: string; error: Error };
}

class MistralEventEmitter extends EventEmitter {
  private client: Mistral;

  constructor() {
    super();
    this.client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });
  }

  async chat(requestId: string, messages: any[], model = 'mistral-small-latest') {
    this.emit('chat:start', { requestId, model, timestamp: new Date() });

    try {
      const stream = await this.client.chat.stream({ model, messages });

      let fullResponse = '';
      let index = 0;

      for await (const event of stream) {
        const content = event.data?.choices?.[0]?.delta?.content;
        if (content) {
          fullResponse += content;
          this.emit('chat:chunk', { requestId, content, index: index++ });
        }
      }

      const usage = { totalTokens: fullResponse.length / 4 }; // Estimate
      this.emit('chat:complete', { requestId, fullResponse, usage });

      return fullResponse;
    } catch (error) {
      this.emit('chat:error', { requestId, error: error as Error });
      throw error;
    }
  }
}

// Usage
const mistral = new MistralEventEmitter();

mistral.on('chat:start', ({ requestId, model }) => {
  console.log(`[${requestId}] Starting chat with ${model}`);
});

mistral.on('chat:chunk', ({ requestId, content }) => {
  process.stdout.write(content);
});

mistral.on('chat:complete', ({ requestId, usage }) => {
  console.log(`\n[${requestId}] Complete. Tokens: ${usage.totalTokens}`);
});

mistral.on('chat:error', ({ requestId, error }) => {
  console.error(`[${requestId}] Error:`, error.message);
});

await mistral.chat('req-123', [{ role: 'user', content: 'Hello!' }]);
```

### Step 2: Background Job Processing with BullMQ

```typescript
import { Queue, Worker, Job } from 'bullmq';
import Mistral from '@mistralai/mistralai';
import Redis from 'ioredis';

const connection = new Redis(process.env.REDIS_URL);

// Define job types
interface ChatJob {
  id: string;
  messages: Array<{ role: string; content: string }>;
  model: string;
  callback?: string; // Webhook URL to call on completion
}

// Create queue
const chatQueue = new Queue<ChatJob>('mistral-chat', { connection });

// Create worker
const chatWorker = new Worker<ChatJob>(
  'mistral-chat',
  async (job: Job<ChatJob>) => {
    const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });

    const response = await client.chat.complete({
      model: job.data.model,
      messages: job.data.messages,
    });

    const result = {
      jobId: job.id,
      requestId: job.data.id,
      content: response.choices?.[0]?.message?.content,
      usage: response.usage,
      completedAt: new Date().toISOString(),
    };

    // Call webhook if provided
    if (job.data.callback) {
      await fetch(job.data.callback, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result),
      });
    }

    return result;
  },
  {
    connection,
    concurrency: 5,
    limiter: {
      max: 10,
      duration: 1000, // Max 10 jobs per second  # 1000: 1 second in ms
    },
  }
);

// Event handlers
chatWorker.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed:`, result);
});

chatWorker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err.message);
});

// API endpoint to queue jobs
export async function POST(request: Request) {
  const body = await request.json();

  const job = await chatQueue.add('chat', {
    id: crypto.randomUUID(),
    messages: body.messages,
    model: body.model || 'mistral-small-latest',
    callback: body.callback,
  }, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 1000 },  # 1 second in ms
  });

  return Response.json({
    jobId: job.id,
    status: 'queued',
    statusUrl: `/api/jobs/${job.id}`,
  });
}
```

### Step 3: Webhook Notification System

```typescript
import crypto from 'crypto';

interface WebhookPayload {
  event: string;
  timestamp: string;
  data: any;
}

class WebhookNotifier {
  private secret: string;

  constructor(secret: string) {
    this.secret = secret;
  }

  private sign(payload: string): string {
    return crypto
      .createHmac('sha256', this.secret)
      .update(payload)
      .digest('hex');
  }

  async notify(url: string, event: string, data: any): Promise<boolean> {
    const payload: WebhookPayload = {
      event,
      timestamp: new Date().toISOString(),
      data,
    };

    const body = JSON.stringify(payload);
    const signature = this.sign(body);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Webhook-Signature': signature,
          'X-Webhook-Timestamp': payload.timestamp,
        },
        body,
      });

      return response.ok;
    } catch (error) {
      console.error('Webhook failed:', error);
      return false;
    }
  }
}

// Usage
const notifier = new WebhookNotifier(process.env.WEBHOOK_SECRET!);

// After Mistral completion
await notifier.notify(
  'https://yourapp.com/webhooks/mistral',
  'chat.completed',
  {
    requestId: 'req-123',
    content: response.choices?.[0]?.message?.content,
    usage: response.usage,
  }
);
```

### Step 4: Server-Sent Events (SSE) for Real-Time Updates

```typescript
// api/chat/stream/route.ts
import Mistral from '@mistralai/mistralai';

export async function POST(request: Request) {
  const { messages } = await request.json();

  const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });

  const stream = await client.chat.stream({
    model: 'mistral-small-latest',
    messages,
  });

  const encoder = new TextEncoder();

  const readable = new ReadableStream({
    async start(controller) {
      // Send initial event
      controller.enqueue(encoder.encode(`event: start\ndata: {"status":"started"}\n\n`));

      try {
        let tokenCount = 0;
        for await (const event of stream) {
          const content = event.data?.choices?.[0]?.delta?.content;
          if (content) {
            tokenCount++;
            controller.enqueue(
              encoder.encode(`event: chunk\ndata: ${JSON.stringify({ content, tokenCount })}\n\n`)
            );
          }
        }

        // Send completion event
        controller.enqueue(
          encoder.encode(`event: complete\ndata: ${JSON.stringify({ totalTokens: tokenCount })}\n\n`)
        );
      } catch (error: any) {
        controller.enqueue(
          encoder.encode(`event: error\ndata: ${JSON.stringify({ error: error.message })}\n\n`)
        );
      }

      controller.close();
    },
  });

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}
```

### Step 5: Client-Side SSE Consumption

```typescript
// Client-side JavaScript
function streamChat(messages: any[]): EventSource {
  const eventSource = new EventSource('/api/chat/stream', {
    // Note: EventSource doesn't support POST directly
    // Use fetch with ReadableStream instead, or use a library
  });

  eventSource.addEventListener('start', (e) => {
    console.log('Stream started');
  });

  eventSource.addEventListener('chunk', (e) => {
    const { content } = JSON.parse(e.data);
    process.stdout.write(content);
  });

  eventSource.addEventListener('complete', (e) => {
    const { totalTokens } = JSON.parse(e.data);
    console.log(`\nComplete. Tokens: ${totalTokens}`);
    eventSource.close();
  });

  eventSource.addEventListener('error', (e) => {
    console.error('Stream error:', e);
    eventSource.close();
  });

  return eventSource;
}
```

## Output
- Event-driven Mistral AI integration
- Background job processing
- Webhook notification system
- Real-time streaming with SSE

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Job stuck in queue | Worker crashed | Implement job timeout and retry |
| Webhook failed | Network/auth issue | Retry with exponential backoff |
| SSE disconnected | Client timeout | Implement reconnection logic |
| Event backpressure | Too many events | Implement buffering |

## Examples

### Python Async Pattern
```python
import asyncio
from mistralai import Mistral

async def process_batch(prompts: list[str]):
    client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

    async def process_one(prompt: str):
        response = await client.chat.complete_async(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    results = await asyncio.gather(*[process_one(p) for p in prompts])
    return results
```

## Resources
- [BullMQ Documentation](https://docs.bullmq.io/)
- [Server-Sent Events MDN](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Mistral AI Streaming](https://docs.mistral.ai/capabilities/completion/#streaming)

## Next Steps
For performance optimization, see `mistral-performance-tuning`.