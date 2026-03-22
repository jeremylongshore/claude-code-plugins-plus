---
name: mistral-migration-deep-dive
description: |
  Execute migration to Mistral AI from OpenAI, Anthropic, or other providers.
  Use when migrating to Mistral AI from another provider, performing major refactoring,
  or re-platforming existing AI integrations to Mistral AI.
  Trigger with phrases like "migrate to mistral", "mistral migration",
  "switch to mistral", "openai to mistral", "anthropic to mistral".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, migration]

---
# Mistral AI Migration Deep Dive

## Current State
!`npm list openai @anthropic-ai/sdk @mistralai/mistralai 2>/dev/null | grep -E "openai|anthropic|mistral" || echo 'No AI SDKs found'`

## Overview
Comprehensive migration guide from OpenAI or Anthropic to Mistral AI using the adapter pattern with feature-flag controlled rollout. Covers model mapping, API differences, prompt adjustments, validation testing, and rollback procedures.

## Prerequisites
- Current AI integration documented
- Mistral AI SDK installed (`@mistralai/mistralai`)
- Feature flag infrastructure (env vars or LaunchDarkly)
- Rollback plan tested

## Migration Complexity

| Migration | Effort | Duration | Risk |
|-----------|--------|----------|------|
| Fresh install (no existing AI) | Low | Days | Low |
| OpenAI to Mistral | Medium | 1-2 weeks | Medium |
| Anthropic to Mistral | Medium | 1-2 weeks | Medium |
| Multi-provider to Mistral | High | 2-4 weeks | Medium |

## Instructions

### Step 1: Assessment — Find All AI Touchpoints

```bash
set -euo pipefail
# Count integration points
echo "=== AI Integration Assessment ==="
echo "OpenAI imports: $(grep -r "from 'openai'" src/ --include='*.ts' -l 2>/dev/null | wc -l)"
echo "Anthropic imports: $(grep -r "from '@anthropic'" src/ --include='*.ts' -l 2>/dev/null | wc -l)"
echo "Chat completions: $(grep -r "chat\.completions\|messages\.create" src/ --include='*.ts' -c 2>/dev/null | wc -l)"
echo "Embeddings: $(grep -r "embeddings\.create" src/ --include='*.ts' -c 2>/dev/null | wc -l)"
echo "Streaming: $(grep -r "stream\|for await" src/ --include='*.ts' -c 2>/dev/null | wc -l)"
```

### Step 2: Model Mapping

| OpenAI | Anthropic | Mistral | Notes |
|--------|-----------|---------|-------|
| gpt-4o | claude-3-5-sonnet | `mistral-large-latest` | Complex reasoning |
| gpt-4o-mini | claude-3-5-haiku | `mistral-small-latest` | Fast, cheap |
| gpt-3.5-turbo | — | `mistral-small-latest` | General purpose |
| text-embedding-3-small | — | `mistral-embed` | 1024 dims (vs 1536) |
| — | — | `codestral-latest` | Code-specialized |
| gpt-4-vision | claude-3-5-sonnet | `pixtral-large-latest` | Vision + text |

### Step 3: Provider-Agnostic Adapter

```typescript
// adapters/types.ts
export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content: string;
}

export interface ChatOptions {
  model?: string;
  temperature?: number;
  maxTokens?: number;
  stream?: boolean;
}

export interface ChatResponse {
  content: string;
  usage: { inputTokens: number; outputTokens: number };
  model: string;
}

export interface AIAdapter {
  chat(messages: Message[], options?: ChatOptions): Promise<ChatResponse>;
  chatStream(messages: Message[], options?: ChatOptions): AsyncGenerator<string>;
  embed(texts: string[]): Promise<number[][]>;
}
```

### Step 4: Mistral Adapter

```typescript
// adapters/mistral.adapter.ts
import { Mistral } from '@mistralai/mistralai';
import type { AIAdapter, Message, ChatOptions, ChatResponse } from './types.js';

export class MistralAdapter implements AIAdapter {
  private client: Mistral;
  private defaultModel: string;

  constructor(apiKey: string, defaultModel = 'mistral-small-latest') {
    this.client = new Mistral({ apiKey });
    this.defaultModel = defaultModel;
  }

  async chat(messages: Message[], options?: ChatOptions): Promise<ChatResponse> {
    const response = await this.client.chat.complete({
      model: options?.model ?? this.defaultModel,
      messages,
      temperature: options?.temperature,
      maxTokens: options?.maxTokens,
    });

    return {
      content: response.choices?.[0]?.message?.content ?? '',
      usage: {
        inputTokens: response.usage?.promptTokens ?? 0,
        outputTokens: response.usage?.completionTokens ?? 0,
      },
      model: response.model ?? this.defaultModel,
    };
  }

  async *chatStream(messages: Message[], options?: ChatOptions): AsyncGenerator<string> {
    const stream = await this.client.chat.stream({
      model: options?.model ?? this.defaultModel,
      messages,
      temperature: options?.temperature,
      maxTokens: options?.maxTokens,
    });

    for await (const event of stream) {
      const content = event.data?.choices?.[0]?.delta?.content;
      if (content) yield content;
    }
  }

  async embed(texts: string[]): Promise<number[][]> {
    const response = await this.client.embeddings.create({
      model: 'mistral-embed',
      inputs: texts,
    });
    return response.data.map(d => d.embedding);
  }
}
```

