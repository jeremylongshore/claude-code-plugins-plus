---
name: salesforce-reliability-patterns
description: |
  Implement Salesforce reliability patterns including circuit breakers, idempotent upserts, and fallback caching.
  Use when building fault-tolerant Salesforce integrations, implementing retry strategies,
  or adding resilience to production Salesforce services.
  Trigger with phrases like "salesforce reliability", "salesforce circuit breaker",
  "salesforce idempotent", "salesforce resilience", "salesforce fallback", "salesforce retry".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Reliability Patterns

## Overview
Production-grade reliability patterns for Salesforce integrations: circuit breakers for API outages, idempotent operations using External IDs, graceful degradation with cached data, and dead letter queues for failed operations.

## Prerequisites
- jsforce connection configured
- Understanding of Salesforce error codes (see `salesforce-common-errors`)
- Redis or database for state management (optional)
- opossum or similar circuit breaker library

## Instructions

### Step 1: Circuit Breaker for Salesforce API

```typescript
import CircuitBreaker from 'opossum';
import { getConnection } from './salesforce/connection';

// Circuit breaker wraps all Salesforce calls
const sfBreaker = new CircuitBreaker(
  async (fn: () => Promise<any>) => fn(),
  {
    timeout: 30000,                // SF calls can be slow — 30s timeout
    errorThresholdPercentage: 50,  // Open circuit at 50% error rate
    resetTimeout: 60000,           // Try again after 1 minute
    volumeThreshold: 10,           // Need 10 calls before evaluating
    errorFilter: (error: any) => {
      // Don't count client errors as circuit-breaking failures
      const nonCircuitErrors = ['INVALID_FIELD', 'MALFORMED_QUERY', 'REQUIRED_FIELD_MISSING'];
      return nonCircuitErrors.includes(error.errorCode);
    },
  }
);

sfBreaker.on('open', () => {
  console.error('CIRCUIT OPEN: Salesforce API failing — requests will fail fast');
  // Alert ops team
});

sfBreaker.on('halfOpen', () => {
  console.info('CIRCUIT HALF-OPEN: Testing Salesforce recovery...');
});

sfBreaker.on('close', () => {
  console.info('CIRCUIT CLOSED: Salesforce API recovered');
});

// Usage — all SF calls go through the breaker
async function safeSfQuery<T>(soql: string): Promise<T[]> {
  return sfBreaker.fire(async () => {
    const conn = await getConnection();
    const result = await conn.query<T>(soql);
    return result.records;
  });
}
```

### Step 2: Idempotent Operations with External IDs

```typescript
// Salesforce's upsert with External ID is naturally idempotent
// Same data sent twice = same result (no duplicates)

async function idempotentSync(
  objectType: string,
  records: Record<string, any>[],
  externalIdField: string = 'External_ID__c'
): Promise<{ success: number; failed: number; errors: any[] }> {
  const conn = await getConnection();
  let success = 0;
  let failed = 0;
  const errors: any[] = [];

  // Process in batches of 200 (sObject Collections limit)
  for (let i = 0; i < records.length; i += 200) {
    const batch = records.slice(i, i + 200);

    const results = await conn.sobject(objectType).upsert(batch, externalIdField);

    for (const result of Array.isArray(results) ? results : [results]) {
      if (result.success) {
        success++;
      } else {
        failed++;
        errors.push(result.errors);
      }
    }
  }

  return { success, failed, errors };
}

// Safe to retry — same External_ID__c values will update, not duplicate
await idempotentSync('Account', [
  { External_ID__c: 'EXT-001', Name: 'Acme', Industry: 'Tech' },
  { External_ID__c: 'EXT-002', Name: 'Globex', Industry: 'Manufacturing' },
], 'External_ID__c');
```

### Step 3: Retry with Salesforce-Specific Error Classification

```typescript
const SF_RETRYABLE_ERRORS = [
  'REQUEST_LIMIT_EXCEEDED',    // API limit — wait and retry
  'SERVER_UNAVAILABLE',        // SF is down temporarily
  'UNABLE_TO_LOCK_ROW',        // Record contention
  'INVALID_SESSION_ID',        // Token expired — re-auth and retry
];

const SF_FATAL_ERRORS = [
  'INVALID_FIELD',             // Code bug — won't fix itself
  'MALFORMED_QUERY',           // Code bug
  'REQUIRED_FIELD_MISSING',    // Data issue
  'INVALID_TYPE',              // Wrong sObject name
  'INSUFFICIENT_ACCESS_OR_READONLY', // Permission issue
];

async function retryableSfCall<T>(
  operation: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error: any) {
      const errorCode = error.errorCode || error.name;

      if (SF_FATAL_ERRORS.includes(errorCode)) {
        throw error; // Don't retry — it won't help
      }

      if (errorCode === 'INVALID_SESSION_ID') {
        // Re-authenticate, then retry
        await getConnection(); // Forces re-login
        continue;
      }

      if (attempt === maxRetries) throw error;

      const delay = 2000 * Math.pow(2, attempt - 1); // 2s, 4s, 8s
      console.warn(`Retryable SF error ${errorCode}, attempt ${attempt}/${maxRetries}`);
      await new Promise(r => setTimeout(r, delay));
    }
  }
  throw new Error('Unreachable');
}
```

