---
name: clay-sdk-patterns
description: |
  Apply production-ready patterns for integrating with Clay via webhooks and HTTP API.
  Use when building Clay integrations, implementing webhook handlers,
  or establishing team coding standards for Clay data pipelines.
  Trigger with phrases like "clay SDK patterns", "clay best practices",
  "clay code patterns", "clay integration patterns", "clay webhook patterns".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, python, typescript]

---
# Clay Integration Patterns

## Overview

Production-ready patterns for Clay integrations. Clay does not have an official SDK -- you interact via webhooks (inbound), HTTP API enrichment columns (outbound from Clay), and the Enterprise API (programmatic lookups). These patterns wrap those interfaces into reliable, reusable code.

## Prerequisites

- Completed `clay-install-auth` setup
- Familiarity with async/await patterns
- Understanding of Clay's webhook and HTTP API model

## Instructions

### Step 1: Create a Clay Webhook Client (TypeScript)

```typescript
// src/clay/client.ts — typed wrapper for Clay webhook and Enterprise API
interface ClayConfig {
  webhookUrl: string;         // Table's webhook URL for inbound data
  enterpriseApiKey?: string;  // Enterprise API key (optional)
  baseUrl?: string;           // Default: https://api.clay.com
  maxRetries?: number;
  timeoutMs?: number;
}

class ClayClient {
  private config: Required<ClayConfig>;

  constructor(config: ClayConfig) {
    this.config = {
      baseUrl: 'https://api.clay.com',
      maxRetries: 3,
      timeoutMs: 30_000,
      enterpriseApiKey: '',
      ...config,
    };
  }

  /** Send a record to a Clay table via webhook */
  async sendToTable(data: Record<string, unknown>): Promise<void> {
    const res = await this.fetchWithRetry(this.config.webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      throw new ClayWebhookError(`Webhook failed: ${res.status}`, res.status);
    }
  }

  /** Send multiple records in sequence with rate limiting */
  async sendBatch(rows: Record<string, unknown>[], delayMs = 200): Promise<BatchResult> {
    const results: BatchResult = { sent: 0, failed: 0, errors: [] };
    for (const row of rows) {
      try {
        await this.sendToTable(row);
        results.sent++;
      } catch (err) {
        results.failed++;
        results.errors.push({ row, error: (err as Error).message });
      }
      if (delayMs > 0) await new Promise(r => setTimeout(r, delayMs));
    }
    return results;
  }

  /** Enterprise API: Enrich a person by email (Enterprise plan only) */
  async enrichPerson(email: string): Promise<PersonEnrichment> {
    if (!this.config.enterpriseApiKey) {
      throw new Error('Enterprise API key required for person enrichment');
    }
    const res = await this.fetchWithRetry(`${this.config.baseUrl}/v1/people/enrich`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.enterpriseApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    return res.json();
  }

  /** Enterprise API: Enrich a company by domain (Enterprise plan only) */
  async enrichCompany(domain: string): Promise<CompanyEnrichment> {
    if (!this.config.enterpriseApiKey) {
      throw new Error('Enterprise API key required for company enrichment');
    }
    const res = await this.fetchWithRetry(`${this.config.baseUrl}/v1/companies/enrich`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.config.enterpriseApiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ domain }),
    });
    return res.json();
  }

  private async fetchWithRetry(url: string, init: RequestInit): Promise<Response> {
    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), this.config.timeoutMs);
        const res = await fetch(url, { ...init, signal: controller.signal });
        clearTimeout(timeout);

        if (res.status === 429) {
          const retryAfter = parseInt(res.headers.get('Retry-After') || '5');
          await new Promise(r => setTimeout(r, retryAfter * 1000));
          continue;
        }
        return res;
      } catch (err) {
        if (attempt === this.config.maxRetries) throw err;
        await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
      }
    }
    throw new Error('Max retries exceeded');
  }
}
```

### Step 2: Type Definitions for Clay Data

```typescript
// src/clay/types.ts
interface PersonEnrichment {
  name?: string;
  email?: string;
  title?: string;
  company?: string;
  linkedin_url?: string;
  location?: string;
}

interface CompanyEnrichment {
  name?: string;
  domain?: string;
  industry?: string;
  employee_count?: number;
  linkedin_url?: string;
  location?: string;
  description?: string;
}

interface BatchResult {
  sent: number;
  failed: number;
  errors: Array<{ row: Record<string, unknown>; error: string }>;
}

class ClayWebhookError extends Error {
  constructor(message: string, public statusCode: number) {
    super(message);
    this.name = 'ClayWebhookError';
  }
}
```

### Step 3: Python Client

```python
# clay_client.py — Python wrapper for Clay webhook and Enterprise API
import httpx
import asyncio
from dataclasses import dataclass, field
from typing import Any

@dataclass
class ClayClient:
    webhook_url: str
    enterprise_api_key: str = ""
    base_url: str = "https://api.clay.com"
    max_retries: int = 3
    timeout: float = 30.0

    async def send_to_table(self, data: dict[str, Any]) -> None:
        """Send a single record to a Clay table via webhook."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(self.max_retries + 1):
                response = await client.post(
                    self.webhook_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "5"))
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                return
        raise Exception("Max retries exceeded")

    async def send_batch(self, rows: list[dict], delay: float = 0.2) -> dict:
        """Send multiple records with rate limiting."""
        results = {"sent": 0, "failed": 0, "errors": []}
        for row in rows:
            try:
                await self.send_to_table(row)
                results["sent"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({"row": row, "error": str(e)})
            await asyncio.sleep(delay)
        return results

    async def enrich_person(self, email: str) -> dict:
        """Enterprise API: Look up person data by email."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1/people/enrich",
                json={"email": email},
                headers={"Authorization": f"Bearer {self.enterprise_api_key}"},
            )
            response.raise_for_status()
            return response.json()
```

### Step 4: Singleton Pattern for Multi-Use

```typescript
// src/clay/instance.ts — reuse a single client across your app
let instance: ClayClient | null = null;

export function getClayClient(): ClayClient {
  if (!instance) {
    instance = new ClayClient({
      webhookUrl: process.env.CLAY_WEBHOOK_URL!,
      enterpriseApiKey: process.env.CLAY_API_KEY,
    });
  }
  return instance;
}
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Retry with backoff | 429 rate limits, network errors | Automatic recovery |
| Batch with delay | Sending many rows | Respects Clay rate limits |
| Enterprise API guard | Missing API key | Clear error before API call |
| Timeout control | Slow webhook delivery | Prevents hung connections |

## Examples

### Webhook Handler for Clay Callbacks

```typescript
// Express handler for Clay HTTP API column callbacks
app.post('/api/clay/callback', (req, res) => {
  // Respond 200 immediately (Clay expects fast response)
  res.json({ ok: true });

  // Process async
  processEnrichedData(req.body).catch(console.error);
});
```

## Resources

- [Clay University -- HTTP API Integration](https://university.clay.com/docs/http-api-integration-overview)
- [Clay University -- Webhook Guide](https://university.clay.com/docs/webhook-integration-guide)
- [Clay University -- Using Clay as an API](https://www.clay.com/university/guide/using-clay-as-an-api)

## Next Steps

Apply patterns in `clay-core-workflow-a` for real-world lead enrichment.
