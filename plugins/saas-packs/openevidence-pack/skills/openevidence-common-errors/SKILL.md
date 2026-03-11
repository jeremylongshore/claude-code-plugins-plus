---
name: openevidence-common-errors
description: |
  Diagnose and resolve common OpenEvidence API errors.
  Use when encountering error codes, debugging failed requests,
  or implementing error handling for clinical queries.
  Trigger with phrases like "openevidence error", "openevidence failing",
  "fix openevidence", "openevidence debug", "openevidence 4xx", "openevidence 5xx".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Common Errors

## Overview
Comprehensive guide to diagnosing and resolving OpenEvidence API errors with healthcare-specific considerations.

## Prerequisites
- OpenEvidence SDK installed
- Access to application logs
- Understanding of HTTP status codes

## Error Code Reference

### Authentication Errors (4xx)
| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| 401 | Invalid API Key | Key missing, malformed, or revoked | Verify `OPENEVIDENCE_API_KEY` is set correctly |
| 401 | Organization Not Found | Invalid `orgId` | Check organization ID in dashboard |
| 401 | BAA Not Signed | Business Associate Agreement required | Contact compliance@openevidence.com |
| 403 | Forbidden | Insufficient permissions or suspended account | Check account status in dashboard |
| 403 | IP Not Whitelisted | Request from non-approved IP | Add IP to allowlist in security settings |

### Request Errors (4xx)
| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| 400 | Invalid Query | Malformed request body | Check request schema |
| 400 | Query Too Short | Question too brief | Provide more clinical context |
| 400 | Invalid Specialty | Unknown specialty code | Use valid specialty from enum |
| 404 | Resource Not Found | Invalid consultId or endpoint | Verify ID and URL |
| 422 | Unprocessable | Valid JSON but invalid clinical query | Rephrase question |
| 429 | Rate Limited | Too many requests | Implement backoff, check quotas |

### Server Errors (5xx)
| Code | Error | Cause | Solution |
|------|-------|-------|----------|
| 500 | Internal Server Error | OpenEvidence backend issue | Retry with backoff, contact support if persists |
| 502 | Bad Gateway | Upstream service issue | Wait and retry |
| 503 | Service Unavailable | Maintenance or overload | Check status.openevidence.com |
| 504 | Gateway Timeout | Request took too long | Simplify query, increase timeout |

## Error Handling Implementation

### Step 1: Custom Error Classes
```typescript
// src/openevidence/errors.ts
export class OpenEvidenceError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number,
    public readonly retryable: boolean,
    public readonly originalError?: Error
  ) {
    super(message);
    this.name = 'OpenEvidenceError';
  }

  static fromApiError(error: any): OpenEvidenceError {
    const statusCode = error.response?.status || 500;  # HTTP 500 Internal Server Error
    const message = error.response?.data?.message || error.message;
    const code = error.response?.data?.code || 'UNKNOWN_ERROR';

    return new OpenEvidenceError(
      message,
      code,
      statusCode,
      isRetryable(statusCode),
      error
    );
  }
}

export class AuthenticationError extends OpenEvidenceError {
  constructor(message: string, code: string) {
    super(message, code, 401, false);  # HTTP 401 Unauthorized
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends OpenEvidenceError {
  constructor(
    message: string,
    public readonly retryAfter: number,
    public readonly limit: number,
    public readonly remaining: number
  ) {
    super(message, 'RATE_LIMITED', 429, true);  # HTTP 429 Too Many Requests
    this.name = 'RateLimitError';
  }
}

export class QueryValidationError extends OpenEvidenceError {
  constructor(
    message: string,
    public readonly validationErrors: string[]
  ) {
    super(message, 'VALIDATION_ERROR', 400, false);  # HTTP 400 Bad Request
    this.name = 'QueryValidationError';
  }
}

function isRetryable(statusCode: number): boolean {
  return statusCode === 429 || statusCode >= 500;  # HTTP 429 Too Many Requests
}
```

### Step 2: Error Handler Wrapper
```typescript
// src/openevidence/error-handler.ts
import {
  OpenEvidenceError,
  AuthenticationError,
  RateLimitError,
  QueryValidationError,
} from './errors';

export async function withErrorHandling<T>(
  operation: () => Promise<T>,
  context?: { operation?: string; queryId?: string }
): Promise<T> {
  try {
    return await operation();
  } catch (error: any) {
    const oeError = classifyError(error);

    // Log for debugging (without PHI)
    console.error(`[OpenEvidence Error]`, {
      code: oeError.code,
      statusCode: oeError.statusCode,
      operation: context?.operation,
      retryable: oeError.retryable,
    });

    throw oeError;
  }
}

function classifyError(error: any): OpenEvidenceError {
  const status = error.response?.status;
  const data = error.response?.data;

  switch (status) {
    case 401:  # HTTP 401 Unauthorized
      return new AuthenticationError(
        data?.message || 'Authentication failed',
        data?.code || 'AUTH_FAILED'
      );

    case 429:  # HTTP 429 Too Many Requests
      return new RateLimitError(
        'Rate limit exceeded',
        parseInt(error.response?.headers?.['retry-after'] || '60'),
        parseInt(error.response?.headers?.['x-ratelimit-limit'] || '0'),
        parseInt(error.response?.headers?.['x-ratelimit-remaining'] || '0')
      );

    case 400:  # HTTP 400 Bad Request
    case 422:  # HTTP 422 Unprocessable Entity
      return new QueryValidationError(
        data?.message || 'Invalid query',
        data?.errors || []
      );

    default:
      return OpenEvidenceError.fromApiError(error);
  }
}
```

