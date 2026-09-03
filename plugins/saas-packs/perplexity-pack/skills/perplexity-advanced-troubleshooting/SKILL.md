---
name: perplexity-advanced-troubleshooting
description: 'Apply advanced debugging techniques for hard-to-diagnose Perplexity
  Sonar API issues.

  Use when standard troubleshooting fails, investigating inconsistent citations,

  or preparing evidence for support escalation.

  Trigger with phrases like "perplexity hard bug", "perplexity mystery error",

  "perplexity inconsistent results", "difficult perplexity issue", "perplexity deep
  debug".

  '
allowed-tools: Read, Grep, Bash(curl:*), Bash(jq:*)
version: 1.13.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- perplexity
- debugging
- scaling
compatibility: Designed for Claude Code
---
# Perplexity Advanced Troubleshooting

## Overview

Deep debugging for Perplexity Sonar API issues that resist standard fixes. Common hard problems: inconsistent citations between identical queries, intermittent timeouts on sonar-pro, search results not matching recency filter, and response quality degradation.

## Prerequisites

- Read-only access to production logs and metrics
- `PERPLEXITY_API_KEY` supplied by the approved secret manager
- `curl` and `jq` for the metadata-only API probe
- Understanding of Perplexity's search-augmented generation model

## Instructions

1. Use `Read` and `Grep` against approved logs to record the incident window, affected route, request IDs, model, and aggregate status/latency counts. Do not collect prompts, answers, API keys, or full response bodies.
2. Run the metadata-only layer probe below against the fixed `https://api.perplexity.ai` origin. Stop on transport, authentication, billing, throttling, or schema failure.
3. Reproduce with a synthetic, non-customer query and one variable changed at a time: model, timeout, or search filter.
4. Compare at least five bounded synthetic runs before classifying citation or latency variance. Keep only counts, status classes, and timings.
5. Escalate with the sanitized template after local network, request-shape, and model-specific causes have been separated.

## Diagnostic Tools

### Layer-by-Layer Test

```bash
set -euo pipefail
test -n "${PERPLEXITY_API_KEY:-}" || {
  echo "PERPLEXITY_API_KEY is not set" >&2
  exit 1
}

# curl appends status and latency after the JSON body. Command substitution
# removes trailing newlines, leaving the two final lines as stable delimiters.
response="$(curl --silent --show-error --connect-timeout 5 --max-time 30 \
  --write-out $'\n%{http_code}\n%{time_total}' \
  -H "Authorization: Bearer ${PERPLEXITY_API_KEY}" \
  -H "Content-Type: application/json" \
  --data '{"model":"sonar","messages":[{"role":"user","content":"Reply with the single word ready."}],"max_tokens":8}' \
  https://api.perplexity.ai/chat/completions)"

latency_seconds="${response##*$'\n'}"
without_latency="${response%$'\n'*}"
http_status="${without_latency##*$'\n'}"
body="${without_latency%$'\n'*}"

case "${http_status}" in
  200)
    printf '%s\n' "${body}" | jq -er \
      --arg status "${http_status}" \
      --arg latency "${latency_seconds}" '
        {
          http_status: ($status | tonumber),
          latency_seconds: ($latency | tonumber),
          model: (.model | select(type == "string" and length > 0)),
          finish_reason: (.choices[0].finish_reason | select(type == "string")),
          citation_count: ((.citations // []) | length),
          total_tokens: (.usage.total_tokens | select(type == "number"))
        }
      '
    ;;
  # 401 is authentication, 402 is billing, and 429 is throttling.
  401|402|429)
    echo "Perplexity probe failed with HTTP ${http_status}; classify credentials, billing, or limits without printing the body." >&2
    exit 1
    ;;
  *)
    echo "Perplexity probe failed with HTTP ${http_status}." >&2
    exit 1
    ;;
esac
```

### Inconsistent Citation Investigation

```typescript
// Same query can return different citations due to live web search
// Run a synthetic query N times and compare opaque fingerprints.
import { createHash } from "node:crypto";

async function citationStabilityTest(query: string, runs: number = 5) {
  const results: Array<{ citationFingerprints: string[] }> = [];

  for (let i = 0; i < runs; i++) {
    const response = await perplexity.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: query }],
      max_tokens: 500,
    });

    const citations = (response as { citations?: string[] }).citations || [];
    const citationFingerprints = citations.map((raw) =>
      createHash("sha256").update(raw).digest("hex").slice(0, 16)
    );
    results.push({ citationFingerprints });

    await new Promise((r) => setTimeout(r, 2000)); // Rate limit
  }

  // Analyze consistency
  const allCitations = results.flatMap((r) => r.citationFingerprints);
  const citationFreq = allCitations.reduce((acc, url) => {
    acc[url] = (acc[url] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const stable = Object.entries(citationFreq)
    .filter(([, count]) => count >= runs * 0.6)
    .map(([url]) => url);

  console.log(`Stable citations (>60% appearance): ${stable.length}/${Object.keys(citationFreq).length}`);
  console.log("All unique:", Object.keys(citationFreq).length);

  return { results, citationFreq, stableCitations: stable };
}
```

