---
name: figma-data-handling
description: |
  Handle Figma API data correctly: comments, versions, user data, and privacy compliance.
  Use when working with Figma comments API, version history,
  or ensuring GDPR compliance for Figma user data.
  Trigger with phrases like "figma data", "figma comments",
  "figma versions", "figma GDPR", "figma user data".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Data Handling

## Overview
Work with Figma's data APIs: comments, version history, and user information. Handle sensitive data correctly with redaction and privacy compliance.

## Prerequisites
- `FIGMA_PAT` with appropriate scopes (`file_comments:read/write`, `file_versions:read`)
- Understanding of GDPR/CCPA basics

## Instructions

### Step 1: Comments API
```typescript
const PAT = process.env.FIGMA_PAT!;
const FILE_KEY = process.env.FIGMA_FILE_KEY!;

// GET /v1/files/:key/comments -- requires file_comments:read scope
async function getComments(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const data = await res.json();

  // data.comments is an array of:
  // { id, message, file_key, parent_id, user, client_meta, resolved_at, created_at, order_id }
  return data.comments;
}

// GET with as_md=true to get rich-text comments as markdown
async function getCommentsAsMarkdown(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments?as_md=true`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  return (await res.json()).comments;
}

// POST /v1/files/:key/comments -- requires file_comments:write scope
async function postComment(fileKey: string, message: string, nodeId?: string) {
  const body: any = { message };
  if (nodeId) {
    body.client_meta = { node_id: nodeId };
  }

  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments`,
    {
      method: 'POST',
      headers: {
        'X-Figma-Token': PAT,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    }
  );
  return res.json();
}

// POST reactions to a comment -- requires file_comments:write
async function reactToComment(fileKey: string, commentId: string, emoji: string) {
  return fetch(
    `https://api.figma.com/v1/files/${fileKey}/comments/${commentId}/reactions`,
    {
      method: 'POST',
      headers: {
        'X-Figma-Token': PAT,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ emoji }),
    }
  ).then(r => r.json());
}
```

### Step 2: Version History API
```typescript
// GET /v1/files/:key/versions -- requires file_versions:read scope
async function getVersionHistory(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/versions`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const data = await res.json();

  // data.versions: array of { id, created_at, label, description, user }
  // Ordered by created_at (most recent first)
  return data.versions;
}

// Paginate through all versions
async function getAllVersions(fileKey: string) {
  const versions: any[] = [];
  let url: string | null = `https://api.figma.com/v1/files/${fileKey}/versions`;

  while (url) {
    const res = await fetch(url, { headers: { 'X-Figma-Token': PAT } });
    const data = await res.json();
    versions.push(...data.versions);

    // Pagination uses cursor-based pagination
    url = data.pagination?.next_page
      ? `https://api.figma.com/v1/files/${fileKey}/versions?before=${data.pagination.next_page}`
      : null;
  }

  return versions;
}
```

### Step 3: User Data and Privacy
```typescript
// GET /v1/me -- returns authenticated user
interface FigmaUser {
  id: string;
  handle: string;
  img_url: string;
  email: string;   // PII -- handle carefully
}

// Redact PII before logging or storing
function redactFigmaUser(user: FigmaUser): Omit<FigmaUser, 'email'> & { email: string } {
  return {
    ...user,
    email: '[REDACTED]',
    img_url: '[REDACTED]',
  };
}

// Data classification for Figma responses
interface DataClassification {
  field: string;
  sensitivity: 'public' | 'internal' | 'pii';
  handling: string;
}

const figmaDataClassification: DataClassification[] = [
  { field: 'user.email', sensitivity: 'pii', handling: 'Encrypt at rest, redact in logs' },
  { field: 'user.handle', sensitivity: 'internal', handling: 'Do not expose to unauthorized users' },
  { field: 'user.img_url', sensitivity: 'pii', handling: 'Do not cache without consent' },
  { field: 'file.name', sensitivity: 'internal', handling: 'Standard handling' },
  { field: 'comment.message', sensitivity: 'internal', handling: 'May contain PII -- scan before storing' },
  { field: 'PAT token', sensitivity: 'pii', handling: 'Never log, never store in code' },
];
```

### Step 4: Data Retention
```typescript
// Figma image export URLs expire after 30 days
// Plan data retention accordingly

interface CachedFigmaData {
  data: any;
  fetchedAt: Date;
  expiresAt: Date;
}

function createCacheEntry(data: any, ttlMs: number): CachedFigmaData {
  const now = new Date();
  return {
    data,
    fetchedAt: now,
    expiresAt: new Date(now.getTime() + ttlMs),
  };
}

// Cleanup expired entries
async function cleanupExpiredData(db: any) {
  const now = new Date();
  const deleted = await db.figmaCache.deleteMany({
    expiresAt: { $lt: now },
  });
  console.log(`Cleaned up ${deleted.count} expired Figma cache entries`);
}
```

### Step 5: Safe Logging
```typescript
// Never log these fields from Figma responses
const REDACT_FIELDS = ['email', 'img_url', 'access_token', 'refresh_token'];

function safeFigmaLog(label: string, data: any) {
  const safe = JSON.parse(JSON.stringify(data));

  function redact(obj: any) {
    for (const key of Object.keys(obj)) {
      if (REDACT_FIELDS.includes(key)) {
        obj[key] = '[REDACTED]';
      } else if (typeof obj[key] === 'object' && obj[key] !== null) {
        redact(obj[key]);
      }
    }
  }

  redact(safe);
  console.log(`[figma] ${label}:`, JSON.stringify(safe));
}
```

## Output
- Comments fetched and posted via REST API
- Version history retrieved with pagination
- PII redacted before logging and storage
- Data retention policies applied

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 403 on comments | Missing `file_comments:read` scope | Regenerate PAT with scope |
| Empty version history | New file with no saved versions | Create a named version in Figma first |
| PII in logs | Missing redaction | Apply `safeFigmaLog` wrapper |
| Stale image URLs | URLs older than 30 days | Re-export images; do not cache URLs long-term |

## Resources
- [Figma Comments Endpoints](https://developers.figma.com/docs/rest-api/comments-endpoints/)
- [Figma Version History](https://developers.figma.com/docs/rest-api/version-history-endpoints/)
- [GDPR Developer Guide](https://gdpr.eu/developers/)

## Next Steps
For enterprise access control, see `figma-enterprise-rbac`.
