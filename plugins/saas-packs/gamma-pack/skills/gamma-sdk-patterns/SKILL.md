---
name: gamma-sdk-patterns
description: |
  Reusable patterns for the Gamma REST API (no SDK exists).
  Use when building typed wrappers, generation helpers,
  template factories, or error handling for Gamma.
  Trigger: "gamma patterns", "gamma client wrapper",
  "gamma best practices", "gamma API helper", "gamma code structure".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, gamma, patterns, api]

---
# Gamma API Patterns

## Overview

Gamma has no published SDK — all interaction is via REST at `https://public-api.gamma.app/v1.0/`. This skill provides production-grade patterns for typed clients, generation helpers, polling, template workflows, and error handling.

## Prerequisites

- Completed `gamma-install-auth` setup
- TypeScript project with `fetch` (Node.js 18+)
- Understanding of the generate-poll-retrieve workflow

## Instructions

### Step 1: Typed Client Singleton

```typescript
// lib/gamma.ts
const GAMMA_BASE = "https://public-api.gamma.app/v1.0";

interface GammaConfig {
  apiKey: string;
  baseUrl?: string;
  timeoutMs?: number;
}

// Types based on actual API responses
interface GenerateRequest {
  content: string;
  outputFormat?: "presentation" | "document" | "webpage" | "social_post";
  themeId?: string;
  exportAs?: "pdf" | "pptx" | "png";
  textMode?: "generate" | "condense" | "preserve";
  textAmount?: "brief" | "medium" | "detailed" | "extensive";
  imageOptions?: { style?: string };
  sharingOptions?: {
    workspaceAccess?: "noAccess" | "view" | "comment" | "edit" | "fullAccess";
    externalAccess?: "noAccess" | "view" | "comment" | "edit" | "fullAccess";
  };
  folderIds?: string[];
}

interface GenerateResult {
  generationId: string;
  status: "in_progress" | "completed" | "failed";
  gammaUrl?: string;
  exportUrl?: string;
  creditsUsed?: number;
}

let instance: ReturnType<typeof createGammaClient> | null = null;

export function getGamma() {
  if (!instance) {
    instance = createGammaClient({
      apiKey: process.env.GAMMA_API_KEY!,
    });
  }
  return instance;
}

export function createGammaClient(config: GammaConfig) {
  const base = config.baseUrl ?? GAMMA_BASE;
  const headers: Record<string, string> = {
    "X-API-KEY": config.apiKey,
    "Content-Type": "application/json",
  };

  async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), config.timeoutMs ?? 30000);
    try {
      const res = await fetch(`${base}${path}`, {
        method,
        headers,
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });
      if (!res.ok) {
        const text = await res.text();
        throw new GammaApiError(res.status, text, path);
      }
      return res.json() as T;
    } finally {
      clearTimeout(timeout);
    }
  }

  return {
    generate: (body: GenerateRequest) =>
      request<{ generationId: string }>("POST", "/generations", body),
    generateFromTemplate: (body: TemplateRequest) =>
      request<{ generationId: string }>("POST", "/generations/from-template", body),
    poll: (id: string) =>
      request<GenerateResult>("GET", `/generations/${id}`),
    getFileUrls: (id: string) =>
      request<{ exportUrl: string }>("GET", `/generations/${id}/files`),
    listThemes: () => request<Theme[]>("GET", "/themes"),
    listFolders: () => request<Folder[]>("GET", "/folders"),
  };
}
```

### Step 2: Custom Error Class

```typescript
// lib/errors.ts
export class GammaApiError extends Error {
  constructor(
    public status: number,
    public body: string,
    public path: string
  ) {
    super(`Gamma API ${status} on ${path}: ${body}`);
    this.name = "GammaApiError";
  }

  get isRateLimit() { return this.status === 429; }
  get isAuth() { return this.status === 401 || this.status === 403; }
  get isServerError() { return this.status >= 500; }
}
```

### Step 3: Poll-Until-Done Helper

