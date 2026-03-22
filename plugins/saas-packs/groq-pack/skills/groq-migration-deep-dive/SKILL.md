---
name: groq-migration-deep-dive
description: |
  Migrate from OpenAI/Anthropic/other LLM providers to Groq, or migrate
  between Groq model generations with zero-downtime traffic shifting.
  Trigger with phrases like "migrate to groq", "switch to groq",
  "groq migration", "openai to groq", "groq replatform".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, migration]

---
# Groq Migration Deep Dive

## Current State
!`npm list groq-sdk openai @anthropic-ai/sdk 2>/dev/null | grep -E "groq|openai|anthropic" || echo 'No LLM SDKs found'`

## Overview
Migrate to Groq from OpenAI, Anthropic, or other LLM providers. Groq's OpenAI-compatible API makes migration straightforward -- the primary changes are: different SDK import, different model IDs, and different response metadata. The reward is 10-50x faster inference.

## Migration Complexity

| Source | Complexity | Key Changes |
|--------|-----------|-------------|
| OpenAI | Low | Import, model IDs, base URL -- API shape is identical |
| Anthropic | Medium | Different API shape, message format, streaming protocol |
| Local LLMs | Medium | Remove infra, add API calls |
| Other cloud (Bedrock, Vertex) | Medium | Remove cloud SDK, add groq-sdk |

## Instructions

### Step 1: OpenAI to Groq Migration
```typescript
// BEFORE: OpenAI
import OpenAI from "openai";
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
const result = await openai.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "Hello" }],
});

// AFTER: Groq (minimal changes)
import Groq from "groq-sdk";
const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const result = await groq.chat.completions.create({
  model: "llama-3.3-70b-versatile",  // or "llama-3.1-8b-instant"
  messages: [{ role: "user", content: "Hello" }],
});

// Same response shape: result.choices[0].message.content
```

### Step 2: Model ID Mapping
```typescript
// OpenAI → Groq model equivalents
const MODEL_MAP: Record<string, string> = {
  // OpenAI → Groq (quality equivalent)
  "gpt-4o":        "llama-3.3-70b-versatile",
  "gpt-4o-mini":   "llama-3.1-8b-instant",
  "gpt-4-turbo":   "llama-3.3-70b-versatile",
  "gpt-3.5-turbo": "llama-3.1-8b-instant",

  // Anthropic → Groq (approximate)
  "claude-3-5-sonnet": "llama-3.3-70b-versatile",
  "claude-3-haiku":    "llama-3.1-8b-instant",
};

function migrateModelId(model: string): string {
  return MODEL_MAP[model] || "llama-3.3-70b-versatile";
}
```

### Step 3: Provider Abstraction Layer
```typescript
// Build a provider-agnostic layer for zero-downtime migration
interface LLMProvider {
  name: string;
  complete(messages: any[], model: string, maxTokens: number): Promise<{
    content: string;
    model: string;
    tokens: { prompt: number; completion: number; total: number };
  }>;
}

class GroqProvider implements LLMProvider {
  name = "groq";
  private client: Groq;

  constructor() {
    this.client = new Groq();
  }

  async complete(messages: any[], model: string, maxTokens: number) {
    const result = await this.client.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
    });

    return {
      content: result.choices[0].message.content || "",
      model: result.model,
      tokens: {
        prompt: result.usage!.prompt_tokens,
        completion: result.usage!.completion_tokens,
        total: result.usage!.total_tokens,
      },
    };
  }
}

class OpenAIProvider implements LLMProvider {
  name = "openai";
  private client: OpenAI;

  constructor() {
    this.client = new OpenAI();
  }

  async complete(messages: any[], model: string, maxTokens: number) {
    const result = await this.client.chat.completions.create({
      model,
      messages,
      max_tokens: maxTokens,
    });

    return {
      content: result.choices[0].message.content || "",
      model: result.model,
      tokens: {
        prompt: result.usage!.prompt_tokens,
        completion: result.usage!.completion_tokens,
        total: result.usage!.total_tokens,
      },
    };
  }
}
```

### Step 4: Feature Flag Traffic Shifting
```typescript
// Gradually shift traffic from OpenAI to Groq
function getProvider(): LLMProvider {
  const groqPercentage = getFeatureFlag("groq_migration_pct"); // 0-100

  if (Math.random() * 100 < groqPercentage) {
    return new GroqProvider();
  }
  return new OpenAIProvider();
}

// Migration schedule:
// Week 1: groq_migration_pct = 10  (canary)
// Week 2: groq_migration_pct = 50  (validate quality)
// Week 3: groq_migration_pct = 90  (near-complete)
// Week 4: groq_migration_pct = 100 (done, remove OpenAI)
```

