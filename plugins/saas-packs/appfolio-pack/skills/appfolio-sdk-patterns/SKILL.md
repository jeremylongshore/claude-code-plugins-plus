---
name: appfolio-sdk-patterns
description: 'Apply production-ready patterns for AppFolio REST API integration.

  Trigger: "appfolio patterns".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- property-management
- appfolio
- real-estate
compatibility: Designed for Claude Code
---
# AppFolio SDK Patterns

## Overview
Production-ready patterns for the AppFolio property management REST API. AppFolio uses HTTP Basic Auth with client credentials and returns JSON responses for properties, tenants, leases, and work orders. A structured singleton client prevents credential sprawl, enforces consistent error handling, and centralizes pagination logic across all property management endpoints.

## Singleton Client
```typescript
import axios, { AxiosInstance } from 'axios';
let _client: AxiosInstance | null = null;
export function getClient(): AxiosInstance {
  if (!_client) {
    const clientId = process.env.APPFOLIO_CLIENT_ID;
    const clientSecret = process.env.APPFOLIO_CLIENT_SECRET;
    const baseURL = process.env.APPFOLIO_BASE_URL;
    if (!clientId || !clientSecret || !baseURL) throw new Error('APPFOLIO_CLIENT_ID, SECRET, and BASE_URL required');
    _client = axios.create({ baseURL, auth: { username: clientId, password: clientSecret }, timeout: 30000 });
  }
  return _client;
}
```

## Error Wrapper
```typescript
export class AppFolioError extends Error {
  constructor(public status: number, public code: string, message: string) { super(message); }
}
export async function safeCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    const status = err.response?.status ?? 0;
    if (status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    if (status === 401) throw new AppFolioError(401, 'AUTH', 'Invalid APPFOLIO_CLIENT_ID or SECRET');
    throw new AppFolioError(status, 'API_ERROR', `${operation} failed [${status}]: ${err.message}`);
  }
}
```

## Request Builder
```typescript
class AppFolioQuery {
  private params: Record<string, string> = {};
  status(s: 'active' | 'past' | 'future') { this.params.status = s; return this; }
  propertyId(id: string) { this.params.property_id = id; return this; }
  page(n: number) { this.params.page = String(n); return this; }
  perPage(n: number) { this.params.per_page = String(Math.min(n, 200)); return this; }
  since(date: string) { this.params.updated_since = date; return this; }
  build() { return this.params; }
}
// Usage: new AppFolioQuery().status('active').perPage(50).build();
```

## Response Types
```typescript
interface Property {
  id: string; name: string; property_type: 'residential' | 'commercial' | 'mixed';
  address: { street: string; city: string; state: string; zip: string };
  unit_count: number; status: string;
}
interface Tenant {
  id: string; first_name: string; last_name: string;
  email: string; phone: string; unit_id: string; lease_id: string;
}
interface Lease {
  id: string; unit_id: string; tenant_id: string;
  start_date: string; end_date: string; rent_amount: number; status: 'active' | 'expired' | 'future';
}
interface WorkOrder {
  id: string; property_id: string; unit_id: string;
  description: string; priority: 'low' | 'medium' | 'high' | 'emergency';
  status: 'open' | 'in_progress' | 'completed';
}
```

## Testing Utilities
```typescript
export function mockProperty(overrides: Partial<Property> = {}): Property {
  return { id: 'prop-001', name: 'Maple Ridge Apts', property_type: 'residential',
    address: { street: '100 Main St', city: 'Austin', state: 'TX', zip: '78701' },
    unit_count: 24, status: 'active', ...overrides };
}
export function mockLease(overrides: Partial<Lease> = {}): Lease {
  return { id: 'lease-001', unit_id: 'unit-001', tenant_id: 'ten-001',
    start_date: '2025-01-01', end_date: '2026-01-01', rent_amount: 1500, status: 'active', ...overrides };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All API calls | Prevents uncaught 4xx/5xx from crashing flows |
| Retry on 429 | Rate-limited batch imports | Reads `Retry-After` header for backoff |
| Auth validation | Client init | Throws early if credentials are missing |
| Pagination loop | Listing properties/tenants | Increment `page` until empty response |

## Resources
- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)

## Next Steps
Apply patterns in `appfolio-core-workflow-a`.
