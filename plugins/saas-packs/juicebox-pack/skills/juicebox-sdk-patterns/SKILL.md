---
name: juicebox-sdk-patterns
description: |
  Apply production-ready Juicebox SDK patterns.
  Use when implementing robust error handling, retry logic,
  or enterprise-grade Juicebox integrations.
  Trigger with phrases like "juicebox best practices", "juicebox patterns",
  "production juicebox", "juicebox SDK architecture".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, juicebox, juicebox-sdk]

---
# Juicebox SDK Patterns

## Overview

Production-ready patterns for building robust Juicebox PeopleGPT integrations. Covers a typed client wrapper with automatic retry and auth management, strongly-typed response models for search and enrichment endpoints, a cursor-based pagination helper, a Result monad for safe error propagation, and a builder pattern for constructing complex people search queries without string manipulation.

## Prerequisites

- Node.js 18+ with TypeScript 5.0+
- Juicebox API credentials (`JUICEBOX_USERNAME`, `JUICEBOX_API_TOKEN` in environment)
- Familiarity with async/await and generic types
- `npm install` or equivalent for project dependencies

## Instructions

### Step 1: Create a Typed Client Wrapper with Auto-Retry

The client handles authentication, content negotiation, automatic retries on transient errors, and exposes typed methods for each API endpoint.

```typescript
// lib/juicebox-client.ts
export interface JuiceboxClientConfig {
  username: string;
  apiToken: string;
  baseUrl?: string;
  timeoutMs?: number;
  maxRetries?: number;
}

export class JuiceboxClient {
  private readonly baseUrl: string;
  private readonly authHeader: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;

  constructor(config: JuiceboxClientConfig) {
    this.baseUrl = config.baseUrl ?? "https://api.juicebox.ai";
    this.authHeader = `token ${config.username}:${config.apiToken}`;
    this.timeoutMs = config.timeoutMs ?? 30_000;
    this.maxRetries = config.maxRetries ?? 3;
  }

  async search(params: SearchParams): Promise<SearchResponse> {
    const qs = new URLSearchParams();
    qs.set("q", params.query);
    if (params.limit) qs.set("limit", String(params.limit));
    if (params.offset) qs.set("offset", String(params.offset));
    if (params.cursor) qs.set("cursor", params.cursor);
    if (params.location) qs.set("location", params.location);
    if (params.title) qs.set("title", params.title);
    if (params.company) qs.set("company", params.company);
    if (params.skills) qs.set("skills", params.skills.join(","));

    return this.request<SearchResponse>(`/api/v1/search?${qs.toString()}`);
  }

  async getProfile(profileId: string): Promise<Profile> {
    return this.request<Profile>(`/api/v1/profiles/${encodeURIComponent(profileId)}`);
  }

  async enrichProfiles(profileIds: string[], fields?: string[]): Promise<EnrichmentResponse> {
    return this.request<EnrichmentResponse>("/api/v1/enrichments", {
      method: "POST",
      body: JSON.stringify({
        profile_ids: profileIds,
        fields: fields ?? ["email", "phone", "social_profiles"],
      }),
    });
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    let lastError: Error | undefined;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), this.timeoutMs);

      try {
        const res = await fetch(`${this.baseUrl}${path}`, {
          ...init,
          signal: controller.signal,
          headers: {
            Authorization: this.authHeader,
            "Content-Type": "application/json",
            Accept: "application/json",
            ...init?.headers,
          },
        });

        if (res.ok) {
          return (await res.json()) as T;
        }

        // Retry on 429 and 5xx
        if ((res.status === 429 || res.status >= 500) && attempt < this.maxRetries) {
          const retryAfter = parseInt(res.headers.get("Retry-After") ?? "0", 10);
          const backoff = retryAfter > 0
            ? retryAfter * 1000
            : Math.min(1000 * Math.pow(2, attempt), 30_000);
          const jitter = Math.random() * 500;
          await new Promise((r) => setTimeout(r, backoff + jitter));
          continue;
        }

        // Non-retryable error
        const body = await res.text();
        throw new JuiceboxApiError(res.status, body, path);
      } catch (err) {
        if (err instanceof JuiceboxApiError) throw err;
        lastError = err as Error;
        if (attempt < this.maxRetries) {
          await new Promise((r) => setTimeout(r, 1000 * Math.pow(2, attempt)));
          continue;
        }
      } finally {
        clearTimeout(timeout);
      }
    }

    throw lastError ?? new Error("Request failed after retries");
  }
}

export class JuiceboxApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly body: string,
    public readonly path: string
  ) {
    super(`Juicebox API error ${status} on ${path}: ${body.slice(0, 200)}`);
    this.name = "JuiceboxApiError";
  }
}
```

