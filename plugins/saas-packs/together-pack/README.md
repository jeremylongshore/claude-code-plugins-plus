# Together AI Skill Pack

> 18 production-ready Claude Code skills for Together AI -- real OpenAI-compatible inference, fine-tuning, and model deployment code.

## What This Is

A complete skill pack for building AI applications with Together AI. Every skill contains real API code: chat completions, streaming, image generation, embeddings, fine-tuning jobs, batch inference, and model management. Uses the official `together` Python SDK and OpenAI-compatible Node.js client.

## Installation

```bash
/plugin install together-pack@claude-code-plugins-plus
```

## Skills

### Standard Skills (S01-S12)

| # | Skill | What It Does |
|---|-------|-------------|
| S01 | `together-install-auth` | Install `together` SDK, configure API key, verify with model list |
| S02 | `together-hello-world` | Chat completions, streaming, image generation, embeddings |
| S03 | `together-local-dev-loop` | Mock responses, test fixtures, environment separation |
| S04 | `together-sdk-patterns` | OpenAI client wrapper, model selection, typed responses |
| S05 | `together-core-workflow-a` | Fine-tuning: JSONL prep, upload, create job, monitor, deploy |
| S06 | `together-core-workflow-b` | Batch inference, dedicated endpoints, model comparison |
| S07 | `together-common-errors` | Fix 401, model not found, rate limits, timeout errors |
| S08 | `together-debug-bundle` | API connectivity, model availability, usage diagnostics |
| S09 | `together-rate-limits` | Per-model rate limits, request throttling, queue management |
| S10 | `together-security-basics` | API key protection, input validation, output filtering |
| S11 | `together-prod-checklist` | Model selection, fallback chains, monitoring, health checks |
| S12 | `together-upgrade-migration` | SDK version updates, model deprecations, API changes |

### Pro Skills (P13-P18)

| # | Skill | What It Does |
|---|-------|-------------|
| P13 | `together-ci-integration` | GitHub Actions for model testing, fine-tuning validation |
| P14 | `together-deploy-integration` | Deploy inference endpoints to Vercel/Cloud Run |
| P15 | `together-webhooks-events` | Fine-tuning job status polling, completion callbacks |
| P16 | `together-performance-tuning` | Streaming, model warm-up, concurrent requests |
| P17 | `together-cost-tuning` | Model tier pricing, batch inference (50% off), caching |
| P18 | `together-reference-architecture` | AI service layer, model routing, fallback chains |

## Key Concepts

- **Base URL**: `https://api.together.xyz/v1` (OpenAI-compatible)
- **Models**: Llama 3.3, Mixtral, Qwen 2.5, DeepSeek V3, FLUX.1
- **Endpoints**: `/chat/completions`, `/completions`, `/embeddings`, `/images/generations`
- **Fine-tuning**: Upload JSONL, create job, monitor, deploy custom model
- **Batch**: 50% cost reduction for async processing
- **Pricing**: $0.10-5.00 per 1M tokens depending on model size

## License

MIT
