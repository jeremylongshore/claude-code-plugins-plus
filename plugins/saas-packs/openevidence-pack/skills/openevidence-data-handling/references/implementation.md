# OpenEvidence Data Handling - Implementation Details

## PHI Detection and Removal
```typescript
const PHI_PATTERNS = {
  ssn: /\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b/g,
  mrn: /\b(MRN|Medical Record)[\s:#]*\d{6,12}\b/gi,
  phone: /\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  dob: /\b(DOB|Date of Birth)[\s:]*\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b/gi,
  name: /\b(Mr\.|Mrs\.|Ms\.|Dr\.|Patient)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b/g,
};

export function sanitizeForOpenEvidence(text: string): string {
  let sanitized = text;
  for (const [pattern, regex] of Object.entries(PHI_PATTERNS)) {
    sanitized = sanitized.replace(regex, `[${pattern.toUpperCase()}_REDACTED]`);
  }
  return sanitized;
}
```

## Patient Context De-identification
Maps exact ages to age ranges (infant, toddler, child, adolescent, young-adult, adult, middle-aged, elderly), specific conditions to categories (cardiovascular, metabolic, respiratory, mental-health), and drug names to drug classes.

## Encrypted Storage (AES-256-GCM)
```typescript
export class EncryptionService {
  encrypt(plaintext: string): string { /* IV + AuthTag + Encrypted */ }
  decrypt(ciphertext: string): string { /* Reverse process */ }
}

export class EncryptedCacheStore {
  async set(key: string, value: any, ttlSeconds: number): Promise<void> { /* Encrypt then store */ }
  async get<T>(key: string): Promise<T | null> { /* Fetch then decrypt */ }
}
```

## Data Retention Policies
```typescript
const HIPAA_RETENTION_POLICIES = [
  { dataType: 'audit_logs', retentionDays: 2190, archiveAfterDays: 365, encryptionRequired: true },
  { dataType: 'query_cache', retentionDays: 1, encryptionRequired: true },
  { dataType: 'deepconsult_reports', retentionDays: 365, archiveAfterDays: 90, encryptionRequired: true },
  { dataType: 'error_logs', retentionDays: 90, encryptionRequired: false },
];
```

## Audit Trail for PHI Access
Encrypted audit logging with userId, userRole, action, resourceType, ipAddress fields. IP addresses and user agents encrypted at rest. 6-year retention per HIPAA.
