---
name: lucidchart-core-workflow-b
description: 'Execute Lucidchart secondary workflow: Data-Linked Diagrams.

  Trigger: "lucidchart data-linked diagrams", "secondary lucidchart workflow".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lucidchart
- diagramming
compatibility: Designed for Claude Code
---
# Lucidchart — Collaboration & Sharing

## Overview

Invite collaborators, configure permissions, and manage real-time editing sessions on
Lucidchart documents. Use this workflow when you need to share diagrams with teammates,
set granular access controls, track revision history, or manage comments on shared
documents. This is the secondary workflow — for diagram creation and data linking,
see `lucidchart-core-workflow-a`.

## Instructions

### Step 1: Invite Collaborators with Role-Based Permissions

```typescript
const invites = await client.documents.share(doc.documentId, {
  recipients: [
    { email: 'architect@example.com', role: 'editor' },
    { email: 'manager@example.com', role: 'commenter' },
    { email: 'stakeholder@example.com', role: 'viewer' },
  ],
  message: 'Please review the updated architecture diagram',
  notify: true,
});
invites.forEach(inv =>
  console.log(`Invited ${inv.email} as ${inv.role} — status: ${inv.status}`)
);
```

### Step 2: Configure Document-Level Access Controls

```typescript
const permissions = await client.documents.updatePermissions(doc.documentId, {
  link_sharing: 'organization',  // 'private' | 'organization' | 'anyone_with_link'
  allow_download: false,
  allow_copy: false,
  require_login: true,
  expiry: '2026-05-01T00:00:00Z',
});
console.log(`Sharing: ${permissions.link_sharing}, expires: ${permissions.expiry}`);
console.log(`Download: ${permissions.allow_download}, Copy: ${permissions.allow_copy}`);
```

### Step 3: Manage Comments and Review Threads

```typescript
const comments = await client.documents.comments.list(doc.documentId, {
  status: 'open',
  sort: 'created_desc',
});
comments.items.forEach(c =>
  console.log(`[${c.author}] ${c.text} (${c.replies.length} replies)`)
);

// Resolve a comment thread
await client.documents.comments.resolve(doc.documentId, comments.items[0].id, {
  resolution_note: 'Updated per feedback — moved DB to separate VPC',
});
```

### Step 4: Track Revision History

```typescript
const revisions = await client.documents.revisions.list(doc.documentId, {
  limit: 10,
  sort: 'date_desc',
});
revisions.items.forEach(r =>
  console.log(`v${r.version} by ${r.author} at ${r.timestamp} — ${r.change_summary}`)
);
await client.documents.revisions.restore(doc.documentId, revisions.items[2].id);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired OAuth token | Re-authenticate via OAuth2 flow |
| `403 Insufficient permissions` | User lacks edit/share access | Request owner to grant editor role |
| `404 Document not found` | Wrong documentId or document deleted | Verify ID with `client.documents.list()` |
| `409 Conflict` | Concurrent edit collision | Retry — Lucidchart auto-merges most conflicts |
| `422 Invalid email` | Malformed recipient email address | Validate email format before sending invite |

## Output

A successful workflow sends collaboration invites with role-based permissions,
locks down document access with organization-level controls and expiry dates,
and provides a full audit trail of comments, resolutions, and revision history.

## Resources

- [Lucidchart Developer Docs](https://developer.lucid.co/reference/overview)

## Next Steps

See `lucidchart-sdk-patterns` for OAuth configuration and webhook setup.