### Step 5: Feature-Flag Controlled Rollout

```typescript
// adapters/factory.ts
import { MistralAdapter } from './mistral.adapter.js';
import { OpenAIAdapter } from './openai.adapter.js';

export function createAdapter(): AIAdapter {
  const rolloutPercent = parseInt(process.env.MISTRAL_ROLLOUT_PERCENT ?? '0');
  const useMistral = Math.random() * 100 < rolloutPercent;

  if (useMistral) {
    console.log('[AI] Using Mistral');
    return new MistralAdapter(process.env.MISTRAL_API_KEY!);
  }

  console.log('[AI] Using OpenAI (legacy)');
  return new OpenAIAdapter(process.env.OPENAI_API_KEY!);
}
```

### Step 6: Gradual Rollout Plan

| Phase | Rollout % | Duration | Criteria to Advance |
|-------|-----------|----------|---------------------|
| 0. Validation | 0% | 1-2 days | A/B tests pass |
| 1. Canary | 5% | 2-3 days | Error rate < 1%, latency OK |
| 2. Partial | 25% | 3-5 days | Quality metrics match |
| 3. Majority | 50% | 5-7 days | Cost reduction confirmed |
| 4. Full | 100% | — | Remove old adapter code |

```bash
# Advance rollout
export MISTRAL_ROLLOUT_PERCENT=5   # Canary
export MISTRAL_ROLLOUT_PERCENT=25  # Partial
export MISTRAL_ROLLOUT_PERCENT=100 # Full migration
export MISTRAL_ROLLOUT_PERCENT=0   # Emergency rollback
```

### Step 7: A/B Validation Testing

```typescript
async function validateMigration(adapter1: AIAdapter, adapter2: AIAdapter) {
  const testPrompts = [
    'Summarize: TypeScript adds static typing to JavaScript.',
    'Classify: "The app crashes on login" — bug, feature, or question?',
    'What is 2+2?',
  ];

  for (const prompt of testPrompts) {
    const messages = [{ role: 'user' as const, content: prompt }];
    const [r1, r2] = await Promise.all([
      adapter1.chat(messages, { temperature: 0 }),
      adapter2.chat(messages, { temperature: 0 }),
    ]);

    console.log(`Prompt: ${prompt.slice(0, 50)}...`);
    console.log(`  Provider 1: ${r1.content.slice(0, 100)} (${r1.usage.outputTokens} tokens)`);
    console.log(`  Provider 2: ${r2.content.slice(0, 100)} (${r2.usage.outputTokens} tokens)`);
    console.log();
  }
}
```

### Key API Differences

| Feature | OpenAI | Mistral |
|---------|--------|---------|
| SDK import | `import OpenAI from 'openai'` | `import { Mistral } from '@mistralai/mistralai'` |
| Chat method | `client.chat.completions.create()` | `client.chat.complete()` |
| Stream events | `chunk.choices[0]?.delta?.content` | `event.data?.choices?.[0]?.delta?.content` |
| Embeddings | `client.embeddings.create()` | `client.embeddings.create()` (same) |
| Tool calling | Identical JSON Schema format | Identical JSON Schema format |
| JSON mode | `response_format: { type: 'json_object' }` | `responseFormat: { type: 'json_object' }` |
| Vision | Base64 in content array | Same approach with `pixtral` models |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Different output quality | Model differences | Adjust prompts, tune temperature |
| Embedding dimension mismatch | 1536 vs 1024 | Re-embed all vectors, update vector DB config |
| Missing feature | Not supported by Mistral | Implement fallback in adapter |
| Cost increase | Token counting differs | Monitor and optimize prompts |

## Resources
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [Mistral vs OpenAI Comparison](https://docs.mistral.ai/getting-started/models/)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)

## Output
- Integration assessment with effort estimation
- Provider-agnostic adapter interface
- Mistral adapter implementation
- Feature-flag controlled gradual rollout
- Model mapping and API difference reference
- A/B validation test suite
- Rollback procedure (set MISTRAL_ROLLOUT_PERCENT=0)
