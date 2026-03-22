---
name: perplexity-data-handling
description: |
  Implement Perplexity query sanitization, citation validation, result caching,
  and conversation context management for search workflows.
  Trigger with phrases like "perplexity data", "perplexity PII",
  "perplexity citations", "perplexity cache", "perplexity context".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, compliance]

---
# Perplexity Data Handling

## Overview
Manage data flowing through Perplexity Sonar API. Critical concern: queries are sent to Perplexity for web search, so any PII in queries is exposed to external infrastructure. Responses contain citations (third-party URLs) that must be validated before displaying to users.

## Data Flow

```
User Input → Query Sanitization → Perplexity API → Response Parsing
                                                         │
                                           ┌─────────────┼──────────────┐
                                           │             │              │
                                      Answer Text    Citations    Search Results
                                           │             │              │
                                      Format &      Validate &    Store for
                                      Display       Deduplicate   Analytics
```

## Prerequisites
- Perplexity API key configured
- Understanding of PII regulations (GDPR/CCPA)
- Cache storage (Redis or in-memory)

## Instructions

### Step 1: Query Sanitization
```typescript
function sanitizeQuery(query: string): { clean: string; redacted: boolean } {
  let clean = query;
  let redacted = false;

  const patterns: Array<[RegExp, string]> = [
    [/\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, "[email]"],
    [/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, "[phone]"],
    [/\b\d{3}-\d{2}-\d{4}\b/g, "[ssn]"],
    [/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, "[card]"],
    [/\b(pplx-|sk-|pk_|sk_live_)\w{20,}\b/g, "[token]"],
    [/\b(user|customer|account)\s*#?\s*\d+\b/gi, "[id]"],
  ];

  for (const [pattern, replacement] of patterns) {
    if (pattern.test(clean)) {
      clean = clean.replace(pattern, replacement);
      redacted = true;
    }
  }

  return { clean, redacted };
}

async function safeSearch(rawQuery: string) {
  const { clean, redacted } = sanitizeQuery(rawQuery);
  if (redacted) {
    console.warn("[Data] PII redacted from Perplexity query");
  }

  return perplexity.chat.completions.create({
    model: "sonar",
    messages: [{ role: "user", content: clean }],
  });
}
```

### Step 2: Citation Validation
```typescript
interface ValidatedCitation {
  url: string;
  domain: string;
  valid: boolean;
  index: number;
}

function validateCitations(citations: string[]): ValidatedCitation[] {
  return citations.map((url, i) => {
    try {
      const parsed = new URL(url);
      return {
        url: url.replace(/[.,;:]+$/, ""),
        domain: parsed.hostname,
        valid: ["http:", "https:"].includes(parsed.protocol),
        index: i + 1,
      };
    } catch {
      return { url, domain: "unknown", valid: false, index: i + 1 };
    }
  });
}

function deduplicateCitations(citations: ValidatedCitation[]): ValidatedCitation[] {
  const seen = new Set<string>();
  return citations.filter((c) => {
    const normalized = c.url.split("?")[0].replace(/\/$/, "");
    if (seen.has(normalized)) return false;
    seen.add(normalized);
    return true;
  });
}

// Replace [1] markers with linked citations
function renderCitations(answer: string, citations: ValidatedCitation[]): string {
  let rendered = answer;
  for (const c of citations.filter((c) => c.valid)) {
    rendered = rendered.replaceAll(`[${c.index}]`, `[${c.index}](${c.url})`);
  }
  return rendered;
}
```

### Step 3: Result Caching with Freshness Policy
```typescript
import { LRUCache } from "lru-cache";
import { createHash } from "crypto";

interface CachedResult {
  answer: string;
  citations: ValidatedCitation[];
  cachedAt: number;
  model: string;
}

const CACHE_TTL: Record<string, number> = {
  news: 30 * 60_000,       // 30 min for breaking/current events
  research: 4 * 3600_000,  // 4 hours for research topics
  factual: 24 * 3600_000,  // 24 hours for stable facts
  default: 1 * 3600_000,   // 1 hour default
};

const resultCache = new LRUCache<string, CachedResult>({ max: 500 });

function detectQueryType(query: string): keyof typeof CACHE_TTL {
  if (/\b(latest|today|breaking|recent|this week)\b/i.test(query)) return "news";
  if (/\b(research|study|paper|analysis|compare)\b/i.test(query)) return "research";
  if (/\b(what is|define|how does|who is)\b/i.test(query)) return "factual";
  return "default";
}

async function cachedSearch(query: string, model = "sonar") {
  const hash = createHash("sha256")
    .update(`${model}:${query.toLowerCase().trim()}`)
    .digest("hex");

  const cached = resultCache.get(hash);
  if (cached) return { ...cached, fromCache: true };

  const response = await safeSearch(query);
  const rawCitations = (response as any).citations || [];
  const citations = deduplicateCitations(validateCitations(rawCitations));
  const queryType = detectQueryType(query);

  const entry: CachedResult = {
    answer: response.choices[0].message.content || "",
    citations,
    cachedAt: Date.now(),
    model: response.model,
  };

  resultCache.set(hash, entry, { ttl: CACHE_TTL[queryType] });
  return { ...entry, fromCache: false };
}
```

### Step 4: Conversation Context Management
```typescript
import OpenAI from "openai";

type Message = OpenAI.ChatCompletionMessageParam;

class SearchContext {
  private messages: Message[] = [];
  private readonly maxMessages = 10;
  private readonly maxEstimatedTokens = 8000;

  constructor(systemPrompt?: string) {
    if (systemPrompt) {
      this.messages.push({ role: "system", content: systemPrompt });
    }
  }

  addUserMessage(content: string) {
    this.messages.push({ role: "user", content });
    this.trim();
  }

  addAssistantMessage(content: string) {
    this.messages.push({ role: "assistant", content });
    this.trim();
  }

  getMessages(): Message[] {
    return [...this.messages];
  }

  private trim() {
    // Keep system prompt + last N messages
    while (this.messages.length > this.maxMessages) {
      const systemIdx = this.messages[0].role === "system" ? 1 : 0;
      this.messages.splice(systemIdx, 1);
    }

    // Trim if estimated tokens too high
    while (this.estimateTokens() > this.maxEstimatedTokens && this.messages.length > 2) {
      const systemIdx = this.messages[0].role === "system" ? 1 : 0;
      this.messages.splice(systemIdx, 1);
    }
  }

  private estimateTokens(): number {
    return this.messages.reduce(
      (sum, m) => sum + Math.ceil(String(m.content).length / 4),
      0
    );
  }

  clear() {
    const system = this.messages.find((m) => m.role === "system");
    this.messages = system ? [system] : [];
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in search query | User entered personal data | Apply `sanitizeQuery` before API call |
| Broken citation URLs | Source page moved/deleted | Validate URLs, filter invalid ones |
| Stale cached results | TTL too long for news | Use query-type-aware TTL |
| Context overflow | Too many conversation turns | Automatic trimming in SearchContext |
| Duplicate citations | Same source cited multiple times | Deduplicate by normalized URL |

## Output
- Query sanitization stripping PII before API calls
- Citation validation and deduplication
- Cache with query-type-aware TTL
- Conversation context with automatic trimming

## Resources
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Perplexity Privacy Policy](https://www.perplexity.ai/privacy)

## Next Steps
For access control, see `perplexity-enterprise-rbac`.
