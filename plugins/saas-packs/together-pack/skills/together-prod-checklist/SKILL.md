---
name: together-prod-checklist
description: |
  Together AI prod checklist for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together prod checklist".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Production Checklist

## Overview

Together AI provides OpenAI-compatible inference across 100+ open-source models (Llama, Mixtral, Qwen, FLUX) plus fine-tuning and batch processing. A production integration routes completions, embeddings, or image generation through Together's API. Failures mean inference latency spikes, model availability gaps, or unexpected cost overruns from uncontrolled batch jobs.

## Authentication & Secrets

- [ ] `TOGETHER_API_KEY` stored in secrets manager (not source code)
- [ ] API key restricted to production workspace
- [ ] Key rotation schedule documented (90-day cycle)
- [ ] Separate keys for dev/staging/prod environments
- [ ] Fine-tuning job tokens scoped separately from inference tokens

## API Integration

- [ ] Production base URL configured (`https://api.together.xyz/v1`)
- [ ] Rate limit handling with exponential backoff
- [ ] Model IDs validated against `client.models.list()` before deployment
- [ ] Completion streaming implemented for real-time use cases
- [ ] Embedding batch size optimized (max 2048 inputs per request)
- [ ] Batch inference configured for non-real-time workloads (50% cost savings)
- [ ] Fallback model configured if primary model is unavailable

## Error Handling & Resilience

- [ ] Circuit breaker configured for Together API outages
- [ ] Retry with backoff for 429/5xx responses
- [ ] Model-not-found errors caught before user-facing requests
- [ ] Token usage tracked per request to prevent budget overruns
- [ ] Fine-tuning job failure alerts configured
- [ ] Timeout handling for long-running generation requests (>30s)

## Monitoring & Alerting

- [ ] API latency tracked per model and endpoint (chat, embeddings, images)
- [ ] Error rate alerts set (threshold: >5% over 5 minutes)
- [ ] Token consumption monitored against daily/monthly budget caps
- [ ] Model availability checked (Together status page integration)
- [ ] Batch job completion rate tracked

## Validation Script

```typescript
async function checkTogetherReadiness(): Promise<void> {
  const checks: { name: string; pass: boolean; detail: string }[] = [];
  // API connectivity
  try {
    const res = await fetch('https://api.together.xyz/v1/models', {
      headers: { Authorization: `Bearer ${process.env.TOGETHER_API_KEY}` },
    });
    checks.push({ name: 'Together API', pass: res.ok, detail: res.ok ? 'Connected' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Together API', pass: false, detail: e.message }); }
  // Credentials present
  checks.push({ name: 'API Key Set', pass: !!process.env.TOGETHER_API_KEY, detail: process.env.TOGETHER_API_KEY ? 'Present' : 'MISSING' });
  // Inference test
  try {
    const res = await fetch('https://api.together.xyz/v1/chat/completions', {
      method: 'POST',
      headers: { Authorization: `Bearer ${process.env.TOGETHER_API_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: 'meta-llama/Llama-3-8b-chat-hf', messages: [{ role: 'user', content: 'ping' }], max_tokens: 5 }),
    });
    checks.push({ name: 'Inference', pass: res.ok, detail: res.ok ? 'Model responding' : `HTTP ${res.status}` });
  } catch (e: any) { checks.push({ name: 'Inference', pass: false, detail: e.message }); }
  for (const c of checks) console.log(`[${c.pass ? 'PASS' : 'FAIL'}] ${c.name}: ${c.detail}`);
}
checkTogetherReadiness();
```

## Error Handling

| Check | Risk if Skipped | Priority |
|-------|----------------|----------|
| API key rotation | Expired key halts all inference | P1 |
| Token budget monitoring | Unexpected cost overruns | P1 |
| Model availability check | Requests fail on deprecated models | P2 |
| Rate limit backoff | Burst traffic triggers 429 cascade | P2 |
| Fine-tuning job alerts | Failed jobs waste compute budget | P3 |

## Resources

- [Together AI Docs](https://docs.together.ai/)
- [API Reference](https://docs.together.ai/reference/chat-completions-1)
- [Model List](https://docs.together.ai/docs/inference-models)

## Next Steps

See `together-security-basics` for API key management and cost controls.