### Step 2: Define Typed Response Models

Strong types for every API response prevent runtime surprises and enable IDE auto-completion.

```typescript
// types/juicebox.ts
export interface SearchParams {
  query: string;
  limit?: number;
  offset?: number;
  cursor?: string;
  location?: string;
  title?: string;
  company?: string;
  skills?: string[];
}

export interface Profile {
  id: string;
  name: string;
  title: string;
  company: string;
  location: string;
  skills: string[];
  experience_years: number;
  education: Education[];
  social_profiles: SocialProfiles;
  email?: string;
  phone?: string;
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  year?: number;
}

export interface SocialProfiles {
  linkedin?: string;
  github?: string;
  twitter?: string;
}

export interface SearchResponse {
  profiles: Profile[];
  total: number;
  cursor?: string;
  has_more: boolean;
}

export interface EnrichmentResponse {
  profiles: EnrichedProfile[];
  credits_used: number;
  credits_remaining: number;
}

export interface EnrichedProfile extends Profile {
  email: string;
  phone: string;
  enriched_at: string;
}
```

### Step 3: Build a Pagination Helper

Create an async generator (`lib/paginator.ts`) that transparently fetches all pages using cursor-based pagination, yielding profiles one at a time. Include a `collectAll()` convenience function with a configurable max-results cap. See [advanced patterns](references/advanced-patterns.md) for the full implementation.

### Step 4: Implement a Result Monad for Error Handling

Create a `Result<T, E>` type (`lib/result.ts`) with `ok()`, `err()`, `tryAsync()`, `map()`, and `flatMap()` combinators. Wrap Juicebox client calls in `safeSearch()` and `safeGetProfile()` functions that return Result instead of throwing. See [advanced patterns](references/advanced-patterns.md) for the full implementation.

### Step 5: Builder Pattern for Complex Search Queries

Create a `SearchBuilder` class (`lib/search-builder.ts`) with fluent methods: `.role()`, `.withSkills()`, `.inLocation()`, `.atCompany()`, `.withTitle()`, `.limit()`, `.offset()`. Validates constraints at build time (limit 1-100, offset >= 0, non-empty query). Include a static `candidateSearch()` factory for common queries. See [advanced patterns](references/advanced-patterns.md) for the full implementation.

## Output

- `lib/juicebox-client.ts` — Typed client wrapper with auth, timeout, and auto-retry
- `types/juicebox.ts` — Complete TypeScript models for profiles, search, and enrichment
- `lib/paginator.ts` — Cursor-based async pagination generator with configurable limits
- `lib/result.ts` — Result monad with `tryAsync`, `map`, and `flatMap` combinators
- `lib/search-builder.ts` — Fluent builder for constructing validated search queries

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Auto-retry with backoff | 429 and 5xx transient failures | Higher success rate without caller intervention |
| `JuiceboxApiError` class | Structured error with status, body, path | Enables pattern matching on `status` for recovery |
| `Result<T, E>` monad | Composable error pipelines | No uncaught exceptions; errors are explicit in types |
| Builder validation | Malformed search queries | Catches constraint violations at build time, not at API call |
| AbortController timeout | Hung requests | Prevents indefinite waits; configurable per-client |

## Examples

### Complete Client Usage

```typescript
const client = new JuiceboxClient({
  username: process.env.JUICEBOX_USERNAME!,
  apiToken: process.env.JUICEBOX_API_TOKEN!,
  timeoutMs: 15_000,
  maxRetries: 3,
});

// Build a search with fluent builder + safe Result monad
const params = new SearchBuilder()
  .role("Staff Software Engineer")
  .withSkills("TypeScript", "React", "Node.js")
  .inLocation("San Francisco Bay Area")
  .limit(25)
  .build();

const result = await safeSearch(client, params);
if (result.ok) {
  console.log(`Found ${result.value.total} matches`);
}
```

For paginated collection, enrichment pipelines, and singleton patterns, see [advanced patterns](references/advanced-patterns.md).

## Resources

- [Juicebox API Reference](https://juicebox.ai/docs/api)
- [SDK Best Practices](https://juicebox.ai/docs/best-practices)
- [Error Handling Guide](https://juicebox.ai/docs/errors)
- [Search Query Syntax](https://juicebox.ai/docs/search/syntax)

## Next Steps

Apply these patterns then explore `juicebox-core-workflow-a` for people search workflows, or `juicebox-rate-limits` for advanced throttling.
