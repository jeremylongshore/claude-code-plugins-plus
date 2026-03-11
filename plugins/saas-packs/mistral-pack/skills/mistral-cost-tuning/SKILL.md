---
name: mistral-cost-tuning
description: |
  Optimize Mistral AI costs through model selection, token management, and usage monitoring.
  Use when analyzing Mistral billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "mistral cost", "mistral billing",
  "reduce mistral costs", "mistral pricing", "mistral expensive", "mistral budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Cost Tuning

## Overview
Optimize Mistral AI costs through smart model selection, token management, and usage monitoring.

## Prerequisites
- Access to Mistral AI console
- Understanding of current usage patterns
- Database for usage tracking (optional)
- Alerting system configured (optional)

## Pricing Overview (as of 2024)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Best For |
|-------|----------------------|------------------------|----------|
| mistral-small-latest | $0.20 | $0.60 | Fast, simple tasks |
| mistral-large-latest | $2.00 | $6.00 | Complex reasoning |
| mistral-embed | $0.10 | - | Embeddings |

**Note:** Prices subject to change. Check console.mistral.ai for current pricing.

## Instructions

### Step 1: Cost Estimation Calculator

```typescript
interface TokenUsage {
  inputTokens: number;
  outputTokens: number;
}

interface CostEstimate {
  model: string;
  inputCost: number;
  outputCost: number;
  totalCost: number;
  currency: string;
}

const PRICING = {
  'mistral-small-latest': { input: 0.20, output: 0.60 },
  'mistral-large-latest': { input: 2.00, output: 6.00 },
  'mistral-embed': { input: 0.10, output: 0 },
} as const;

function estimateCost(model: keyof typeof PRICING, usage: TokenUsage): CostEstimate {
  const prices = PRICING[model];
  const inputCost = (usage.inputTokens / 1_000_000) * prices.input;
  const outputCost = (usage.outputTokens / 1_000_000) * prices.output;

  return {
    model,
    inputCost,
    outputCost,
    totalCost: inputCost + outputCost,
    currency: 'USD',
  };
}

// Usage
const cost = estimateCost('mistral-small-latest', {
  inputTokens: 500_000,
  outputTokens: 200_000,
});
console.log(`Estimated cost: $${cost.totalCost.toFixed(4)}`);
// Estimated cost: $0.2200
```

### Step 2: Model Selection by Task

```typescript
type TaskType = 'simple' | 'moderate' | 'complex' | 'embedding';

interface ModelRecommendation {
  model: string;
  reason: string;
  estimatedCostPer1000Requests: number;  # 1000ms = 1 second
}

function recommendModel(
  taskType: TaskType,
  avgInputTokens: number,
  avgOutputTokens: number
): ModelRecommendation {
  switch (taskType) {
    case 'simple':
      // Classification, extraction, simple Q&A
      return {
        model: 'mistral-small-latest',
        reason: 'Fast and cost-effective for simple tasks',
        estimatedCostPer1000Requests:
          (avgInputTokens * 0.20 + avgOutputTokens * 0.60) / 1000,  # 1 second in ms
      };

    case 'moderate':
      // Summarization, translation, basic coding
      return {
        model: 'mistral-small-latest',
        reason: 'Good balance of capability and cost',
        estimatedCostPer1000Requests:
          (avgInputTokens * 0.20 + avgOutputTokens * 0.60) / 1000,  # 1 second in ms
      };

    case 'complex':
      // Complex reasoning, code generation, analysis
      return {
        model: 'mistral-large-latest',
        reason: 'Required for complex tasks',
        estimatedCostPer1000Requests:
          (avgInputTokens * 2.00 + avgOutputTokens * 6.00) / 1000,  # 1 second in ms
      };

    case 'embedding':
      return {
        model: 'mistral-embed',
        reason: 'Specialized for embeddings',
        estimatedCostPer1000Requests: (avgInputTokens * 0.10) / 1000,  # 1 second in ms
      };
  }
}

// Usage
const rec = recommendModel('simple', 500, 200);  # 200: HTTP 500 Internal Server Error
console.log(`Recommended: ${rec.model} - $${rec.estimatedCostPer1000Requests.toFixed(4)}/1000 req`);  # 1 second in ms
```

### Step 3: Token Budget Management

```typescript
class TokenBudgetManager {
  private dailyBudget: number;
  private monthlyBudget: number;
  private dailyUsage: Map<string, number> = new Map();
  private monthlyUsage = 0;

  constructor(dailyBudget: number, monthlyBudget: number) {
    this.dailyBudget = dailyBudget;
    this.monthlyBudget = monthlyBudget;
  }

  recordUsage(model: string, tokens: number): void {
    const today = new Date().toISOString().split('T')[0];
    const key = `${today}:${model}`;

    const current = this.dailyUsage.get(key) || 0;
    this.dailyUsage.set(key, current + tokens);
    this.monthlyUsage += tokens;

    this.checkBudgetAlerts();
  }

  canMakeRequest(model: string, estimatedTokens: number): boolean {
    const today = new Date().toISOString().split('T')[0];
    const key = `${today}:${model}`;
    const todayUsage = this.dailyUsage.get(key) || 0;

    return (
      todayUsage + estimatedTokens <= this.dailyBudget &&
      this.monthlyUsage + estimatedTokens <= this.monthlyBudget
    );
  }

  private checkBudgetAlerts(): void {
    if (this.monthlyUsage > this.monthlyBudget * 0.8) {
      console.warn(`Budget alert: ${((this.monthlyUsage / this.monthlyBudget) * 100).toFixed(1)}% of monthly budget used`);
    }
  }

  getUsageReport(): { daily: Record<string, number>; monthly: number } {
    return {
      daily: Object.fromEntries(this.dailyUsage),
      monthly: this.monthlyUsage,
    };
  }
}
```

