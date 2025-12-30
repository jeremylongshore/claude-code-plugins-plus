---
name: vercel-known-pitfalls
description: |
  Identify and avoid Vercel anti-patterns and common integration mistakes.
  Use when reviewing Vercel code for issues, onboarding new developers,
  or auditing existing Vercel integrations for best practices violations.
  Trigger with phrases like "vercel mistakes", "vercel anti-patterns",
  "vercel pitfalls", "vercel what not to do", "vercel code review".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Vercel Known Pitfalls

## Overview
Common mistakes and anti-patterns when integrating with Vercel.

## Prerequisites
- Access to Vercel codebase for review
- Understanding of async/await patterns
- Knowledge of security best practices
- Familiarity with rate limiting concepts

## Pitfall #1: Synchronous API Calls in Request Path

### ❌ Anti-Pattern
```typescript
// User waits for Vercel API call
app.post('/checkout', async (req, res) => {
  const payment = await vercelClient.processPayment(req.body);  // 2-5s latency
  const notification = await vercelClient.sendEmail(payment);   // Another 1-2s
  res.json({ success: true });  // User waited 3-7s
});
```

### ✅ Better Approach
```typescript
// Return immediately, process async
app.post('/checkout', async (req, res) => {
  const jobId = await queue.enqueue('process-checkout', req.body);
  res.json({ jobId, status: 'processing' });  // 50ms response
});

// Background job
async function processCheckout(data) {
  const payment = await vercelClient.processPayment(data);
  await vercelClient.sendEmail(payment);
}
```

---

## Pitfall #2: Not Handling Rate Limits

### ❌ Anti-Pattern
```typescript
// Blast requests, crash on 429
for (const item of items) {
  await vercelClient.process(item);  // Will hit rate limit
}
```

### ✅ Better Approach
```typescript
import pLimit from 'p-limit';

const limit = pLimit(5);  // Max 5 concurrent
const rateLimiter = new RateLimiter({ tokensPerSecond: 10 });

for (const item of items) {
  await rateLimiter.acquire();
  await limit(() => vercelClient.process(item));
}
```

---

## Pitfall #3: Leaking API Keys

### ❌ Anti-Pattern
```typescript
// In frontend code (visible to users!)
const client = new VercelClient({
  apiKey: 'sk_live_ACTUAL_KEY_HERE',  // Anyone can see this
});

// In git history
git commit -m "add API key"  // Exposed forever
```

### ✅ Better Approach
```typescript
// Backend only, environment variable
const client = new VercelClient({
  apiKey: process.env.VERCEL_API_KEY,
});

// Use .gitignore
.env
.env.local
.env.*.local
```

---

## Pitfall #4: Ignoring Idempotency

### ❌ Anti-Pattern
```typescript
// Network error on response = duplicate charge!
try {
  await vercelClient.charge(order);
} catch (error) {
  if (error.code === 'NETWORK_ERROR') {
    await vercelClient.charge(order);  // Charged twice!
  }
}
```

### ✅ Better Approach
```typescript
const idempotencyKey = `order-${order.id}-${Date.now()}`;

await vercelClient.charge(order, {
  idempotencyKey,  // Safe to retry
});
```

---

## Pitfall #5: Not Validating Webhooks

### ❌ Anti-Pattern
```typescript
// Trust any incoming request
app.post('/webhook', (req, res) => {
  processWebhook(req.body);  // Attacker can send fake events
  res.sendStatus(200);
});
```

### ✅ Better Approach
```typescript
app.post('/webhook',
  express.raw({ type: 'application/json' }),
  (req, res) => {
    const signature = req.headers['x-vercel-signature'];
    if (!verifyVercelSignature(req.body, signature)) {
      return res.sendStatus(401);
    }
    processWebhook(JSON.parse(req.body));
    res.sendStatus(200);
  }
);
```

---

## Pitfall #6: Missing Error Handling

### ❌ Anti-Pattern
```typescript
// Crashes on any error
const result = await vercelClient.get(id);
console.log(result.data.nested.value);  // TypeError if missing
```