### Latency Profiling

```typescript
async function profileLatency(
  cases: Array<{ caseId: string; syntheticQuery: string }>,
  models: string[] = ["sonar", "sonar-pro"]
) {
  const results: Array<{
    caseId: string;
    model: string;
    latencyMs: number;
    tokens: number;
    citations: number;
  }> = [];

  for (const model of models) {
    for (const { caseId, syntheticQuery } of cases) {
      if (!/^[A-Za-z0-9_-]{1,40}$/.test(caseId)) throw new Error("invalid case id");
      const start = performance.now();
      try {
        const response = await perplexity.chat.completions.create({
          model,
          messages: [{ role: "user", content: syntheticQuery }],
          max_tokens: 500,
        });

        results.push({
          caseId,
          model,
          latencyMs: Math.round(performance.now() - start),
          tokens: response.usage?.total_tokens || 0,
          citations: (response as any).citations?.length || 0,
        });
      } catch (err: any) {
        results.push({
          caseId,
          model,
          latencyMs: Math.round(performance.now() - start),
          tokens: 0,
          citations: 0,
        });
      }

      await new Promise((r) => setTimeout(r, 1500));
    }
  }

  // Print report
  console.table(results);

  const byModel = results.reduce((acc, r) => {
    if (!acc[r.model]) acc[r.model] = [];
    acc[r.model].push(r.latencyMs);
    return acc;
  }, {} as Record<string, number[]>);

  for (const [model, latencies] of Object.entries(byModel)) {
    const sorted = latencies.sort((a, b) => a - b);
    console.log(`${model}: p50=${sorted[Math.floor(sorted.length * 0.5)]}ms p95=${sorted[Math.floor(sorted.length * 0.95)]}ms`);
  }
}
```

### Recency Filter Validation

```typescript
// Verify search_recency_filter is actually working
async function testRecencyFilter() {
  const query = "latest technology news";
  const filters: Array<"hour" | "day" | "week" | "month"> = ["hour", "day", "week", "month"];

  for (const filter of filters) {
    const response = await perplexity.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: query }],
      search_recency_filter: filter,
      max_tokens: 200,
    } as any);

    const citations = (response as any).citations || [];
    console.log(`\nRecency: ${filter}`);
    console.log(`  Citations: ${citations.length}`);
    console.log(`  Finish reason: ${response.choices[0].finish_reason || "unknown"}`);

    await new Promise((r) => setTimeout(r, 2000));
  }
}
```

## Support Escalation Template

Copy only the allowlisted fields below after completing the evidence review in the linked reference.

```markdown
## Perplexity Support Escalation

**Issue:** [Brief description]
**Severity:** [P1-P4]
**First observed:** [ISO 8601 timestamp]
**Frequency:** [Always / Intermittent / Once]

### Steps to Reproduce
1. Call `POST https://api.perplexity.ai/chat/completions`
2. Body: `{"model": "sonar", "messages": [{"role": "user", "content": "..."}]}`
3. Observed: [What happened]
4. Expected: [What should happen]

### Evidence
- Metadata-only probe: [HTTP status, latency, model, finish reason, citation count, token count]
- Latency profile: [p50/p95 values]
- Citation stability: [X/Y stable citations]
- Provider request IDs: [IDs only; no prompts, answers, citations, headers, or response JSON]

### Workarounds Attempted
1. [Workaround] — Result: [outcome]
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Different citations per call | Web search is non-deterministic | Cache results; accept variability |
| recency filter ignored | Query overrides filter context | Make query explicitly time-bounded |
| sonar-pro timeout | Complex multi-source search | Set 30s timeout, fall back to sonar |
| Answer quality varies | Different web sources found | Use `search_domain_filter` for consistency |

## Examples

### Isolate a model-specific latency regression

Run the synthetic probe five times with `sonar`, then five times with the affected model while keeping the prompt, network path, and timeout fixed. Compare status distribution and p50/p95 latency; do not retain generated text. If only one model regresses, route eligible traffic to the healthy model and attach the metadata-only comparison plus provider request IDs to the escalation.

### Investigate citation instability safely

Use a public, non-sensitive question and an explicit allowlist of authoritative domains. Record citation counts and normalized hostnames rather than full answers or URLs. Treat normal source rotation separately from missing citations or citations outside the approved domain set.

## Output

- Layer-by-layer diagnostic results
- Citation stability analysis
- Latency profiling by model
- Support escalation package

## Resources

- [Perplexity Community Forum](https://community.perplexity.ai)
- [Perplexity API Documentation](https://docs.perplexity.ai)
- [Sanitized escalation and evidence contract](references/sanitized-escalation.md)

## Next Steps

For load testing, see `perplexity-load-scale`.
