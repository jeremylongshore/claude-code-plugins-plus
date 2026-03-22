---
name: miro-data-handling
description: |
  Implement Miro REST API v2 data handling with PII detection in board content,
  data export via API, retention policies, and GDPR/CCPA compliance patterns.
  Trigger with phrases like "miro data", "miro PII",
  "miro GDPR", "miro data export", "miro privacy", "miro compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, data-handling, privacy, compliance]
compatible-with: claude-code
---

# Miro Data Handling

## Overview

Handle sensitive data correctly when integrating with Miro REST API v2. Miro boards can contain PII in sticky notes, cards, and text items. This skill covers detecting PII in board content, exporting board data for DSAR requests, implementing retention policies, and ensuring GDPR/CCPA compliance.

## Data Classification for Miro Content

| Category | Examples in Miro | Handling |
|----------|-----------------|----------|
| PII | Emails/names in sticky notes, assignee info in cards | Detect, redact in logs, export on DSAR request |
| Sensitive | OAuth tokens, API keys in text items | Never cache, alert on detection |
| Business | Board names, project plans, diagrams | Standard handling, respect board sharing policy |
| Public | Template content, product names | No special handling needed |

## PII Detection in Board Items

Scan board content for personally identifiable information:

```typescript
const PII_PATTERNS = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'ssn', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: 'credit_card', regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
  { type: 'ip_address', regex: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g },
];

interface PiiFindings {
  boardId: string;
  itemId: string;
  itemType: string;
  findings: Array<{ type: string; field: string; count: number }>;
}

async function scanBoardForPii(boardId: string): Promise<PiiFindings[]> {
  const results: PiiFindings[] = [];

  // Fetch all text-containing items
  const itemTypes = ['sticky_note', 'card', 'text', 'shape'];
  for (const type of itemTypes) {
    const items = await fetchAllItems(boardId, type);

    for (const item of items) {
      const contentFields = extractTextContent(item);
      const findings: PiiFindings['findings'] = [];

      for (const [field, text] of Object.entries(contentFields)) {
        if (!text) continue;
        for (const pattern of PII_PATTERNS) {
          const matches = text.match(pattern.regex);
          if (matches) {
            findings.push({ type: pattern.type, field, count: matches.length });
          }
        }
      }

      if (findings.length > 0) {
        results.push({ boardId, itemId: item.id, itemType: item.type, findings });
      }
    }
  }

  return results;
}

function extractTextContent(item: any): Record<string, string> {
  switch (item.type) {
    case 'sticky_note': return { content: item.data?.content };
    case 'card': return { title: item.data?.title, description: item.data?.description };
    case 'text': return { content: item.data?.content };
    case 'shape': return { content: item.data?.content };
    default: return {};
  }
}
```

## Board Data Export (for DSAR Requests)

When a user requests their data under GDPR Article 15 / CCPA:

```typescript
interface BoardDataExport {
  exportedAt: string;
  requestedBy: string;
  boards: Array<{
    boardId: string;
    boardName: string;
    role: string;
    items: Array<{
      id: string;
      type: string;
      content: string | null;
      createdAt: string;
      createdBy: string;
    }>;
  }>;
}

async function exportUserBoardData(userId: string): Promise<BoardDataExport> {
  // Step 1: List all boards the user has access to
  const boards = await fetchAllBoards();

  const exportData: BoardDataExport = {
    exportedAt: new Date().toISOString(),
    requestedBy: userId,
    boards: [],
  };

  for (const board of boards) {
    // Step 2: Get board members to check user's role
    const members = await miroFetch(`/v2/boards/${board.id}/members?limit=50`);
    const userMember = members.data.find((m: any) => m.id === userId);
    if (!userMember) continue;

    // Step 3: Get all items created by this user
    const allItems = await fetchAllItems(board.id);
    const userItems = allItems.filter((item: any) => item.createdBy?.id === userId);

    exportData.boards.push({
      boardId: board.id,
      boardName: board.name,
      role: userMember.role,
      items: userItems.map((item: any) => ({
        id: item.id,
        type: item.type,
        content: item.data?.content ?? item.data?.title ?? null,
        createdAt: item.createdAt,
        createdBy: item.createdBy?.id,
      })),
    });
  }

  return exportData;
}
```

## Data Redaction in Logs

Never log board content that might contain PII:

