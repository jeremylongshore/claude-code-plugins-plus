---
name: together-upgrade-migration
description: |
  Together AI upgrade migration for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together upgrade migration".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Upgrade & Migration

## Overview

Together AI provides an OpenAI-compatible inference platform hosting 100+ open-source models (Llama, Mixtral, Qwen, FLUX) with fine-tuning and batch inference capabilities. The API lives at `api.together.xyz/v1` and follows OpenAI's chat completions format. Tracking model deprecations and API changes matters because Together regularly retires older model versions, updates model IDs when weights are refreshed, and changes fine-tuning job schemas — causing silent failures when a model ID that worked yesterday returns `404` today with no advance warning in the response.

## Version Detection

```typescript
const TOGETHER_BASE = "https://api.together.xyz/v1";

async function detectTogetherChanges(apiKey: string): Promise<void> {
  // List available models and check for deprecations
  const res = await fetch(`${TOGETHER_BASE}/models`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  const data = await res.json();
  const models = data.data ?? data;

  // Check if commonly used models are still available
  const trackedModels = [
    "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "Qwen/Qwen2.5-72B-Instruct-Turbo",
  ];
  for (const modelId of trackedModels) {
    const available = models.some((m: any) => m.id === modelId);
    if (!available) console.warn(`Model deprecated or renamed: ${modelId}`);
  }

  // Check API version headers
  const version = res.headers.get("x-together-api-version");
  if (version) console.log(`Together API version: ${version}`);
}
```

## Migration Checklist

- [ ] Check Together model list for deprecated or renamed model IDs
- [ ] Update all hardcoded model ID strings in codebase
- [ ] Verify fine-tuning job creation schema (new required fields or parameter renames)
- [ ] Test chat completions response format for new fields (usage breakdown, etc.)
- [ ] Check if embeddings endpoint model list changed
- [ ] Validate batch inference job API for schema or pricing tier changes
- [ ] Update function calling format if tool use schema evolved
- [ ] Test streaming response for new SSE event types or finish reasons
- [ ] Verify image generation models (FLUX) for parameter changes
- [ ] Run cost comparison — pricing per token may change with model updates

## Schema Migration

```typescript
// Together model IDs change when model versions are updated
interface ModelMigration {
  oldId: string;
  newId: string;
  breakingChanges: string[];
}

const MODEL_MIGRATIONS: ModelMigration[] = [
  {
    oldId: "togethercomputer/llama-2-70b-chat",
    newId: "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    breakingChanges: ["New chat template format", "Different tokenizer", "Higher context window"],
  },
  {
    oldId: "mistralai/Mixtral-8x7B-Instruct-v0.1",
    newId: "mistralai/Mixtral-8x22B-Instruct-v0.1",
    breakingChanges: ["Different pricing tier", "Changed max_tokens default"],
  },
];

function migrateModelId(oldId: string): string {
  const migration = MODEL_MIGRATIONS.find((m) => m.oldId === oldId);
  if (migration) {
    console.log(`Migrating model: ${oldId} → ${migration.newId}`);
    console.log(`Breaking changes: ${migration.breakingChanges.join(", ")}`);
    return migration.newId;
  }
  return oldId;
}

// Update fine-tuning job schema: old flat config → new structured config
interface OldFineTuneRequest {
  model: string;
  training_file: string;
  n_epochs: number;
  learning_rate: number;
}

interface NewFineTuneRequest {
  model: string;
  training_file: string;
  hyperparameters: { n_epochs: number; learning_rate: number; batch_size: number };
  suffix?: string;
}

function migrateFineTuneRequest(old: OldFineTuneRequest): NewFineTuneRequest {
  return {
    model: migrateModelId(old.model),
    training_file: old.training_file,
    hyperparameters: { n_epochs: old.n_epochs, learning_rate: old.learning_rate, batch_size: 4 },
  };
}
```

## Rollback Strategy

```typescript
class TogetherClient {
  private modelFallbacks: Record<string, string[]>;

  constructor(private apiKey: string) {
    this.modelFallbacks = {
      "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo": [
        "meta-llama/Meta-Llama-3-70B-Instruct-Turbo",
        "meta-llama/Llama-2-70b-chat-hf",
      ],
    };
  }

  async chatCompletion(model: string, messages: any[]): Promise<any> {
    const candidates = [model, ...(this.modelFallbacks[model] ?? [])];
    for (const candidate of candidates) {
      try {
        const res = await fetch("https://api.together.xyz/v1/chat/completions", {
          method: "POST",
          headers: { Authorization: `Bearer ${this.apiKey}`, "Content-Type": "application/json" },
          body: JSON.stringify({ model: candidate, messages }),
        });
        if (res.status === 404) { console.warn(`Model not found: ${candidate}`); continue; }
        if (!res.ok) throw new Error(`Together ${res.status}`);
        return await res.json();
      } catch (err) {
        if (candidate === candidates[candidates.length - 1]) throw err;
        console.warn(`Failed with ${candidate}, trying next fallback`);
      }
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Model ID deprecated | `404 Model not found` | Check `/models` endpoint for current ID; update model string |
| Fine-tune schema changed | `400` with `unknown parameter: n_epochs` | Nest hyperparameters under `hyperparameters` object |
| Streaming format changed | SSE parser receives unexpected `[DONE]` event format | Update stream parser to handle both old and new termination events |
| Token pricing changed | Unexpected cost spike on same workload | Verify per-token pricing on Together dashboard; switch to batch endpoint for 50% savings |
| Function calling format updated | `tool_calls` field missing from response | Update to new tool use schema matching OpenAI's latest format |

## Resources

- [Together AI Docs](https://docs.together.ai/)
- [API Reference](https://docs.together.ai/reference/chat-completions-1)
- [Model List](https://docs.together.ai/docs/inference-models)
- [Together Changelog](https://docs.together.ai/changelog)

## Next Steps

For CI pipeline integration, see `together-ci-integration`.
