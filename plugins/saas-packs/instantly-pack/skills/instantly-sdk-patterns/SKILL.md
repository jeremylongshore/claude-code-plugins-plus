---
name: instantly-sdk-patterns
description: |
  Apply production-ready Instantly.ai API client patterns for TypeScript and Python.
  Use when building reusable API wrappers, implementing retry logic,
  or establishing coding standards for Instantly integrations.
  Trigger with phrases like "instantly SDK patterns", "instantly best practices",
  "instantly client wrapper", "instantly code patterns", "idiomatic instantly".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, instantly, patterns, typescript, python]

---
# Instantly SDK Patterns

## Overview
Production-ready patterns for Instantly API v2 integrations. Instantly has no official SDK — all integrations use direct REST calls to `https://api.instantly.ai/api/v2/`. These patterns provide type safety, retry logic, pagination, and multi-tenant support.

## Prerequisites
- Completed `instantly-install-auth` setup
- Familiarity with async/await and TypeScript generics
- Understanding of REST API pagination patterns

## Instructions

### Step 1: Type-Safe Client with Error Classification
```typescript
// src/instantly/client.ts
import "dotenv/config";

export class InstantlyClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(options?: { apiKey?: string; baseUrl?: string }) {
    this.apiKey = options?.apiKey || process.env.INSTANTLY_API_KEY || "";
    this.baseUrl = options?.baseUrl || "https://api.instantly.ai/api/v2";
    if (!this.apiKey) throw new Error("INSTANTLY_API_KEY is required");
  }

  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
        ...options.headers,
      },
    });

    if (!res.ok) {
      const body = await res.text();
      throw new InstantlyApiError(res.status, path, body);
    }

    return res.json() as Promise<T>;
  }

  // Typed convenience methods
  async getCampaigns(params?: { limit?: number; status?: number; search?: string }) {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.status !== undefined) qs.set("status", String(params.status));
    if (params?.search) qs.set("search", params.search);
    return this.request<Campaign[]>(`/campaigns?${qs}`);
  }

  async getCampaign(id: string) {
    return this.request<Campaign>(`/campaigns/${id}`);
  }

  async createCampaign(data: CreateCampaignInput) {
    return this.request<Campaign>("/campaigns", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async activateCampaign(id: string) {
    return this.request<void>(`/campaigns/${id}/activate`, { method: "POST" });
  }

  async pauseCampaign(id: string) {
    return this.request<void>(`/campaigns/${id}/pause`, { method: "POST" });
  }

  async getAccounts(params?: { limit?: number; status?: number }) {
    const qs = new URLSearchParams();
    if (params?.limit) qs.set("limit", String(params.limit));
    if (params?.status !== undefined) qs.set("status", String(params.status));
    return this.request<Account[]>(`/accounts?${qs}`);
  }

  async addLead(data: CreateLeadInput) {
    return this.request<Lead>("/leads", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listLeads(filter: ListLeadsInput) {
    return this.request<Lead[]>("/leads/list", {
      method: "POST",
      body: JSON.stringify(filter),
    });
  }

  async getCampaignAnalytics(ids: string[]) {
    const qs = ids.map((id) => `ids=${id}`).join("&");
    return this.request<CampaignAnalytics[]>(`/campaigns/analytics?${qs}`);
  }
}

// Error classification
export class InstantlyApiError extends Error {
  public retryable: boolean;

  constructor(public status: number, public path: string, public body: string) {
    super(`Instantly ${status} on ${path}: ${body}`);
    this.name = "InstantlyApiError";
    this.retryable = status === 429 || status >= 500;
  }
}
```

### Step 2: TypeScript Interfaces
```typescript
// src/instantly/types.ts
export interface Campaign {
  id: string;
  name: string;
  status: number; // 0=Draft,1=Active,2=Paused,3=Completed,4=Running Subsequences
  campaign_schedule: CampaignSchedule;
  sequences: Sequence[];
  daily_limit: number | null;
  stop_on_reply: boolean;
  email_gap: number;
  timestamp_created: string;
}

export interface CampaignSchedule {
  start_date: string | null;
  end_date: string | null;
  schedules: Array<{
    name: string;
    timing: { from: string; to: string };
    days: Record<string, boolean>;
    timezone: string;
  }>;
}

export interface Sequence {
  steps: SequenceStep[];
}

export interface SequenceStep {
  type: "email";
  delay: number;
  delay_unit?: "minutes" | "hours" | "days";
  variants: Array<{ subject: string; body: string; v_disabled?: boolean }>;
}

export interface Account {
  email: string;
  first_name: string;
  last_name: string;
  status: number;
  warmup_status: string;
  daily_limit: number | null;
  provider_code: number;
  warmup: { limit: number; increment: string; advanced: Record<string, unknown> };
}

export interface Lead {
  id: string;
  email: string | null;
  first_name: string | null;
  last_name: string | null;
  company_name: string | null;
  status: number; // 1=Active,2=Paused,3=Completed,-1=Bounced,-2=Unsubscribed,-3=Skipped
  campaign: string | null;
  email_open_count: number;
  email_reply_count: number;
}

export interface CreateCampaignInput {
  name: string;
  campaign_schedule: CampaignSchedule;
  sequences: Sequence[];
  daily_limit?: number;
  stop_on_reply?: boolean;
  email_gap?: number;
  open_tracking?: boolean;
  link_tracking?: boolean;
}

export interface CreateLeadInput {
  campaign?: string;
  list_id?: string;
  email: string;
  first_name?: string;
  last_name?: string;
  company_name?: string;
  custom_variables?: Record<string, string>;
  skip_if_in_workspace?: boolean;
  verify_leads_on_import?: boolean;
}

export interface ListLeadsInput {
  campaign?: string;
  list_id?: string;
  limit?: number;
  starting_after?: string;
}

export interface CampaignAnalytics {
  campaign_id: string;
  total_leads: number;
  emails_sent: number;
  emails_opened: number;
  emails_replied: number;
  emails_bounced: number;
}
```

