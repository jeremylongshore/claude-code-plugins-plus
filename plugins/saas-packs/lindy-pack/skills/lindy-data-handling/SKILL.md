---
name: lindy-data-handling
description: |
  Implement Lindy PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Lindy integrations.
  Trigger with phrases like "lindy data", "lindy PII",
  "lindy GDPR", "lindy data retention", "lindy privacy", "lindy CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, lindy]
---

# Lindy Data Handling

## Overview
Handle sensitive data correctly when integrating with Lindy.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- Lindy SDK with data export capabilities
- Database for audit logging
- Scheduled job infrastructure for cleanup

## Data Classification

| Category | Examples | Handling |
|----------|----------|----------|
| PII | Email, name, phone | Encrypt, minimize |
| Sensitive | API keys, tokens | Never log, rotate |
| Business | Usage metrics | Aggregate when possible |
| Public | Product names | Standard handling |

## PII Detection

```typescript
const PII_PATTERNS = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'ssn', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: 'credit_card', regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
];

function detectPII(text: string): { type: string; match: string }[] {
  const findings: { type: string; match: string }[] = [];

  for (const pattern of PII_PATTERNS) {
    const matches = text.matchAll(pattern.regex);
    for (const match of matches) {
      findings.push({ type: pattern.type, match: match[0] });
    }
  }

  return findings;
}
```

## Data Redaction

```typescript
function redactPII(data: Record<string, any>): Record<string, any> {
  const sensitiveFields = ['email', 'phone', 'ssn', 'password', 'apiKey'];
  const redacted = { ...data };

  for (const field of sensitiveFields) {
    if (redacted[field]) {
      redacted[field] = '[REDACTED]';
    }
  }

  return redacted;
}

// Use in logging
console.log('Lindy request:', redactPII(requestData));
```

## Data Retention Policy

### Retention Periods
| Data Type | Retention | Reason |
|-----------|-----------|--------|
| API logs | 30 days | Debugging |
| Error logs | 90 days | Root cause analysis |
| Audit logs | 7 years | Compliance |
| PII | Until deletion request | GDPR/CCPA |

### Automatic Cleanup

```typescript
async function cleanupLindyData(retentionDays: number): Promise<void> {
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - retentionDays);

  await db.lindyLogs.deleteMany({
    createdAt: { $lt: cutoff },
    type: { $nin: ['audit', 'compliance'] },
  });
}

// Schedule daily cleanup
cron.schedule('0 3 * * *', () => cleanupLindyData(30));
```

## GDPR/CCPA Compliance

### Data Subject Access Request (DSAR)

```typescript
async function exportUserData(userId: string): Promise<DataExport> {
  const lindyData = await lindyClient.getUserData(userId);

  return {
    source: 'Lindy',
    exportedAt: new Date().toISOString(),
    data: {
      profile: lindyData.profile,
      activities: lindyData.activities,
      // Include all user-related data
    },
  };
}
```

### Right to Deletion

```typescript
async function deleteUserData(userId: string): Promise<DeletionResult> {
  // 1. Delete from Lindy
  await lindyClient.deleteUser(userId);

  // 2. Delete local copies
  await db.lindyUserCache.deleteMany({ userId });

  // 3. Audit log (required to keep)
  await auditLog.record({
    action: 'GDPR_DELETION',
    userId,
    service: 'lindy',
    timestamp: new Date(),
  });

  return { success: true, deletedAt: new Date() };
}
```

## Data Minimization

```typescript
// Only request needed fields
const user = await lindyClient.getUser(userId, {
  fields: ['id', 'name'], // Not email, phone, address
});

// Don't store unnecessary data
const cacheData = {
  id: user.id,
  name: user.name,
  // Omit sensitive fields
};
```

## Instructions

### Step 1: Classify Data
Categorize all Lindy data by sensitivity level.

### Step 2: Implement PII Detection
Add regex patterns to detect sensitive data in logs.

### Step 3: Configure Redaction
Apply redaction to sensitive fields before logging.

### Step 4: Set Up Retention
Configure automatic cleanup with appropriate retention periods.

## Output
- Data classification documented
- PII detection implemented
- Redaction in logging active
- Retention policy enforced

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in logs | Missing redaction | Wrap logging with redact |
| Deletion failed | Data locked | Check dependencies |
| Export incomplete | Timeout | Increase batch size |
| Audit gap | Missing entries | Review log pipeline |

## Examples

### Quick PII Scan
```typescript
const findings = detectPII(JSON.stringify(userData));
if (findings.length > 0) {
  console.warn(`PII detected: ${findings.map(f => f.type).join(', ')}`);
}
```

### Redact Before Logging
```typescript
const safeData = redactPII(apiResponse);
logger.info('Lindy response:', safeData);
```

### GDPR Data Export
```typescript
const userExport = await exportUserData('user-123');
await sendToUser(userExport);
```

## Resources
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [CCPA Compliance Guide](https://oag.ca.gov/privacy/ccpa)
- [Lindy Privacy Guide](https://docs.lindy.com/privacy)

## Next Steps
For enterprise access control, see `lindy-enterprise-rbac`.