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

Juicebox search uses cursor-based pagination. This async generator transparently fetches all pages, yielding profiles one at a time.

```typescript
// lib/paginator.ts
import { JuiceboxClient } from "./juicebox-client";
import { SearchParams, Profile } from "../types/juicebox";

export async function* paginateSearch(
  client: JuiceboxClient,
  params: Omit<SearchParams, "cursor">,
  options?: { maxPages?: number; pageSize?: number }
): AsyncGenerator<Profile, void, undefined> {
  const pageSize = options?.pageSize ?? 50;
  const maxPages = options?.maxPages ?? Infinity;
  let cursor: string | undefined;
  let page = 0;

  do {
    const response = await client.search({
      ...params,
      limit: pageSize,
      cursor,
    });

    for (const profile of response.profiles) {
      yield profile;
    }

    cursor = response.cursor;
    page++;

    if (page >= maxPages) {
      console.log(`Reached max pages (${maxPages}). Stopping pagination.`);
      break;
    }
  } while (cursor);
}

// Convenience: collect all results into an array
export async function collectAll(
  client: JuiceboxClient,
  params: Omit<SearchParams, "cursor">,
  maxResults = 500
): Promise<Profile[]> {
  const results: Profile[] = [];

  for await (const profile of paginateSearch(client, params)) {
    results.push(profile);
    if (results.length >= maxResults) break;
  }

  return results;
}
```

### Step 4: Implement a Result Monad for Error Handling

Instead of try/catch everywhere, use a `Result<T, E>` type that makes errors explicit in function signatures and enables composable pipelines.

```typescript
// lib/result.ts
export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

export function ok<T>(value: T): Result<T, never> {
  return { ok: true, value };
}

export function err<E>(error: E): Result<never, E> {
  return { ok: false, error };
}

export async function tryAsync<T>(fn: () => Promise<T>): Promise<Result<T, Error>> {
  try {
    return ok(await fn());
  } catch (e) {
    return err(e instanceof Error ? e : new Error(String(e)));
  }
}

export function map<T, U, E>(result: Result<T, E>, fn: (v: T) => U): Result<U, E> {
  return result.ok ? ok(fn(result.value)) : result;
}

export function flatMap<T, U, E>(
  result: Result<T, E>,
  fn: (v: T) => Result<U, E>
): Result<U, E> {
  return result.ok ? fn(result.value) : result;
}

// Usage with Juicebox client
import { JuiceboxClient, JuiceboxApiError } from "./juicebox-client";

export async function safeSearch(
  client: JuiceboxClient,
  params: SearchParams
): Promise<Result<SearchResponse, JuiceboxApiError | Error>> {
  return tryAsync(() => client.search(params));
}

export async function safeGetProfile(
  client: JuiceboxClient,
  id: string
): Promise<Result<Profile, JuiceboxApiError | Error>> {
  return tryAsync(() => client.getProfile(id));
}
```

### Step 5: Builder Pattern for Complex Search Queries

For complex search criteria across multiple dimensions, a fluent builder prevents query string bugs and validates constraints at build time.

```typescript
// lib/search-builder.ts
import { SearchParams } from "../types/juicebox";

export class SearchBuilder {
  private params: Partial<SearchParams> = {};
  private queryParts: string[] = [];

  role(role: string): this {
    this.queryParts.push(role);
    return this;
  }

  withSkills(...skills: string[]): this {
    if (skills.length > 0) {
      this.queryParts.push(`skills:(${skills.join(" OR ")})`);
    }
    this.params.skills = skills;
    return this;
  }

  inLocation(location: string): this {
    this.params.location = location;
    return this;
  }

  atCompany(company: string): this {
    this.params.company = company;
    return this;
  }

  withTitle(title: string): this {
    this.params.title = title;
    return this;
  }

  limit(n: number): this {
    if (n < 1 || n > 100) {
      throw new Error("Limit must be between 1 and 100");
    }
    this.params.limit = n;
    return this;
  }

  offset(n: number): this {
    if (n < 0) throw new Error("Offset must be >= 0");
    this.params.offset = n;
    return this;
  }

  build(): SearchParams {
    if (this.queryParts.length === 0) {
      throw new Error("Search query is empty. Call .role() or add query terms first.");
    }
    return {
      query: this.queryParts.join(" AND "),
      ...this.params,
    };
  }

  // Static factory for common searches
  static candidateSearch(role: string, skills: string[], location?: string): SearchParams {
    const builder = new SearchBuilder().role(role).withSkills(...skills).limit(50);
    if (location) builder.inLocation(location);
    return builder.build();
  }
}
```

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
import { JuiceboxClient } from "./lib/juicebox-client";
import { SearchBuilder } from "./lib/search-builder";
import { paginateSearch } from "./lib/paginator";
import { safeSearch, safeGetProfile } from "./lib/result";