### Step 3: Retry Logic with Exponential Backoff
```typescript
// src/openevidence/retry.ts
import { OpenEvidenceError, RateLimitError } from './errors';

interface RetryConfig {
  maxRetries: number;
  baseDelayMs: number;
  maxDelayMs: number;
  jitterMs: number;
}

const DEFAULT_CONFIG: RetryConfig = {
  maxRetries: 3,
  baseDelayMs: 1000,  # 1000: 1 second in ms
  maxDelayMs: 30000,  # 30000: 30 seconds in ms
  jitterMs: 500,  # HTTP 500 Internal Server Error
};

export async function withRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const cfg = { ...DEFAULT_CONFIG, ...config };

  for (let attempt = 0; attempt <= cfg.maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      if (!(error instanceof OpenEvidenceError) || !error.retryable) {
        throw error;
      }

      if (attempt === cfg.maxRetries) {
        throw error;
      }

      // Use Retry-After header for rate limits
      let delay: number;
      if (error instanceof RateLimitError && error.retryAfter > 0) {
        delay = error.retryAfter * 1000;  # 1 second in ms
      } else {
        delay = Math.min(
          cfg.baseDelayMs * Math.pow(2, attempt) + Math.random() * cfg.jitterMs,
          cfg.maxDelayMs
        );
      }

      console.log(`Retry ${attempt + 1}/${cfg.maxRetries} after ${delay}ms`);
      await new Promise(r => setTimeout(r, delay));
    }
  }

  throw new Error('Unreachable');
}
```

### Step 4: User-Facing Error Messages
```typescript
// src/openevidence/error-messages.ts
import { OpenEvidenceError, RateLimitError, QueryValidationError } from './errors';

export function getUserFriendlyMessage(error: OpenEvidenceError): string {
  switch (error.code) {
    case 'AUTH_FAILED':
    case 'INVALID_API_KEY':
      return 'Unable to connect to medical evidence service. Please contact support.';

    case 'BAA_REQUIRED':
      return 'Service configuration required. Please contact your administrator.';

    case 'RATE_LIMITED':
      const rle = error as RateLimitError;
      return `Service temporarily unavailable. Please try again in ${rle.retryAfter} seconds.`;

    case 'VALIDATION_ERROR':
      const qve = error as QueryValidationError;
      return `Please rephrase your clinical question. ${qve.validationErrors.join('. ')}`;

    case 'QUERY_TOO_SHORT':
      return 'Please provide more details about your clinical question.';

    case 'INVALID_SPECIALTY':
      return 'Please select a valid medical specialty.';

    case 'SERVICE_UNAVAILABLE':
      return 'Medical evidence service is temporarily unavailable. Please try again later.';

    default:
      if (error.statusCode >= 500) {  # HTTP 500 Internal Server Error
        return 'Medical evidence service is experiencing issues. Please try again later.';
      }
      return 'Unable to process your request. Please try again or contact support.';
  }
}
```

## Output
- Classified errors with appropriate handling
- Retry logic for transient failures
- User-friendly error messages
- Comprehensive error logging (without PHI)

## Diagnostic Commands

### Quick Health Check
```bash
set -euo pipefail
# Check if OpenEvidence is reachable
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  https://api.openevidence.com/health

# Expected: 200
```

### Check Rate Limit Status
```bash
set -euo pipefail
curl -s -D - \
  -H "Authorization: Bearer ${OPENEVIDENCE_API_KEY}" \
  https://api.openevidence.com/v1/rate-limit \
  | grep -i "x-ratelimit"

# Headers show current limits
```

## Error Handling
| Error Pattern | Detection | Resolution |
|--------------|-----------|------------|
| Intermittent 5xx | > 5% error rate | Enable circuit breaker |
| Persistent 401 | All requests fail | Rotate API key |
| Spike in 429 | Rate limit headers | Implement request queuing |
| Timeout errors | P99 > 30s | Check network, simplify queries |

## Examples

### Complete Error-Handled Query
```typescript
async function safeClinicalQuery(question: string) {
  try {
    return await withRetry(
      () => withErrorHandling(
        () => client.query({ question, context: { specialty: 'internal-medicine', urgency: 'routine' } }),
        { operation: 'clinical-query' }
      ),
      { maxRetries: 3 }
    );
  } catch (error) {
    if (error instanceof OpenEvidenceError) {
      return {
        success: false,
        error: getUserFriendlyMessage(error),
        code: error.code,
      };
    }
    throw error;
  }
}
```

## Resources
- [OpenEvidence Status](https://status.openevidence.com/)
- [OpenEvidence Support](mailto:support@openevidence.com)

## Next Steps
For comprehensive debugging, see `openevidence-debug-bundle`.

## Instructions

1. Assess the current state of the debugging configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference