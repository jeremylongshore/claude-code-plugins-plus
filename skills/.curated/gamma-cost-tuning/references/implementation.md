# Gamma Cost Tuning - Implementation Details

## Usage Monitoring

```typescript
interface UsageTracker {
  presentations: number;
  generations: number;
  exports: number;
  apiCalls: number;
}

const dailyUsage: UsageTracker = { presentations: 0, generations: 0, exports: 0, apiCalls: 0 };

function trackUsage(operation: keyof UsageTracker) {
  dailyUsage[operation]++;
  const limits = { presentations: 100, generations: 50, exports: 100, apiCalls: 60 };
  const percentage = (dailyUsage[operation] / limits[operation]) * 100;
  if (percentage >= 80) {
    alertOps(`Gamma ${operation} usage high: ${percentage}%`);
  }
}
```

## User Quotas

```typescript
interface UserQuota {
  userId: string;
  presentationsRemaining: number;
  generationsRemaining: number;
  exportsRemaining: number;
  resetsAt: Date;
}

async function checkQuota(userId: string, operation: string): Promise<boolean> {
  const quota = await getQuota(userId);
  const quotaField = `${operation}Remaining` as keyof UserQuota;
  if (typeof quota[quotaField] === 'number' && quota[quotaField] <= 0) {
    throw new QuotaExceededError(`${operation} quota exceeded`);
  }
  return true;
}

async function consumeQuota(userId: string, operation: string) {
  await db.quotas.update({
    where: { userId },
    data: { [`${operation}Remaining`]: { decrement: 1 } },
  });
}
```

## Optimize AI Generation Usage

```typescript
// Cost-effective: Template + targeted AI
const costEffective = await gamma.presentations.create({
  template: 'business-pitch',
  title: 'Our AI Solution',
  slides: [
    { title: 'Introduction', content: predefinedContent },
    { title: 'Problem', generateAI: true }, // AI only where needed
    { title: 'Solution', generateAI: true },
    { title: 'Team', content: teamData },
    { title: 'Contact', content: contactInfo },
  ],
});
```

## Caching to Reduce API Calls

```typescript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);
const CACHE_TTL = 3600;

async function getCachedOrFetch<T>(key: string, fetchFn: () => Promise<T>): Promise<T> {
  const cached = await redis.get(key);
  if (cached) return JSON.parse(cached);

  const data = await fetchFn();
  await redis.setex(key, CACHE_TTL, JSON.stringify(data));
  return data;
}
```

## Batch Operations

```typescript
// Cost-effective: Batch operation
await gamma.presentations.createBatch(items); // 1 API call

// Or queue for off-peak processing
await queue.addBulk(items.map(item => ({
  name: 'create-presentation',
  data: item,
  opts: { delay: calculateOffPeakDelay() },
})));
```

## Cost Alerts and Budgets

```typescript
const budget = { monthly: 100, current: 0, alertThresholds: [50, 75, 90, 100] };

async function recordCost(operation: string, cost: number) {
  budget.current += cost;
  for (const threshold of budget.alertThresholds) {
    const percentage = (budget.current / budget.monthly) * 100;
    if (percentage >= threshold) {
      await sendBudgetAlert(threshold, budget.current);
    }
  }
  if (budget.current >= budget.monthly) {
    await disableNonCriticalFeatures();
  }
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
