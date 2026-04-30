---
name: together-deploy-integration
description: 'Together AI deploy integration for inference, fine-tuning, and model
  deployment.

  Use when working with Together AI''s OpenAI-compatible API.

  Trigger: "together deploy integration".

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
# Together AI Deploy Integration

## Overview

Deploy a containerized Together AI inference integration service with Docker. This skill covers building a production image that connects to Together's OpenAI-compatible API for running completions, embeddings, and image generation across 100+ open-source models. Includes environment configuration for model selection and batch processing, health checks that verify API key validity and model availability, and rolling update strategies for zero-downtime deployments serving real-time inference requests.

## Docker Configuration

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "src/server.py"]
```

## Environment Variables

```bash
export TOGETHER_API_KEY="tog_xxxxxxxxxxxx"
export TOGETHER_BASE_URL="https://api.together.xyz/v1"
export TOGETHER_DEFAULT_MODEL="meta-llama/Llama-3.1-8B-Instruct"
export TOGETHER_MAX_TOKENS="2048"
export LOG_LEVEL="info"
export PORT="8000"
```

## Health Check Endpoint

```typescript
import express from 'express';

const app = express();

app.get('/health', async (req, res) => {
  try {
    const response = await fetch(`${process.env.TOGETHER_BASE_URL}/models`, {
      headers: { 'Authorization': `Bearer ${process.env.TOGETHER_API_KEY}` },
    });
    if (!response.ok) throw new Error(`Together API returned ${response.status}`);
    res.json({ status: 'healthy', service: 'together-integration', model: process.env.TOGETHER_DEFAULT_MODEL, timestamp: new Date().toISOString() });
  } catch (error) {
    res.status(503).json({ status: 'unhealthy', error: (error as Error).message });
  }
});
```

## Deployment Steps

### Step 1: Build

```bash
docker build -t together-integration:latest .
```

### Step 2: Run

```bash
docker run -d --name together-integration \
  -p 8000:8000 \
  -e TOGETHER_API_KEY -e TOGETHER_BASE_URL -e TOGETHER_DEFAULT_MODEL \
  together-integration:latest
```

### Step 3: Verify

```bash
curl -s http://localhost:8000/health | jq .
```

### Step 4: Rolling Update

```bash
docker build -t together-integration:v2 . && \
docker stop together-integration && \
docker rm together-integration && \
docker run -d --name together-integration -p 8000:8000 \
  -e TOGETHER_API_KEY -e TOGETHER_BASE_URL -e TOGETHER_DEFAULT_MODEL \
  together-integration:v2
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate key at api.together.xyz/settings |
| `Model not found` | Wrong model ID string | List models with `GET /v1/models` or check docs |
| `429 Rate Limited` | Exceeding requests per minute | Implement backoff; use batch inference for 50% cost savings |
| `500 Server Error` | Model overloaded or unavailable | Retry with exponential backoff; try alternate model |
| Slow inference | Model cold start on first request | Use a smaller model or keep-alive with periodic requests |

## Resources

- [Together AI Docs](https://docs.together.ai/)
- [API Reference](https://docs.together.ai/reference/chat-completions-1)
- [Model List](https://docs.together.ai/docs/inference-models)

## Next Steps

See `together-webhooks-events`.
