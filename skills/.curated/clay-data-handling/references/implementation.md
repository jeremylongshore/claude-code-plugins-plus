# Clay Data Handling - Implementation Details

## Configuration

### PII Detection and Redaction

```typescript
interface PiiConfig {
  fields: string[];
  strategy: 'redact' | 'hash' | 'encrypt';
  salt?: string;
}

const PII_FIELDS: PiiConfig = {
  fields: ['email', 'phone', 'ssn', 'address', 'date_of_birth'],
  strategy: 'hash',
  salt: process.env.PII_SALT,
};

function redactPii(record: Record<string, any>, config: PiiConfig): Record<string, any> {
  const result = { ...record };
  for (const field of config.fields) {
    if (result[field]) {
      switch (config.strategy) {
        case 'redact':
          result[field] = '[REDACTED]';
          break;
        case 'hash':
          result[field] = hashValue(result[field], config.salt);
          break;
        case 'encrypt':
          result[field] = encryptValue(result[field]);
          break;
      }
    }
  }
  return result;
}

function hashValue(value: string, salt?: string): string {
  const crypto = require('crypto');
  return crypto.createHash('sha256').update(`${salt}${value}`).digest('hex').slice(0, 16);
}
```

## Advanced Patterns

### GDPR Data Subject Access Request (DSAR)

```typescript
async function handleDsar(subjectEmail: string) {
  // 1. Find all records associated with this email
  const records = await clay.search({
    filters: [{ field: 'email', operator: 'eq', value: subjectEmail }],
  });

  // 2. Export all data for the subject
  const exportData = records.map((r: any) => ({
    id: r.id,
    collected_at: r.created_at,
    data_categories: Object.keys(r),
    source: r._enrichment_source,
    values: r,
  }));

  return {
    subject: subjectEmail,
    exported_at: new Date().toISOString(),
    record_count: exportData.length,
    data: exportData,
  };
}

async function handleDeletionRequest(subjectEmail: string) {
  const records = await clay.search({
    filters: [{ field: 'email', operator: 'eq', value: subjectEmail }],
  });

  const results = [];
  for (const record of records) {
    await clay.delete(`/records/${record.id}`);
    results.push({ id: record.id, deleted: true });
  }

  return {
    subject: subjectEmail,
    deleted_at: new Date().toISOString(),
    records_deleted: results.length,
    audit_trail: results,
  };
}
```

### Data Retention Policy Enforcement

```typescript
interface RetentionPolicy {
  dataCategory: string;
  maxAgeDays: number;
  action: 'delete' | 'archive' | 'anonymize';
}

const RETENTION_POLICIES: RetentionPolicy[] = [
  { dataCategory: 'enrichment_raw', maxAgeDays: 90, action: 'delete' },
  { dataCategory: 'contact_data', maxAgeDays: 365, action: 'anonymize' },
  { dataCategory: 'analytics', maxAgeDays: 730, action: 'archive' },
];

async function enforceRetention() {
  for (const policy of RETENTION_POLICIES) {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - policy.maxAgeDays);

    const expired = await clay.search({
      filters: [
        { field: 'data_category', operator: 'eq', value: policy.dataCategory },
        { field: 'created_at', operator: 'lt', value: cutoff.toISOString() },
      ],
    });

    console.log(`[Retention] ${policy.dataCategory}: ${expired.length} records past ${policy.maxAgeDays}d`);

    for (const record of expired) {
      switch (policy.action) {
        case 'delete': await clay.delete(`/records/${record.id}`); break;
        case 'anonymize': await clay.patch(`/records/${record.id}`, redactPii(record, PII_FIELDS)); break;
        case 'archive': await archiveToStorage(record); break;
      }
    }
  }
}
```

## Troubleshooting

### Verifying PII Redaction

```bash
# Check that exported data has no raw PII
cat export.json | jq '.data[] | select(.email != null and (.email | test("@")))' | head -5
# Should return empty if all emails are properly hashed

# Verify hash consistency
echo -n "salt_value:test@example.com" | sha256sum | cut -c1-16
```

### CCPA Opt-Out Verification

```typescript
async function verifyCcpaOptOut(email: string): Promise<boolean> {
  const records = await clay.search({
    filters: [{ field: 'email', operator: 'eq', value: email }],
  });
  return records.length === 0;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
