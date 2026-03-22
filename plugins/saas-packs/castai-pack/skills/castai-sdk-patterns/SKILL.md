---
name: castai-sdk-patterns
description: |
  Production-ready CAST AI REST API wrapper patterns in TypeScript and Python.
  Use when building reusable CAST AI clients, implementing retry logic,
  or wrapping the CAST AI API for team use.
  Trigger with phrases like "cast ai API patterns", "cast ai client wrapper",
  "cast ai TypeScript", "cast ai Python client".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI SDK Patterns

## Overview

CAST AI uses a REST API with `X-API-Key` header authentication. There is no official SDK -- build typed wrappers around `fetch` or `requests`. These patterns cover singleton clients, typed responses, retry with backoff, and multi-cluster management.

## Prerequisites

- Completed `castai-install-auth` setup
- TypeScript 5+ or Python 3.10+
- Familiarity with async/await patterns

## Instructions

### Step 1: TypeScript API Client

```typescript
// src/castai/client.ts
interface CastAIConfig {
  apiKey: string;
  baseUrl?: string;
  timeoutMs?: number;
}

interface CastAICluster {
  id: string;
  name: string;
  status: string;
  providerType: "eks" | "gke" | "aks";
  agentStatus: string;
  createdAt: string;
}

interface CastAISavings {
  monthlySavings: number;
  savingsPercentage: number;
  currentMonthlyCost: number;
  optimizedMonthlyCost: number;
}

interface CastAINode {
  name: string;
  instanceType: string;
  lifecycle: "on-demand" | "spot";
  allocatableCpu: string;
  allocatableMemory: string;
  zone: string;
}

class CastAIClient {
  private apiKey: string;
  private baseUrl: string;
  private timeoutMs: number;

  constructor(config: CastAIConfig) {
    this.apiKey = config.apiKey;
    this.baseUrl = config.baseUrl ?? "https://api.cast.ai";
    this.timeoutMs = config.timeoutMs ?? 30000;
  }

  private async request<T>(path: string, options?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...options,
        headers: {
          "X-API-Key": this.apiKey,
          "Content-Type": "application/json",
          ...options?.headers,
        },
        signal: controller.signal,
      });

      if (!response.ok) {
        const body = await response.text();
        throw new CastAIError(response.status, body, path);
      }

      return response.json();
    } finally {
      clearTimeout(timeout);
    }
  }

  async listClusters(): Promise<CastAICluster[]> {
    const data = await this.request<{ items: CastAICluster[] }>(
      "/v1/kubernetes/external-clusters"
    );
    return data.items;
  }

  async getSavings(clusterId: string): Promise<CastAISavings> {
    return this.request(`/v1/kubernetes/clusters/${clusterId}/savings`);
  }

  async listNodes(clusterId: string): Promise<CastAINode[]> {
    const data = await this.request<{ items: CastAINode[] }>(
      `/v1/kubernetes/external-clusters/${clusterId}/nodes`
    );
    return data.items;
  }

  async updatePolicies(clusterId: string, policies: Record<string, unknown>): Promise<void> {
    await this.request(`/v1/kubernetes/clusters/${clusterId}/policies`, {
      method: "PUT",
      body: JSON.stringify(policies),
    });
  }
}

class CastAIError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: string,
    public readonly path: string
  ) {
    super(`CAST AI ${status} on ${path}: ${body}`);
    this.name = "CastAIError";
  }

  get retryable(): boolean {
    return this.status === 429 || this.status >= 500;
  }
}
```

### Step 2: Singleton with Retry

```typescript
// src/castai/index.ts
let instance: CastAIClient | null = null;

export function getCastAIClient(): CastAIClient {
  if (!instance) {
    if (!process.env.CASTAI_API_KEY) {
      throw new Error("CASTAI_API_KEY environment variable required");
    }
    instance = new CastAIClient({ apiKey: process.env.CASTAI_API_KEY });
  }
  return instance;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (attempt === maxRetries) throw err;
      if (err instanceof CastAIError && !err.retryable) throw err;
      const delay = 1000 * Math.pow(2, attempt) + Math.random() * 500;
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw new Error("Unreachable");
}
```

### Step 3: Python Client

```python
# castai_client.py
import os
import time
import requests
from dataclasses import dataclass
from typing import Optional

@dataclass
class CastAIConfig:
    api_key: str
    base_url: str = "https://api.cast.ai"
    timeout: int = 30

class CastAIClient:
    def __init__(self, config: Optional[CastAIConfig] = None):
        self.config = config or CastAIConfig(
            api_key=os.environ["CASTAI_API_KEY"]
        )
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.config.api_key,
            "Content-Type": "application/json",
        })

    def _get(self, path: str) -> dict:
        resp = self.session.get(
            f"{self.config.base_url}{path}",
            timeout=self.config.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def list_clusters(self) -> list[dict]:
        return self._get("/v1/kubernetes/external-clusters")["items"]

    def get_savings(self, cluster_id: str) -> dict:
        return self._get(f"/v1/kubernetes/clusters/{cluster_id}/savings")

    def list_nodes(self, cluster_id: str) -> list[dict]:
        return self._get(
            f"/v1/kubernetes/external-clusters/{cluster_id}/nodes"
        )["items"]

    def get_policies(self, cluster_id: str) -> dict:
        return self._get(f"/v1/kubernetes/clusters/{cluster_id}/policies")
```

## Error Handling

| Status | Meaning | Action |
|--------|---------|--------|
| 401 | Invalid API key | Rotate key at console.cast.ai |
| 403 | Insufficient permissions | Use Full Access key |
| 404 | Cluster not found | Verify cluster ID |
| 429 | Rate limited | Backoff and retry |
| 5xx | Server error | Retry with exponential backoff |

## Resources

- [CAST AI OpenAPI Spec](https://api.cast.ai/v1/spec/openapi.json)
- [CAST AI Terraform Provider Source](https://github.com/castai/terraform-provider-castai)

## Next Steps

Apply these patterns in `castai-core-workflow-a` to manage cluster optimization.
