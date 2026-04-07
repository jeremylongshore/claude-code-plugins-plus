---
name: juicebox-sdk-patterns
description: |
  Apply production Juicebox SDK patterns.
  Trigger: "juicebox patterns", "juicebox best practices".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, recruiting, juicebox]
compatible-with: claude-code
---

# Juicebox SDK Patterns

## Overview
Production-ready patterns for the Juicebox AI-powered people search API. Juicebox provides REST endpoints for searching professional profiles and enriching candidate data. The API authenticates via `JUICEBOX_API_KEY` and returns structured profile objects with LinkedIn URLs as natural dedup keys. A singleton client centralizes rate-limit handling across search and enrich endpoints.

## Singleton Client
```typescript
const JUICEBOX_BASE = 'https://api.juicebox.work/v1';
let _client: JuiceboxClient | null = null;
export function getClient(): JuiceboxClient {
  if (!_client) {
    const apiKey = process.env.JUICEBOX_API_KEY;
    if (!apiKey) throw new Error('JUICEBOX_API_KEY must be set — get it from juicebox.work/settings');
    _client = new JuiceboxClient(apiKey);
  }
  return _client;
}
class JuiceboxClient {
  private headers: Record<string, string>;
  constructor(apiKey: string) { this.headers = { 'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json' }; }
  async search(query: string, limit = 20): Promise<SearchResponse> {
    const res = await fetch(`${JUICEBOX_BASE}/search`, {
      method: 'POST', headers: this.headers, body: JSON.stringify({ query, limit }) });
    if (!res.ok) throw new JuiceboxError(res.status, await res.text()); return res.json();
  }
  async enrich(linkedinUrl: string): Promise<Profile> {
    const res = await fetch(`${JUICEBOX_BASE}/enrich`, {
      method: 'POST', headers: this.headers, body: JSON.stringify({ linkedin_url: linkedinUrl }) });
    if (!res.ok) throw new JuiceboxError(res.status, await res.text()); return res.json();
  }
}
```

## Error Wrapper
```typescript
export class JuiceboxError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = 'JuiceboxError'; }
}
export async function safeCall<T>(operation: string, fn: () => Promise<T>): Promise<T> {
  try { return await fn(); }
  catch (err: any) {
    if (err instanceof JuiceboxError && err.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    if (err instanceof JuiceboxError && err.status === 401) throw new JuiceboxError(401, 'Invalid JUICEBOX_API_KEY');
    throw new JuiceboxError(err.status ?? 0, `${operation} failed: ${err.message}`);
  }
}
```

## Request Builder
```typescript
class JuiceboxSearchBuilder {
  private body: Record<string, any> = {};
  query(q: string) { this.body.query = q; return this; }
  limit(n: number) { this.body.limit = Math.min(n, 100); return this; }
  location(loc: string) { this.body.location = loc; return this; }
  title(t: string) { this.body.title_filter = t; return this; }
  company(c: string) { this.body.company_filter = c; return this; }
  yearsExp(min: number, max: number) { this.body.years_experience = { min, max }; return this; }
  build() { return this.body; }
}
// Usage: new JuiceboxSearchBuilder().query('ML engineer').location('San Francisco').yearsExp(3, 8).build();
```

## Response Types
```typescript
interface Profile {
  id: string; name: string; title: string; company: string;
  linkedin_url: string; location: string; skills: string[]; experience_years: number;
}
interface SearchResponse {
  profiles: Profile[]; total: number; has_more: boolean; cursor?: string;
}
interface EnrichResult {
  profile: Profile; education: Array<{ school: string; degree: string; year: number }>;
  experience: Array<{ company: string; title: string; start: string; end: string | null }>;
}
```

## Testing Utilities
```typescript
export function mockProfile(overrides: Partial<Profile> = {}): Profile {
  return { id: 'prof-001', name: 'Jane Smith', title: 'Senior ML Engineer',
    company: 'Acme Corp', linkedin_url: 'https://linkedin.com/in/janesmith',
    location: 'San Francisco, CA', skills: ['Python', 'PyTorch', 'MLOps'],
    experience_years: 6, ...overrides };
}
export function mockSearchResponse(count = 3): SearchResponse {
  return { profiles: Array.from({ length: count }, (_, i) => mockProfile({ id: `prof-${i}` })),
    total: count, has_more: false };
}
```

## Error Handling
| Pattern | When to Use | Example |
|---------|-------------|---------|
| `safeCall` wrapper | All Juicebox API calls | Structured error with operation context |
| Retry on 429 | Batch search pipelines | 5s backoff before retry |
| LinkedIn dedup | Multi-query search | `Set<string>` on `linkedin_url` prevents duplicates |
| Cursor pagination | Search results > 100 | Pass `cursor` from previous response |

## Resources
- [Juicebox API Docs](https://docs.juicebox.work/sdk)

## Next Steps
Apply patterns in `juicebox-core-workflow-a`.
