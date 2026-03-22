---
name: ideogram-sdk-patterns
description: |
  Apply production-ready Ideogram API patterns for TypeScript and Python.
  Use when implementing Ideogram integrations, refactoring API usage,
  or establishing team coding standards for Ideogram.
  Trigger with phrases like "ideogram SDK patterns", "ideogram best practices",
  "ideogram code patterns", "idiomatic ideogram", "ideogram wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, ideogram, python, typescript, patterns]

---
# Ideogram SDK Patterns

## Overview
Production-ready patterns for Ideogram's REST API. Since Ideogram has no official SDK, these patterns provide type-safe wrappers, retry logic, response validation, and multi-tenant support for the `api.ideogram.ai` endpoints.

## Prerequisites
- Completed `ideogram-install-auth` setup
- Familiarity with async/await and fetch API
- Understanding of Ideogram response lifecycle (URLs expire)

## Instructions

### Step 1: Singleton Client with Auto-Download
```typescript
// src/ideogram/client.ts
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const API_BASE = "https://api.ideogram.ai";

let instance: IdeogramClient | null = null;

export function getIdeogramClient(): IdeogramClient {
  if (!instance) {
    const key = process.env.IDEOGRAM_API_KEY;
    if (!key) throw new Error("IDEOGRAM_API_KEY not set");
    instance = new IdeogramClient(key);
  }
  return instance;
}

export class IdeogramClient {
  constructor(private apiKey: string) {}

  async generate(prompt: string, options: {
    model?: string;
    style_type?: string;
    aspect_ratio?: string;
    negative_prompt?: string;
    magic_prompt_option?: string;
    num_images?: number;
    seed?: number;
  } = {}) {
    const response = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Api-Key": this.apiKey, "Content-Type": "application/json" },
      body: JSON.stringify({
        image_request: {
          prompt,
          model: options.model ?? "V_2",
          style_type: options.style_type ?? "AUTO",
          aspect_ratio: options.aspect_ratio ?? "ASPECT_1_1",
          magic_prompt_option: options.magic_prompt_option ?? "AUTO",
          negative_prompt: options.negative_prompt,
          num_images: options.num_images ?? 1,
          seed: options.seed,
        },
      }),
    });
    return this.handleResponse(response);
  }

  async describe(imagePath: string) {
    const form = new FormData();
    const file = new Blob([await import("fs").then(fs => fs.readFileSync(imagePath))]);
    form.append("image_file", file, "image.png");
    const response = await fetch(`${API_BASE}/describe`, {
      method: "POST",
      headers: { "Api-Key": this.apiKey },
      body: form,
    });
    return this.handleResponse(response);
  }

  async downloadImage(url: string, outputDir: string, filename?: string): Promise<string> {
    mkdirSync(outputDir, { recursive: true });
    const imgResponse = await fetch(url);
    if (!imgResponse.ok) throw new Error(`Download failed: ${imgResponse.status}`);
    const buffer = Buffer.from(await imgResponse.arrayBuffer());
    const outPath = join(outputDir, filename ?? `ideogram-${Date.now()}.png`);
    writeFileSync(outPath, buffer);
    return outPath;
  }

  private async handleResponse(response: Response) {
    if (!response.ok) {
      const body = await response.text();
      throw new IdeogramApiError(response.status, body);
    }
    return response.json();
  }
}

export class IdeogramApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`Ideogram ${status}: ${body}`);
    this.name = "IdeogramApiError";
  }
  get isRateLimited() { return this.status === 429; }
  get isSafetyRejected() { return this.status === 422; }
  get isAuthError() { return this.status === 401; }
}
```

### Step 2: Retry with Exponential Backoff
```typescript
export async function withRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 3, baseDelayMs: 1000, maxDelayMs: 30000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      if (attempt === config.maxRetries) throw err;
      // Only retry on 429 (rate limit) or 5xx (server error)
      const status = err.status ?? err.response?.status;
      if (status && status !== 429 && status < 500) throw err;

      const delay = Math.min(
        config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500,
        config.maxDelayMs
      );
      console.warn(`Ideogram retry ${attempt + 1}/${config.maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage: await withRetry(() => client.generate("a sunset"));
```

### Step 3: Response Validation with Zod
```typescript
import { z } from "zod";

const ImageResultSchema = z.object({
  url: z.string().url(),
  prompt: z.string(),
  resolution: z.string(),
  is_image_safe: z.boolean(),
  seed: z.number(),
  style_type: z.string().optional(),
});

const GenerateResponseSchema = z.object({
  created: z.string(),
  data: z.array(ImageResultSchema).min(1),
});

export function validateGenerateResponse(raw: unknown) {
  return GenerateResponseSchema.parse(raw);
}
```

### Step 4: Python Client
```python
# ideogram_client.py
import os, requests, hashlib, time
from pathlib import Path

class IdeogramClient:
    BASE_URL = "https://api.ideogram.ai"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("IDEOGRAM_API_KEY", "")
        if not self.api_key:
            raise ValueError("IDEOGRAM_API_KEY required")

    def generate(self, prompt: str, model="V_2", style_type="AUTO",
                 aspect_ratio="ASPECT_1_1", **kwargs) -> dict:
        resp = requests.post(f"{self.BASE_URL}/generate", headers=self._headers(),
            json={"image_request": {"prompt": prompt, "model": model,
                "style_type": style_type, "aspect_ratio": aspect_ratio,
                "magic_prompt_option": kwargs.get("magic_prompt", "AUTO"),
                **{k: v for k, v in kwargs.items() if k != "magic_prompt"}}})
        resp.raise_for_status()
        return resp.json()

    def download(self, url: str, output_dir: str = "./images") -> str:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        resp = requests.get(url)
        resp.raise_for_status()
        path = f"{output_dir}/ideogram-{int(time.time())}.png"
        Path(path).write_bytes(resp.content)
        return path

    def _headers(self):
        return {"Api-Key": self.api_key, "Content-Type": "application/json"}
```

### Step 5: Multi-Tenant Factory
```typescript
const tenantClients = new Map<string, IdeogramClient>();

export function getClientForTenant(tenantId: string): IdeogramClient {
  if (!tenantClients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId); // from your secret store
    tenantClients.set(tenantId, new IdeogramClient(apiKey));
  }
  return tenantClients.get(tenantId)!;
}
```

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | Shared client across modules | Single connection, consistent config |
| Retry wrapper | Rate limits and transient errors | Automatic recovery from 429/5xx |
| Zod validation | Response validation | Catches API changes at parse time |
| Auto-download | Image persistence | Prevents URL expiry data loss |
| Multi-tenant | SaaS platforms | Per-customer API key isolation |

## Output
- Type-safe client singleton with generate and describe methods
- Retry logic with exponential backoff and jitter
- Runtime validation for API responses
- Auto-download to prevent URL expiration issues

## Resources
- [Ideogram API Reference](https://developer.ideogram.ai/api-reference)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `ideogram-core-workflow-a` for real-world usage.