### ✅ Better Approach
```typescript
try {
  const result = await vercelClient.get(id);
  console.log(result?.data?.nested?.value ?? 'default');
} catch (error) {
  if (error instanceof VercelNotFoundError) {
    return null;
  }
  if (error instanceof VercelRateLimitError) {
    await sleep(error.retryAfter);
    return this.get(id);  // Retry
  }
  throw error;  // Rethrow unknown errors
}
```

---

## Pitfall #7: Hardcoding Configuration

### ❌ Anti-Pattern
```typescript
const client = new VercelClient({
  timeout: 5000,  // Too short for some operations
  baseUrl: 'https://api.vercel.com',  // Can't change for staging
});
```

### ✅ Better Approach
```typescript
const client = new VercelClient({
  timeout: parseInt(process.env.VERCEL_TIMEOUT || '30000'),
  baseUrl: process.env.VERCEL_BASE_URL || 'https://api.vercel.com',
});
```

---

## Pitfall #8: Not Implementing Circuit Breaker

### ❌ Anti-Pattern
```typescript
// When Vercel is down, every request hangs
for (const user of users) {
  await vercelClient.sync(user);  // All timeout sequentially
}
```

### ✅ Better Approach
```typescript
import CircuitBreaker from 'opossum';

const breaker = new CircuitBreaker(vercelClient.sync, {
  timeout: 10000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
});

// Fails fast when circuit is open
for (const user of users) {
  await breaker.fire(user).catch(handleFailure);
}
```

---

## Pitfall #9: Logging Sensitive Data

### ❌ Anti-Pattern
```typescript
console.log('Request:', JSON.stringify(request));  // Logs API key, PII
console.log('User:', user);  // Logs email, phone
```

### ✅ Better Approach
```typescript
const redacted = {
  ...request,
  apiKey: '[REDACTED]',
  user: { id: user.id },  // Only non-sensitive fields
};
console.log('Request:', JSON.stringify(redacted));
```

---

## Pitfall #10: No Graceful Degradation

### ❌ Anti-Pattern
```typescript
// Entire feature broken if Vercel is down
const recommendations = await vercelClient.getRecommendations(userId);
return renderPage({ recommendations });  // Page crashes
```

### ✅ Better Approach
```typescript
let recommendations;
try {
  recommendations = await vercelClient.getRecommendations(userId);
} catch (error) {
  recommendations = await getFallbackRecommendations(userId);
  reportDegradedService('vercel', error);
}
return renderPage({ recommendations, degraded: !recommendations });
```

---

## Instructions

### Step 1: Review for Anti-Patterns
Scan codebase for each pitfall pattern.

### Step 2: Prioritize Fixes
Address security issues first, then performance.

### Step 3: Implement Better Approach
Replace anti-patterns with recommended patterns.

### Step 4: Add Prevention
Set up linting and CI checks to prevent recurrence.

## Output
- Anti-patterns identified
- Fixes prioritized and implemented
- Prevention measures in place
- Code quality improved

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Too many findings | Legacy codebase | Prioritize security first |
| Pattern not detected | Complex code | Manual review |
| False positive | Similar code | Whitelist exceptions |
| Fix breaks tests | Behavior change | Update tests |

## Examples

### Quick Pitfall Scan
```bash
# Check for common pitfalls
grep -r "sk_live_" --include="*.ts" src/        # Key leakage
grep -r "console.log" --include="*.ts" src/     # Potential PII logging
```

## Resources
- [Vercel Security Guide](https://vercel.com/docs/security)
- [Vercel Best Practices](https://vercel.com/docs/best-practices)

## Quick Reference Card

| Pitfall | Detection | Prevention |
|---------|-----------|------------|
| Sync in request | High latency | Use queues |
| Rate limit ignore | 429 errors | Implement backoff |
| Key leakage | Git history scan | Env vars, .gitignore |
| No idempotency | Duplicate records | Idempotency keys |
| Unverified webhooks | Security audit | Signature verification |
| Missing error handling | Crashes | Try-catch, types |
| Hardcoded config | Code review | Environment variables |
| No circuit breaker | Cascading failures | opossum, resilience4j |
| Logging PII | Log audit | Redaction middleware |
| No degradation | Total outages | Fallback systems |