### Step 5: Automated Migration Scanner
```bash
set -euo pipefail
echo "=== Migration Assessment ==="

echo ""
echo "--- OpenAI references ---"
grep -rn "from ['\"]openai['\"]" src/ --include="*.ts" --include="*.js" 2>/dev/null | wc -l
grep -rn "openai\." src/ --include="*.ts" --include="*.js" 2>/dev/null | head -5

echo ""
echo "--- Model IDs to migrate ---"
grep -roh "model.*['\"]gpt-[^'\"]*['\"]" src/ --include="*.ts" --include="*.js" 2>/dev/null | sort -u

echo ""
echo "--- OpenAI-specific features used ---"
grep -rn "\.images\.\|\.audio\.\|\.embeddings\.\|\.moderations\.\|\.files\.\|\.fine_tuning\." \
  src/ --include="*.ts" --include="*.js" 2>/dev/null || echo "None (chat.completions only -- easy migration)"

echo ""
echo "--- API keys to update ---"
grep -rn "OPENAI_API_KEY" src/ .env* --include="*.ts" --include="*.js" --include=".env*" 2>/dev/null | wc -l
```

### Step 6: Comparison Benchmark
```typescript
// Run the same prompts through both providers to compare quality + speed
async function migrationBenchmark(prompts: string[]) {
  const groq = new GroqProvider();
  const openai = new OpenAIProvider();

  for (const prompt of prompts) {
    const messages = [{ role: "user" as const, content: prompt }];

    const startGroq = performance.now();
    const groqResult = await groq.complete(messages, "llama-3.3-70b-versatile", 256);
    const groqMs = performance.now() - startGroq;

    const startOAI = performance.now();
    const oaiResult = await openai.complete(messages, "gpt-4o-mini", 256);
    const oaiMs = performance.now() - startOAI;

    console.log(`Prompt: "${prompt.slice(0, 50)}..."`);
    console.log(`  Groq:   ${groqMs.toFixed(0)}ms | ${groqResult.tokens.total} tokens`);
    console.log(`  OpenAI: ${oaiMs.toFixed(0)}ms | ${oaiResult.tokens.total} tokens`);
    console.log(`  Speedup: ${(oaiMs / groqMs).toFixed(1)}x faster with Groq`);
    console.log();
  }
}
```

### Step 7: Key Differences to Handle

| Feature | OpenAI | Groq |
|---------|--------|------|
| SDK import | `import OpenAI from "openai"` | `import Groq from "groq-sdk"` |
| Env var | `OPENAI_API_KEY` | `GROQ_API_KEY` |
| Models | `gpt-4o`, `gpt-4o-mini` | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant` |
| Embeddings | `openai.embeddings.create()` | Not available (use OpenAI or local) |
| Fine-tuning | Supported | Not available |
| Image generation | `openai.images.generate()` | Not available |
| Audio (STT) | `openai.audio.transcriptions` | `groq.audio.transcriptions` (faster) |
| Structured outputs | `strict: true` | `strict: true` (same format) |
| Tool calling | Supported | Supported (same format) |
| JSON mode | `response_format: { type: "json_object" }` | Same |
| Vision | `gpt-4o` with images | Llama 4 Scout/Maverick |
| Streaming | Supported | Supported (same SSE format) |
| Response usage | Standard fields | Adds `queue_time`, `completion_time`, `total_time` |

## Rollback Plan
```bash
set -euo pipefail
# Immediate rollback: flip feature flag
# groq_migration_pct = 0

# Verify:
# - All requests routing to OpenAI
# - Error rates returned to baseline
# - No Groq API calls in logs
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Quality regression | Different model strengths | Tune system prompts for Llama models |
| Missing features | Groq doesn't have embeddings/images | Keep OpenAI for those features |
| Rate limits | Different limits than OpenAI | Configure per-model rate limits |
| Cost increase | Different pricing structure | Route simple tasks to 8B model |

## Resources
- [Groq Quickstart](https://console.groq.com/docs/quickstart)
- [Groq Models](https://console.groq.com/docs/models)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [groq-sdk npm](https://www.npmjs.com/package/groq-sdk)

## Next Steps
For ongoing SDK version upgrades, see `groq-upgrade-migration`.
