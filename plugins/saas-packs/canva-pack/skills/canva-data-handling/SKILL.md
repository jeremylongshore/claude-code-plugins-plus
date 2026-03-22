---
name: canva-data-handling
description: |
  Implement Canva Connect API data handling, PII protection, and GDPR/CCPA compliance.
  Use when handling user design data, implementing data retention policies,
  or ensuring privacy compliance for Canva integrations.
  Trigger with phrases like "canva data", "canva PII",
  "canva GDPR", "canva data retention", "canva privacy", "canva CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Data Handling

## Overview

Handle Canva Connect API data responsibly. The API exposes user identifiers, design metadata, design content (via exports), uploaded assets, and comments. Apply proper classification, retention, and privacy controls.

## Data Classification — Canva API Responses

| Data Type | Source Endpoint | Sensitivity | Handling |
|-----------|----------------|-------------|----------|
| User ID, Team ID | `GET /v1/users/me` | Internal | Don't expose externally |
| User profile | `GET /v1/users/me/profile` | PII | Encrypt at rest, minimize |
| Design metadata | `GET /v1/designs` | Business | Standard protection |
| Design content | Export URLs from `/v1/exports` | Confidential | Time-limited URLs, don't cache |
| OAuth tokens | `/v1/oauth/token` | Secret | Encrypt, never log |
| Asset files | `/v1/asset-uploads` | Business | Validate, scan for malware |
| Comments | `/v1/designs/{id}/comment_threads` | PII | May contain personal data |
| Webhook payloads | Incoming POST | Mixed | Verify signature first |

## Token Protection

```typescript
// NEVER log tokens — they grant full access to a user's Canva account
function redactCanvaData(data: any): any {
  const sensitiveKeys = [
    'access_token', 'refresh_token', 'authorization',
    'client_secret', 'code_verifier',
  ];

  if (typeof data !== 'object' || data === null) return data;

  const redacted = Array.isArray(data) ? [...data] : { ...data };
  for (const key of Object.keys(redacted)) {
    if (sensitiveKeys.includes(key.toLowerCase())) {
      redacted[key] = '[REDACTED]';
    } else if (typeof redacted[key] === 'object') {
      redacted[key] = redactCanvaData(redacted[key]);
    }
  }
  return redacted;
}

// Safe logging
console.log('Canva response:', JSON.stringify(redactCanvaData(apiResponse)));
```

## Temporary URL Handling

Canva API responses include URLs with limited lifetimes. Never cache beyond expiry.

```typescript
interface CanvaUrlPolicy {
  type: string;
  ttl: number;        // milliseconds
  cacheable: boolean;
}

const URL_POLICIES: Record<string, CanvaUrlPolicy> = {
  thumbnail:  { type: 'thumbnail',  ttl: 15 * 60 * 1000,      cacheable: false }, // 15 min
  edit_url:   { type: 'edit_url',   ttl: 30 * 24 * 60 * 60 * 1000, cacheable: true }, // 30 days
  view_url:   { type: 'view_url',   ttl: 30 * 24 * 60 * 60 * 1000, cacheable: true }, // 30 days
  export_url: { type: 'export_url', ttl: 24 * 60 * 60 * 1000, cacheable: false }, // 24 hours
};

// Track URL expiry
class CanvaUrlTracker {
  private urls = new Map<string, { url: string; expiresAt: number }>();

  store(id: string, type: string, url: string): void {
    const policy = URL_POLICIES[type];
    this.urls.set(`${id}:${type}`, {
      url,
      expiresAt: Date.now() + (policy?.ttl || 0),
    });
  }

  get(id: string, type: string): string | null {
    const entry = this.urls.get(`${id}:${type}`);
    if (!entry || Date.now() > entry.expiresAt) return null;
    return entry.url;
  }
}
```

## Data Retention

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| OAuth tokens | Until user disconnects | Active session |
| Design metadata (cached) | 5-60 minutes | Performance cache |
| Export download URLs | Max 24 hours | Canva-enforced expiry |
| API request logs | 30 days | Debugging |
| Error logs | 90 days | Root cause analysis |
| Audit logs | 7 years | Compliance |
| Webhook events | 30 days | Processing/replay |

### Automatic Cleanup

```typescript
async function cleanupCanvaData(): Promise<void> {
  const now = Date.now();

  // Remove expired export URLs
  await db.exportUrls.deleteMany({ expiresAt: { $lt: new Date(now) } });

  // Remove old API logs
  const thirtyDaysAgo = new Date(now - 30 * 24 * 60 * 60 * 1000);
  await db.canvaApiLogs.deleteMany({
    createdAt: { $lt: thirtyDaysAgo },
    type: { $nin: ['audit'] },
  });

  // Remove tokens for deleted/inactive users
  await db.canvaTokens.deleteMany({ userId: { $in: await getDeletedUserIds() } });
}
```

## GDPR/CCPA Compliance

### Data Subject Access Request

```typescript
async function exportCanvaUserData(userId: string): Promise<object> {
  const tokens = await tokenStore.get(userId);

  return {
    source: 'Canva Connect API',
    exportedAt: new Date().toISOString(),
    data: {
      identity: tokens ? await canvaAPI('/users/me', tokens.accessToken) : null,
      hasActiveConnection: !!tokens,
      // Note: Canva stores the user's designs — their data is in Canva's system
      // Your app only stores: tokens, cached metadata, and integration state
    },
  };
}
```

### Right to Deletion

```typescript
async function deleteCanvaUserData(userId: string): Promise<void> {
  // 1. Revoke tokens (disconnects from Canva)
  const tokens = await tokenStore.get(userId);
  if (tokens) {
    await revokeCanvaToken(tokens.accessToken, clientId, clientSecret);
  }

  // 2. Delete stored tokens
  await tokenStore.delete(userId);

  // 3. Clear cached design metadata
  await cache.deletePattern(`canva:user:${userId}:*`);

  // 4. Audit log (required — do not delete)
  await auditLog.record({
    action: 'GDPR_DELETION',
    userId,
    service: 'canva',
    timestamp: new Date(),
  });
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Token in logs | Missing redaction | Wrap all logging with redactCanvaData |
| Expired URL served | No expiry tracking | Use CanvaUrlTracker |
| DSAR incomplete | Missing data inventory | Document all Canva data stored |
| Orphaned tokens | User deleted without cleanup | Run periodic cleanup job |

## Resources

- [Canva Privacy Policy](https://www.canva.com/policies/privacy-policy/)
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [Canva API Reference](https://www.canva.dev/docs/connect/api-reference/)

## Next Steps

For enterprise access control, see `canva-enterprise-rbac`.
