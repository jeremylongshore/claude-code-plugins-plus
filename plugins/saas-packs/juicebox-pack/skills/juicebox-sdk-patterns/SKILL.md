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

## Singleton Client
```typescript
let instance: JuiceboxClient | null = null;
export function getClient(): JuiceboxClient {
  if (!instance) instance = new JuiceboxClient({ apiKey: process.env.JUICEBOX_API_KEY });
  return instance;
}
```

## Batch Search with Dedup
```typescript
async function batchSearch(queries: string[]): Promise<Profile[]> {
  const seen = new Set<string>();
  const all: Profile[] = [];
  for (const q of queries) {
    const r = await client.search({ query: q, limit: 20 });
    for (const p of r.profiles) {
      if (!seen.has(p.linkedin_url)) { seen.add(p.linkedin_url); all.push(p); }
    }
  }
  return all;
}
```

## Error Wrapper
```typescript
async function safeCall<T>(fn: () => Promise<T>): Promise<T | null> {
  try { return await fn(); }
  catch (e: any) {
    if (e.status === 429) { await new Promise(r => setTimeout(r, 5000)); return fn(); }
    return null;
  }
}
```

## Resources
- [SDK Reference](https://docs.juicebox.work/sdk)

## Next Steps
Apply in `juicebox-core-workflow-a`.
