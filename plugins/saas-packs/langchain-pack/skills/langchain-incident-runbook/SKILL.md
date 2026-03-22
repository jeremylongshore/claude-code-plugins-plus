---
name: langchain-incident-runbook
description: |
  Incident response procedures for LangChain production issues:
  provider outages, high error rates, latency spikes, and cost overruns.
  Trigger: "langchain incident", "langchain outage", "langchain production issue",
  "langchain emergency", "langchain down", "LLM provider outage".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, llm, incident-response]

---
# LangChain Incident Runbook

## Overview

Standard operating procedures for LangChain production incidents: provider outages, error rate spikes, latency degradation, memory issues, and cost overruns.

## Severity Classification

| Level | Description | Response Time | Example |
|-------|-------------|---------------|---------|
| SEV1 | Complete outage | 15 min | All LLM calls failing |
| SEV2 | Major degradation | 30 min | >50% error rate, >10s latency |
| SEV3 | Minor degradation | 2 hours | <10% errors, slow responses |
| SEV4 | Low impact | 24 hours | Intermittent issues, warnings |

## Runbook 1: LLM Provider Outage

### Detect

```bash
# Check provider status pages
curl -s https://status.openai.com/api/v2/status.json | jq '.status'
curl -s https://status.anthropic.com/api/v2/status.json | jq '.status'
```

### Diagnose

```typescript
async function diagnoseProviders() {
  const results: Record<string, string> = {};

  try {
    const openai = new ChatOpenAI({ model: "gpt-4o-mini", timeout: 10000 });
    await openai.invoke("ping");
    results.openai = "OK";
  } catch (e: any) {
    results.openai = `FAIL: ${e.message.slice(0, 100)}`;
  }

  try {
    const anthropic = new ChatAnthropic({ model: "claude-sonnet-4-20250514" });
    await anthropic.invoke("ping");
    results.anthropic = "OK";
  } catch (e: any) {
    results.anthropic = `FAIL: ${e.message.slice(0, 100)}`;
  }

  console.table(results);
  return results;
}
```

### Mitigate

```typescript
// Enable fallback — switch to healthy provider
const primary = new ChatOpenAI({
  model: "gpt-4o-mini",
  maxRetries: 1,
  timeout: 5000,
});

const fallback = new ChatAnthropic({
  model: "claude-sonnet-4-20250514",
  maxRetries: 1,
});

const resilientModel = primary.withFallbacks({
  fallbacks: [fallback],
});

// All chains using resilientModel auto-failover
```

### Recover

1. Monitor provider status page for resolution
2. Verify primary provider works: `await diagnoseProviders()`
3. Remove fallback config (or keep it for resilience)
4. Document incident timeline for post-mortem

## Runbook 2: High Error Rate

### Detect

```bash
# Check LangSmith for error spike
# https://smith.langchain.com/o/YOUR_ORG/projects/YOUR_PROJECT/runs?filter=error:true

# Check application logs
grep -c "Error\|error\|ERROR" /var/log/app/langchain.log | tail -5
```

### Diagnose

```typescript
// Common error patterns
const ERROR_CAUSES: Record<string, string> = {
  "RateLimitError":     "API quota exceeded -> reduce concurrency",
  "AuthenticationError": "API key invalid -> check secrets",
  "Timeout":            "Provider slow -> increase timeout",
  "OutputParserException": "LLM output format changed -> check prompts",
  "ValidationError":    "Schema mismatch -> update Zod schemas",
  "ContextLengthExceeded": "Input too long -> truncate or chunk",
};
```

### Mitigate

```typescript
// 1. Reduce load
// Lower maxConcurrency on batch operations

// 2. Enable caching for repeated queries
const cache = new Map();
async function withCache(chain: any, input: any) {
  const key = JSON.stringify(input);
  if (cache.has(key)) return cache.get(key);
  const result = await chain.invoke(input);
  cache.set(key, result);
  return result;
}

// 3. Enable fallback model
const model = primary.withFallbacks({ fallbacks: [fallback] });
```

## Runbook 3: Latency Spike

### Detect

```
# Prometheus query
histogram_quantile(0.95, rate(langchain_llm_latency_seconds_bucket[5m])) > 5
```

### Diagnose

```typescript
// Measure per-component latency
const tracer = new MetricsCallback();
await chain.invoke({ input: "test" }, { callbacks: [tracer] });
console.table(tracer.getReport());
// Check: is it the LLM, retriever, or tool that's slow?
```

### Mitigate

1. Switch to faster model: `gpt-4o-mini` (200ms TTFT) vs `gpt-4o` (400ms)
2. Enable streaming to reduce perceived latency
3. Enable caching for repeated queries
4. Reduce context length (shorter prompts)

## Runbook 4: Cost Overrun

### Detect

```bash
# Check OpenAI usage dashboard
# https://platform.openai.com/usage
```

### Mitigate

```typescript
// 1. Emergency model downgrade
// gpt-4o ($2.50/1M) -> gpt-4o-mini ($0.15/1M) = 17x cheaper

// 2. Enable budget enforcement
const budget = new BudgetEnforcer(50.0); // $50 daily limit
const model = new ChatOpenAI({
  model: "gpt-4o-mini",
  callbacks: [budget],
});

// 3. Enable aggressive caching
// (see langchain-cost-tuning skill)
```

## Runbook 5: Memory/OOM Issues

### Detect

```bash
# Check process memory
ps aux --sort=-%mem | head -5

# Node.js heap stats
node -e "console.log(process.memoryUsage())"
```

### Mitigate

1. Clear caches: reset in-memory caches
2. Reduce batch sizes: lower `maxConcurrency`
3. Use streaming instead of accumulating full responses
4. Restart pods: `kubectl rollout restart deployment/langchain-api`

## Incident Response Checklist

### During Incident

- [ ] Acknowledge in incident channel
- [ ] Classify severity (SEV1-4)
- [ ] Check provider status pages
- [ ] Run diagnostic script
- [ ] Apply mitigation (fallback/cache/throttle)
- [ ] Communicate status to stakeholders
- [ ] Document timeline

### Post-Incident

- [ ] Verify full recovery
- [ ] Schedule post-mortem (within 48h)
- [ ] Write incident report
- [ ] Create follow-up tickets
- [ ] Update monitoring/alerting rules
- [ ] Update this runbook if needed

## Resources

- [OpenAI Status](https://status.openai.com)
- [Anthropic Status](https://status.anthropic.com)
- [LangSmith](https://smith.langchain.com)
- [PagerDuty Best Practices](https://response.pagerduty.com/)

## Next Steps

Use `langchain-debug-bundle` for detailed evidence collection during incidents.
