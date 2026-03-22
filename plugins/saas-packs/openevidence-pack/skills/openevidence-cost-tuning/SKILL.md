---
name: openevidence-cost-tuning
description: |
  Optimize OpenEvidence costs through tier selection, sampling, and usage monitoring.
  Use when analyzing OpenEvidence billing, reducing API costs,
  or implementing usage monitoring and budget alerts.
  Trigger with phrases like "openevidence cost", "openevidence billing",
  "reduce openevidence costs", "openevidence pricing", "openevidence expensive", "openevidence budget".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, openevidence]
---

# OpenEvidence Cost Tuning

## Overview
Optimize OpenEvidence costs through smart tier selection, sampling, and usage monitoring.

## Prerequisites
- Access to OpenEvidence billing dashboard
- Understanding of current usage patterns
- Database for usage tracking (optional)
- Alerting system configured (optional)

## Pricing Tiers

| Tier | Monthly Cost | Included | Overage |
|------|-------------|----------|---------|
| Free / Developer | $0 | 1,000 requests | N/A |
| Pro / Growth | $99 | 100,000 requests | $0.001/request |
| Enterprise | Custom | Unlimited | Volume discounts |

## Cost Estimation

```typescript
interface UsageEstimate {
  requestsPerMonth: number;
  tier: string;
  estimatedCost: number;
  recommendation?: string;
}

function estimateOpenEvidenceCost(requestsPerMonth: number): UsageEstimate {
  if (requestsPerMonth <= 1000) {
    return { requestsPerMonth, tier: 'Free', estimatedCost: 0 };
  }

  if (requestsPerMonth <= 100000) {
    return { requestsPerMonth, tier: 'Pro', estimatedCost: 99 };
  }

  const proOverage = (requestsPerMonth - 100000) * 0.001;
  const proCost = 99 + proOverage;

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
class OpenEvidenceUsageMonitor {
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
      this.sendAlert('Approaching OpenEvidence budget limit');
    }
  }

  estimatedCost(): number {
    return estimateOpenEvidenceCost(this.requestCount).estimatedCost;
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
  await openevidenceClient.trackEvent(event);
}
```

### Step 2: Batching Requests
```typescript
// Instead of N individual calls
await Promise.all(ids.map(id => openevidenceClient.get(id)));

// Use batch endpoint (1 call)
await openevidenceClient.batchGet(ids);
```

### Step 3: Caching (from P16)
- Cache frequently accessed data
- Use cache invalidation webhooks
- Set appropriate TTLs

### Step 4: Compression
```typescript
const client = new OpenEvidenceClient({
  compression: true, // Enable gzip
});
```

## Budget Alerts

```bash
# Set up billing alerts in OpenEvidence dashboard
# Or use API if available:
# Check OpenEvidence documentation for billing APIs
```

## Cost Dashboard Query

```sql
-- If tracking usage in your database
SELECT
  DATE_TRUNC('day', created_at) as date,
  COUNT(*) as requests,
  SUM(response_bytes) as bytes,
  COUNT(*) * 0.001 as estimated_cost
FROM openevidence_api_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

## Instructions

### Step 1: Analyze Current Usage
Review OpenEvidence dashboard for usage patterns and costs.

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
const estimate = estimateOpenEvidenceCost(yourMonthlyRequests);
console.log(`Tier: ${estimate.tier}, Cost: $${estimate.estimatedCost}`);
if (estimate.recommendation) {
  console.log(`💡 ${estimate.recommendation}`);
}
```

## Resources
- [OpenEvidence Pricing](https://openevidence.com/pricing)
- [OpenEvidence Billing Dashboard](https://dashboard.openevidence.com/billing)

## Next Steps
For architecture patterns, see `openevidence-reference-architecture`.