### Step 4: Graceful Degradation with Stale Data

```typescript
import { Redis } from 'ioredis';
const redis = new Redis(process.env.REDIS_URL);

async function queryWithFallback<T>(
  soql: string,
  cacheKey: string,
  cacheTtlSeconds = 300
): Promise<{ data: T[]; stale: boolean }> {
  try {
    // Try live Salesforce query
    const records = await safeSfQuery<T>(soql);

    // Update cache for fallback
    await redis.set(cacheKey, JSON.stringify(records), 'EX', cacheTtlSeconds * 10);

    return { data: records, stale: false };
  } catch (error) {
    // Salesforce unavailable — serve cached data
    const cached = await redis.get(cacheKey);
    if (cached) {
      console.warn(`SF unavailable, serving stale data for ${cacheKey}`);
      return { data: JSON.parse(cached), stale: true };
    }

    throw new Error(`Salesforce unavailable and no cached data for ${cacheKey}`);
  }
}

// Usage
const { data: accounts, stale } = await queryWithFallback<Account>(
  "SELECT Id, Name, Industry FROM Account WHERE Industry = 'Technology' LIMIT 50",
  'sf:accounts:tech'
);
if (stale) {
  // Show warning to user: "Data may be outdated"
}
```

### Step 5: Dead Letter Queue for Failed Operations

```typescript
interface SfDeadLetter {
  id: string;
  operation: string;
  objectType: string;
  payload: Record<string, any>;
  errorCode: string;
  errorMessage: string;
  attempts: number;
  firstFailure: Date;
  lastAttempt: Date;
}

class SalesforceDeadLetterQueue {
  async enqueue(entry: Omit<SfDeadLetter, 'id' | 'firstFailure' | 'lastAttempt' | 'attempts'>): Promise<void> {
    const dlq: SfDeadLetter = {
      ...entry,
      id: crypto.randomUUID(),
      attempts: 1,
      firstFailure: new Date(),
      lastAttempt: new Date(),
    };
    await redis.lpush('sf:dlq', JSON.stringify(dlq));
    console.error(`DLQ: ${entry.operation} on ${entry.objectType} failed: ${entry.errorCode}`);
  }

  async reprocess(): Promise<{ processed: number; failed: number }> {
    let processed = 0, failed = 0;
    let entry: string | null;

    while ((entry = await redis.rpop('sf:dlq')) !== null) {
      const dlq: SfDeadLetter = JSON.parse(entry);
      try {
        const conn = await getConnection();
        await conn.sobject(dlq.objectType)[dlq.operation](dlq.payload);
        processed++;
      } catch (error: any) {
        dlq.attempts++;
        dlq.lastAttempt = new Date();
        if (dlq.attempts < 5) {
          await redis.lpush('sf:dlq', JSON.stringify(dlq));
        } else {
          console.error(`DLQ: Giving up on ${dlq.id} after 5 attempts`);
          // Move to permanent failure store
        }
        failed++;
      }
    }
    return { processed, failed };
  }
}
```

## Output
- Circuit breaker preventing cascading failures
- Idempotent upserts using External IDs
- Error classification (retryable vs fatal)
- Graceful degradation with stale cache data
- Dead letter queue for failed operations

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Circuit stays open | SF outage or wrong threshold | Check status.salesforce.com; tune thresholds |
| Duplicate records | Not using External ID upsert | Add External_ID__c field, use upsert |
| DLQ growing | Persistent error (e.g., permission) | Check error codes — may need fix, not retry |
| Stale cache too old | Long SF outage | Set max stale age, show user warning |

## Resources
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Opossum Documentation](https://nodeshift.dev/opossum/)
- [External ID Fields](https://help.salesforce.com/s/articleView?id=sf.fields_about_external_ids.htm)
- [Salesforce Error Codes](https://developer.salesforce.com/docs/atlas.en-us.api_rest.meta/api_rest/errorcodes.htm)

## Next Steps
For policy enforcement, see `salesforce-policy-guardrails`.
