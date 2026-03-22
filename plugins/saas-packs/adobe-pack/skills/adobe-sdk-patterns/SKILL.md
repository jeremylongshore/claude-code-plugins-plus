---
name: adobe-sdk-patterns
description: |
  Apply production-ready patterns for Adobe Firefly Services SDK, PDF Services SDK,
  and raw REST API usage in TypeScript and Python.
  Use when implementing Adobe integrations, refactoring SDK usage,
  or establishing team coding standards for Adobe APIs.
  Trigger with phrases like "adobe SDK patterns", "adobe best practices",
  "adobe code patterns", "idiomatic adobe", "adobe typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe SDK Patterns

## Overview

Production-ready patterns for Adobe SDK usage across Firefly Services (`@adobe/firefly-apis`, `@adobe/photoshop-apis`, `@adobe/lightroom-apis`), PDF Services (`@adobe/pdfservices-node-sdk`), and direct REST API calls.

## Prerequisites

- Completed `adobe-install-auth` setup
- Familiarity with async/await patterns
- Understanding of the Adobe API you are integrating

## Instructions

### Pattern 1: Singleton Auth Client with Token Caching

```typescript
// src/adobe/client.ts
import { ServicePrincipalCredentials, PDFServices } from '@adobe/pdfservices-node-sdk';

let pdfServicesInstance: PDFServices | null = null;
let tokenCache: { token: string; expiresAt: number } | null = null;

export function getPDFServices(): PDFServices {
  if (!pdfServicesInstance) {
    const credentials = new ServicePrincipalCredentials({
      clientId: process.env.ADOBE_CLIENT_ID!,
      clientSecret: process.env.ADOBE_CLIENT_SECRET!,
    });
    pdfServicesInstance = new PDFServices({ credentials });
  }
  return pdfServicesInstance;
}

export async function getAccessToken(): Promise<string> {
  if (tokenCache && tokenCache.expiresAt > Date.now() + 300_000) {
    return tokenCache.token;
  }

  const res = await fetch('https://ims-na1.adobelogin.com/ims/token/v3', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      client_id: process.env.ADOBE_CLIENT_ID!,
      client_secret: process.env.ADOBE_CLIENT_SECRET!,
      grant_type: 'client_credentials',
      scope: process.env.ADOBE_SCOPES!,
    }),
  });

  if (!res.ok) throw new Error(`Adobe IMS token error: ${res.status}`);
  const data = await res.json();
  tokenCache = { token: data.access_token, expiresAt: Date.now() + data.expires_in * 1000 };
  return tokenCache.token;
}
```

### Pattern 2: Typed API Wrapper with Error Classification

```typescript
// src/adobe/firefly-client.ts
export class AdobeApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly retryAfter?: number
  ) {
    super(message);
    this.name = 'AdobeApiError';
  }
}

export async function adobeApiFetch<T>(
  url: string,
  options: RequestInit & { apiKey?: string }
): Promise<T> {
  const token = await getAccessToken();
  const { apiKey, ...fetchOptions } = options;

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      'Authorization': `Bearer ${token}`,
      'x-api-key': apiKey || process.env.ADOBE_CLIENT_ID!,
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    },
  });

  if (!response.ok) {
    const body = await response.text();
    const retryAfter = response.headers.get('Retry-After');
    throw new AdobeApiError(
      `Adobe API ${response.status}: ${body}`,
      response.status,
      response.status === 429 ? 'RATE_LIMITED' :
      response.status === 401 ? 'AUTH_EXPIRED' :
      response.status >= 500 ? 'SERVER_ERROR' : 'CLIENT_ERROR',
      response.status === 429 || response.status >= 500,
      retryAfter ? parseInt(retryAfter) : undefined
    );
  }

  return response.json();
}
```

### Pattern 3: Retry with Exponential Backoff

```typescript
// src/adobe/retry.ts
export async function withRetry<T>(
  operation: () => Promise<T>,
  config = { maxRetries: 3, baseDelayMs: 1000 }
): Promise<T> {
  for (let attempt = 0; attempt <= config.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err: any) {
      if (attempt === config.maxRetries) throw err;

      // Only retry on transient errors
      if (err instanceof AdobeApiError && !err.retryable) throw err;

      // Honor Retry-After header from Adobe
      const delay = err.retryAfter
        ? err.retryAfter * 1000
        : config.baseDelayMs * Math.pow(2, attempt) + Math.random() * 500;

      console.warn(`Adobe retry ${attempt + 1}/${config.maxRetries} in ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Pattern 4: Job Polling for Async APIs (Photoshop, Lightroom)

```typescript
// src/adobe/polling.ts — Photoshop/Lightroom APIs are async (submit job, poll status)
interface AdobeJobStatus {
  status: 'pending' | 'running' | 'succeeded' | 'failed';
  _links?: { self: { href: string } };
  output?: any;
  error?: { code: string; message: string };
}

export async function pollAdobeJob(
  statusUrl: string,
  options = { intervalMs: 2000, timeoutMs: 120_000 }
): Promise<AdobeJobStatus> {
  const token = await getAccessToken();
  const deadline = Date.now() + options.timeoutMs;

  while (Date.now() < deadline) {
    const res = await fetch(statusUrl, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
      },
    });

    const status: AdobeJobStatus = await res.json();

    if (status.status === 'succeeded') return status;
    if (status.status === 'failed') {
      throw new Error(`Adobe job failed: ${status.error?.message || 'Unknown error'}`);
    }

    await new Promise(r => setTimeout(r, options.intervalMs));
  }

  throw new Error('Adobe job polling timeout');
}
```

### Pattern 5: Zod Validation for API Responses

```typescript
import { z } from 'zod';

const FireflyImageOutputSchema = z.object({
  outputs: z.array(z.object({
    image: z.object({
      url: z.string().url(),
    }),
    seed: z.number(),
  })),
});

const PhotoshopJobSchema = z.object({
  status: z.enum(['pending', 'running', 'succeeded', 'failed']),
  _links: z.object({
    self: z.object({ href: z.string().url() }),
  }).optional(),
});

// Usage
const raw = await adobeApiFetch<unknown>(fireflyUrl, { method: 'POST', body });
const validated = FireflyImageOutputSchema.parse(raw);
```

## Output

- Type-safe client singleton with token caching
- Error classification (retryable vs permanent)
- Automatic retry with Adobe `Retry-After` header support
- Async job polling for Photoshop/Lightroom operations
- Zod runtime validation for API responses

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Token caching | All API calls | Avoids redundant IMS token requests |
| Error classification | Retry decisions | Only retries transient failures |
| Job polling | Photoshop/Lightroom | Handles async operation lifecycle |
| Zod validation | All responses | Catches API contract changes at runtime |

## Resources

- [Firefly Services SDK GitHub](https://github.com/Firefly-Services/firefly-services-sdk-js)
- [PDF Services Node SDK](https://www.npmjs.com/package/@adobe/pdfservices-node-sdk)
- [Firefly API Reference](https://developer.adobe.com/firefly-services/docs/firefly-api/api/)
- [Photoshop API Reference](https://developer.adobe.com/firefly-services/docs/photoshop/api/)

## Next Steps

Apply patterns in `adobe-core-workflow-a` for real-world usage.