### Step 3: Retry with Exponential Backoff
```typescript
// src/instantly/retry.ts
export async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  baseDelayMs = 1000
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      if (err instanceof InstantlyApiError && !err.retryable) throw err;

      const delay = baseDelayMs * Math.pow(2, attempt);
      const jitter = Math.random() * delay * 0.1;
      console.warn(`Retry ${attempt + 1}/${maxRetries} in ${delay}ms...`);
      await new Promise((r) => setTimeout(r, delay + jitter));
    }
  }
  throw new Error("Unreachable");
}

// Usage
const campaigns = await withRetry(() => client.getCampaigns({ limit: 50 }));
```

### Step 4: Cursor-Based Pagination
```typescript
// src/instantly/paginate.ts
export async function* paginate<T extends { id: string }>(
  client: InstantlyClient,
  path: string,
  pageSize = 100
): AsyncGenerator<T[], void, void> {
  let startingAfter: string | undefined;

  while (true) {
    const qs = new URLSearchParams({ limit: String(pageSize) });
    if (startingAfter) qs.set("starting_after", startingAfter);

    const page = await client.request<T[]>(`${path}?${qs}`);
    if (page.length === 0) break;

    yield page;
    startingAfter = page[page.length - 1].id;

    if (page.length < pageSize) break;
  }
}

// Usage — iterate all campaigns
for await (const batch of paginate<Campaign>(client, "/campaigns")) {
  for (const campaign of batch) {
    console.log(campaign.name, campaign.status);
  }
}
```

### Step 5: Multi-Tenant Factory (Agency Pattern)
```typescript
// src/instantly/factory.ts
const clients = new Map<string, InstantlyClient>();

export function getClientForWorkspace(workspaceId: string, apiKey: string): InstantlyClient {
  if (!clients.has(workspaceId)) {
    clients.set(workspaceId, new InstantlyClient({ apiKey }));
  }
  return clients.get(workspaceId)!;
}

// Usage — agency managing multiple client workspaces
const clientA = getClientForWorkspace("acme", process.env.ACME_API_KEY!);
const clientB = getClientForWorkspace("globex", process.env.GLOBEX_API_KEY!);
```

### Python Client
```python
# instantly/client.py
import os, time, httpx
from dataclasses import dataclass
from typing import Optional

@dataclass
class InstantlyClient:
    api_key: str = ""
    base_url: str = "https://api.instantly.ai/api/v2"

    def __post_init__(self):
        self.api_key = self.api_key or os.getenv("INSTANTLY_API_KEY", "")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            timeout=30.0,
        )

    def get(self, path: str, params: Optional[dict] = None):
        r = self._client.get(path, params=params)
        r.raise_for_status()
        return r.json()

    def post(self, path: str, json_data: Optional[dict] = None):
        r = self._client.post(path, json=json_data)
        r.raise_for_status()
        return r.json()

    def patch(self, path: str, json_data: dict):
        r = self._client.patch(path, json=json_data)
        r.raise_for_status()
        return r.json()

    def delete(self, path: str):
        r = self._client.delete(path)
        r.raise_for_status()

    def list_campaigns(self, limit: int = 50):
        return self.get("/campaigns", params={"limit": limit})

    def get_campaign_analytics(self, campaign_id: str):
        return self.get("/campaigns/analytics", params={"id": campaign_id})
```

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Error classification | All API calls | `retryable` flag prevents retrying 400/403 errors |
| Exponential backoff | 429 / 5xx errors | Respects rate limits automatically |
| Cursor pagination | Large datasets | Memory-efficient iteration |
| Multi-tenant factory | Agency/multi-workspace | Isolated clients per workspace |

## Resources
- [Instantly API v2 Docs](https://developer.instantly.ai/)
- [API Schemas](https://developer.instantly.ai/api/v2/schemas)
- [OpenAPI Spec](https://developer.instantly.ai/api-reference/openapi.json)

## Next Steps
Apply patterns in `instantly-core-workflow-a` for real-world campaign automation.
