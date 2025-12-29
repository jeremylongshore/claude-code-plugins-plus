---
name: supabase-cost-tuning
description: |
  Supabase cost optimization with tier selection and usage monitoring.
  Trigger phrases: "supabase cost", "supabase billing",
  "reduce supabase costs", "supabase pricing", "supabase expensive".
allowed-tools: Read, Bash, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Supabase Cost Tuning

## Overview
Optimize Supabase costs through smart tier selection, sampling, and usage monitoring.

## Pricing Tiers

| Tier | Monthly Cost | Included | Overage |
|------|-------------|----------|---------|
| Free | $0 | 500MB database, 1GB storage, 50K MAUs | N/A |
| Pro | $25 | 8GB database, 100GB storage, 100K MAUs | $0.001/request |
| Enterprise | Custom | Unlimited | Volume discounts |

## Cost Estimation

```typescript
interface UsageEstimate {
  requestsPerMonth: number;
  tier: string;
  estimatedCost: number;
  recommendation?: string;
}

function estimateSupabaseCost(requestsPerMonth: number): UsageEstimate {
  if (requestsPerMonth <= 1000) {
    return { requestsPerMonth, tier: 'Free', estimatedCost: 0 };
  }

  if (requestsPerMonth <= 100000) {
    return { requestsPerMonth, tier: 'Pro', estimatedCost: 25 };
  }

  const proOverage = (requestsPerMonth - 100000) * 0.001;
  const proCost = 25 + proOverage;

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
class SupabaseUsageMonitor {
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
      this.sendAlert('Approaching Supabase budget limit');
    }
  }

  estimatedCost(): number {
    return estimateSupabaseCost(this.requestCount).estimatedCost;
  }

  private sendAlert(message: string) {
    // Send to Slack, email, PagerDuty, etc.
  }
}
```

## Cost Reduction Strategies

### 1. Request Sampling
```typescript
function shouldSample(samplingRate = 0.1): boolean {
  return Math.random() < samplingRate;
}

// Use for non-critical telemetry
if (shouldSample(0.1)) { // 10% sample
  await supabaseClient.trackEvent(event);
}
```

### 2. Batching Requests
```typescript
// Instead of N individual calls
await Promise.all(ids.map(id => supabaseClient.get(id)));

// Use batch endpoint (1 call)
await supabaseClient.batchGet(ids);
```

### 3. Caching (from P16)
- Cache frequently accessed data
- Use cache invalidation webhooks
- Set appropriate TTLs

### 4. Compression
```typescript
const client = new SupabaseClient({
  compression: true, // Enable gzip
});
```

## Budget Alerts

```bash
# Set up billing alerts in Supabase dashboard
# Or use API if available:
# Check Supabase documentation for billing APIs
```

## Cost Dashboard Query

```sql
-- If tracking usage in your database
SELECT
  DATE_TRUNC('day', created_at) as date,
  COUNT(*) as requests,
  SUM(response_bytes) as bytes,
  COUNT(*) * 0.001 as estimated_cost
FROM supabase_api_logs
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY 1
ORDER BY 1;
```

## Next Steps
For architecture patterns, see `supabase-reference-architecture`.