---
name: perplexity-advanced-troubleshooting
description: |
  Apply advanced debugging techniques for hard-to-diagnose Perplexity Sonar API issues.
  Use when standard troubleshooting fails, investigating inconsistent citations,
  or preparing evidence for support escalation.
  Trigger with phrases like "perplexity hard bug", "perplexity mystery error",
  "perplexity inconsistent results", "difficult perplexity issue", "perplexity deep debug".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, perplexity, debugging, scaling]

---
# Perplexity Advanced Troubleshooting

## Overview
Deep debugging for Perplexity Sonar API issues that resist standard fixes. Common hard problems: inconsistent citations between identical queries, intermittent timeouts on sonar-pro, search results not matching recency filter, and response quality degradation.

## Prerequisites
- Access to production logs and metrics
- `curl` for direct API testing
- Understanding of Perplexity's search-augmented generation model

## Diagnostic Tools

### Layer-by-Layer Test
```bash
#!/bin/bash
set -euo pipefail
echo "=== Perplexity Layer Diagnostics ==="

# Layer 1: DNS
echo -n "1. DNS: "
dig +short api.perplexity.ai || echo "FAIL"

# Layer 2: TCP connectivity
echo -n "2. TCP: "
timeout 5 bash -c 'echo > /dev/tcp/api.perplexity.ai/443 && echo "OK"' 2>/dev/null || echo "FAIL"

# Layer 3: TLS handshake
echo -n "3. TLS: "
echo | openssl s_client -connect api.perplexity.ai:443 2>/dev/null | grep -c "Verify return code: 0" | sed 's/1/OK/;s/0/FAIL/'

# Layer 4: HTTP with auth
echo -n "4. Auth: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"test"}],"max_tokens":5}' \
  https://api.perplexity.ai/chat/completions

echo ""

# Layer 5: Response quality
echo "5. Quality check:"
RESPONSE=$(curl -s \
  -H "Authorization: Bearer $PERPLEXITY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"sonar","messages":[{"role":"user","content":"What is 2+2?"}],"max_tokens":50}' \
  https://api.perplexity.ai/chat/completions)

echo "   Model: $(echo $RESPONSE | jq -r '.model')"
echo "   Answer: $(echo $RESPONSE | jq -r '.choices[0].message.content' | head -c 100)"
echo "   Citations: $(echo $RESPONSE | jq -r '.citations | length')"
echo "   Tokens: $(echo $RESPONSE | jq -r '.usage.total_tokens')"
```

### Inconsistent Citation Investigation
```typescript
// Same query can return different citations due to live web search
// Run N times and compare to identify pattern vs randomness

async function citationStabilityTest(query: string, runs: number = 5) {
  const results: Array<{ citations: string[]; answer: string }> = [];

  for (let i = 0; i < runs; i++) {
    const response = await perplexity.chat.completions.create({
      model: "sonar",
      messages: [{ role: "user", content: query }],
      max_tokens: 500,
    });

    results.push({
      answer: response.choices[0].message.content || "",
      citations: (response as any).citations || [],
    });

    await new Promise((r) => setTimeout(r, 2000)); // Rate limit
  }

  // Analyze consistency
  const allCitations = results.flatMap((r) => r.citations);
  const citationFreq = allCitations.reduce((acc, url) => {
    acc[url] = (acc[url] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const stable = Object.entries(citationFreq)
    .filter(([, count]) => count >= runs * 0.6)
    .map(([url]) => url);

  console.log(`Stable citations (>60% appearance): ${stable.length}/${Object.keys(citationFreq).length}`);
  console.log("Stable:", stable);
  console.log("All unique:", Object.keys(citationFreq).length);

  return { results, citationFreq, stableCitations: stable };
}
```

### Latency Profiling
```typescript
async function profileLatency(
  queries: string[],
  models: string[] = ["sonar", "sonar-pro"]
) {
  const results: Array<{
    query: string;
    model: string;
    latencyMs: number;
    tokens: number;
    citations: number;
  }> = [];

  for (const model of models) {
    for (const query of queries) {
      const start = performance.now();
      try {
        const response = await perplexity.chat.completions.create({
          model,
          messages: [{ role: "user", content: query }],
          max_tokens: 500,
        });

        results.push({
          query: query.slice(0, 50),
          model,
          latencyMs: Math.round(performance.now() - start),
          tokens: response.usage?.total_tokens || 0,
          citations: (response as any).citations?.length || 0,
        });
      } catch (err: any) {
        results.push({
          query: query.slice(0, 50),
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
    console.log(`  Answer preview: ${(response.choices[0].message.content || "").slice(0, 100)}...`);

    await new Promise((r) => setTimeout(r, 2000));
  }
}
```

## Support Escalation Template
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
- Layer diagnostic results: [paste output]
- Latency profile: [p50/p95 values]
- Citation stability: [X/Y stable citations]
- Response JSON: [attach]

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

## Output
- Layer-by-layer diagnostic results
- Citation stability analysis
- Latency profiling by model
- Support escalation package

## Resources
- [Perplexity Community Forum](https://community.perplexity.ai)
- [Perplexity API Documentation](https://docs.perplexity.ai)

## Next Steps
For load testing, see `perplexity-load-scale`.
