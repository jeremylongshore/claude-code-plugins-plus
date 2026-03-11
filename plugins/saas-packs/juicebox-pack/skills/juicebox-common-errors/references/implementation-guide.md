# Juicebox Common Errors - Implementation Guide

Detailed implementation examples and code patterns.

## Error Reference

### Authentication Errors

#### 401 Unauthorized
```
Error: Invalid or expired API key
Code: AUTHENTICATION_FAILED
```

**Causes:**
- API key is incorrect
- API key has been revoked
- Environment variable not set

**Solutions:**
```bash
# Verify API key is set
echo $JUICEBOX_API_KEY

# Test with curl
curl -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/auth/verify
```

#### 403 Forbidden
```
Error: Insufficient permissions for this operation
Code: PERMISSION_DENIED
```

**Causes:**
- API key lacks required scope
- Account tier limitation
- Feature not available in plan

**Solutions:**
- Check API key permissions in dashboard
- Upgrade account tier if needed
- Contact support for access

### Rate Limiting Errors

#### 429 Too Many Requests
```
Error: Rate limit exceeded
Code: RATE_LIMITED
Retry-After: 60
```

**Causes:**
- Exceeded requests per minute
- Exceeded daily quota
- Burst limit hit

**Solutions:**
```typescript
// Implement exponential backoff
async function withBackoff(fn: () => Promise<any>, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (error.code === 'RATE_LIMITED') {
        const delay = error.retryAfter * 1000 || Math.pow(2, i) * 1000;
        await sleep(delay);
        continue;
      }
      throw error;
    }
  }
}
```

### Search Errors

#### 400 Bad Request - Invalid Query
```
Error: Invalid search query syntax
Code: INVALID_QUERY
Details: Unexpected token at position 15
```

**Causes:**
- Malformed query syntax
- Invalid field name
- Unclosed quotes

**Solutions:**
```typescript
// Validate query before sending
function validateQuery(query: string): boolean {
  const openQuotes = (query.match(/"/g) || []).length;
  if (openQuotes % 2 !== 0) return false;

  const openParens = (query.match(/\(/g) || []).length;
  const closeParens = (query.match(/\)/g) || []).length;
  if (openParens !== closeParens) return false;

  return true;
}
```

#### 404 Profile Not Found
```
Error: Profile with ID 'xxx' not found
Code: NOT_FOUND
```

**Causes:**
- Profile ID is invalid
- Profile has been removed
- Stale cache reference

**Solutions:**
- Verify profile ID format
- Handle not found gracefully
- Implement cache invalidation

### Network Errors

#### ETIMEDOUT
```
Error: Request timed out
Code: TIMEOUT
```

**Solutions:**
```typescript
// Increase timeout for large searches
const client = new JuiceboxClient({
  apiKey: process.env.JUICEBOX_API_KEY,
  timeout: 60000 // 60 seconds
});
```

## Diagnostic Commands

```bash
# Check API status
curl https://status.juicebox.ai/api/status

# Verify connectivity
curl -I https://api.juicebox.ai/v1/health

# Test authentication
curl -H "Authorization: Bearer $JUICEBOX_API_KEY" \
  https://api.juicebox.ai/v1/auth/me
```

## Error Handling Pattern

```typescript
try {
  const results = await juicebox.search.people(query);
} catch (error) {
  if (error.code === 'RATE_LIMITED') {
    // Queue for retry
  } else if (error.code === 'INVALID_QUERY') {
    // Fix query syntax
  } else if (error.code === 'AUTHENTICATION_FAILED') {
    // Refresh credentials
  } else {
    // Log and alert
    logger.error('Juicebox error', { error });
  }
}
```
