---
name: mistral-core-workflow-a
description: |
  Execute Mistral AI chat completions with streaming, multi-turn, and guardrails.
  Use when implementing chat interfaces, building conversational AI,
  or integrating Mistral for text generation.
  Trigger with phrases like "mistral chat", "mistral completion",
  "mistral streaming", "mistral conversation", "mistral guardrails".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, workflow]

---
# Mistral AI Core Workflow A: Chat Completions

## Overview
Production chat completion patterns for Mistral AI: multi-turn conversations, streaming responses, JSON mode structured output, guardrails/moderation, and model selection. Uses the `@mistralai/mistralai` SDK.

## Prerequisites
- Completed `mistral-install-auth` setup
- `MISTRAL_API_KEY` environment variable set
- Understanding of Mistral model tiers

## Instructions

### Step 1: Basic Chat Completion

```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

async function chat(userMessage: string): Promise<string> {
  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: userMessage },
    ],
  });
  return response.choices?.[0]?.message?.content ?? '';
}
```

### Step 2: Multi-Turn Conversation Manager

```typescript
interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

class MistralConversation {
  private messages: Message[] = [];
  private client: Mistral;
  private model: string;

  constructor(systemPrompt: string, model = 'mistral-small-latest') {
    this.client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });
    this.model = model;
    this.messages.push({ role: 'system', content: systemPrompt });
  }

  async send(userMessage: string): Promise<string> {
    this.messages.push({ role: 'user', content: userMessage });

    const response = await this.client.chat.complete({
      model: this.model,
      messages: this.messages,
    });

    const reply = response.choices?.[0]?.message?.content ?? '';
    this.messages.push({ role: 'assistant', content: reply });
    return reply;
  }

  // Prevent context window overflow
  trimHistory(maxTurns = 20): void {
    const system = this.messages[0];
    const recent = this.messages.slice(1).slice(-maxTurns * 2);
    this.messages = [system, ...recent];
  }
}

// Usage
const conv = new MistralConversation('You are a coding tutor.');
await conv.send('How do I reverse a list in Python?');
await conv.send('What about in-place?');
```

### Step 3: Streaming Responses

```typescript
async function streamChat(
  messages: Message[],
  onChunk: (text: string) => void,
): Promise<string> {
  const stream = await client.chat.stream({
    model: 'mistral-small-latest',
    messages,
  });

  let full = '';
  for await (const event of stream) {
    const text = event.data?.choices?.[0]?.delta?.content;
    if (text) {
      full += text;
      onChunk(text);
    }
  }
  return full;
}

// Express.js SSE endpoint
app.post('/chat/stream', async (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  const stream = await client.chat.stream({
    model: 'mistral-small-latest',
    messages: req.body.messages,
  });

  for await (const event of stream) {
    const content = event.data?.choices?.[0]?.delta?.content;
    if (content) {
      res.write(`data: ${JSON.stringify({ content })}\n\n`);
    }
  }
  res.write('data: [DONE]\n\n');
  res.end();
});
```

### Step 4: JSON Mode and JSON Schema Mode

```typescript
// JSON mode — model returns valid JSON
const jsonResponse = await client.chat.complete({
  model: 'mistral-small-latest',
  messages: [
    { role: 'user', content: 'List 3 countries with capitals as JSON array.' },
  ],
  responseFormat: { type: 'json_object' },
});
const data = JSON.parse(jsonResponse.choices?.[0]?.message?.content ?? '{}');

// JSON Schema mode — guarantees structure conformance
const schemaResponse = await client.chat.complete({
  model: 'mistral-small-latest',
  messages: [
    { role: 'user', content: 'Classify this ticket: "Login page crashes on mobile"' },
  ],
  responseFormat: {
    type: 'json_schema',
    jsonSchema: {
      name: 'ticket_classification',
      schema: {
        type: 'object',
        properties: {
          category: { type: 'string', enum: ['bug', 'feature', 'question'] },
          severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
          summary: { type: 'string' },
        },
        required: ['category', 'severity', 'summary'],
      },
    },
  },
});
```

### Step 5: Guardrails and Moderation

```typescript
// Built-in safe_prompt flag — injects safety system prompt
const safeResponse = await client.chat.complete({
  model: 'mistral-small-latest',
  messages: [{ role: 'user', content: userInput }],
  safePrompt: true,
});

// Dedicated moderation API — classify text against policy categories
const moderation = await client.classifiers.moderate({
  model: 'mistral-moderation-latest',
  inputs: [userInput],
});

const flagged = moderation.results[0].categories;
// Check: flagged.sexual, flagged.hate_and_discrimination, flagged.violence, etc.
if (Object.values(flagged).some(Boolean)) {
  throw new Error('Content flagged by moderation');
}
```

### Step 6: Model Selection Guide

```typescript
type UseCase = 'realtime' | 'analysis' | 'code' | 'vision' | 'embedding';

const MODEL_MAP: Record<UseCase, { model: string; note: string }> = {
  realtime:  { model: 'mistral-small-latest',   note: '256k ctx, fast, $0.1/M in' },
  analysis:  { model: 'mistral-large-latest',   note: '256k ctx, reasoning, $0.5/M in' },
  code:      { model: 'codestral-latest',        note: '256k ctx, code + FIM, $0.3/M in' },
  vision:    { model: 'pixtral-large-latest',    note: '128k ctx, multimodal' },
  embedding: { model: 'mistral-embed',           note: '1024-dim vectors, $0.1/M in' },
};

function selectModel(use: UseCase): string {
  return MODEL_MAP[use].model;
}
```

## Output
- Chat completions with configurable parameters
- Multi-turn conversation management with history trimming
- Real-time streaming responses
- JSON and JSON Schema structured output
- Content moderation via guardrails

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Verify `MISTRAL_API_KEY` |
| `429 Rate Limited` | RPM or TPM exceeded | Implement backoff (see `mistral-rate-limits`) |
| `400 Bad Request` | Invalid model or params | Check model ID and message format |
| Context exceeded | Too many tokens | Trim conversation history |
| Empty JSON response | Missing instruction | Tell model to respond in JSON in prompt |

## Resources
- [Chat Completions API](https://docs.mistral.ai/api/endpoint/chat/)
- [JSON Mode](https://docs.mistral.ai/capabilities/structured_output/json_mode/)
- [Guardrails](https://docs.mistral.ai/capabilities/guardrailing/)
- [Models Overview](https://docs.mistral.ai/getting-started/models/)

## Next Steps
For embeddings and function calling, see `mistral-core-workflow-b`.
