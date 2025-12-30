---
name: vercel-cost-tuning
description: |
  Optimize Vercel costs through tier selection, sampling, and usage monitoring.
  Use when analyzing Vercel billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "vercel cost", "vercel billing",
  "reduce vercel costs", "vercel pricing", "vercel expensive", "vercel budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Cost Tuning

## Overview
Optimize Vercel costs through smart tier selection, sampling, and usage monitoring.

## Prerequisites
- Access to Vercel billing dashboard
- Understanding of current usage patterns
- Database for usage tracking (optional)
- Alerting system configured (optional)

## Pricing Tiers

| Tier | Monthly Cost | Included | Overage |
|------|-------------|----------|---------|
| Hobby | $0 | 100GB bandwidth, 100GB-hrs functions | N/A |
| Pro | $20 | 1TB bandwidth, 1000GB-hrs functions | $0.001/request |
| Enterprise | Custom | Unlimited | Volume discounts |

## Cost Estimation

```typescript
interface UsageEstimate {
  requestsPerMonth: number;
  tier: string;
  estimatedCost: number;
  recommendation?: string;
}

function estimateVercelCost(requestsPerMonth: number): UsageEstimate {
  if (requestsPerMonth <= 1000) {
    return { requestsPerMonth, tier: 'Free', estimatedCost: 0 };
  }

  if (requestsPerMonth <= 100000) {
    return { requestsPerMonth, tier: 'Pro', estimatedCost: 20 };
  }

  const proOverage = (requestsPerMonth - 100000) * 0.001;
  const proCost = 20 + proOverage;

  return {
    requestsPerMonth,
    tier: 'Pro (with overage)',
    estimatedCost: proCost,
    recommendation: proCost > 500
      ? 'Consider Enterprise tier for volume discounts'
      : undefined,
  };
}
```

## Usage Monitoring

```typescript
class VercelUsageMonitor {
  private requestCount = 0;
  private bytesTransferred = 0;
  private alertThreshold: number;

  constructor(monthlyBudget: number) {
    this.alertThreshold = monthlyBudget * 0.8; // 80% warning
  }

  track(request: { bytes: number }) {
    this.requestCount++;
    this.bytesTransferred += request.bytes;

    if (this.estimatedCost() > this.alertThreshold) {
      this.sendAlert('Approaching Vercel budget limit');
    }
  }

  estimatedCost(): number {
    return estimateVercelCost(this.requestCount).estimatedCost;
  }

  private sendAlert(message: string) {
    // Send to Slack, email, PagerDuty, etc.
  }
}
```

## Cost Reduction Strategies

### Step 1: Request Sampling
```typescript
function shouldSample(samplingRate = 0.1): boolean {
  return Math.random() < samplingRate;
}

// Use for non-critical telemetry
if (shouldSample(0.1)) { // 10% sample
  await vercelClient.trackEvent(event);
}
```

### Step 2: Batching Requests
```typescript
// Instead of N individual calls
await Promise.all(ids.map(id => vercelClient.get(id)));

// Use batch endpoint (1 call)
await vercelClient.batchGet(ids);
```

### Step 3: Caching (from P16)
- Cache frequently accessed data
- Use cache invalidation webhooks
- Set appropriate TTLs

### Step 4: Compression
```typescript
const client = new VercelClient({
  compression: true, // Enable gzip
});
```

## Budget Alerts

```bash
# Set up billing alerts in Vercel dashboard
# Or use API if available:
# Check Vercel documentation for billing APIs
```

## Cost Dashboard Query

```sql
-- If tracking usage in your database
SELECT
  DATE_TRUNC('day', created_at) as date,
  COUNT(*) as requests,
  SUM(response_bytes) as bytes,
  COUNT(*) * 0.001 as estimated_cost
FROM vercel_api_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

## Instructions

### Step 1: Analyze Current Usage
Review Vercel dashboard for usage patterns and costs.

### Step 2: Select Optimal Tier
Use the cost estimation function to find the right tier.

### Step 3: Implement Monitoring
Add usage tracking to catch budget overruns early.

### Step 4: Apply Optimizations
Enable batching, caching, and sampling where appropriate.

## Output
- Optimized tier selection
- Usage monitoring implemented
- Budget alerts configured
- Cost reduction strategies applied

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected charges | Untracked usage | Implement monitoring |
| Overage fees | Wrong tier | Upgrade tier |
| Budget exceeded | No alerts | Set up alerts |
| Inefficient usage | No batching | Enable batch requests |

## Examples

### Quick Cost Check
```typescript
// Estimate monthly cost for your usage
const estimate = estimateVercelCost(yourMonthlyRequests);
console.log(`Tier: ${estimate.tier}, Cost: $${estimate.estimatedCost}`);
if (estimate.recommendation) {
  console.log(`💡 ${estimate.recommendation}`);
}
```

## Resources
- [Vercel Pricing](https://vercel.com/pricing)
- [Vercel Billing Dashboard](https://dashboard.vercel.com/billing)

## Next Steps
For architecture patterns, see `vercel-reference-architecture`.