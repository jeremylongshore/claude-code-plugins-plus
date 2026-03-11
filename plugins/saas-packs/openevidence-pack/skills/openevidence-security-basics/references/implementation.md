# OpenEvidence Security Basics - Implementation Details

## Secret Manager Integration (GCP)
```typescript
export async function getOpenEvidenceCredentials() {
  const [apiKeyVersion] = await client.accessSecretVersion({ name: 'projects/my-project/secrets/openevidence-api-key/versions/latest' });
  const [orgIdVersion] = await client.accessSecretVersion({ name: 'projects/my-project/secrets/openevidence-org-id/versions/latest' });
  return { apiKey: apiKeyVersion.payload!.data!.toString(), orgId: orgIdVersion.payload!.data!.toString() };
}
```

## PHI Handling - Input Sanitization
```typescript
export function sanitizeQueryForOpenEvidence(question: string, patientContext?: PatientContext): SanitizedQuery {
  let sanitized = question;
  sanitized = sanitized.replace(/\b(Mr\.|Mrs\.|Ms\.|Dr\.)\s+[A-Z][a-z]+\b/g, '[PATIENT]');
  sanitized = sanitized.replace(/\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b/g, '[DATE]');
  sanitized = sanitized.replace(/\bMRN[:\s]*\d+\b/gi, '[MRN]');
  sanitized = sanitized.replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]');
  return { question: sanitized, context: patientContext ? { ageRange: getAgeRange(patientContext.age), sex: patientContext.sex } : undefined };
}
```

## HIPAA Audit Logging
```typescript
export class HIPAAAuditLogger {
  async logClinicalQuery(userId, userRole, queryId, success, request) {
    await this.logStore.insert({
      timestamp: new Date(), eventType: 'query', userId, userRole,
      action: 'clinical_query', resourceId: queryId, ipAddress: this.getClientIP(request), success,
    });
  }
}
```

## Webhook Signature Verification
Timing-safe HMAC-SHA256 signature comparison with 5-minute replay attack protection.

## Data Retention
```typescript
const HIPAA_RETENTION = {
  auditLogs: 2190,        // 6 years
  queryResults: 0,        // Do not store
  deepConsultReports: 365, // 1 year
};
```

## Secure Query Service
```typescript
export async function secureClinicalQuery(question, patientContext, user, request) {
  const sanitized = sanitizeQueryForOpenEvidence(question, patientContext);
  const response = await client.query({ question: sanitized.question, context: { specialty: 'internal-medicine', ...sanitized.context } });
  await auditLogger.logClinicalQuery(user.id, user.role, response.id, true, request);
  return response;
}
```
