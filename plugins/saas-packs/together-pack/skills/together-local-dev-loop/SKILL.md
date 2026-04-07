---
name: together-local-dev-loop
description: |
  Together AI local dev loop for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together local dev loop".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Local Dev Loop

## Overview
Local development workflow for Together AI inference API integration. Provides a fast feedback loop with mock chat completions, embeddings, and model listing endpoints so you can build AI-powered applications without consuming live API credits. Together AI is OpenAI-compatible, so the same client libraries work with both. Toggle between mock mode for rapid iteration and live mode for model evaluation.

## Environment Setup
```bash
cp .env.example .env
# Set your credentials:
# TOGETHER_API_KEY=tog_xxxxxxxxxxxx
# TOGETHER_BASE_URL=https://api.together.xyz/v1
# MOCK_MODE=true
npm install express axios dotenv tsx typescript @types/node
npm install -D vitest supertest @types/express
# Or for Python: pip install together openai httpx pytest
```

## Dev Server
```typescript
// src/dev/server.ts
import express from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
const app = express();
app.use(express.json());
const MOCK = process.env.MOCK_MODE === "true";
if (!MOCK) {
  app.use("/v1", createProxyMiddleware({
    target: process.env.TOGETHER_BASE_URL,
    changeOrigin: true,
    headers: { Authorization: `Bearer ${process.env.TOGETHER_API_KEY}` },
  }));
} else {
  const { mountMockRoutes } = require("./mocks");
  mountMockRoutes(app);
}
app.listen(3009, () => console.log(`Together dev server on :3009 [mock=${MOCK}]`));
```

## Mock Mode
```typescript
// src/dev/mocks.ts — OpenAI-compatible mock responses for inference
export function mountMockRoutes(app: any) {
  app.post("/v1/chat/completions", (req: any, res: any) => res.json({
    id: "chatcmpl-mock-001", object: "chat.completion", model: req.body.model || "meta-llama/Llama-3-70b-chat-hf",
    choices: [{ index: 0, message: { role: "assistant", content: "This is a mock response from Together AI." }, finish_reason: "stop" }],
    usage: { prompt_tokens: 25, completion_tokens: 12, total_tokens: 37 },
  }));
  app.post("/v1/embeddings", (req: any, res: any) => res.json({
    object: "list", model: req.body.model || "togethercomputer/m2-bert-80M-8k-retrieval",
    data: [{ object: "embedding", index: 0, embedding: Array(768).fill(0).map(() => Math.random() * 2 - 1) }],
  }));
  app.get("/v1/models", (_req: any, res: any) => res.json({
    data: [
      { id: "meta-llama/Llama-3-70b-chat-hf", type: "chat", context_length: 8192 },
      { id: "mistralai/Mixtral-8x22B-Instruct-v0.1", type: "chat", context_length: 65536 },
      { id: "togethercomputer/m2-bert-80M-8k-retrieval", type: "embedding", context_length: 8192 },
    ],
  }));
}
```

## Testing Workflow
```bash
npm run dev:mock &                    # Start mock server in background
npm run test                          # Unit tests with vitest
npm run test -- --watch               # Watch mode for rapid iteration
MOCK_MODE=false npm run test:integration  # Integration test against real API
```

## Debug Tips
- Together AI is OpenAI-compatible — set `base_url` to `http://localhost:3009/v1` for local dev
- Use `/v1/models` to discover available model IDs instead of hardcoding them
- Monitor `usage.total_tokens` in responses to estimate costs before switching to live mode
- Batch inference (`/v1/batch`) runs at 50% cost but is async — poll for completion
- Set `max_tokens` explicitly to avoid unexpectedly large responses and costs

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid API key | Regenerate at api.together.xyz dashboard |
| `404 Model not found` | Wrong model ID string | Use `client.models.list()` to verify |
| `429 Rate Limited` | Too many requests per minute | Implement exponential backoff |
| `500 Server Error` | Model overloaded or cold start | Retry with backoff after 5s |
| `ECONNREFUSED :3009` | Dev server not running | Run `npm run dev:mock` first |

## Resources
- [Together AI Docs](https://docs.together.ai/)
- [API Reference](https://docs.together.ai/reference/chat-completions-1)
- [Model List](https://docs.together.ai/docs/inference-models)

## Next Steps
See `together-debug-bundle`.
