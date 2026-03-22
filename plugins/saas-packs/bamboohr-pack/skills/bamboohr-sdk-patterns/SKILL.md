---
name: bamboohr-sdk-patterns
description: |
  Apply production-ready BambooHR API patterns for TypeScript and Python.
  Use when implementing BambooHR integrations, building reusable clients,
  or establishing team coding standards for BambooHR REST API.
  Trigger with phrases like "bamboohr SDK patterns", "bamboohr best practices",
  "bamboohr code patterns", "idiomatic bamboohr", "bamboohr client wrapper".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hr, bamboohr, patterns]
compatible-with: claude-code
---

# BambooHR SDK Patterns

## Overview

Production-ready patterns for the BambooHR REST API. BambooHR has no official Node.js SDK — you call the API directly via `fetch` or `axios`. These patterns wrap the raw HTTP calls into type-safe, retry-aware, multi-tenant-ready code.

## Prerequisites

- Completed `bamboohr-install-auth` setup
- Familiarity with async/await and TypeScript generics

## Instructions

### Step 1: Type-Safe Client with Error Handling

```typescript
// src/bamboohr/client.ts
import 'dotenv/config';

export interface BambooHRConfig {
  companyDomain: string;
  apiKey: string;
  timeoutMs?: number;
}

export interface BambooEmployee {
  id: string;
  firstName: string;
  lastName: string;
  displayName: string;
  jobTitle: string;
  department: string;
  division: string;
  workEmail: string;
  location: string;
  status: string;
  hireDate: string;
  supervisor: string;
  employeeNumber: string;
  photoUrl?: string;
}

export class BambooHRClient {
  private base: string;
  private auth: string;
  private timeout: number;

  constructor(config: BambooHRConfig) {
    this.base = `https://api.bamboohr.com/api/gateway.php/${config.companyDomain}/v1`;
    this.auth = `Basic ${Buffer.from(`${config.apiKey}:x`).toString('base64')}`;
    this.timeout = config.timeoutMs ?? 30_000;
  }

  async request<T>(method: string, path: string, body?: unknown): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), this.timeout);

    try {
      const res = await fetch(`${this.base}${path}`, {
        method,
        headers: {
          Authorization: this.auth,
          Accept: 'application/json',
          ...(body ? { 'Content-Type': 'application/json' } : {}),
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      if (!res.ok) {
        const errMsg = res.headers.get('X-BambooHR-Error-Message') || res.statusText;
        throw new BambooHRApiError(res.status, errMsg, path, {
          retryAfter: res.headers.get('Retry-After'),
        });
      }

      // Some endpoints return 200 with no body (e.g., PUT updates)
      const text = await res.text();
      return text ? JSON.parse(text) : ({} as T);
    } finally {
      clearTimeout(timer);
    }
  }

  // ── Employee endpoints ────────────────────────────────
  async getEmployee(id: number | string, fields: string[]) {
    return this.request<Record<string, string>>('GET', `/employees/${id}/?fields=${fields.join(',')}`);
  }

  async getDirectory() {
    return this.request<{ fields: any[]; employees: BambooEmployee[] }>('GET', '/employees/directory');
  }

  async addEmployee(data: { firstName: string; lastName: string; [k: string]: string }) {
    return this.request<{ headers: { location: string } }>('POST', '/employees/', data);
  }

  async updateEmployee(id: number | string, data: Record<string, string>) {
    return this.request<void>('POST', `/employees/${id}/`, data);
  }

  // ── Reports ───────────────────────────────────────────
  async customReport(fields: string[], filters?: Record<string, any>) {
    return this.request<{ title: string; employees: Record<string, string>[] }>(
      'POST', '/reports/custom?format=JSON',
      { title: 'Custom Report', fields, filters },
    );
  }

  // ── Time Off ──────────────────────────────────────────
  async getTimeOffRequests(start: string, end: string, status?: string) {
    const params = new URLSearchParams({ start, end, ...(status && { status }) });
    return this.request<any[]>('GET', `/time_off/requests/?${params}`);
  }

  // ── Tables (job history, compensation, etc.) ──────────
  async getTableRows(employeeId: number | string, table: string) {
    return this.request<any[]>('GET', `/employees/${employeeId}/tables/${table}`);
  }

  async addTableRow(employeeId: number | string, table: string, data: Record<string, string>) {
    return this.request<void>('POST', `/employees/${employeeId}/tables/${table}`, data);
  }
}

export class BambooHRApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public path: string,
    public meta: { retryAfter?: string | null } = {},
  ) {
    super(`BambooHR ${status}: ${message} [${path}]`);
    this.name = 'BambooHRApiError';
  }

  get retryable(): boolean {
    return this.status === 429 || this.status === 503 || this.status >= 500;
  }
}
```

### Step 2: Retry Wrapper with Exponential Backoff

```typescript
// src/bamboohr/retry.ts
import { BambooHRApiError } from './client';

