---
name: flexport-sdk-patterns
description: |
  Apply production-ready Flexport API patterns for TypeScript and Python.
  Use when building typed HTTP clients, implementing pagination,
  or establishing team coding standards for Flexport logistics integration.
  Trigger: "flexport SDK patterns", "flexport best practices", "flexport client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport SDK Patterns

## Overview

Production-ready patterns for the Flexport REST API v2. Since Flexport has no official npm/pip SDK, you build typed HTTP clients. Key patterns: singleton client, paginated iteration, retry wrapper, and Zod response validation.

## Instructions

### Pattern 1: Singleton Client with Auto-Retry

```typescript
// src/flexport/client.ts
import { z } from 'zod';

class FlexportClient {
  private static instance: FlexportClient | null = null;
  private base = 'https://api.flexport.com';
  private headers: Record<string, string>;

  private constructor(apiKey: string) {
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Flexport-Version': '2',
      'Content-Type': 'application/json',
    };
  }

  static getInstance(): FlexportClient {
    if (!this.instance) {
      const key = process.env.FLEXPORT_API_KEY;
      if (!key) throw new Error('Missing FLEXPORT_API_KEY');
      this.instance = new FlexportClient(key);
    }
    return this.instance;
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const res = await fetch(`${this.base}${path}`, { ...options, headers: { ...this.headers, ...options.headers } });
    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      await new Promise(r => setTimeout(r, retryAfter * 1000));
      return this.request(path, options);  // Retry once
    }
    if (!res.ok) {
      const body = await res.text();
      throw new FlexportAPIError(res.status, body, path);
    }
    return res.json();
  }
}

class FlexportAPIError extends Error {
  constructor(public status: number, public body: string, public path: string) {
    super(`Flexport ${status} on ${path}: ${body}`);
    this.name = 'FlexportAPIError';
  }
}
```

### Pattern 2: Paginated Iterator

```typescript
// Iterate all pages of a Flexport list endpoint
async function* paginate<T>(path: string, perPage = 25): AsyncGenerator<T> {
  const client = FlexportClient.getInstance();
  let page = 1;
  while (true) {
    const separator = path.includes('?') ? '&' : '?';
    const res = await client.request<{ data: { records: T[]; total_count: number } }>(
      `${path}${separator}page=${page}&per=${perPage}`
    );
    for (const record of res.data.records) yield record;
    if (res.data.records.length < perPage) break;
    page++;
  }
}

// Usage: iterate all shipments
for await (const shipment of paginate<Shipment>('/shipments')) {
  console.log(shipment.id, shipment.status);
}
```

### Pattern 3: Zod Response Validation

```typescript
const ShipmentSchema = z.object({
  id: z.string(),
  status: z.enum(['booked', 'in_transit', 'arrived', 'delivered']),
  freight_type: z.enum(['ocean', 'air', 'trucking']),
  origin_port: z.object({ code: z.string(), name: z.string() }),
  destination_port: z.object({ code: z.string(), name: z.string() }),
  cargo_ready_date: z.string(),
  estimated_arrival_date: z.string().nullable(),
});

type Shipment = z.infer<typeof ShipmentSchema>;

async function getShipment(id: string): Promise<Shipment> {
  const client = FlexportClient.getInstance();
  const res = await client.request<{ data: unknown }>(`/shipments/${id}`);
  return ShipmentSchema.parse(res.data);  // Throws ZodError on mismatch
}
```

### Pattern 4: Python Typed Client

```python
import os, requests
from dataclasses import dataclass
from typing import Iterator

@dataclass
class Shipment:
    id: str
    status: str
    freight_type: str

class FlexportClient:
    BASE = 'https://api.flexport.com'

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {os.environ["FLEXPORT_API_KEY"]}',
            'Flexport-Version': '2',
        })

    def list_shipments(self, per: int = 25) -> Iterator[Shipment]:
        page = 1
        while True:
            r = self.session.get(f'{self.BASE}/shipments', params={'page': page, 'per': per})
            r.raise_for_status()
            records = r.json()['data']['records']
            for rec in records:
                yield Shipment(id=rec['id'], status=rec['status'], freight_type=rec['freight_type'])
            if len(records) < per:
                break
            page += 1
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | All API calls | One instance, consistent config |
| Paginator | List endpoints | No data loss from pagination |
| Zod validation | Response parsing | Catches API contract changes early |
| Error class | All failures | Structured error data for logging |

## Resources

- [Flexport API Reference](https://apidocs.flexport.com/)
- [Zod Documentation](https://zod.dev/)

## Next Steps

Apply patterns in `flexport-core-workflow-a` for real-world usage.
