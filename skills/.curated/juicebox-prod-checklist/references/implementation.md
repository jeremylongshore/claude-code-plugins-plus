# Juicebox Production Checklist - Implementation

## Environment Verification

```bash
required_vars=(JUICEBOX_API_KEY JUICEBOX_PROJECT_ID JUICEBOX_WEBHOOK_SECRET)
for var in "${required_vars[@]}"; do
  [ -z "${!var}" ] && echo "MISSING: $var" || echo "OK: $var"
done
```

## API Connectivity Test

```bash
curl -X GET "https://api.juicebox.io/v1/projects/$JUICEBOX_PROJECT_ID/health" \
  -H "Authorization: Bearer $JUICEBOX_API_KEY" | jq '.status'
# Expected: "healthy"
```

## Data Sync Verification

```typescript
const stats = await client.getProjectStats(process.env.JUICEBOX_PROJECT_ID!);
if (Date.now() - new Date(stats.lastSyncAt).getTime() > 3600000) {
  throw new Error('Data sync stale (>1h)');
}
console.log(`Records synced: ${stats.recordCount}`);
```

## Webhook Validation

```typescript
import crypto from 'crypto';
function validateWebhook(payload: string, sig: string): boolean {
  const expected = crypto
    .createHmac('sha256', process.env.JUICEBOX_WEBHOOK_SECRET!)
    .update(payload).digest('hex');
  return crypto.timingSafeEqual(Buffer.from(sig,'hex'), Buffer.from(expected,'hex'));
}
```

## Checklist

| Item | Check | Expected |
|------|-------|----------|
| API health | GET /health | status: healthy |
| Auth valid | GET /me | 200 response |
| Webhooks | Dashboard | All endpoints green |
| SSL cert | openssl s_client | Valid, not expiring |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
