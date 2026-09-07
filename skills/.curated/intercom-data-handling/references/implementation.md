# Intercom Data Handling — Full Implementation

Complete, copy-ready TypeScript for each of the five compliance workflows. Every
function assumes `INTERCOM_ACCESS_TOKEN` is set (see the Authentication section in
`SKILL.md`) and that `localDb`, `hashEmail`, and the `intercom-client` SDK are
available in scope.

## Step 1: GDPR Data Subject Access Request (DSAR)

Export all Intercom data for a specific user.

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

async function exportContactData(contactId: string): Promise<{
  contact: any;
  conversations: any[];
  tags: any[];
  segments: any[];
  events: any[];
}> {
  // 1. Get contact profile
  const contact = await client.contacts.find({ contactId });

  // 2. Get conversations for this contact
  const conversations = [];
  const convList = await client.conversations.search({
    query: {
      field: "contact_ids",
      operator: "=",
      value: contactId,
    },
  });
  for (const convo of convList.conversations) {
    // Get full conversation with parts
    const full = await client.conversations.find({
      conversationId: convo.id,
    });
    conversations.push(full);
  }

  // 3. Get tags
  const tags = await client.contacts.listTags({ contactId });

  // 4. Get segments
  const segments = await client.contacts.listSegments({ contactId });

  // 5. Get data events
  const events = await client.dataEvents.list({
    type: "user",
    userId: contact.externalId,
  });

  return {
    contact: {
      id: contact.id,
      email: contact.email,
      name: contact.name,
      phone: contact.phone,
      role: contact.role,
      external_id: contact.externalId,
      custom_attributes: contact.customAttributes,
      location: contact.location,
      created_at: contact.createdAt,
      last_seen_at: contact.lastSeenAt,
    },
    conversations,
    tags: tags.data || [],
    segments: segments.data || [],
    events: events.data || [],
  };
}
```

## Step 2: Right to Deletion (GDPR Article 17)

```typescript
async function deleteContactData(contactId: string): Promise<{
  deleted: boolean;
  auditRecord: any;
}> {
  // 1. Export data for audit trail BEFORE deletion
  const exportedData = await exportContactData(contactId);

  // 2. Delete from Intercom
  await client.contacts.delete({ contactId });

  // 3. Delete from local cache/database
  await localDb.intercomContacts.deleteMany({ intercom_id: contactId });
  await localDb.intercomCache.deleteMany({ contact_id: contactId });

  // 4. Record audit entry (required by GDPR to prove deletion)
  const auditRecord = {
    action: "GDPR_DELETION",
    contact_id: contactId,
    contact_email_hash: hashEmail(exportedData.contact.email), // Hash, don't store
    deleted_at: new Date().toISOString(),
    data_sources_purged: ["intercom", "local_cache", "local_db"],
    conversations_affected: exportedData.conversations.length,
  };

  await localDb.auditLog.insert(auditRecord);

  return { deleted: true, auditRecord };
}
```

## Step 3: Intercom Data Export API (Bulk)

```typescript
// Export all messages for a date range (bulk export)
async function bulkExportMessages(
  startDate: string,
  endDate: string
): Promise<string> {
  // POST /export/messages/data
  const response = await fetch("https://api.intercom.io/export/messages/data", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${process.env.INTERCOM_ACCESS_TOKEN}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      created_at_after: Math.floor(new Date(startDate).getTime() / 1000),
      created_at_before: Math.floor(new Date(endDate).getTime() / 1000),
    }),
  });

  const data = await response.json();
  // Returns: { job_identifier: "abc123", status: "pending", download_url: null }

  // Poll for completion
  return data.job_identifier;
}

async function checkExportStatus(jobId: string): Promise<{
  status: string;
  downloadUrl?: string;
}> {
  const response = await fetch(
    `https://api.intercom.io/export/messages/data/${jobId}`,
    {
      headers: { Authorization: `Bearer ${process.env.INTERCOM_ACCESS_TOKEN}` },
    }
  );

  const data = await response.json();
  // When complete: { status: "complete", download_url: "https://..." }
  // Download URL provides a CSV file
  return { status: data.status, downloadUrl: data.download_url };
}
```

## Step 4: PII Redaction in Logs

```typescript
// Fields to always redact from log output
const PII_FIELDS = new Set([
  "email", "name", "phone", "location", "ip_address",
  "custom_attributes.address", "custom_attributes.ssn",
]);

function redactIntercomData(data: Record<string, any>): Record<string, any> {
  const redacted = { ...data };

  for (const field of PII_FIELDS) {
    const parts = field.split(".");
    let current: any = redacted;
    for (let i = 0; i < parts.length - 1; i++) {
      current = current[parts[i]];
      if (!current) break;
    }
    if (current && current[parts[parts.length - 1]]) {
      current[parts[parts.length - 1]] = "[REDACTED]";
    }
  }

  return redacted;
}

// Use in all logging
console.log("Contact data:", redactIntercomData(contact));
// Output: { id: "abc", email: "[REDACTED]", name: "[REDACTED]", role: "user" }
```

## Step 5: Data Retention Policy

```typescript
// Retention periods for cached Intercom data
const RETENTION = {
  contact_cache: 30,      // days - cached contact profiles
  conversation_cache: 90,  // days - cached conversations
  webhook_events: 30,      // days - processed webhook records
  audit_log: 2555,         // days (7 years) - compliance requirement
  data_export: 7,          // days - export download files
};

async function enforceRetention(): Promise<{ deleted: Record<string, number> }> {
  const results: Record<string, number> = {};

  for (const [type, days] of Object.entries(RETENTION)) {
    if (type === "audit_log") continue; // Never auto-delete audit logs

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - days);

    const result = await localDb.collection(type).deleteMany({
      created_at: { $lt: cutoff },
    });

    results[type] = result.deletedCount;
  }

  return { deleted: results };
}

// Schedule daily at 3 AM
// cron: "0 3 * * *"
```
