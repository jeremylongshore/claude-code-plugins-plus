# MaintainX Common Errors - Implementation Guide

> Full implementation details and code examples for the `maintainx-common-errors` skill.

# MaintainX Common Errors

## Overview

Quick reference guide for diagnosing and resolving common MaintainX API errors.

## Prerequisites

- MaintainX API credentials configured
- Basic understanding of HTTP status codes
- Access to API logs

## Error Reference

### Authentication Errors (4xx)

#### 401 Unauthorized

```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

**Causes:**
1. Missing API key in request
2. Invalid or expired API key
3. Incorrect Authorization header format

**Solutions:**

```typescript
// Check 1: Verify API key is set
const apiKey = process.env.MAINTAINX_API_KEY;
if (!apiKey) {
  throw new Error('MAINTAINX_API_KEY environment variable not set');
}

// Check 2: Correct header format (note the space after "Bearer")
const headers = {
  'Authorization': `Bearer ${apiKey}`,  // Correct
  // NOT: `Bearer${apiKey}` (missing space)
  // NOT: apiKey (missing Bearer prefix)
  'Content-Type': 'application/json',
};

// Check 3: Test with curl
// curl -H "Authorization: Bearer YOUR_API_KEY" \
//      https://api.getmaintainx.com/v1/users?limit=1
```

**Quick Fix Script:**

```bash
#!/bin/bash
# test-maintainx-auth.sh

if [ -z "$MAINTAINX_API_KEY" ]; then
  echo "ERROR: MAINTAINX_API_KEY not set"
  exit 1
fi

echo "Testing MaintainX authentication..."
RESPONSE=$(curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $MAINTAINX_API_KEY" \
  -H "Content-Type: application/json" \
  "https://api.getmaintainx.com/v1/users?limit=1")

HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" == "200" ]; then
  echo "SUCCESS: Authentication working"
  echo "$BODY" | jq '.users | length' | xargs -I {} echo "Found {} users"
else
  echo "FAILED: HTTP $HTTP_CODE"
  echo "$BODY"
fi
```

#### 403 Forbidden

```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions for this operation"
}
```

**Causes:**
1. API key doesn't have required permissions
2. Plan tier doesn't include this feature
3. Organization restrictions

**Solutions:**

```typescript
// Check your subscription tier
// Professional/Enterprise required for full API access

// Verify in MaintainX dashboard:
// Settings > Account > Subscription

// For multi-org tokens, ensure org ID header:
const headers = {
  'Authorization': `Bearer ${apiKey}`,
  'X-Organization-Id': orgId,  // Required for multi-org
  'Content-Type': 'application/json',
};
```

### Request Errors (4xx)

#### 400 Bad Request

```json
{
  "error": "Bad Request",
  "message": "Validation failed",
  "details": {
    "title": "Title is required"
  }
}
```

**Common Causes:**

```typescript
// Missing required fields
await client.createWorkOrder({
  // ERROR: title is required
  description: 'Some description',
});

// FIX: Include required fields
await client.createWorkOrder({
  title: 'Work Order Title',  // Required
  description: 'Some description',
});

// Invalid enum values
await client.createWorkOrder({
  title: 'Test',
  priority: 'URGENT',  // ERROR: Invalid value
});

// FIX: Use valid enum values
await client.createWorkOrder({
  title: 'Test',
  priority: 'HIGH',  // Valid: NONE, LOW, MEDIUM, HIGH
});

// Invalid date format
await client.createWorkOrder({
  title: 'Test',
  dueDate: '2025-01-15',  // May need full ISO format
});

// FIX: Use ISO 8601 format
await client.createWorkOrder({
  title: 'Test',
  dueDate: new Date('2025-01-15').toISOString(),  // 2025-01-15T00:00:00.000Z
});
```

#### 404 Not Found

```json
{
  "error": "Not Found",
  "message": "Work order not found"
}
```

**Causes & Solutions:**

```typescript
// Cause 1: Wrong resource ID
const workOrder = await client.getWorkOrder('invalid_id');

// Solution: Verify ID exists
async function safeGetWorkOrder(client, id) {
  try {
    return await client.getWorkOrder(id);
  } catch (error) {
    if (error.response?.status === 404) {
      console.error(`Work order ${id} not found`);
      return null;
    }
    throw error;
  }
}

// Cause 2: Wrong endpoint
// GET /v1/workorder/123  (wrong - singular)
// GET /v1/workorders/123 (correct - plural)

