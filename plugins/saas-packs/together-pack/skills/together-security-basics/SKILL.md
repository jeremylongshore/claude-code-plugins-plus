---
name: together-security-basics
description: |
  Together AI security basics for inference, fine-tuning, and model deployment.
  Use when working with Together AI's OpenAI-compatible API.
  Trigger: "together security basics".
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, inference, together]
compatible-with: claude-code
---

# Together AI Security Basics

## Overview
Together AI provides inference and fine-tuning for 100+ open-source models (Llama, Mixtral, Qwen, FLUX) via an OpenAI-compatible API. Security concerns include API key management for production inference, protecting fine-tuning datasets that may contain proprietary or sensitive data, rate limit handling to prevent cost overruns, and ensuring model outputs are not logged with sensitive prompt content. A leaked API key grants full access to inference, fine-tuning, and model management endpoints.

## API Key Management
```typescript
function createTogetherClient(): { apiKey: string; baseUrl: string } {
  const apiKey = process.env.TOGETHER_API_KEY;
  if (!apiKey) {
    throw new Error("Missing TOGETHER_API_KEY — store in secrets manager, never in code");
  }
  // Together keys access inference + fine-tuning — treat as production credentials
  console.log("Together AI client initialized (key suffix:", apiKey.slice(-4), ")");
  return { apiKey, baseUrl: "https://api.together.xyz/v1" };
}
```

## Webhook Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyTogetherWebhook(req: Request, res: Response, next: NextFunction): void {
  const signature = req.headers["x-together-signature"] as string;
  const secret = process.env.TOGETHER_WEBHOOK_SECRET!;
  const expected = crypto.createHmac("sha256", secret).update(req.body).digest("hex");
  if (!signature || !crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    res.status(401).send("Invalid signature");
    return;
  }
  next();
}
```

## Input Validation
```typescript
import { z } from "zod";

const InferenceRequestSchema = z.object({
  model: z.string().min(1).max(200),
  messages: z.array(z.object({
    role: z.enum(["system", "user", "assistant"]),
    content: z.string().max(100_000),
  })).min(1),
  max_tokens: z.number().int().min(1).max(4096).default(512),
  temperature: z.number().min(0).max(2).default(0.7),
  stop: z.array(z.string()).max(4).optional(),
});

function validateInferenceRequest(data: unknown) {
  return InferenceRequestSchema.parse(data);
}
```

## Data Protection
```typescript
const TOGETHER_SENSITIVE_FIELDS = ["api_key", "prompt_content", "fine_tune_dataset", "model_output", "system_prompt"];

function redactTogetherLog(record: Record<string, unknown>): Record<string, unknown> {
  const redacted = { ...record };
  for (const field of TOGETHER_SENSITIVE_FIELDS) {
    if (field in redacted) redacted[field] = "[REDACTED]";
  }
  return redacted;
}
```

## Security Checklist
- [ ] API key stored in secrets manager, never in source code
- [ ] Separate keys for dev/staging/prod environments
- [ ] Fine-tuning datasets reviewed for sensitive content before upload
- [ ] Prompt content and model outputs never logged in plaintext
- [ ] Rate limit handling with exponential backoff to prevent cost overruns
- [ ] API key rotation scheduled quarterly
- [ ] Pre-commit hook blocks `TOGETHER_API_KEY` patterns
- [ ] Model access scoped to required models only

## Error Handling
| Vulnerability | Risk | Mitigation |
|---|---|---|
| Leaked API key | Unauthorized inference and fine-tuning access | Secrets manager + rotation |
| Sensitive data in fine-tuning datasets | Proprietary data embedded in model weights | Dataset review + sanitization before upload |
| Prompt content in logs | Confidential queries exposed | Field-level redaction pipeline |
| Missing rate limit handling | Unexpected cost overruns from runaway requests | Exponential backoff + spending alerts |
| Unrestricted model access | Cost from premium model usage | API key scoped to approved models |

## Resources
- [Together AI Docs](https://docs.together.ai/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)

## Next Steps
See `together-prod-checklist`.
