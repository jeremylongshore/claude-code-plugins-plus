---
name: salesforce-data-handling
description: |
  Implement Salesforce data privacy, GDPR/CCPA compliance, and field-level encryption patterns.
  Use when handling PII in Salesforce records, implementing data subject access requests,
  or configuring Salesforce Shield encryption.
  Trigger with phrases like "salesforce data privacy", "salesforce PII",
  "salesforce GDPR", "salesforce data retention", "salesforce encryption", "salesforce CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Data Handling

## Overview
Handle sensitive data correctly when integrating with Salesforce: PII classification, GDPR/CCPA compliance with Salesforce's Individual object, data retention, and field-level encryption.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- Salesforce org with data classification enabled (Setup > Data Classification)
- For encryption: Salesforce Shield license (Platform Encryption)

## Instructions

### Step 1: Salesforce Data Classification

```typescript
// Salesforce has built-in data classification on fields
// Setup > Object Manager > [Object] > Fields > [Field] > Edit > Data Sensitivity Level

// Query field classification metadata
const conn = await getConnection();
const contactMeta = await conn.sobject('Contact').describe();

const sensitiveFields = contactMeta.fields
  .filter((f: any) => f.compoundFieldName === null) // Skip compound fields
  .map((f: any) => ({
    name: f.name,
    label: f.label,
    type: f.type,
    encrypted: f.encrypted || false,
    // Check custom data sensitivity via field metadata
  }));

// PII fields in standard Salesforce objects
const PII_FIELDS: Record<string, string[]> = {
  Contact: ['FirstName', 'LastName', 'Email', 'Phone', 'MailingAddress', 'Birthdate'],
  Lead: ['FirstName', 'LastName', 'Email', 'Phone', 'Company'],
  Account: ['Phone', 'Website'], // Less PII, but may contain it
  User: ['Email', 'Phone', 'Username'],
  Case: ['SuppliedEmail', 'SuppliedName', 'SuppliedPhone'],
};
```

### Step 2: GDPR — Individual Object & Consent

```typescript
// Salesforce has a built-in "Individual" object for GDPR consent tracking
// Setup > Data Protection and Privacy > Enable Individual object

// Link Contact to Individual for consent tracking
await conn.sobject('Individual').create({
  FirstName: 'Jane',
  LastName: 'Smith',
  HasOptedOutTracking: false,
  HasOptedOutProcessing: false,
  HasOptedOutSolicit: true,
});

// Check consent before processing
const contact = await conn.query(`
  SELECT Id, FirstName, LastName, Email,
    Individual.HasOptedOutTracking,
    Individual.HasOptedOutProcessing
  FROM Contact
  WHERE Id = '003xxxxxxxxxxxx'
`);

const individual = contact.records[0]?.Individual;
if (individual?.HasOptedOutProcessing) {
  console.log('Contact has opted out of data processing — skip');
}
```

### Step 3: Data Subject Access Request (DSAR)

```typescript
// GDPR Article 15: Right of Access
async function exportContactData(contactId: string): Promise<object> {
  const conn = await getConnection();

  // Gather all data related to this contact
  const [contact, cases, activities, opportunities] = await Promise.all([
    conn.query(`
      SELECT FIELDS(ALL) FROM Contact WHERE Id = '${contactId}' LIMIT 1
    `),
    conn.query(`
      SELECT Id, Subject, Description, CreatedDate, Status
      FROM Case WHERE ContactId = '${contactId}'
    `),
    conn.query(`
      SELECT Id, Subject, ActivityDate, Description
      FROM Task WHERE WhoId = '${contactId}'
    `),
    conn.query(`
      SELECT Id, Name, StageName, Amount
      FROM Opportunity WHERE Id IN (
        SELECT OpportunityId FROM OpportunityContactRole WHERE ContactId = '${contactId}'
      )
    `),
  ]);

  return {
    exportDate: new Date().toISOString(),
    subject: 'Data Subject Access Request',
    contact: contact.records[0],
    cases: cases.records,
    activities: activities.records,
    opportunities: opportunities.records,
  };
}
```

### Step 4: Right to Deletion (Right to be Forgotten)

```typescript
// GDPR Article 17: Right to Erasure
async function deleteContactData(contactId: string): Promise<void> {
  const conn = await getConnection();

  // 1. Delete related records first (due to lookup relationships)
  const tasks = await conn.query(`SELECT Id FROM Task WHERE WhoId = '${contactId}'`);
  if (tasks.records.length > 0) {
    await conn.sobject('Task').destroy(tasks.records.map((t: any) => t.Id));
  }

  // 2. Delete the contact
  await conn.sobject('Contact').destroy(contactId);

  // 3. Audit log (required — don't delete this)
  await conn.sobject('Integration_Log__c').create({
    Action__c: 'GDPR_DELETION',
    Record_Id__c: contactId,
    Object_Type__c: 'Contact',
    Timestamp__c: new Date().toISOString(),
  });

  // 4. Delete from local caches/databases too
  console.log(`Contact ${contactId} deleted from Salesforce (GDPR erasure)`);
}
```

### Step 5: Data Redaction in Logs

```typescript
// NEVER log raw Salesforce records containing PII
function redactSfRecord(record: Record<string, any>, objectType: string): Record<string, any> {
  const piiFields = PII_FIELDS[objectType] || [];
  const redacted = { ...record };

  for (const field of piiFields) {
    if (redacted[field]) {
      redacted[field] = '[REDACTED]';
    }
  }

  return redacted;
}

// Usage in logging
const contacts = await conn.query('SELECT Id, FirstName, LastName, Email FROM Contact LIMIT 5');
for (const contact of contacts.records) {
  console.log('Processing:', redactSfRecord(contact, 'Contact'));
  // Logs: { Id: '003xx', FirstName: '[REDACTED]', LastName: '[REDACTED]', Email: '[REDACTED]' }
}
```

### Step 6: Salesforce Shield Platform Encryption

```
For field-level encryption at rest (Salesforce Shield license required):

Setup > Platform Encryption > Encryption Policy:
- Encrypt: Contact.Email, Contact.Phone, Lead.Email
- Key Management: Salesforce-managed or customer-managed (BYOK)

Limitations of encrypted fields:
- Cannot use in WHERE clause (use deterministic encryption for filters)
- Cannot use in ORDER BY
- Cannot use in aggregate functions
- SOQL LIKE operator not supported on encrypted fields
```

## Output
- Data classification for PII fields documented
- GDPR consent tracking via Individual object
- DSAR export function for data subject access
- Right to deletion with audit trail
- Log redaction preventing PII exposure

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `FIELD_NOT_FOUND: Individual` | Individual object not enabled | Setup > Data Protection > Enable Individual |
| Can't delete Contact | Related records exist | Delete related Tasks/Events first |
| Encrypted field in WHERE | Shield encryption limitation | Use deterministic encryption or query differently |
| PII in logs | Missing redaction | Wrap all SF logging with redactSfRecord |

## Resources
- [Salesforce Data Protection & Privacy](https://help.salesforce.com/s/articleView?id=sf.data_protection_and_privacy.htm)
- [Individual Object](https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_individual.htm)
- [Shield Platform Encryption](https://help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm)
- [GDPR Compliance in Salesforce](https://www.salesforce.com/company/privacy/)

## Next Steps
For enterprise access control, see `salesforce-enterprise-rbac`.
