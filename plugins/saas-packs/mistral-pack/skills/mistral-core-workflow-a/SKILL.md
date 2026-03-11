---
name: mistral-core-workflow-a
description: |
  Execute Mistral AI primary workflow: Chat Completions and Streaming.
  Use when implementing chat interfaces, building conversational AI,
  or integrating Mistral for text generation.
  Trigger with phrases like "mistral chat", "mistral completion",
  "mistral streaming", "mistral conversation".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Core Workflow A: Chat Completions

## Overview
Primary money-path workflow for Mistral AI: Chat completions with streaming support.

## Prerequisites
- Completed `mistral-install-auth` setup
- Understanding of Mistral AI models
- Valid API credentials configured

## Instructions

### Step 1: Basic Chat Completion

**TypeScript**
```typescript
import Mistral from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
});

async function basicChat(userMessage: string): Promise<string> {
  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: userMessage },
    ],
  });

  return response.choices?.[0]?.message?.content ?? '';
}

// Usage
const answer = await basicChat('What is the capital of France?');
console.log(answer); // Paris is the capital of France...
```

### Step 2: Multi-Turn Conversation

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

  async chat(userMessage: string): Promise<string> {
    this.messages.push({ role: 'user', content: userMessage });

    const response = await this.client.chat.complete({
      model: this.model,
      messages: this.messages,
    });

    const assistantMessage = response.choices?.[0]?.message?.content ?? '';
    this.messages.push({ role: 'assistant', content: assistantMessage });

    return assistantMessage;
  }

  getHistory(): Message[] {
    return [...this.messages];
  }

  clearHistory(): void {
    const systemMessage = this.messages[0];
    this.messages = [systemMessage];
  }
}

// Usage
const conv = new MistralConversation('You are a helpful coding assistant.');
const response1 = await conv.chat('How do I create a list in Python?');
const response2 = await conv.chat('How do I add items to it?');
```

### Step 3: Streaming Responses

```typescript
async function streamingChat(
  userMessage: string,
  onChunk: (chunk: string) => void
): Promise<string> {
  const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

  const stream = await client.chat.stream({
    model: 'mistral-small-latest',
    messages: [
      { role: 'user', content: userMessage },
    ],
  });

  let fullResponse = '';

  for await (const event of stream) {
    const content = event.data?.choices?.[0]?.delta?.content;
    if (content) {
      fullResponse += content;
      onChunk(content);
    }
  }

  return fullResponse;
}

// Usage
const response = await streamingChat(
  'Write a short poem about coding.',
  (chunk) => process.stdout.write(chunk)
);
```

### Step 4: With Generation Parameters

```typescript
interface ChatConfig {
  temperature?: number;      // 0-1, default 0.7
  maxTokens?: number;        // Max tokens to generate
  topP?: number;             // Nucleus sampling, 0-1
  randomSeed?: number;       // For reproducibility
  safePrompt?: boolean;      // Enable safety checks
}

async function configuredChat(
  messages: Message[],
  config: ChatConfig = {}
): Promise<{ content: string; usage: any }> {
  const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

  const response = await client.chat.complete({
    model: 'mistral-large-latest',
    messages,
    temperature: config.temperature ?? 0.7,
    maxTokens: config.maxTokens,
    topP: config.topP,
    randomSeed: config.randomSeed,
    safePrompt: config.safePrompt ?? false,
  });

  return {
    content: response.choices?.[0]?.message?.content ?? '',
    usage: response.usage,
  };
}

// Example: Deterministic output
const result = await configuredChat(
  [{ role: 'user', content: 'Summarize quantum computing in 2 sentences.' }],
  { temperature: 0, randomSeed: 42, maxTokens: 100 }
);
```

### Step 5: Model Selection

```typescript
type MistralModel =
  | 'mistral-large-latest'   // Most capable, complex reasoning
  | 'mistral-medium-latest'  // Balanced
  | 'mistral-small-latest'   // Fast, cost-effective
  | 'open-mistral-7b'        // Open source
  | 'open-mixtral-8x7b';     // Open source MoE

function selectModel(task: 'complex' | 'balanced' | 'fast'): MistralModel {
  switch (task) {
    case 'complex':
      return 'mistral-large-latest';
    case 'balanced':
      return 'mistral-medium-latest';
    case 'fast':
      return 'mistral-small-latest';
  }
}
```

## Output
- Chat completions with configurable parameters
- Multi-turn conversation management
- Real-time streaming responses
- Model selection based on task

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API key | Check MISTRAL_API_KEY |
| 429 Rate Limited | Too many requests | Implement backoff |
| 400 Bad Request | Invalid parameters | Check model/message format |
| Context Exceeded | Too many tokens | Reduce conversation history |

## Examples

### Express.js Streaming Endpoint
```typescript
import express from 'express';
import Mistral from '@mistralai/mistralai';

const app = express();
const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

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

### Token Usage Tracking
```typescript
let totalTokens = 0;

async function trackedChat(messages: Message[]): Promise<string> {
  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages,
  });

  if (response.usage) {
    totalTokens += response.usage.totalTokens || 0;
    console.log(`Tokens used: ${response.usage.totalTokens}, Total: ${totalTokens}`);
  }

  return response.choices?.[0]?.message?.content ?? '';
}
```

## Resources
- [Mistral AI Chat Completions](https://docs.mistral.ai/api/#tag/chat)
- [Mistral AI Models](https://docs.mistral.ai/getting-started/models/)
- [Mistral AI Streaming](https://docs.mistral.ai/capabilities/completion/#streaming)

## Next Steps
For embeddings and function calling, see `mistral-core-workflow-b`.