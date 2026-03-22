---
name: mistral-cost-tuning
description: |
  Optimize Mistral AI costs through model selection, token management, and usage monitoring.
  Use when analyzing Mistral billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "mistral cost", "mistral billing",
  "reduce mistral costs", "mistral pricing", "mistral budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, api, monitoring, cost-optimization]

---
# Mistral AI Cost Tuning

## Overview
Optimize Mistral AI costs through model selection, token management, caching, batch inference, and budget monitoring. Mistral offers the best price-performance in the market with models from $0.1/M tokens (Ministral/Small) to $0.5/M tokens (Large).

## Prerequisites
- Access to [Mistral AI console](https://console.mistral.ai/) for usage data
- Understanding of current usage patterns
- Database for usage tracking (optional)

## Pricing Reference (as of 2025)

| Model | Input $/M tokens | Output $/M tokens | Best For |
|-------|------------------|--------------------|----------|
| `ministral-latest` (3B) | $0.10 | $0.10 | Simple tasks, edge |
| `mistral-small-latest` | $0.10 | $0.30 | General purpose, fast |
| `codestral-latest` | $0.30 | $0.90 | Code generation |
| `mistral-large-latest` | $0.50 | $1.50 | Complex reasoning |
| `pixtral-large-latest` | $2.00 | $6.00 | Vision + text |
| `mistral-embed` | $0.10 | — | Embeddings |
| Batch API (any model) | **50% off** | **50% off** | Non-realtime bulk |

**Always check [docs.mistral.ai/deployment/laplateforme/pricing](https://docs.mistral.ai/deployment/laplateforme/pricing/) for current rates.**

## Instructions

### Step 1: Cost Calculator

```typescript
const PRICING: Record<string, { input: number; output: number }> = {
  'ministral-latest':      { input: 0.10, output: 0.10 },
  'mistral-small-latest':  { input: 0.10, output: 0.30 },
  'codestral-latest':      { input: 0.30, output: 0.90 },
  'mistral-large-latest':  { input: 0.50, output: 1.50 },
  'pixtral-large-latest':  { input: 2.00, output: 6.00 },
  'mistral-embed':         { input: 0.10, output: 0 },
};

function calculateCost(
  model: string,
  inputTokens: number,
  outputTokens: number,
  isBatch = false,
): number {
  const p = PRICING[model] ?? PRICING['mistral-small-latest'];
  const multiplier = isBatch ? 0.5 : 1.0;
  return ((inputTokens / 1e6) * p.input + (outputTokens / 1e6) * p.output) * multiplier;
}

// Example: 100K requests/month, avg 500 in + 200 out tokens
const monthlySmall = calculateCost('mistral-small-latest', 50_000_000, 20_000_000);
const monthlyLarge = calculateCost('mistral-large-latest', 50_000_000, 20_000_000);
console.log(`Small: $${monthlySmall.toFixed(2)}/month`);  // $11.00
console.log(`Large: $${monthlyLarge.toFixed(2)}/month`);  // $55.00
```

### Step 2: Smart Model Router

```typescript
type TaskComplexity = 'trivial' | 'simple' | 'moderate' | 'complex';

function selectModel(complexity: TaskComplexity): string {
  switch (complexity) {
    case 'trivial':  return 'ministral-latest';       // $0.10/M — yes/no, extract, format
    case 'simple':   return 'mistral-small-latest';   // $0.10/M — classify, summarize, Q&A
    case 'moderate': return 'codestral-latest';       // $0.30/M — code gen, moderate reasoning
    case 'complex':  return 'mistral-large-latest';   // $0.50/M — multi-step reasoning, analysis
  }
}

// Auto-detect complexity by prompt characteristics
function estimateComplexity(prompt: string): TaskComplexity {
  const tokens = Math.ceil(prompt.length / 4);
  if (tokens < 50) return 'trivial';
  if (tokens < 200) return 'simple';
  if (prompt.includes('code') || prompt.includes('analyze')) return 'moderate';
  return 'complex';
}
```

### Step 3: Token Budget Manager

```typescript
class BudgetManager {
  private dailyBudgetUsd: number;
  private monthlyBudgetUsd: number;
  private dailySpend = 0;
  private monthlySpend = 0;
  private lastResetDay = new Date().getDate();

  constructor(dailyBudget: number, monthlyBudget: number) {
    this.dailyBudgetUsd = dailyBudget;
    this.monthlyBudgetUsd = monthlyBudget;
  }

  canAfford(model: string, estimatedInputTokens: number, estimatedOutputTokens: number): boolean {
    const cost = calculateCost(model, estimatedInputTokens, estimatedOutputTokens);
    this.maybeResetDaily();
    return this.dailySpend + cost <= this.dailyBudgetUsd
        && this.monthlySpend + cost <= this.monthlyBudgetUsd;
  }

  recordSpend(model: string, usage: { promptTokens: number; completionTokens: number }): void {
    const cost = calculateCost(model, usage.promptTokens, usage.completionTokens);
    this.dailySpend += cost;
    this.monthlySpend += cost;
    this.checkAlerts();
  }

  private checkAlerts(): void {
    const monthPct = (this.monthlySpend / this.monthlyBudgetUsd) * 100;
    if (monthPct > 90) console.error(`BUDGET CRITICAL: ${monthPct.toFixed(1)}% of monthly budget`);
    else if (monthPct > 80) console.warn(`Budget warning: ${monthPct.toFixed(1)}% of monthly budget`);
  }

  private maybeResetDaily(): void {
    const today = new Date().getDate();
    if (today !== this.lastResetDay) {
      this.dailySpend = 0;
      this.lastResetDay = today;
    }
  }

  report() {
    return {
      daily: { spent: this.dailySpend, budget: this.dailyBudgetUsd },
      monthly: { spent: this.monthlySpend, budget: this.monthlyBudgetUsd },
    };
  }
}
```

### Step 4: Prompt Optimization

```typescript
// Reduce tokens = reduce cost directly
function optimizeForCost(systemPrompt: string): string {
  // Remove filler words
  return systemPrompt
    .replace(/please\s+/gi, '')
    .replace(/I would like you to\s+/gi, '')
    .replace(/\s+/g, ' ')
    .trim();
}

// Before: "I would like you to please provide a comprehensive and detailed explanation of how REST APIs work." (~25 tokens)
// After: "Explain REST APIs concisely." (~6 tokens, 76% reduction)

// Set maxTokens to prevent runaway output
const response = await client.chat.complete({
  model: 'mistral-small-latest',
  messages,
  maxTokens: 200, // Cap output — prevents 4000-token essays
});
```

### Step 5: Batch API for Bulk Workloads

```typescript
// Batch API = 50% cost reduction for non-realtime processing
// Instead of 100K individual API calls at $11/month (small)
// Use batch: $5.50/month for the same work

// Supported endpoints:
// /v1/chat/completions, /v1/embeddings, /v1/fim/completions,
// /v1/moderations, /v1/ocr, /v1/classifications

// See mistral-webhooks-events for implementation details
```

### Step 6: Usage Tracking SQL

```sql
CREATE TABLE mistral_usage (
  id SERIAL PRIMARY KEY,
  model VARCHAR(50) NOT NULL,
  input_tokens INTEGER NOT NULL,
  output_tokens INTEGER NOT NULL,
  cost_usd DECIMAL(10, 6) NOT NULL,
  is_batch BOOLEAN DEFAULT FALSE,
  endpoint VARCHAR(50),
  user_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Daily cost report
SELECT
  DATE(created_at) AS day,
  model,
  SUM(input_tokens) AS total_input,
  SUM(output_tokens) AS total_output,
  SUM(cost_usd) AS total_cost
FROM mistral_usage
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY 1, 2
ORDER BY 1 DESC, 5 DESC;

-- Highest-cost users
SELECT user_id, SUM(cost_usd) AS cost, COUNT(*) AS requests
FROM mistral_usage
WHERE created_at >= DATE_TRUNC('month', NOW())
GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
```

## Cost Reduction Strategies

| Strategy | Savings | Effort |
|----------|---------|--------|
| Use mistral-small instead of large | 80% | Low |
| Batch API for bulk | 50% | Medium |
| Response caching (temp=0) | 30-80% | Medium |
| Prompt optimization | 20-50% | Low |
| Set maxTokens | 10-40% | Low |
| Use ministral for simple tasks | 90% vs large | Low |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected costs | Untracked usage | Implement BudgetManager |
| Budget exceeded | No alerts | Set alerts at 80% and 90% |
| Wrong model | No routing logic | Use complexity-based model selection |
| Long responses | No maxTokens | Always set maxTokens |

## Resources
- [Mistral Pricing](https://docs.mistral.ai/deployment/laplateforme/pricing/)
- [Mistral Console](https://console.mistral.ai/)
- [Batch Inference](https://docs.mistral.ai/capabilities/batch/)

## Output
- Cost calculator with current pricing
- Smart model router by task complexity
- Token budget manager with alerts
- Prompt optimization patterns
- Usage tracking SQL schema