```typescript
// lib/poll.ts
export async function pollUntilDone(
  gamma: ReturnType<typeof createGammaClient>,
  generationId: string,
  opts = { intervalMs: 5000, timeoutMs: 180000 }
): Promise<GenerateResult> {
  const deadline = Date.now() + opts.timeoutMs;

  while (Date.now() < deadline) {
    const result = await gamma.poll(generationId);

    if (result.status === "completed") return result;
    if (result.status === "failed") {
      throw new Error(`Generation ${generationId} failed`);
    }

    await new Promise((r) => setTimeout(r, opts.intervalMs));
  }

  throw new Error(`Poll timeout for ${generationId} after ${opts.timeoutMs}ms`);
}
```

### Step 4: Generate-and-Wait Convenience

```typescript
// lib/generate.ts
export async function generateAndWait(
  gamma: ReturnType<typeof createGammaClient>,
  request: GenerateRequest
): Promise<GenerateResult> {
  const { generationId } = await gamma.generate(request);
  console.log(`Generation started: ${generationId}`);
  return pollUntilDone(gamma, generationId);
}

// Usage
const gamma = getGamma();
const result = await generateAndWait(gamma, {
  content: "Quarterly business review for Q1 2026",
  outputFormat: "presentation",
  themeId: "theme_abc123",
  exportAs: "pptx",
  textAmount: "medium",
  imageOptions: { style: "photorealistic corporate" },
});
console.log(`View: ${result.gammaUrl}`);
console.log(`Download: ${result.exportUrl}`);
```

### Step 5: Template-Based Generation

```typescript
// lib/templates.ts
// Uses POST /v1.0/generations/from-template
// The template gamma must contain exactly one page

interface TemplateRequest {
  gammaId: string;     // Template gamma ID (one-page template)
  prompt: string;      // Content + instructions for the template
  themeId?: string;
  exportAs?: "pdf" | "pptx" | "png";
  imageOptions?: { style?: string };
  sharingOptions?: object;
  folderIds?: string[];
}

export async function generateFromTemplate(
  gamma: ReturnType<typeof createGammaClient>,
  templateId: string,
  prompt: string,
  options: Partial<TemplateRequest> = {}
): Promise<GenerateResult> {
  const { generationId } = await gamma.generateFromTemplate({
    gammaId: templateId,
    prompt,
    ...options,
  });
  return pollUntilDone(gamma, generationId);
}
```

### Step 6: Retry with Backoff

```typescript
// lib/retry.ts
export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      if (err instanceof GammaApiError && !err.isRateLimit && !err.isServerError) {
        throw err; // Don't retry auth errors or 4xx
      }
      const delay = baseDelayMs * Math.pow(2, attempt);
      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${delay}ms`);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const result = await withRetry(() =>
  generateAndWait(gamma, { content: "My deck", outputFormat: "presentation" })
);
```

## API Endpoints Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/v1.0/generations` | Generate from text content |
| POST | `/v1.0/generations/from-template` | Generate from a template gamma |
| GET | `/v1.0/generations/{id}` | Poll generation status |
| GET | `/v1.0/generations/{id}/files` | Get export file URLs |
| GET | `/v1.0/themes` | List workspace themes |
| GET | `/v1.0/folders` | List workspace folders |

## Error Handling

| Pattern | Use Case |
|---------|----------|
| `GammaApiError` class | Typed error handling with `isRateLimit`, `isAuth`, `isServerError` |
| `withRetry()` | Auto-retry on 429/5xx with exponential backoff |
| `pollUntilDone()` | Timeout-aware polling with configurable interval |
| Singleton `getGamma()` | Consistent config across modules |

## Resources

- [Gamma API Reference](https://developers.gamma.app/reference/generate-a-gamma)
- [Generate API Parameters](https://developers.gamma.app/guides/generate-api-parameters-explained)
- [Create from Template](https://developers.gamma.app/guides/create-from-template-api-parameters-explained)

## Next Steps

Proceed to `gamma-core-workflow-a` for content generation workflows.
