---
name: flexport-local-dev-loop
description: |
  Configure Flexport local development with mock API responses and testing.
  Use when setting up a development environment, creating mock shipment data,
  or establishing a fast iteration cycle for Flexport logistics integration.
  Trigger: "flexport dev setup", "flexport local development", "flexport mock API".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Flexport integrations. Since Flexport has no official SDK, the dev loop centers on a typed HTTP client wrapper with mock responses for testing.

## Instructions

### Step 1: Project Structure

```
flexport-integration/
├── src/
│   ├── flexport/
│   │   ├── client.ts          # Typed Flexport API client
│   │   ├── types.ts           # API response types
│   │   └── mock-data.ts       # Test fixtures
│   └── index.ts
├── tests/
│   ├── flexport.test.ts       # Unit tests with mocks
│   └── integration.test.ts   # Live API tests (CI only)
├── .env.local                 # Local secrets (git-ignored)
├── .env.example
└── package.json
```

### Step 2: Typed Client Wrapper

```typescript
// src/flexport/types.ts
interface FlexportShipment {
  id: string;
  status: 'booked' | 'in_transit' | 'arrived' | 'delivered';
  freight_type: 'ocean' | 'air' | 'trucking';
  origin_port: { code: string; name: string };
  destination_port: { code: string; name: string };
  cargo_ready_date: string;
  estimated_arrival_date: string;
}

interface FlexportResponse<T> {
  data: { records: T[]; total_count: number };
}

// src/flexport/client.ts
export class FlexportClient {
  private base = 'https://api.flexport.com';
  private headers: Record<string, string>;

  constructor(apiKey: string) {
    this.headers = {
      'Authorization': `Bearer ${apiKey}`,
      'Flexport-Version': '2',
      'Content-Type': 'application/json',
    };
  }

  async listShipments(page = 1, per = 25): Promise<FlexportResponse<FlexportShipment>> {
    const res = await fetch(`${this.base}/shipments?page=${page}&per=${per}`, {
      headers: this.headers,
    });
    if (!res.ok) throw new Error(`Flexport ${res.status}: ${await res.text()}`);
    return res.json();
  }
}
```

### Step 3: Mock Data for Testing

```typescript
// src/flexport/mock-data.ts
export const mockShipment: FlexportShipment = {
  id: 'shp_test_001',
  status: 'in_transit',
  freight_type: 'ocean',
  origin_port: { code: 'CNSHA', name: 'Shanghai' },
  destination_port: { code: 'USLAX', name: 'Los Angeles' },
  cargo_ready_date: '2025-04-01',
  estimated_arrival_date: '2025-05-15',
};

export function mockFlexportFetch(path: string) {
  if (path.includes('/shipments')) {
    return { data: { records: [mockShipment], total_count: 1 } };
  }
  throw new Error(`No mock for ${path}`);
}
```

### Step 4: Vitest Unit Tests

```typescript
// tests/flexport.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FlexportClient } from '../src/flexport/client';
import { mockShipment } from '../src/flexport/mock-data';

describe('FlexportClient', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: { records: [mockShipment], total_count: 1 } }),
    }));
  });

  it('lists shipments', async () => {
    const client = new FlexportClient('test-key');
    const result = await client.listShipments();
    expect(result.data.records).toHaveLength(1);
    expect(result.data.records[0].freight_type).toBe('ocean');
  });

  it('sends correct auth header', async () => {
    const client = new FlexportClient('test-key');
    await client.listShipments();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/shipments'),
      expect.objectContaining({ headers: expect.objectContaining({ 'Flexport-Version': '2' }) }),
    );
  });
});
```

### Step 5: Dev Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "FLEXPORT_LIVE=1 vitest tests/integration.test.ts"
  }
}
```

## Resources

- [Flexport Developer Portal](https://developers.flexport.com/)
- [Vitest Documentation](https://vitest.dev/)

## Next Steps

See `flexport-sdk-patterns` for production-ready code patterns.
