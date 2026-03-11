# Customer.io Security Basics - Implementation Guide

### Step 1: Secure Credential Management
```typescript
// lib/secrets.ts
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

// Use a secrets manager instead of env vars for production
async function getCustomerIOCredentials(): Promise<{
  siteId: string;
  apiKey: string;
}> {
  // Option 1: Google Cloud Secret Manager
  const client = new SecretManagerServiceClient();
  const [siteIdVersion] = await client.accessSecretVersion({
    name: 'projects/PROJECT_ID/secrets/customerio-site-id/versions/latest'
  });
  const [apiKeyVersion] = await client.accessSecretVersion({
    name: 'projects/PROJECT_ID/secrets/customerio-api-key/versions/latest'
  });

  return {
    siteId: siteIdVersion.payload?.data?.toString() || '',
    apiKey: apiKeyVersion.payload?.data?.toString() || ''
  };
}

// Option 2: AWS Secrets Manager
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

async function getCredentialsFromAWS() {
  const client = new SecretsManager({ region: 'us-east-1' });
  const response = await client.getSecretValue({
    SecretId: 'customerio-credentials'
  });
  return JSON.parse(response.SecretString || '{}');
}
```

### Step 2: PII Data Handling
```typescript
// lib/pii-handler.ts
import crypto from 'crypto';

// Hash sensitive identifiers before sending
function hashPII(value: string): string {
  return crypto
    .createHash('sha256')
    .update(value + process.env.PII_SALT)
    .digest('hex');
}

// Sanitize attributes before sending to Customer.io
function sanitizeUserAttributes(attributes: Record<string, any>): Record<string, any> {
  const sensitiveFields = ['ssn', 'credit_card', 'password', 'bank_account'];
  const piiFields = ['phone', 'address', 'date_of_birth'];

  const sanitized = { ...attributes };

  // Remove highly sensitive fields
  for (const field of sensitiveFields) {
    delete sanitized[field];
  }

  // Hash PII fields if needed for matching but not display
  for (const field of piiFields) {
    if (sanitized[field]) {
      sanitized[`${field}_hash`] = hashPII(sanitized[field]);
      // Optionally remove plain text version
      // delete sanitized[field];
    }
  }

  return sanitized;
}

// Usage
const safeAttributes = sanitizeUserAttributes({
  email: 'user@example.com',
  phone: '+1234567890',
  ssn: '123-45-6789', // Will be removed
  plan: 'premium'
});
```

### Step 3: API Key Rotation
```typescript
// scripts/rotate-api-key.ts
async function rotateAPIKey(): Promise<void> {
  console.log('API Key Rotation Checklist:');
  console.log('1. Generate new API key in Customer.io dashboard');
  console.log('2. Update secrets manager with new key');
  console.log('3. Deploy application with new key');
  console.log('4. Verify integration works with new key');
  console.log('5. Revoke old API key in dashboard');
  console.log('6. Update documentation');

  // Automated rotation (if using secrets manager)
  // 1. Create new key via API (if supported)
  // 2. Update secret in manager
  // 3. Wait for propagation
  // 4. Revoke old key
}

// Schedule rotation every 90 days
// Add to cron or scheduled task
```

### Step 4: Webhook Security
```typescript
// lib/webhook-security.ts
import crypto from 'crypto';
import { Request, Response, NextFunction } from 'express';

// Verify Customer.io webhook signatures
function verifyWebhookSignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

// Express middleware for webhook verification
export function webhookAuthMiddleware(webhookSecret: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const signature = req.headers['x-cio-signature'] as string;

    if (!signature) {
      return res.status(401).json({ error: 'Missing signature' });
    }

    const payload = JSON.stringify(req.body);

    if (!verifyWebhookSignature(payload, signature, webhookSecret)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    next();
  };
}

// Usage
app.post('/webhooks/customerio',
  webhookAuthMiddleware(process.env.CUSTOMERIO_WEBHOOK_SECRET!),
  (req, res) => {
    // Handle verified webhook
  }
);
```

### Step 5: Access Control
```typescript
// lib/access-control.ts
interface TeamMember {
  email: string;
  role: 'admin' | 'editor' | 'viewer';
  permissions: string[];
}

// Recommended role-based access
const rolePermissions = {
  admin: [
    'manage_api_keys',
    'manage_team',
    'manage_integrations',
    'view_all_data',
    'send_campaigns'
  ],
  editor: [
    'create_campaigns',
    'edit_campaigns',
    'view_analytics',
    'manage_segments'
  ],
  viewer: [
    'view_campaigns',
    'view_analytics'
  ]
};

// Audit logging for security-sensitive operations
function logSecurityEvent(event: {
  action: string;
  actor: string;
  resource: string;
  details?: Record<string, any>;
}) {
  console.log(JSON.stringify({
    type: 'security_audit',
    timestamp: new Date().toISOString(),
    ...event
  }));
}
```

### Step 6: Data Retention
```typescript
// lib/data-retention.ts
import { APIClient } from '@customerio/track';

// Suppress/delete users for GDPR/CCPA compliance
async function deleteUserData(client: APIClient, userId: string) {
  // 1. Suppress the user (stops all messaging)
  await client.suppress(userId);

  // 2. Request full deletion through Customer.io dashboard or API
  // Note: Full deletion may require support ticket

  console.log(`User ${userId} suppressed and deletion requested`);
}

// Anonymous historical data retention
function anonymizeForAnalytics(userData: Record<string, any>) {
  return {
    ...userData,
    email: undefined,
    phone: undefined,
    first_name: undefined,
    last_name: undefined,
    // Keep aggregated/analytical data
    plan: userData.plan,
    signup_date: userData.created_at,
    total_events: userData.event_count
  };
}
```