// Initialize client
const client = new JuiceboxClient({
  username: process.env.JUICEBOX_USERNAME!,
  apiToken: process.env.JUICEBOX_API_TOKEN!,
  timeoutMs: 15_000,
  maxRetries: 3,
});

// Build a search query with the builder
const params = new SearchBuilder()
  .role("Staff Software Engineer")
  .withSkills("TypeScript", "React", "Node.js")
  .inLocation("San Francisco Bay Area")
  .limit(25)
  .build();

// Safe search with Result monad
const result = await safeSearch(client, params);
if (!result.ok) {
  console.error("Search failed:", result.error.message);
  process.exit(1);
}

console.log(`Found ${result.value.total} total matches`);
result.value.profiles.forEach((p) =>
  console.log(`  ${p.name} — ${p.title} at ${p.company}`)
);
```

### Paginated Candidate Collection

```typescript
import { JuiceboxClient } from "./lib/juicebox-client";
import { paginateSearch, collectAll } from "./lib/paginator";

const client = new JuiceboxClient({
  username: process.env.JUICEBOX_USERNAME!,
  apiToken: process.env.JUICEBOX_API_TOKEN!,
});

// Stream profiles one at a time (memory efficient)
for await (const profile of paginateSearch(client, {
  query: "ML engineer PyTorch distributed training",
  limit: 50,
})) {
  console.log(`${profile.name} (${profile.experience_years}yr) — ${profile.company}`);
}

// Or collect into an array with a cap
const allProfiles = await collectAll(
  client,
  { query: "engineering manager", location: "New York" },
  200 // stop after 200 results
);
console.log(`Collected ${allProfiles.length} profiles`);
```

### Enrichment with Result Monad Pipeline

```typescript
import { JuiceboxClient, JuiceboxApiError } from "./lib/juicebox-client";
import { tryAsync, map, ok, err, Result } from "./lib/result";

const client = new JuiceboxClient({
  username: process.env.JUICEBOX_USERNAME!,
  apiToken: process.env.JUICEBOX_API_TOKEN!,
});

// Search, then enrich — each step returns Result
const searchResult = await tryAsync(() =>
  client.search({ query: "VP Engineering fintech", limit: 10 })
);

if (!searchResult.ok) {
  console.error("Search failed:", searchResult.error.message);
  process.exit(1);
}

const profileIds = searchResult.value.profiles.map((p) => p.id);
const enrichResult = await tryAsync(() =>
  client.enrichProfiles(profileIds, ["email", "phone"])
);

if (enrichResult.ok) {
  console.log(`Enriched ${enrichResult.value.profiles.length} profiles`);
  console.log(`Credits remaining: ${enrichResult.value.credits_remaining}`);
  enrichResult.value.profiles.forEach((p) =>
    console.log(`  ${p.name}: ${p.email ?? "no email"} | ${p.phone ?? "no phone"}`)
  );
} else {
  console.error("Enrichment failed:", enrichResult.error.message);
}
```

### Singleton Pattern for Shared Client

```typescript
// lib/singleton.ts
import { JuiceboxClient } from "./juicebox-client";

let instance: JuiceboxClient | null = null;

export function getJuiceboxClient(): JuiceboxClient {
  if (!instance) {
    const username = process.env.JUICEBOX_USERNAME;
    const apiToken = process.env.JUICEBOX_API_TOKEN;
    if (!username || !apiToken) {
      throw new Error(
        "JUICEBOX_USERNAME and JUICEBOX_API_TOKEN must be set in environment"
      );
    }
    instance = new JuiceboxClient({ username, apiToken });
  }
  return instance;
}
```

## Resources

- [Juicebox API Reference](https://juicebox.ai/docs/api)
- [SDK Best Practices](https://juicebox.ai/docs/best-practices)
- [Error Handling Guide](https://juicebox.ai/docs/errors)
- [Search Query Syntax](https://juicebox.ai/docs/search/syntax)

## Next Steps

Apply these patterns then explore `juicebox-core-workflow-a` for people search workflows, or `juicebox-rate-limits` for advanced throttling.
