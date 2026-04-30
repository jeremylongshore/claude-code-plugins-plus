---
name: together-reference-architecture
description: 'Together AI reference architecture for inference, fine-tuning, and model
  deployment.

  Use when working with Together AI''s OpenAI-compatible API.

  Trigger: "together reference architecture".

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
# Together AI Reference Architecture

## Overview

Production architecture for AI inference, fine-tuning, and batch processing with Together AI's OpenAI-compatible API. Designed for teams routing requests across 100+ open-source models (Llama, Mixtral, Qwen, FLUX) with intelligent model selection, response caching, fine-tune pipeline management, and cost optimization via batch inference at 50% discount. Key design drivers: model routing for cost/quality tradeoffs, inference caching for repeated queries, fine-tune lifecycle management, and graceful degradation across model providers.

## Architecture Diagram
```
Application ──→ Model Router ──→ Cache (Redis) ──→ Together API (v1)
                    ↓                                /chat/completions
               Queue (Bull) ──→ Batch Worker         /completions
                    ↓                                /images/generations
               Fine-Tune Manager ──→ Together API    /fine-tunes
                    ↓                                /models
               Cost Tracker ──→ Analytics Dashboard
```

## Service Layer
```typescript
class InferenceService {
  constructor(private together: TogetherClient, private cache: CacheLayer, private router: ModelRouter) {}

  async complete(request: InferenceRequest): Promise<InferenceResponse> {
    const model = this.router.selectModel(request.task, request.priority);
    const cacheKey = `inference:${model}:${this.hashPrompt(request.prompt)}`;
    const cached = await this.cache.get(cacheKey);
    if (cached && request.allowCached) return cached;
    const response = await this.together.chatCompletions({ model, messages: request.messages, temperature: request.temperature ?? 0.7 });
    await this.cache.set(cacheKey, response, CACHE_CONFIG.inference.ttl);
    await this.costTracker.record(model, response.usage);
    return response;
  }

  async submitBatch(requests: InferenceRequest[]): Promise<string> {
    const batchId = await this.together.createBatch(requests.map(r => ({
      model: this.router.selectModel(r.task, 'batch'), messages: r.messages })));
    return batchId;  // 50% cost reduction for batch processing
  }
}
```

## Caching Strategy
```typescript
const CACHE_CONFIG = {
  inference:   { ttl: 3600,  prefix: 'infer' },    // 1 hr — deterministic prompts (temp=0) cache well
  embeddings:  { ttl: 86400, prefix: 'embed' },     // 24 hr — embeddings are stable for same input
  modelList:   { ttl: 3600,  prefix: 'models' },    // 1 hr — available models change infrequently
  fineTune:    { ttl: 60,    prefix: 'ft' },         // 1 min — training status needs near-real-time
  batchStatus: { ttl: 30,    prefix: 'batch' },      // 30s — batch completion polling
};
// Cache only temp=0 responses by default; stochastic responses bypass cache unless explicitly opted in
```

## Event Pipeline
```typescript
class InferencePipeline {
  private queue = new Bull('together-events', { redis: process.env.REDIS_URL });

  async onFineTuneComplete(event: FineTuneEvent): Promise<void> {
    await this.queue.add('deploy-model', event, { attempts: 3, backoff: { type: 'exponential', delay: 5000 } });
  }

  async processFineTuneEvent(event: FineTuneEvent): Promise<void> {
    if (event.status === 'completed') {
      await this.router.registerModel(event.modelId, { task: event.task, cost: event.inferCostPerToken });
      await this.runEvalSuite(event.modelId, event.evalDataset);
    }
    if (event.status === 'failed') await this.notifyTeam(event.error);
  }

  async processBatchComplete(batchId: string): Promise<void> {
    const results = await this.together.getBatchResults(batchId);
    await this.storeResults(results);
    await this.costTracker.recordBatch(batchId, results.usage);
  }
}
```

## Data Model
```typescript
interface InferenceRequest  { task: 'chat' | 'code' | 'embedding' | 'image'; messages: Message[]; prompt?: string; temperature?: number; priority: 'realtime' | 'standard' | 'batch'; allowCached?: boolean; }
interface ModelRoute         { modelId: string; task: string; costPerToken: number; latencyP50Ms: number; qualityScore: number; }
interface FineTuneJob        { id: string; baseModel: string; trainingFile: string; status: 'pending' | 'running' | 'completed' | 'failed'; epochs: number; learningRate: number; }
interface CostRecord         { model: string; promptTokens: number; completionTokens: number; costUsd: number; timestamp: string; }
```

## Scaling Considerations
- Route low-priority requests to cheaper models (Llama 8B) and high-priority to larger models (Llama 70B, Mixtral)
- Use batch API for non-interactive workloads — 50% cost savings with acceptable latency tradeoff
- Cache embeddings aggressively — identical text produces identical vectors, high cache hit rate
- Monitor per-model cost and latency; auto-shift traffic when a model degrades or pricing changes
- Fine-tune pipeline should use a separate API key with isolated rate limits from production inference

## Error Handling
| Component | Failure Mode | Recovery |
|-----------|-------------|----------|
| Inference request | Model overloaded (500) | Fallback to alternative model in same task category |
| Rate limiting | 429 Too Many Requests | Token bucket with exponential backoff, queue overflow to batch |
| Fine-tune job | Training divergence | Auto-stop on loss plateau, notify team with checkpoint artifacts |
| Batch processing | Partial batch failure | Retry failed items individually, report partial results |
| Model routing | Selected model deprecated | Auto-reroute to replacement model, alert team to update config |

## Resources
- [Together AI Docs](https://docs.together.ai/)
- [API Reference](https://docs.together.ai/reference/chat-completions-1)
- [Model List](https://docs.together.ai/docs/inference-models)

## Next Steps
See `together-deploy-integration`.
