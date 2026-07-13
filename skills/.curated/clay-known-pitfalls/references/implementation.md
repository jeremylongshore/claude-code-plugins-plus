# Clay Known Pitfalls - Implementation Details

## Configuration

### Common Misconfiguration Checklist

```typescript
interface ClayConfigAudit {
  check: string;
  status: 'pass' | 'fail' | 'warn';
  detail: string;
}

function auditClayConfig(): ClayConfigAudit[] {
  const results: ClayConfigAudit[] = [];

  // Pitfall 1: Missing API key rotation
  const keyAge = getApiKeyAge();
  results.push({
    check: 'api_key_rotation',
    status: keyAge > 90 ? 'fail' : keyAge > 60 ? 'warn' : 'pass',
    detail: `API key is ${keyAge} days old (rotate every 90 days)`,
  });

  // Pitfall 2: No rate limit handling
  results.push({
    check: 'rate_limit_handler',
    status: hasRateLimitHandler() ? 'pass' : 'fail',
    detail: 'Rate limit handler prevents 429 cascading failures',
  });

  // Pitfall 3: Unbounded batch sizes
  const batchSize = getConfiguredBatchSize();
  results.push({
    check: 'batch_size',
    status: batchSize > 100 ? 'fail' : batchSize > 50 ? 'warn' : 'pass',
    detail: `Batch size is ${batchSize} (recommended: <=50, max: 100)`,
  });

  // Pitfall 4: Missing webhook signature verification
  results.push({
    check: 'webhook_signature',
    status: hasWebhookSignatureVerification() ? 'pass' : 'fail',
    detail: 'Webhook signature verification prevents spoofed events',
  });

  return results;
}
```

## Advanced Patterns

### Anti-Pattern: Polling Instead of Webhooks

```typescript
// BAD: Polling for enrichment results (wastes API quota)
async function pollForResults(jobId: string) {
  while (true) {
    const result = await clay.get(`/jobs/${jobId}`);
    if (result.status === 'complete') return result;
    await sleep(5000); // burns 720 requests/hour
  }
}

// GOOD: Register a webhook and wait for callback
async function submitWithWebhook(data: any) {
  const job = await clay.post('/enrich', {
    ...data,
    webhook_url: `${process.env.BASE_URL}/api/clay/webhook`,
  });
  return job.id; // result delivered asynchronously via webhook
}
```

### Anti-Pattern: N+1 API Calls

```typescript
// BAD: Individual lookup per contact (N+1 pattern)
async function enrichContacts(emails: string[]) {
  return Promise.all(emails.map((e) => clay.enrich({ email: e })));
  // 1000 emails = 1000 API calls
}

// GOOD: Use bulk endpoint
async function enrichContactsBulk(emails: string[]) {
  const chunks = chunkArray(emails, 50);
  const results = [];
  for (const chunk of chunks) {
    const batch = await clay.post('/enrich/bulk', { emails: chunk });
    results.push(...batch.results);
  }
  return results;
  // 1000 emails = 20 API calls
}
```

### Anti-Pattern: Ignoring Partial Failures

```typescript
// BAD: Entire batch fails on single error
async function processAll(items: any[]) {
  const results = await clay.post('/enrich/bulk', { items });
  return results; // if one fails, you lose the whole response
}

// GOOD: Handle partial successes
async function processAllSafely(items: any[]) {
  const results = await clay.post('/enrich/bulk', { items });
  const succeeded = results.filter((r: any) => r.status === 'success');
  const failed = results.filter((r: any) => r.status === 'error');

  if (failed.length > 0) {
    console.warn(`${failed.length}/${items.length} items failed`);
    await retryQueue.addBatch(failed.map((f: any) => f.input));
  }

  return { succeeded, failed, total: items.length };
}
```

### Anti-Pattern: Storing Raw API Responses

```typescript
// BAD: Storing entire Clay response (bloats storage, PII risk)
await db.insert('contacts', clayResponse);

// GOOD: Extract only needed fields
const contact = {
  id: clayResponse.id,
  company: clayResponse.organization?.name,
  title: clayResponse.title,
  enriched_at: new Date().toISOString(),
};
await db.insert('contacts', contact);
```

## Troubleshooting

### Debugging Silent Failures

```typescript
// Add structured logging to catch swallowed errors
function wrapClayCall(name: string, fn: Function) {
  return async (...args: any[]) => {
    const start = Date.now();
    try {
      const result = await fn(...args);
      console.log(`[Clay:${name}] OK in ${Date.now() - start}ms`);
      return result;
    } catch (err) {
      console.error(`[Clay:${name}] FAIL in ${Date.now() - start}ms`, err);
      throw err;
    }
  };
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
