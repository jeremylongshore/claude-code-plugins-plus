---
name: grammarly-upgrade-migration
description: |
  Upgrade and migration guidance for Grammarly API version changes. Use when migrating
  between Grammarly API versions or updating endpoint references.
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, grammarly, writing]
compatible-with: claude-code
---

# Grammarly Upgrade & Migration

## Overview

Grammarly exposes versioned APIs for writing analysis, AI detection, and plagiarism checking. Each API family versions independently — the Writing Score API may be on v2 while AI Detection remains on v1. Tracking these versions matters because Grammarly deprecates older API versions on a fixed timeline, and the response schemas differ significantly between versions (score breakdowns, suggestion categories, and confidence thresholds all change). Missing a version cutover means silent failures or degraded writing feedback quality.

## Version Detection

```typescript
const GRAMMARLY_BASE = "https://api.grammarly.com/ecosystem/api";

interface GrammarlyVersionMap {
  scores: string;
  aiDetection: string;
  plagiarism: string;
  latestAvailable: Record<string, string>;
}

async function detectGrammarlyVersions(apiKey: string): Promise<GrammarlyVersionMap> {
  const endpoints = {
    scores: `${GRAMMARLY_BASE}/v2/scores`,
    aiDetection: `${GRAMMARLY_BASE}/v1/ai-detection`,
    plagiarism: `${GRAMMARLY_BASE}/v1/plagiarism`,
  };

  const versions: Record<string, string> = {};
  for (const [api, url] of Object.entries(endpoints)) {
    const res = await fetch(url, {
      method: "HEAD",
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    versions[api] = res.headers.get("x-grammarly-api-version") ?? "unknown";
    const deprecated = res.headers.get("x-grammarly-deprecated");
    if (deprecated) console.warn(`${api} endpoint deprecated: ${deprecated}`);
  }
  return { scores: "v2", aiDetection: "v1", plagiarism: "v1", latestAvailable: versions };
}
```

## Migration Checklist

- [ ] Audit codebase for all `api.grammarly.com` endpoint references
- [ ] Map each endpoint to its current API version (v1 vs. v2)
- [ ] Check if Writing Score v2 response includes new sub-score categories
- [ ] Verify AI Detection confidence threshold changes between versions
- [ ] Update plagiarism check response parser if source attribution format changed
- [ ] Test OAuth token flow — scope names may differ between API versions
- [ ] Validate suggestion category enums (clarity, engagement, delivery, correctness)
- [ ] Update error handling for new rate limit headers in v2
- [ ] Check if text submission size limits changed between versions
- [ ] Run A/B comparison of v1 vs. v2 scores on sample corpus to verify parity

## Schema Migration

```typescript
// Grammarly scores response changed from flat scores to structured breakdown
interface OldScoreResponse {
  overall: number;
  correctness: number;
  clarity: number;
  engagement: number;
  delivery: number;
}

interface NewScoreResponse {
  overall: { score: number; label: string };
  dimensions: Array<{
    name: "correctness" | "clarity" | "engagement" | "delivery";
    score: number;
    label: string;
    suggestions: Array<{ category: string; message: string; severity: "critical" | "warning" | "info" }>;
  }>;
  metadata: { wordCount: number; readingTime: number; apiVersion: string };
}

function migrateScoreResponse(old: OldScoreResponse): NewScoreResponse {
  const toLabel = (s: number) => (s >= 80 ? "Strong" : s >= 60 ? "Good" : "Needs work");
  return {
    overall: { score: old.overall, label: toLabel(old.overall) },
    dimensions: (["correctness", "clarity", "engagement", "delivery"] as const).map((name) => ({
      name,
      score: old[name],
      label: toLabel(old[name]),
      suggestions: [],
    })),
    metadata: { wordCount: 0, readingTime: 0, apiVersion: "v1-migrated" },
  };
}
```

## Rollback Strategy

```typescript
class GrammarlyClient {
  private versionMap: Record<string, string> = { scores: "v2", aiDetection: "v1", plagiarism: "v1" };
  private fallbackMap: Record<string, string> = { scores: "v1", aiDetection: "v1", plagiarism: "v1" };

  constructor(private apiKey: string) {}

  async checkText(text: string, api: "scores" | "aiDetection" | "plagiarism"): Promise<any> {
    const version = this.versionMap[api];
    try {
      const res = await fetch(`https://api.grammarly.com/ecosystem/api/${version}/${api}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${this.apiKey}`, "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error(`Grammarly ${api} ${res.status}`);
      return await res.json();
    } catch (err) {
      const fallback = this.fallbackMap[api];
      if (fallback !== version) {
        console.warn(`Falling back ${api} from ${version} to ${fallback}`);
        this.versionMap[api] = fallback;
        return this.checkText(text, api);
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Score dimension renamed | Response missing `engagement`, has `tone` instead | Update parser to map new dimension names to internal schema |
| API version sunset | `410 Gone` on v1 scores endpoint | Migrate all calls to v2 and update response parsing |
| OAuth scope mismatch | `403` after upgrading API version | Re-authorize with scopes matching new version requirements |
| Text length limit changed | `413 Payload Too Large` on previously working requests | Chunk text into smaller segments per new version limits |
| Rate limit structure changed | `429` without `X-RateLimit-Reset` header | Switch to `Retry-After` header or implement exponential backoff |

## Resources

- [Grammarly Developer Portal](https://developer.grammarly.com/)
- [Grammarly API Changelog](https://developer.grammarly.com/changelog)

## Next Steps

For CI pipeline integration, see `grammarly-ci-integration`.
