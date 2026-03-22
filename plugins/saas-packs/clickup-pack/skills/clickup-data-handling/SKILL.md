---
name: clickup-data-handling
description: |
  Handle ClickUp data exports, PII redaction, GDPR compliance, and
  data retention for ClickUp API integrations.
  Trigger: "clickup data", "clickup PII", "clickup GDPR", "clickup data retention",
  "clickup privacy", "clickup CCPA", "clickup data export".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Data Handling

## Overview

Handle sensitive data from ClickUp API v2 responses. ClickUp task data often contains PII (assignee emails, names) and business-sensitive information (task descriptions, comments, custom field values).

## ClickUp Data Classification

| Data Source | PII Risk | Handling |
|-------------|----------|----------|
| `/user` response | High (email, username) | Redact in logs |
| `/team` members | High (emails, names) | Minimize; cache only IDs |
| Task assignees | Medium (user IDs, names) | Aggregate when possible |
| Task descriptions | Variable (may contain PII) | Scan before storing |
| Custom field values | High (email, phone fields) | Encrypt at rest |
| Comments | Variable (user content) | Scan before logging |
| Webhook payloads | Medium (user objects in history) | Redact before queuing |

## PII Detection in ClickUp Data

```typescript
interface PiiFindings {
  field: string;
  type: string;
  value: string;
}

const PII_PATTERNS = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'ssn', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
];

function scanClickUpTaskForPii(task: any): PiiFindings[] {
  const findings: PiiFindings[] = [];

  // Check description
  for (const pattern of PII_PATTERNS) {
    const matches = (task.description ?? '').matchAll(pattern.regex);
    for (const m of matches) {
      findings.push({ field: 'description', type: pattern.type, value: m[0] });
    }
  }

  // Check custom fields
  for (const cf of task.custom_fields ?? []) {
    if (cf.type === 'email' && cf.value) {
      findings.push({ field: `custom_field:${cf.name}`, type: 'email', value: cf.value });
    }
    if (cf.type === 'phone' && cf.value) {
      findings.push({ field: `custom_field:${cf.name}`, type: 'phone', value: cf.value });
    }
  }

  // Check assignees
  for (const assignee of task.assignees ?? []) {
    if (assignee.email) {
      findings.push({ field: 'assignee', type: 'email', value: assignee.email });
    }
  }

  return findings;
}
```

## Redaction for Logging

```typescript
function redactClickUpResponse(data: any): any {
  const redacted = JSON.parse(JSON.stringify(data));

  // Redact user objects
  const redactUser = (user: any) => {
    if (user?.email) user.email = '[REDACTED]';
    if (user?.username) user.username = user.username.substring(0, 2) + '***';
  };

  // Task-level redaction
  if (redacted.assignees) redacted.assignees.forEach(redactUser);
  if (redacted.creator) redactUser(redacted.creator);

  // Webhook payload redaction
  if (redacted.history_items) {
    for (const item of redacted.history_items) {
      if (item.user) redactUser(item.user);
    }
  }

  // Custom fields with PII types
  if (redacted.custom_fields) {
    for (const cf of redacted.custom_fields) {
      if (['email', 'phone'].includes(cf.type) && cf.value) {
        cf.value = '[REDACTED]';
      }
    }
  }

  return redacted;
}

// Use when logging API responses
console.log('[clickup] task fetched:', JSON.stringify(redactClickUpResponse(task)));
```

## Data Export for GDPR/CCPA

```typescript
async function exportUserClickUpData(userId: number, teamId: string) {
  // 1. Get user profile
  const user = await clickupRequest('/user');

  // 2. Get tasks assigned to user across workspace
  const tasks = await clickupRequest(
    `/team/${teamId}/task?assignees[]=${userId}&include_closed=true`
  );

  // 3. Get time entries by user
  const timeEntries = await clickupRequest(
    `/team/${teamId}/time_entries?assignee=${userId}`
  );

  return {
    exportedAt: new Date().toISOString(),
    source: 'ClickUp API v2',
    userData: {
      id: user.user.id,
      username: user.user.username,
      email: user.user.email,
    },
    tasks: tasks.tasks.map((t: any) => ({
      id: t.id,
      name: t.name,
      status: t.status.status,
      url: t.url,
    })),
    timeEntries: timeEntries.data?.map((e: any) => ({
      id: e.id,
      duration: e.duration,
      description: e.description,
      task_id: e.task?.id,
    })) ?? [],
  };
}
```

## Data Retention

```typescript
// Track ClickUp API data locally with retention policies
interface RetentionPolicy {
  dataType: string;
  retentionDays: number;
  reason: string;
}

const RETENTION_POLICIES: RetentionPolicy[] = [
  { dataType: 'api_request_logs', retentionDays: 30, reason: 'Debugging' },
  { dataType: 'webhook_events', retentionDays: 90, reason: 'Audit trail' },
  { dataType: 'cached_tasks', retentionDays: 1, reason: 'Performance' },
  { dataType: 'time_entries', retentionDays: 365, reason: 'Billing' },
  { dataType: 'audit_logs', retentionDays: 2555, reason: 'Compliance (7 years)' },
];

async function enforceRetention(db: any) {
  for (const policy of RETENTION_POLICIES) {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - policy.retentionDays);
    await db.collection(policy.dataType).deleteMany({
      createdAt: { $lt: cutoff },
    });
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII in logs | Missing redaction | Wrap all logging with `redactClickUpResponse` |
| GDPR export incomplete | Pagination not handled | Use async generator for full export |
| Retention job fails | DB connection | Add retry logic to cron job |
| Custom field PII missed | New field types | Re-scan fields via `/list/{id}/field` |

## Resources

- [ClickUp Privacy Policy](https://clickup.com/privacy)
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [ClickUp API User Endpoint](https://developer.clickup.com/reference/getauthorizeduser)

## Next Steps

For enterprise access control, see `clickup-enterprise-rbac`.
