---
name: lindy-rate-limits
description: |
  Manage Lindy AI credits, rate limits, and usage optimization.
  Use when hitting rate limits, optimizing credit consumption,
  or implementing usage controls.
  Trigger with phrases like "lindy rate limit", "lindy credits",
  "lindy quota", "lindy throttling", "lindy API limits".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, api]

---
# Lindy Rate Limits & Credits

## Overview
Lindy uses a **credit-based** consumption model, not traditional API rate limits.
Every task (everything an agent does after being triggered) costs credits. Cost
scales with model intelligence, task complexity, premium actions, and duration.

## Credit Consumption Reference

| Factor | Credit Impact |
|--------|-------------|
| Basic model task | 1-3 credits |
| Large model task (GPT-4, Claude) | ~10 credits |
| Premium actions (webhooks, phone) | Additional credits |
| Phone calls (US/Canada landline) | ~20 credits/minute |
| Phone calls (international mobile) | 21-53 credits/minute |
| Minimum per task | 1 credit |

## Plan Credit Limits

| Plan | Credits/Month | Approx Tasks | Price |
|------|--------------|-------------|-------|
| Free | 400 | ~40-400 | $0 |
| Pro | 5,000 | ~500-1,500 | $49.99/mo |
| Business | 30,000 | ~3,000-30,000 | $299.99/mo |
| Enterprise | Custom | Custom | Custom |

**Important**: Credit limit enforcement is not instant. Lindy can only limit usage
*after* the limit has been breached, not precisely when it is reached. A task that
starts before the limit may complete and push usage slightly over.

## Instructions

### Step 1: Monitor Credit Usage
In the Lindy dashboard:
1. Navigate to **Settings > Billing**
2. Review current credit consumption
3. Track per-agent credit usage
4. Set up alerts for high-consumption agents

### Step 2: Reduce Per-Task Credit Cost
**Choose the right model for each step**:
| Task Type | Recommended Model | Credits |
|-----------|------------------|---------|
| Simple routing/classification | Gemini Flash | ~1 |
| Standard text generation | Claude Sonnet / GPT-4o-mini | ~3 |
| Complex reasoning/analysis | GPT-4 / Claude Opus | ~10 |
| Phone calls (simple) | Gemini Flash | ~20/min |
| Phone calls (complex) | Claude Sonnet | ~20/min |

**Reduce action count per task**:
- Combine multiple LLM calls into one prompt with structured output
- Use deterministic actions (Set Manually) instead of AI-powered fields where possible
- Eliminate unnecessary condition branches
- Use Run Code for data transformation instead of LLM steps

### Step 3: Optimize Trigger Frequency
Prevent credit waste from over-triggering:
```
Problem: Email Received trigger fires on ALL emails → 200 tasks/day
Solution: Add trigger filter: "sender contains '@customers.com'
          AND subject does not contain 'auto-reply'"
          → 20 tasks/day (90% reduction)
```

Trigger filter best practices:
- Use AND/OR conditions with condition groups
- Filter by sender, subject, label for email
- Filter by channel, keyword, user for Slack
- Add keyword filtering to exclude automated messages

### Step 4: Implement Webhook Rate Limiting
When your application triggers Lindy agents via webhooks, rate-limit on your side:

```typescript
// Rate limiter for outbound Lindy webhook triggers
class LindyRateLimiter {
  private tokens: number;
  private maxTokens: number;
  private refillRate: number; // tokens per second
  private lastRefill: number;

  constructor(maxPerMinute: number) {
    this.maxTokens = maxPerMinute;
    this.tokens = maxPerMinute;
    this.refillRate = maxPerMinute / 60;
    this.lastRefill = Date.now();
  }

  async acquire(): Promise<boolean> {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.maxTokens, this.tokens + elapsed * this.refillRate);
    this.lastRefill = now;

    if (this.tokens >= 1) {
      this.tokens -= 1;
      return true;
    }
    return false;
  }

  get remaining(): number {
    return Math.floor(this.tokens);
  }
}

// Usage: limit to 30 webhook triggers per minute
const limiter = new LindyRateLimiter(30);

async function triggerLindy(payload: any) {
  if (!(await limiter.acquire())) {
    console.warn(`Rate limited. ${limiter.remaining} tokens remaining`);
    throw new Error('Lindy trigger rate limited');
  }
  await fetch(WEBHOOK_URL, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${SECRET}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
```

### Step 5: Budget Alerts
Set up monitoring to catch runaway agents before they drain credits:

```typescript
// Credit usage monitor
interface CreditAlert {
  threshold: number;   // percentage of monthly credits
  action: 'warn' | 'pause' | 'notify';
}

const alerts: CreditAlert[] = [
  { threshold: 50, action: 'warn' },    // 50% used: log warning
  { threshold: 80, action: 'notify' },  // 80% used: Slack alert
  { threshold: 95, action: 'pause' },   // 95% used: pause non-critical agents
];
```

### Step 6: Cost Attribution
Track which agents consume the most credits:
1. In dashboard: review per-agent task counts and credit usage
2. Identify top consumers — agents with frequent triggers or large models
3. For each high-cost agent, evaluate: Can the model be smaller? Can steps be consolidated?

## Resource Protection
Lindy includes built-in protection: when a task starts using more resources than
expected, Lindy **pauses and checks in** before continuing. This prevents runaway
agent steps from consuming unlimited credits.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Credits exhausted mid-month | High-usage agents | Upgrade plan or optimize usage |
| Task paused by Lindy | Resource protection triggered | Review agent — likely looping |
| Webhook trigger returns 429 | Too many concurrent requests | Implement client-side rate limiting |
| Agent not running | Credit balance at zero | Wait for monthly reset or upgrade |

## Resources
- [Lindy Pricing](https://www.lindy.ai/pricing)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to `lindy-security-basics` for API key and agent security.
