# Customer.io Common Errors - Implementation Guide

## Error Categories

### Authentication Errors

#### Error: 401 Unauthorized
```json
{
  "meta": {
    "error": "Unauthorized"
  }
}
```
**Cause**: Invalid Site ID or API Key
**Solution**:
1. Verify credentials in Customer.io Settings > API Credentials
2. Check you're using Track API key (not App API key) for identify/track
3. Ensure environment variables are loaded correctly
```bash
# Verify environment variables
echo "Site ID: ${CUSTOMERIO_SITE_ID:0:8}..."
echo "API Key: ${CUSTOMERIO_API_KEY:0:8}..."
```

#### Error: 403 Forbidden
**Cause**: API key doesn't have required permissions
**Solution**: Generate new API key with correct scope (Track vs App API)

### Request Errors

#### Error: 400 Bad Request - Invalid identifier
```json
{
  "meta": {
    "error": "identifier is required"
  }
}
```
**Cause**: Missing or empty user ID
**Solution**:
```typescript
// Wrong
await client.identify('', { email: 'user@example.com' });

// Correct
await client.identify('user-123', { email: 'user@example.com' });
```

#### Error: 400 Bad Request - Invalid timestamp
```json
{
  "meta": {
    "error": "timestamp must be a valid unix timestamp"
  }
}
```
**Cause**: Using milliseconds instead of seconds
**Solution**:
```typescript
// Wrong
{ created_at: Date.now() } // 1704067200000

// Correct
{ created_at: Math.floor(Date.now() / 1000) } // 1704067200
```

#### Error: 400 Bad Request - Invalid email
**Cause**: Malformed email address
**Solution**:
```typescript
// Validate email before sending
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
if (!emailRegex.test(email)) {
  throw new Error('Invalid email format');
}
```

### Rate Limiting

#### Error: 429 Too Many Requests
```json
{
  "meta": {
    "error": "Rate limit exceeded"
  }
}
```
**Cause**: Exceeded API rate limits
**Solution**:
```typescript
// Implement exponential backoff
async function withBackoff(fn: () => Promise<any>, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error: any) {
      if (error.status === 429 && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000;
        await new Promise(r => setTimeout(r, delay));
        continue;
      }
      throw error;
    }
  }
}
```

### Delivery Issues

#### Issue: Email not delivered
**Diagnostic steps**:
1. Check People > User > Activity for event receipt
2. Verify campaign is active and user matches segment
3. Check Deliverability > Suppression list
4. Review message preview for errors

```bash
# Check user exists via API
curl -X GET "https://track.customer.io/api/v1/customers/user-123" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY"
```

#### Issue: Event not triggering campaign
**Cause**: Event name mismatch or missing attributes
**Solution**:
```typescript
// Check exact event name in dashboard
// Event names are case-sensitive
await client.track(userId, {
  name: 'signed_up',  // Must match exactly
  data: { source: 'web' }
});
```

#### Issue: User not in segment
**Cause**: Missing or incorrect attributes
**Solution**:
1. Check segment conditions in dashboard
2. Verify user has required attributes
3. Check attribute types match (string vs number)

### SDK-Specific Errors

#### Node.js: TypeError - Cannot read property
```typescript
// Wrong - SDK not initialized
const client = new TrackClient(undefined, undefined);

// Correct - Check env vars exist
if (!process.env.CUSTOMERIO_SITE_ID) {
  throw new Error('CUSTOMERIO_SITE_ID not set');
}
```

#### Python: ConnectionError
```python
# Handle network errors
import customerio
from customerio.errors import CustomerIOError

try:
    cio.identify(id='user-123', email='user@example.com')
except CustomerIOError as e:
    print(f"Customer.io error: {e}")
except ConnectionError as e:
    print(f"Network error: {e}")
```

## Diagnostic Commands

### Check API Connectivity
```bash
curl -X POST "https://track.customer.io/api/v1/customers/test-user" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}' \
  -w "\nHTTP Status: %{http_code}\n"
```

### Verify Event Delivery
```bash
curl -X POST "https://track.customer.io/api/v1/customers/test-user/events" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"test_event","data":{"test":true}}'
```

## Error Handling
| Error Code | Meaning | Action |
|------------|---------|--------|
| 400 | Bad Request | Check request format and data |
| 401 | Unauthorized | Verify API credentials |
| 403 | Forbidden | Check API key permissions |
| 404 | Not Found | Verify endpoint URL |
| 429 | Rate Limited | Implement backoff |
| 500 | Server Error | Retry with backoff |
