---
name: perplexity-data-handling
description: |
  Implement Perplexity PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Perplexity integrations.
  Trigger with phrases like "perplexity data", "perplexity PII",
  "perplexity GDPR", "perplexity data retention", "perplexity privacy", "perplexity CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Data Handling

## Overview
Manage search query data and results from Perplexity Sonar API. Covers query sanitization, citation validation, result caching with freshness policies, and conversation context management for research workflows.

## Prerequisites
- Perplexity API key
- OpenAI-compatible client library
- Understanding of search result data structures
- Cache storage for results

## Instructions

### Step 1: Query Sanitization
```typescript
function sanitizeQuery(query: string): string {
  // Remove PII that might leak into search queries
  let clean = query
    .replace(/\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, '[email]')
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[phone]')
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[ssn]');

  // Remove overly specific identifiers
  clean = clean
    .replace(/\b(user|customer|account)\s*#?\s*\d+\b/gi, '[ID]')
    .replace(/\b[A-Z0-9]{20,}\b/g, '[TOKEN]');

  return clean;
}

async function safeSearch(rawQuery: string) {
  const query = sanitizeQuery(rawQuery);

  const result = await perplexity.chat.completions.create({
    model: 'sonar',
    messages: [{ role: 'user', content: query }],
  });

  return result;
}
```

### Step 2: Citation Validation and Cleaning
```typescript
interface ValidatedCitation {
  url: string;
  domain: string;
  isAccessible: boolean;
  title?: string;
}

function extractAndValidateCitations(responseText: string): ValidatedCitation[] {
  const urlRegex = /https?:\/\/[^\s\])"]+/g;
  const urls = [...new Set(responseText.match(urlRegex) || [])];

  return urls.map(url => {
    try {
      const parsed = new URL(url);
      return {
        url: url.replace(/[.,;:]+$/, ''), // Clean trailing punctuation
        domain: parsed.hostname,
        isAccessible: true,
      };
    } catch {
      return { url, domain: 'unknown', isAccessible: false };
    }
  }).filter(c => c.isAccessible);
}

function deduplicateCitations(citations: ValidatedCitation[]): ValidatedCitation[] {
  const seen = new Set<string>();
  return citations.filter(c => {
    const key = c.domain + c.url.split('?')[0]; // Ignore query params
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}
```

### Step 3: Result Caching with Freshness Policy
```typescript
import { LRUCache } from 'lru-cache';
import { createHash } from 'crypto';

interface CachedResult {
  response: string;
  citations: ValidatedCitation[];
  cachedAt: number;
  queryHash: string;
}

// Different TTLs based on query type
const CACHE_TTL = {
  factual: 1000 * 60 * 60 * 24,  // 24 hours for stable facts
  news: 1000 * 60 * 30,           // 30 min for news queries
  research: 1000 * 60 * 60 * 4,   // 4 hours for research
  default: 1000 * 60 * 60,        // 1 hour default
};

const resultCache = new LRUCache<string, CachedResult>({ max: 500 });

function detectQueryType(query: string): keyof typeof CACHE_TTL {
  if (/\b(latest|today|breaking|recent)\b/i.test(query)) return 'news';
  if (/\b(research|study|paper|analysis)\b/i.test(query)) return 'research';
  if (/\b(what is|define|how does)\b/i.test(query)) return 'factual';
  return 'default';
}

async function cachedSearch(query: string) {
  const hash = createHash('sha256').update(query.toLowerCase().trim()).digest('hex');
  const cached = resultCache.get(hash);
  if (cached) return cached;

  const result = await safeSearch(query);
  const content = result.choices[0].message.content || '';
  const citations = deduplicateCitations(extractAndValidateCitations(content));
  const queryType = detectQueryType(query);

  const entry: CachedResult = {
    response: content,
    citations,
    cachedAt: Date.now(),
    queryHash: hash,
  };

  resultCache.set(hash, entry, { ttl: CACHE_TTL[queryType] });
  return entry;
}
```

### Step 4: Conversation Context Limits
```typescript
class ResearchContext {
  private messages: any[] = [];
  private maxMessages = 10;
  private maxTokenEstimate = 8000;

  addMessage(role: string, content: string) {
    this.messages.push({ role, content });

    // Trim oldest messages if over limit
    while (this.messages.length > this.maxMessages) {
      this.messages.shift();
    }

    // Trim if estimated tokens too high
    while (this.estimateTokens() > this.maxTokenEstimate && this.messages.length > 2) {
      this.messages.splice(1, 1); // Remove second oldest (keep system prompt)
    }
  }

  getMessages() { return [...this.messages]; }
  clear() { this.messages = []; }

  private estimateTokens(): number {
    return this.messages.reduce((sum, m) => sum + Math.ceil(m.content.length / 4), 0);
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in search query | User entered personal data | Apply `sanitizeQuery` before API call |
| Broken citations | URL changed or removed | Validate URLs, remove inaccessible ones |
| Stale cached results | TTL too long for news queries | Use query-type-aware TTL |
| Context overflow | Too many conversation turns | Trim old messages automatically |

## Examples

### Research Session with Caching
```typescript
const context = new ResearchContext();
context.addMessage('system', 'You are a research assistant.');

const result = await cachedSearch('Latest advances in quantum computing 2025');
console.log(`Response: ${result.response.slice(0, 200)}...`);
console.log(`Citations: ${result.citations.length} sources`);
```

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai/)
- [Perplexity Data Policy](https://perplexity.ai/privacy)
