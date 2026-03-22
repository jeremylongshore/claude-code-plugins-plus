---
name: exa-advanced-troubleshooting
description: |
  Apply advanced debugging techniques for hard-to-diagnose Exa issues.
  Use when standard troubleshooting fails, investigating latency spikes,
  or preparing evidence bundles for Exa support escalation.
  Trigger with phrases like "exa hard bug", "exa mystery error",
  "exa deep debug", "difficult exa issue", "exa latency spike".
allowed-tools: Read, Grep, Bash(curl:*), Bash(node:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, exa, debugging, advanced]

---
# Exa Advanced Troubleshooting

## Overview
Deep debugging for complex Exa issues: latency spikes, intermittent failures, result quality degradation, and content retrieval failures. All Exa error responses include a `requestId` — always capture it.

## Instructions

### Step 1: Layer-by-Layer Diagnostics
```typescript
import Exa from "exa-js";

interface DiagnosticResult {
  layer: string;
  success: boolean;
  latencyMs: number;
  details: string;
}

async function diagnoseExa(): Promise<DiagnosticResult[]> {
  const results: DiagnosticResult[] = [];
  const exa = new Exa(process.env.EXA_API_KEY);

  // Layer 1: DNS + Network
  let start = performance.now();
  try {
    const resp = await fetch("https://api.exa.ai", { method: "HEAD" });
    results.push({
      layer: "network",
      success: true,
      latencyMs: performance.now() - start,
      details: `HTTP ${resp.status}`,
    });
  } catch (err: any) {
    results.push({
      layer: "network",
      success: false,
      latencyMs: performance.now() - start,
      details: err.message,
    });
    return results; // No point continuing if network fails
  }

  // Layer 2: Authentication
  start = performance.now();
  try {
    await exa.search("auth test", { numResults: 1 });
    results.push({
      layer: "auth",
      success: true,
      latencyMs: performance.now() - start,
      details: "API key valid",
    });
  } catch (err: any) {
    results.push({
      layer: "auth",
      success: false,
      latencyMs: performance.now() - start,
      details: `${err.status}: ${err.message}`,
    });
    if (err.status === 401 || err.status === 402) return results;
  }

  // Layer 3: Neural search
  start = performance.now();
  try {
    const r = await exa.search("test neural search quality", {
      type: "neural",
      numResults: 3,
    });
    results.push({
      layer: "neural-search",
      success: true,
      latencyMs: performance.now() - start,
      details: `${r.results.length} results, top score: ${r.results[0]?.score.toFixed(3)}`,
    });
  } catch (err: any) {
    results.push({
      layer: "neural-search",
      success: false,
      latencyMs: performance.now() - start,
      details: `${err.status}: ${err.message}`,
    });
  }

  // Layer 4: Content retrieval
  start = performance.now();
  try {
    const r = await exa.searchAndContents("content retrieval test", {
      numResults: 1,
      text: { maxCharacters: 500 },
      highlights: { maxCharacters: 200 },
    });
    const hasText = !!r.results[0]?.text;
    const hasHighlights = !!r.results[0]?.highlights?.length;
    results.push({
      layer: "content-retrieval",
      success: hasText,
      latencyMs: performance.now() - start,
      details: `text: ${hasText}, highlights: ${hasHighlights}`,
    });
  } catch (err: any) {
    results.push({
      layer: "content-retrieval",
      success: false,
      latencyMs: performance.now() - start,
      details: `${err.status}: ${err.message}`,
    });
  }

  // Layer 5: findSimilar
  start = performance.now();
  try {
    const r = await exa.findSimilar("https://nodejs.org", { numResults: 2 });
    results.push({
      layer: "find-similar",
      success: r.results.length > 0,
      latencyMs: performance.now() - start,
      details: `${r.results.length} similar pages found`,
    });
  } catch (err: any) {
    results.push({
      layer: "find-similar",
      success: false,
      latencyMs: performance.now() - start,
      details: `${err.status}: ${err.message}`,
    });
  }

  return results;
}

// Print diagnostic report
const results = await diagnoseExa();
console.log("=== Exa Diagnostic Report ===");
for (const r of results) {
  const icon = r.success ? "PASS" : "FAIL";
  console.log(`[${icon}] ${r.layer}: ${r.latencyMs.toFixed(0)}ms — ${r.details}`);
}
```