### Step 4: Prompt Optimization

```typescript
// Optimize prompts to reduce token usage
function optimizePrompt(prompt: string): string {
  return prompt
    .replace(/\s+/g, ' ')           // Remove extra whitespace
    .replace(/\n\s*\n/g, '\n')      // Remove blank lines
    .trim();
}

// Use system prompts efficiently
const EFFICIENT_SYSTEM_PROMPT = `
You are a helpful assistant. Be concise. Answer in 1-2 sentences when possible.
`.trim();

// Compare token counts
function countTokensEstimate(text: string): number {
  // Rough estimate: 1 token ≈ 4 characters
  return Math.ceil(text.length / 4);
}

// Example: Reduce prompt size
const originalPrompt = `
  I would like you to help me with the following task.
  Please provide a comprehensive and detailed explanation
  of how to implement a REST API in Node.js.
`;

const optimizedPrompt = `Explain implementing a REST API in Node.js. Be concise.`;

console.log(`Original: ~${countTokensEstimate(originalPrompt)} tokens`);
console.log(`Optimized: ~${countTokensEstimate(optimizedPrompt)} tokens`);
// Original: ~47 tokens
// Optimized: ~13 tokens (72% reduction)
```

### Step 5: Caching for Cost Reduction

```typescript
import crypto from 'crypto';
import { LRUCache } from 'lru-cache';

const responseCache = new LRUCache<string, { response: string; cost: number }>({
  max: 10000,  # 10000: 10 seconds in ms
  ttl: 24 * 60 * 60 * 1000, // 24 hours  # 1000: 1 second in ms
});

interface CachedResult {
  response: string;
  cached: boolean;
  cost: number;
  savedCost: number;
}

async function costAwareChat(
  client: Mistral,
  messages: any[],
  model: string
): Promise<CachedResult> {
  const cacheKey = crypto
    .createHash('sha256')
    .update(JSON.stringify({ messages, model }))
    .digest('hex');

  const cached = responseCache.get(cacheKey);
  if (cached) {
    return {
      response: cached.response,
      cached: true,
      cost: 0,
      savedCost: cached.cost,
    };
  }

  const response = await client.chat.complete({ model, messages });
  const content = response.choices?.[0]?.message?.content ?? '';

  const cost = estimateCost(model as any, {
    inputTokens: response.usage?.promptTokens || 0,
    outputTokens: response.usage?.completionTokens || 0,
  }).totalCost;

  responseCache.set(cacheKey, { response: content, cost });

  return {
    response: content,
    cached: false,
    cost,
    savedCost: 0,
  };
}
```

### Step 6: Usage Dashboard Query

```sql
-- Track usage in your database
CREATE TABLE mistral_usage (
  id SERIAL PRIMARY KEY,
  model VARCHAR(50),
  input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd DECIMAL(10, 6),
  user_id VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Daily cost report
SELECT
  DATE(created_at) as date,
  model,
  SUM(input_tokens) as total_input,
  SUM(output_tokens) as total_output,
  SUM(cost_usd) as total_cost
FROM mistral_usage
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY 1, 2
ORDER BY 1 DESC, 3 DESC;

-- User cost breakdown
SELECT
  user_id,
  SUM(cost_usd) as total_cost,
  COUNT(*) as request_count
FROM mistral_usage
WHERE created_at >= DATE_TRUNC('month', NOW())
GROUP BY 1
ORDER BY 2 DESC
LIMIT 10;
```

## Output
- Optimized model selection
- Token budget management
- Usage monitoring implemented
- Cost reduction strategies applied

## Cost Reduction Strategies

| Strategy | Savings | Effort |
|----------|---------|--------|
| Model selection | 50-90% | Low |
| Prompt optimization | 20-50% | Low |
| Response caching | 30-80% | Medium |
| Batch processing | 10-30% | Medium |
| Max tokens limit | 10-40% | Low |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected costs | Untracked usage | Implement monitoring |
| Budget exceeded | No alerts | Set up budget alerts |
| Inefficient model | Wrong selection | Use task-based selection |
| Long responses | No limit | Set maxTokens |

## Examples

### Quick Cost Check
```typescript
// Estimate monthly cost
const monthlyRequests = 100_000;
const avgInputTokens = 500;  # HTTP 500 Internal Server Error
const avgOutputTokens = 200;  # HTTP 200 OK

const smallCost = estimateCost('mistral-small-latest', {
  inputTokens: avgInputTokens * monthlyRequests,
  outputTokens: avgOutputTokens * monthlyRequests,
});

const largeCost = estimateCost('mistral-large-latest', {
  inputTokens: avgInputTokens * monthlyRequests,
  outputTokens: avgOutputTokens * monthlyRequests,
});

console.log(`Small model: $${smallCost.totalCost.toFixed(2)}/month`);
console.log(`Large model: $${largeCost.totalCost.toFixed(2)}/month`);
// Small model: $22.00/month
// Large model: $220.00/month
```

## Resources
- [Mistral AI Pricing](https://mistral.ai/pricing/)
- [Mistral AI Console](https://console.mistral.ai/)

## Next Steps
For architecture patterns, see `mistral-reference-architecture`.