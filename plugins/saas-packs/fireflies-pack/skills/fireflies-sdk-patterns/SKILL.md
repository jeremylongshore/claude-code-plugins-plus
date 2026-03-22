---
name: fireflies-sdk-patterns
description: |
  Apply production-ready Fireflies.ai GraphQL client patterns for TypeScript and Python.
  Use when implementing Fireflies.ai integrations, building typed clients,
  or establishing team coding standards for the GraphQL API.
  Trigger with phrases like "fireflies SDK patterns", "fireflies best practices",
  "fireflies client", "fireflies GraphQL wrapper", "typed fireflies".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, fireflies, python, typescript]

---
# Fireflies.ai Client Patterns

## Overview
Production-ready patterns for the Fireflies.ai GraphQL API. Fireflies has no official SDK -- all interaction is via HTTP POST to `https://api.fireflies.ai/graphql`. These patterns provide typed wrappers, error handling, caching, and multi-tenant support.

## Prerequisites
- `FIREFLIES_API_KEY` environment variable set
- TypeScript 5+ or Python 3.10+
- Optional: `graphql-request` for typed queries

## Instructions

### Step 1: Typed GraphQL Client (TypeScript)
```typescript
// lib/fireflies-client.ts
const FIREFLIES_API = "https://api.fireflies.ai/graphql";

interface FirefliesError {
  message: string;
  code?: string;
  extensions?: { status: number; helpUrls?: string[] };
}

interface FirefliesResponse<T> {
  data?: T;
  errors?: FirefliesError[];
}

export class FirefliesClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(apiKey?: string) {
    this.apiKey = apiKey || process.env.FIREFLIES_API_KEY!;
    this.baseUrl = FIREFLIES_API;
    if (!this.apiKey) throw new Error("FIREFLIES_API_KEY is required");
  }

  async query<T = any>(gql: string, variables?: Record<string, any>): Promise<T> {
    const res = await fetch(this.baseUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({ query: gql, variables }),
    });

    const json: FirefliesResponse<T> = await res.json();

    if (json.errors?.length) {
      const err = json.errors[0];
      const error = new Error(`Fireflies: ${err.message}`) as any;
      error.code = err.code;
      error.status = err.extensions?.status;
      throw error;
    }

    return json.data!;
  }

  // Convenience methods for common queries
  async getUser() {
    return this.query<{ user: any }>(`{ user { name email user_id is_admin } }`);
  }

  async getTranscripts(limit = 20) {
    return this.query<{ transcripts: any[] }>(`
      query($limit: Int) {
        transcripts(limit: $limit) {
          id title date duration organizer_email participants
          summary { overview action_items keywords }
        }
      }
    `, { limit });
  }

  async getTranscript(id: string) {
    return this.query<{ transcript: any }>(`
      query($id: String!) {
        transcript(id: $id) {
          id title date duration
          speakers { id name }
          sentences { speaker_name text start_time end_time }
          summary { overview action_items keywords short_summary }
          analytics {
            sentiments { positive_pct negative_pct neutral_pct }
            speakers { name duration word_count questions }
          }
        }
      }
    `, { id });
  }
}
```

### Step 2: Singleton Pattern
```typescript
// lib/fireflies.ts
let instance: FirefliesClient | null = null;

export function getFirefliesClient(): FirefliesClient {
  if (!instance) {
    instance = new FirefliesClient();
  }
  return instance;
}
```

### Step 3: Multi-Tenant Factory
```typescript
const tenantClients = new Map<string, FirefliesClient>();

export function getClientForTenant(tenantId: string): FirefliesClient {
  if (!tenantClients.has(tenantId)) {
    const apiKey = getTenantApiKey(tenantId); // from your secret store
    tenantClients.set(tenantId, new FirefliesClient(apiKey));
  }
  return tenantClients.get(tenantId)!;
}
```

### Step 4: Response Validation with Zod
```typescript
import { z } from "zod";

const TranscriptSchema = z.object({
  id: z.string(),
  title: z.string(),
  date: z.string(),
  duration: z.number(),
  speakers: z.array(z.object({ id: z.string(), name: z.string() })),
  summary: z.object({
    overview: z.string().nullable(),
    action_items: z.array(z.string()).nullable(),
    keywords: z.array(z.string()).nullable(),
  }).nullable(),
});

type Transcript = z.infer<typeof TranscriptSchema>;

async function getValidatedTranscript(id: string): Promise<Transcript> {
  const client = getFirefliesClient();
  const { transcript } = await client.getTranscript(id);
  return TranscriptSchema.parse(transcript);
}
```

### Step 5: Python Client
```python
import os
from typing import Any
import requests

class FirefliesClient:
    API_URL = "https://api.fireflies.ai/graphql"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["FIREFLIES_API_KEY"]

    def query(self, gql: str, variables: dict | None = None) -> dict[str, Any]:
        resp = requests.post(
            self.API_URL,
            json={"query": gql, "variables": variables},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        data = resp.json()
        if "errors" in data:
            raise Exception(f"Fireflies: {data['errors'][0]['message']}")
        return data["data"]

    def get_transcripts(self, limit: int = 20) -> list[dict]:
        result = self.query("""
            query($limit: Int) {
                transcripts(limit: $limit) {
                    id title date duration organizer_email
                    summary { overview action_items keywords }
                }
            }
        """, {"limit": limit})
        return result["transcripts"]

    def get_transcript(self, transcript_id: str) -> dict:
        result = self.query("""
            query($id: String!) {
                transcript(id: $id) {
                    id title date duration
                    speakers { name }
                    sentences { speaker_name text start_time end_time }
                    summary { overview action_items keywords }
                }
            }
        """, {"id": transcript_id})
        return result["transcript"]

# Usage
client = FirefliesClient()
for t in client.get_transcripts(5):
    print(f"{t['title']} - {t['duration']}min")
```

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Typed client class | All API calls | Centralized auth and error handling |
| Singleton | Single-tenant apps | Reuse connection, consistent config |
| Factory | Multi-tenant SaaS | Isolated API keys per customer |
| Zod validation | API responses | Runtime type safety, catches schema drift |

## Output
- Type-safe GraphQL client with error codes
- Singleton and factory patterns for different deployment models
- Zod schemas for runtime response validation
- Python client with identical API surface

## Resources
- [Fireflies API Docs](https://docs.fireflies.ai/)
- [Fireflies GraphQL Introspection](https://docs.fireflies.ai/fundamentals/introspection)
- [Zod Documentation](https://zod.dev/)

## Next Steps
Apply patterns in `fireflies-core-workflow-a` for real-world usage.