// Cause 3: Resource deleted or archived
// Check if resource was recently deleted in MaintainX
```

#### 422 Unprocessable Entity

```json
{
  "error": "Unprocessable Entity",
  "message": "Invalid data",
  "details": {
    "assetId": "Asset does not exist"
  }
}
```

**Solutions:**

```typescript
// Verify referenced resources exist
async function createWorkOrderSafe(client, data) {
  // Verify asset exists
  if (data.assetId) {
    try {
      await client.getAsset(data.assetId);
    } catch (e) {
      throw new Error(`Asset ${data.assetId} not found`);
    }
  }

  // Verify location exists
  if (data.locationId) {
    try {
      await client.getLocation(data.locationId);
    } catch (e) {
      throw new Error(`Location ${data.locationId} not found`);
    }
  }

  return client.createWorkOrder(data);
}
```

### Rate Limiting (429)

```json
{
  "error": "Too Many Requests",
  "message": "Rate limit exceeded",
  "retryAfter": 60
}
```

**Solution:**

```typescript
// Implement exponential backoff
async function withRateLimitHandling(operation, maxRetries = 3) {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (error.response?.status === 429) {
        const retryAfter = error.response.headers['retry-after'] || 60;
        console.log(`Rate limited. Waiting ${retryAfter}s...`);

        if (attempt < maxRetries) {
          await new Promise(r => setTimeout(r, retryAfter * 1000));
          continue;
        }
      }
      throw error;
    }
  }
}
```

### Server Errors (5xx)

#### 500 Internal Server Error

**Solutions:**

```typescript
// Retry with exponential backoff for transient errors
async function withRetry(operation, options = {}) {
  const { maxRetries = 3, baseDelay = 1000 } = options;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      const status = error.response?.status;

      // Retry on 5xx errors
      if (status >= 500 && attempt < maxRetries) {
        const delay = baseDelay * Math.pow(2, attempt);
        console.log(`Server error. Retrying in ${delay}ms...`);
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw error;
    }
  }
}
```

#### 503 Service Unavailable

**Solutions:**
1. Check MaintainX status page
2. Wait and retry
3. Implement circuit breaker pattern

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure?: Date;
  private readonly threshold = 5;
  private readonly resetTimeout = 60000; // 1 minute

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.isOpen()) {
      throw new Error('Circuit breaker is open - service unavailable');
    }

    try {
      const result = await operation();
      this.reset();
      return result;
    } catch (error) {
      this.recordFailure();
      throw error;
    }
  }

  private isOpen(): boolean {
    if (this.failures < this.threshold) return false;
    if (!this.lastFailure) return false;

    const elapsed = Date.now() - this.lastFailure.getTime();
    return elapsed < this.resetTimeout;
  }

  private recordFailure() {
    this.failures++;
    this.lastFailure = new Date();
  }

  private reset() {
    this.failures = 0;
    this.lastFailure = undefined;
  }
}
```

## Debugging Checklist

```typescript
// Debug helper function
async function debugApiCall(client, operation, description) {
  console.log(`\n=== ${description} ===`);

  try {
    const startTime = Date.now();
    const result = await operation();
    const duration = Date.now() - startTime;

    console.log(`SUCCESS (${duration}ms)`);
    console.log('Response:', JSON.stringify(result, null, 2).slice(0, 500));
    return result;
  } catch (error) {
    console.log('FAILED');
    console.log('Status:', error.response?.status);
    console.log('Error:', error.response?.data || error.message);
    console.log('Headers:', error.response?.headers);
    throw error;
  }
}

// Usage
await debugApiCall(
  client,
  () => client.getWorkOrders({ limit: 5 }),
  'Fetching work orders'
);
```

## Output

- Identified error cause
- Applied appropriate fix
- Verified resolution

## Quick Reference

| Status | Cause | First Action |
|--------|-------|--------------|
| 401 | Auth issue | Check API key format |
| 403 | Permissions | Verify plan tier |
| 400 | Bad request | Check required fields |
| 404 | Not found | Verify resource ID |
| 422 | Invalid data | Validate references |
| 429 | Rate limit | Wait and retry |
| 5xx | Server error | Retry with backoff |

## Resources

- [MaintainX API Status](https://status.getmaintainx.com)
- [MaintainX Help Center](https://help.getmaintainx.com)
- [API Documentation](https://maintainx.dev/)

## Next Steps

For comprehensive debugging, see `maintainx-debug-bundle`.
