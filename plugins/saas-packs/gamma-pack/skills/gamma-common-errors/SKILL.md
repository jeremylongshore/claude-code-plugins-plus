---
name: gamma-common-errors
description: |
  Debug and resolve common Gamma API errors.
  Use when encountering authentication failures, rate limits,
  generation errors, or unexpected API responses.
  Trigger with phrases like "gamma error", "gamma not working",
  "gamma API error", "gamma debug", "gamma troubleshoot".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Common Errors

## Overview
Reference guide for debugging and resolving common Gamma API errors.

## Prerequisites
- Active Gamma integration
- Access to logs and error messages
- Understanding of HTTP status codes

## Error Reference

### Authentication Errors (401/403)

```typescript
// Error: Invalid API Key
{
  "error": "unauthorized",
  "message": "Invalid or expired API key"
}
```

**Solutions:**
1. Verify API key in Gamma dashboard
2. Check environment variable is set: `echo $GAMMA_API_KEY`
3. Ensure key hasn't been rotated
4. Check for trailing whitespace in key

### Rate Limit Errors (429)

```typescript
// Error: Rate Limited
{
  "error": "rate_limited",
  "message": "Too many requests",
  "retry_after": 60
}
```

**Solutions:**
1. Implement exponential backoff
2. Check rate limit headers: `X-RateLimit-Remaining`
3. Upgrade plan for higher limits
4. Queue requests with delays

```typescript
async function withRetry(fn: () => Promise<any>, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (err) {
      if (err.code === 'rate_limited' && i < maxRetries - 1) {
        const delay = (err.retryAfter || Math.pow(2, i)) * 1000;  # 1000: 1 second in ms
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw err;
    }
  }
}
```

### Generation Errors (400/500)

```typescript
// Error: Generation Failed
{
  "error": "generation_failed",
  "message": "Unable to generate presentation",
  "details": "Content too complex"
}
```

**Solutions:**
1. Simplify prompt or reduce slide count
2. Remove special characters from content
3. Check content length limits
4. Try different style setting

### Timeout Errors

```typescript
// Error: Request Timeout
{
  "error": "timeout",
  "message": "Request timed out after 30000ms"
}
```

**Solutions:**
1. Increase client timeout setting
2. Use async job pattern for large presentations
3. Check network connectivity
4. Reduce request complexity

```typescript
const gamma = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
  timeout: 60000, // 60 seconds  # 60000: 1 minute in ms
});
```

### Export Errors

```typescript
// Error: Export Failed
{
  "error": "export_failed",
  "message": "Unable to export presentation",
  "format": "pdf"
}
```

**Solutions:**
1. Verify presentation exists and is complete
2. Check supported export formats
3. Ensure no pending generation jobs
4. Try exporting with lower quality setting

## Debugging Tools

### Enable Debug Logging
```typescript
const gamma = new GammaClient({
  apiKey: process.env.GAMMA_API_KEY,
  debug: true, // Logs all requests/responses
});
```

### Check API Status
```typescript
const status = await gamma.status();
console.log('API Status:', status.healthy ? 'OK' : 'Issues');
console.log('Services:', status.services);
```

## Error Handling Pattern
```typescript
import { GammaError, RateLimitError, AuthError } from '@gamma/sdk';

try {
  const result = await gamma.presentations.create({ ... });
} catch (err) {
  if (err instanceof AuthError) {
    console.error('Check your API key');
  } else if (err instanceof RateLimitError) {
    console.error(`Retry after ${err.retryAfter}s`);
  } else if (err instanceof GammaError) {
    console.error('API Error:', err.message);
  } else {
    throw err;
  }
}
```

## Resources
- [Gamma Status Page](https://status.gamma.app)
- [Gamma Error Codes](https://gamma.app/docs/errors)
- [Gamma Support](https://gamma.app/support)

## Next Steps
Proceed to `gamma-debug-bundle` for comprehensive debugging tools.

## Instructions

1. Assess the current state of the authentication configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with authentication |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply gamma common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize gamma common errors for production environments with multiple constraints and team-specific requirements.