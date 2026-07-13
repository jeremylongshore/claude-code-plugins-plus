# Gamma Data Handling - Implementation Details

## Data Consent Management

```typescript
interface UserConsent {
  userId: string; gammaDataProcessing: boolean; aiAnalysis: boolean;
  analytics: boolean; consentDate: Date; consentVersion: string;
}

async function checkConsent(userId: string, purpose: string): Promise<boolean> {
  const consent = await db.consents.findUnique({ where: { userId } });
  if (!consent) throw new ConsentRequiredError('User consent not obtained');
  switch (purpose) {
    case 'presentation_creation': return consent.gammaDataProcessing;
    case 'ai_generation': return consent.gammaDataProcessing && consent.aiAnalysis;
    case 'analytics': return consent.analytics;
    default: return false;
  }
}

async function createPresentation(userId: string, data: object) {
  if (!await checkConsent(userId, 'presentation_creation'))
    throw new Error('Consent required for presentation creation');
  return gamma.presentations.create(data);
}
```

## PII Handling

```typescript
const piiFields = [
  { field: 'email', type: 'email', action: 'mask' },
  { field: 'name', type: 'name', action: 'hash' },
  { field: 'phone', type: 'phone', action: 'mask' },
];

function sanitizeForLogging(data: object): object {
  const sanitized = { ...data };
  for (const pii of piiFields) {
    if (sanitized[pii.field]) {
      switch (pii.action) {
        case 'mask': sanitized[pii.field] = maskValue(sanitized[pii.field]); break;
        case 'hash': sanitized[pii.field] = hashValue(sanitized[pii.field]); break;
        case 'remove': delete sanitized[pii.field]; break;
      }
    }
  }
  return sanitized;
}
```

## Data Retention Policies

```typescript
const policies = [
  { dataType: 'presentation_exports', retentionDays: 1, action: 'delete' },
  { dataType: 'user_prompts', retentionDays: 30, action: 'anonymize' },
  { dataType: 'api_logs', retentionDays: 90, action: 'archive' },
  { dataType: 'presentations', retentionDays: 365, action: 'delete' },
];

async function enforceRetentionPolicies() {
  for (const policy of policies) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - policy.retentionDays);
    switch (policy.action) {
      case 'delete': await deleteExpiredData(policy.dataType, cutoffDate); break;
      case 'archive': await archiveExpiredData(policy.dataType, cutoffDate); break;
      case 'anonymize': await anonymizeExpiredData(policy.dataType, cutoffDate); break;
    }
  }
}
// Run daily: scheduleJob('0 2 * * *', enforceRetentionPolicies);
```

## GDPR Data Subject Requests

```typescript
async function handleAccessRequest(userId: string) {
  const userData = {
    account: await db.users.findUnique({ where: { id: userId } }),
    presentations: await db.presentations.findMany({ where: { userId } }),
    exports: await db.exports.findMany({ where: { userId } }),
    consents: await db.consents.findMany({ where: { userId } }),
    activityLogs: await db.activityLogs.findMany({ where: { userId }, take: 1000 }),
  };
  const gammaPresentations = await gamma.presentations.list({ filter: { externalUserId: userId } });
  return { ...userData, gammaData: gammaPresentations, exportedAt: new Date().toISOString() };
}

async function handleErasureRequest(userId: string) {
  await db.presentations.deleteMany({ where: { userId } });
  await db.exports.deleteMany({ where: { userId } });
  await db.activityLogs.deleteMany({ where: { userId } });

  const gammaPresentations = await gamma.presentations.list({ filter: { externalUserId: userId } });
  for (const p of gammaPresentations) await gamma.presentations.delete(p.id);

  await db.users.update({
    where: { id: userId },
    data: { email: `deleted_${Date.now()}@anonymized.local`, name: 'Deleted User', deletedAt: new Date() },
  });
  return { success: true, deletedCount: gammaPresentations.length + 1 };
}
```

## Audit Trail

```typescript
async function logAuditEvent(entry) {
  await db.auditLog.create({
    data: { ...entry, timestamp: new Date() },
  });
}

// Usage
await logAuditEvent({
  userId: user.id, action: 'PRESENTATION_CREATED',
  resource: 'presentation', resourceId: presentation.id,
  details: { title: presentation.title }, ipAddress: req.ip,
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
