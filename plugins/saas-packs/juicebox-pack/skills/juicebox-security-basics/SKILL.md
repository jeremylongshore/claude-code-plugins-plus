---
name: juicebox-security-basics
description: |
  Apply Juicebox security best practices.
  Use when securing API keys, implementing access controls,
  or auditing Juicebox integration security.
  Trigger with phrases like "juicebox security", "secure juicebox",
  "juicebox API key security", "juicebox access control".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Security Basics

## Overview
Implement security best practices for Juicebox API integration.

## Prerequisites
- Juicebox API access configured
- Environment variable management
- Basic security awareness

## Instructions

### Step 1: Secure API Key Storage

**NEVER do this:**
```typescript
// BAD - hardcoded API key
const client = new JuiceboxClient({
  apiKey: 'jb_prod_xxxxxxxxxxxxxxxxx'
});
```

**DO this instead:**
```typescript
// GOOD - environment variable
const client = new JuiceboxClient({
  apiKey: process.env.JUICEBOX_API_KEY
});
```

**For production, use secret managers:**
```typescript
// AWS Secrets Manager
import { SecretsManager } from '@aws-sdk/client-secrets-manager';

async function getApiKey(): Promise<string> {
  const client = new SecretsManager({ region: 'us-east-1' });
  const secret = await client.getSecretValue({
    SecretId: 'juicebox/api-key'
  });
  return JSON.parse(secret.SecretString!).apiKey;
}

// Google Secret Manager
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

async function getApiKey(): Promise<string> {
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: 'projects/my-project/secrets/juicebox-api-key/versions/latest'
  });
  return version.payload!.data!.toString();
}
```

### Step 2: Implement Access Controls
```typescript
// middleware/juicebox-auth.ts
export function requireJuiceboxAccess(requiredScope: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const user = req.user;

    if (!user) {
      return res.status(401).json({ error: 'Authentication required' });  # HTTP 401 Unauthorized
    }

    const hasScope = user.permissions.includes(`juicebox:${requiredScope}`);
    if (!hasScope) {
      return res.status(403).json({ error: 'Insufficient permissions' });  # HTTP 403 Forbidden
    }

    next();
  };
}

// Usage
app.get('/api/search',
  requireJuiceboxAccess('search:read'),
  async (req, res) => {
    // ... search logic
  }
);
```

### Step 3: Audit Logging
```typescript
// lib/audit-logger.ts
export class JuiceboxAuditLogger {
  async logAccess(event: AuditEvent): Promise<void> {
    const entry = {
      timestamp: new Date().toISOString(),
      userId: event.userId,
      action: event.action,
      resource: event.resource,
      ip: event.ip,
      userAgent: event.userAgent,
      success: event.success,
      metadata: event.metadata
    };

    await db.auditLogs.insert(entry);

    // Alert on suspicious activity
    if (this.isSuspicious(event)) {
      await this.sendAlert(entry);
    }
  }

  private isSuspicious(event: AuditEvent): boolean {
    return (
      event.action === 'bulk_export' ||
      event.metadata?.resultCount > 1000 ||  # 1000: 1 second in ms
      this.isOffHours()
    );
  }
}
```

### Step 4: Data Privacy Compliance
```typescript
// lib/data-privacy.ts
export class DataPrivacyHandler {
  // Redact PII before logging
  redactPII(profile: Profile): RedactedProfile {
    return {
      ...profile,
      email: this.maskEmail(profile.email),
      phone: profile.phone ? '***-***-' + profile.phone.slice(-4) : undefined
    };
  }

  // Track data access for compliance
  async recordDataAccess(
    userId: string,
    profileIds: string[],
    purpose: string
  ): Promise<void> {
    await db.dataAccessLog.insert({
      userId,
      profileIds,
      purpose,
      timestamp: new Date(),
      retentionExpiry: addDays(new Date(), 90)
    });
  }

  // Handle data deletion requests
  async handleDeletionRequest(requestId: string): Promise<void> {
    // Remove from local cache/storage
    // Log compliance action
    // Notify relevant systems
  }
}
```

## Security Checklist

```markdown
## Juicebox Security Audit Checklist

### API Key Management
- [ ] API keys stored in secret manager
- [ ] No hardcoded keys in code
- [ ] Keys rotated every 90 days
- [ ] Separate keys for dev/staging/prod

### Access Control
- [ ] Role-based access implemented
- [ ] Principle of least privilege
- [ ] Regular access reviews

### Logging & Monitoring
- [ ] All API calls logged
- [ ] Audit trail maintained
- [ ] Anomaly detection enabled
- [ ] Alerts configured

### Data Privacy
- [ ] PII handling documented
- [ ] Data retention policy
- [ ] GDPR/CCPA compliance
- [ ] Deletion request workflow
```

## Error Handling
| Security Issue | Detection | Response |
|----------------|-----------|----------|
| Key exposure | Git scanning | Rotate immediately |
| Unauthorized access | Audit logs | Revoke access |
| Data breach | Monitoring | Incident response |

## Resources
- [Security Best Practices](https://juicebox.ai/docs/security)
- [Compliance Documentation](https://juicebox.ai/compliance)

## Next Steps
After security setup, see `juicebox-prod-checklist` for deployment readiness.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Examples

**Basic usage**: Apply juicebox security basics to a standard project setup with default configuration options.

**Advanced scenario**: Customize juicebox security basics for production environments with multiple constraints and team-specific requirements.