### Step 2: Latency Profiling
```typescript
async function profileLatency(query: string, iterations = 5) {
  const exa = new Exa(process.env.EXA_API_KEY);
  const timings: { type: string; ms: number }[] = [];

  for (const type of ["instant", "fast", "auto", "neural"] as const) {
    for (let i = 0; i < iterations; i++) {
      const start = performance.now();
      try {
        await exa.search(query, { type, numResults: 3 });
        timings.push({ type, ms: performance.now() - start });
      } catch {
        timings.push({ type, ms: -1 }); // -1 indicates failure
      }
    }
  }

  // Summarize
  const grouped = new Map<string, number[]>();
  for (const t of timings) {
    if (!grouped.has(t.type)) grouped.set(t.type, []);
    if (t.ms > 0) grouped.get(t.type)!.push(t.ms);
  }

  console.log(`\nLatency profile for: "${query}"`);
  for (const [type, times] of grouped) {
    const sorted = times.sort((a, b) => a - b);
    const p50 = sorted[Math.floor(sorted.length * 0.5)];
    const p95 = sorted[Math.floor(sorted.length * 0.95)];
    console.log(`  ${type}: p50=${p50?.toFixed(0)}ms, p95=${p95?.toFixed(0)}ms`);
  }
}
```

### Step 3: Content Retrieval Debugging
```typescript
// When getContents or searchAndContents returns empty text
async function debugContentRetrieval(url: string) {
  const exa = new Exa(process.env.EXA_API_KEY);
  const configs = [
    { name: "default", opts: { text: true } },
    { name: "livecrawl-preferred", opts: { text: true, livecrawl: "preferred" as const, livecrawlTimeout: 15000 } },
    { name: "livecrawl-always", opts: { text: true, livecrawl: "always" as const, livecrawlTimeout: 15000 } },
    { name: "highlights-only", opts: { highlights: { maxCharacters: 500 } } },
    { name: "summary-only", opts: { summary: true } },
  ];

  console.log(`\nContent retrieval debug for: ${url}`);
  for (const { name, opts } of configs) {
    try {
      const result = await exa.getContents([url], opts as any);
      const r = result.results[0];
      console.log(`  ${name}: text=${r?.text?.length || 0} chars, highlights=${r?.highlights?.length || 0}`);
    } catch (err: any) {
      console.log(`  ${name}: ERROR ${err.status} — ${err.message}`);
    }
  }
}
```

### Step 4: Support Escalation Template
```markdown
## Exa Support Escalation

**Severity:** P[1-4]
**RequestId:** [from error response]
**Timestamp:** [ISO 8601 from error]
**SDK:** exa-js [version from npm list]

### Issue Summary
[One paragraph description]

### Steps to Reproduce
1. Initialize Exa client
2. Call [method] with [parameters]
3. Observe [error/unexpected behavior]

### Expected vs Actual
- Expected: [behavior]
- Actual: [behavior]

### Diagnostic Results
[Output from diagnoseExa() function]

### Evidence
- Latency profile attached
- Content retrieval debug output
- Error response with requestId
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Intermittent 5xx | Exa transient failure | Retry with backoff, capture requestId |
| Neural search slow | Complex/long query | Switch to `fast`, shorten query |
| Empty text for valid URL | Site blocks crawling | Try `livecrawl: "always"`, use highlights |
| Score drops across queries | Query drift | Compare with baseline queries |
| findSimilar returns nothing | Seed URL not indexed | Try a more popular seed URL |

## Resources
- [Exa Error Codes](https://docs.exa.ai/reference/error-codes)
- [Exa Support](mailto:hello@exa.ai)
- [Exa Rate Limits](https://docs.exa.ai/reference/rate-limits)

## Next Steps
For load testing, see `exa-load-scale`.