export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseMs = 1000,
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === maxRetries) throw err;

      // Only retry on retryable errors
      if (err instanceof BambooHRApiError && !err.retryable) throw err;

      // Honor Retry-After header if present (BambooHR sends this on 503)
      const retryAfter = err instanceof BambooHRApiError ? err.meta.retryAfter : null;
      const delay = retryAfter
        ? parseInt(retryAfter, 10) * 1000
        : baseMs * Math.pow(2, attempt) + Math.random() * 500;

      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${delay.toFixed(0)}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('unreachable');
}
```

### Step 3: Multi-Tenant Factory

```typescript
// src/bamboohr/factory.ts
import { BambooHRClient, BambooHRConfig } from './client';

const tenantClients = new Map<string, BambooHRClient>();

export function getClientForTenant(tenantDomain: string, apiKey: string): BambooHRClient {
  if (!tenantClients.has(tenantDomain)) {
    tenantClients.set(tenantDomain, new BambooHRClient({ companyDomain: tenantDomain, apiKey }));
  }
  return tenantClients.get(tenantDomain)!;
}

// Cleanup on hot reload
export function clearTenantClients() {
  tenantClients.clear();
}
```

### Step 4: Zod Response Validation

```typescript
import { z } from 'zod';

const EmployeeSchema = z.object({
  id: z.string(),
  firstName: z.string(),
  lastName: z.string(),
  displayName: z.string(),
  jobTitle: z.string().default(''),
  department: z.string().default(''),
  workEmail: z.string().email().optional(),
  status: z.enum(['Active', 'Inactive']).default('Active'),
  hireDate: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
});

const DirectorySchema = z.object({
  employees: z.array(EmployeeSchema),
});

// Usage: validate API responses at runtime
const raw = await client.getDirectory();
const validated = DirectorySchema.parse(raw);  // throws ZodError on mismatch
```

### Python Equivalent

```python
import os, requests
from dataclasses import dataclass
from typing import Optional

@dataclass
class BambooHRClient:
    company_domain: str = ""
    api_key: str = ""

    def __post_init__(self):
        self.company_domain = self.company_domain or os.environ["BAMBOOHR_COMPANY_DOMAIN"]
        self.api_key = self.api_key or os.environ["BAMBOOHR_API_KEY"]
        self.base = f"https://api.bamboohr.com/api/gateway.php/{self.company_domain}/v1"
        self.session = requests.Session()
        self.session.auth = (self.api_key, "x")
        self.session.headers.update({"Accept": "application/json"})

    def get_employee(self, emp_id: int, fields: list[str]) -> dict:
        r = self.session.get(f"{self.base}/employees/{emp_id}/",
                             params={"fields": ",".join(fields)})
        r.raise_for_status()
        return r.json()

    def get_directory(self) -> dict:
        r = self.session.get(f"{self.base}/employees/directory")
        r.raise_for_status()
        return r.json()

    def custom_report(self, fields: list[str]) -> dict:
        r = self.session.post(f"{self.base}/reports/custom",
                              params={"format": "JSON"},
                              json={"title": "Report", "fields": fields})
        r.raise_for_status()
        return r.json()
```

## Output

- Type-safe client with all major BambooHR endpoints
- Custom error class with `retryable` flag and `Retry-After` support
- Exponential backoff retry wrapper
- Multi-tenant factory pattern
- Zod runtime validation for API responses

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| `BambooHRApiError` | All API calls | Structured errors with HTTP status |
| `withRetry()` | 429/5xx transient failures | Automatic recovery |
| Zod schemas | Response validation | Catch API changes early |
| Multi-tenant factory | SaaS/multi-company | Isolated credentials per tenant |

## Resources

- [BambooHR API Technical Overview](https://documentation.bamboohr.com/docs/api-details)
- [BambooHR Field Names](https://documentation.bamboohr.com/docs/list-of-field-names)
- [Zod Documentation](https://zod.dev/)

## Next Steps

Apply these patterns in `bamboohr-core-workflow-a` for employee management workflows.