```typescript
function redactMiroData(data: Record<string, any>): Record<string, any> {
  const sensitiveFields = [
    'content', 'title', 'description', 'assigneeId',
    'access_token', 'refresh_token', 'client_secret',
  ];

  const redacted = JSON.parse(JSON.stringify(data));

  function redactDeep(obj: any): void {
    for (const key of Object.keys(obj)) {
      if (sensitiveFields.includes(key) && typeof obj[key] === 'string') {
        obj[key] = `[REDACTED:${obj[key].length} chars]`;
      } else if (typeof obj[key] === 'object' && obj[key] !== null) {
        redactDeep(obj[key]);
      }
    }
  }

  redactDeep(redacted);
  return redacted;
}

// Use in logging middleware
function logMiroResponse(path: string, status: number, body: any): void {
  console.log('[MIRO]', {
    path,
    status,
    body: redactMiroData(body),  // Content never appears in logs
  });
}
```

## Data Retention for Cached Miro Data

If you cache or sync Miro board data locally:

```typescript
interface RetentionPolicy {
  dataType: string;
  retentionDays: number;
  reason: string;
}

const RETENTION_POLICIES: RetentionPolicy[] = [
  { dataType: 'board_cache', retentionDays: 1, reason: 'Performance cache only' },
  { dataType: 'webhook_events', retentionDays: 30, reason: 'Debugging' },
  { dataType: 'api_audit_logs', retentionDays: 365, reason: 'Compliance' },
  { dataType: 'user_tokens', retentionDays: 0, reason: 'Delete on user disconnect' },
];

async function enforceRetention(db: Database): Promise<RetentionReport> {
  const report: RetentionReport = { deletedCounts: {} };

  for (const policy of RETENTION_POLICIES) {
    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - policy.retentionDays);

    const deleted = await db.deleteWhere(policy.dataType, {
      createdAt: { $lt: cutoff },
    });

    report.deletedCounts[policy.dataType] = deleted;
  }

  return report;
}

// Schedule daily
// cron: 0 3 * * * node -e "enforceRetention(db)"
```

## Right to Deletion (GDPR Article 17)

```typescript
async function deleteUserMiroData(userId: string): Promise<DeletionResult> {
  const steps: string[] = [];

  // 1. Delete cached board data for this user
  await db.boardCache.deleteMany({ userId });
  steps.push('Deleted cached board data');

  // 2. Delete webhook event logs mentioning this user
  await db.webhookEvents.deleteMany({ 'event.createdBy.id': userId });
  steps.push('Deleted webhook event logs');

  // 3. Delete stored OAuth tokens
  await tokenStorage.delete(userId);
  steps.push('Deleted OAuth tokens');

  // 4. Audit log the deletion (required to keep for compliance)
  await db.auditLogs.insert({
    action: 'GDPR_DELETION',
    userId,
    service: 'miro',
    deletedAt: new Date().toISOString(),
    steps,
  });

  // NOTE: You cannot delete data from Miro boards via API on behalf of a user.
  // The user must delete their own board content in Miro directly,
  // or a board admin can remove the user's items.

  return { success: true, steps };
}
```

## Board Content Security Scanning

```typescript
// Detect secrets accidentally pasted into board items
const SECRET_PATTERNS = [
  { type: 'aws_key', regex: /AKIA[0-9A-Z]{16}/g },
  { type: 'github_token', regex: /ghp_[A-Za-z0-9_]{36}/g },
  { type: 'miro_token', regex: /eyJ[A-Za-z0-9_-]{20,}/g },
  { type: 'private_key', regex: /-----BEGIN (RSA |EC )?PRIVATE KEY-----/g },
];

async function scanBoardForSecrets(boardId: string): Promise<SecurityAlert[]> {
  const alerts: SecurityAlert[] = [];
  const items = await fetchAllItems(boardId);

  for (const item of items) {
    const content = item.data?.content ?? item.data?.title ?? '';
    for (const pattern of SECRET_PATTERNS) {
      if (pattern.regex.test(content)) {
        alerts.push({
          severity: 'critical',
          type: pattern.type,
          itemId: item.id,
          itemType: item.type,
          boardId,
        });
        pattern.regex.lastIndex = 0;  // Reset regex
      }
    }
  }

  return alerts;
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII in cached data | No redaction | Apply `redactMiroData()` before caching |
| DSAR export timeout | Too many boards | Paginate and use background job |
| Deletion incomplete | Missing data stores | Audit all locations where Miro data is stored |
| Secret in board | User pasted credentials | Alert via `scanBoardForSecrets()` |

## Resources

- [Miro Privacy Policy](https://miro.com/legal/privacy-policy/)
- [Miro Security](https://miro.com/security/)
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [CCPA Compliance](https://oag.ca.gov/privacy/ccpa)

## Next Steps

For enterprise access control, see `miro-enterprise-rbac`.
