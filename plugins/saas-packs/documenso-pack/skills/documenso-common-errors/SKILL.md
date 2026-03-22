---
name: documenso-common-errors
description: |
  Diagnose and resolve common Documenso API errors and issues.
  Use when encountering Documenso errors, debugging integration issues,
  or troubleshooting failed operations.
  Trigger with phrases like "documenso error", "documenso 401",
  "documenso failed", "fix documenso", "documenso not working".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, documenso, api, debugging]

---
# Documenso Common Errors

## Overview

Quick-reference troubleshooting guide for Documenso API errors. Covers authentication, document lifecycle, field validation, file upload, webhook, and SDK-specific issues with concrete solutions.

## Prerequisites

- Working Documenso integration (see `documenso-install-auth`)
- Access to application logs
- API key available

## HTTP Error Reference

| Status | Error | Cause | Solution |
|--------|-------|-------|----------|
| 401 | Unauthorized | Invalid, expired, or missing API key | Regenerate key in dashboard; verify `Authorization: Bearer <key>` header |
| 403 | Forbidden | Personal key accessing team resources | Use a team-scoped API token |
| 404 | Not Found | Wrong document/template ID or deleted resource | Verify ID with `GET /api/v1/documents` |
| 400 | Bad Request | Invalid payload or missing required fields | Check request body against API spec |
| 413 | Payload Too Large | PDF exceeds upload limit | Compress PDF; cloud plan limit varies by tier |
| 429 | Too Many Requests | Rate limit exceeded | Implement backoff; see `documenso-rate-limits` |
| 500/502/503 | Server Error | Documenso infrastructure issue | Retry with exponential backoff; check [status.documenso.com](https://status.documenso.com) |

## Instructions

### Scenario 1: 401 Unauthorized

```typescript
// WRONG: missing or malformed header
const res = await fetch("https://app.documenso.com/api/v1/documents", {
  headers: { "Authorization": process.env.DOCUMENSO_API_KEY! }, // Missing "Bearer "
});

// CORRECT: include Bearer prefix
const res = await fetch("https://app.documenso.com/api/v1/documents", {
  headers: { "Authorization": `Bearer ${process.env.DOCUMENSO_API_KEY}` },
});

// SDK handles this automatically:
import { Documenso } from "@documenso/sdk-typescript";
const client = new Documenso({ apiKey: process.env.DOCUMENSO_API_KEY! });
```

**Checklist:**
- API key starts with `api_` (personal) or is team-scoped
- No trailing whitespace or newline in env var
- Key hasn't been revoked in dashboard

### Scenario 2: 403 — Personal Key on Team Resources

```typescript
// Error: "Forbidden" when accessing team documents
// Personal API keys can only access YOUR documents
// Fix: generate a team API key from Team Settings > API Tokens
const client = new Documenso({
  apiKey: process.env.DOCUMENSO_TEAM_API_KEY!, // Team-scoped key
});
```

### Scenario 3: Cannot Modify Sent Document (400)

```typescript
// Error: trying to add fields to a PENDING document
// Documents can only be modified in DRAFT status

// Check status first
const doc = await client.documents.getV0(documentId);
if (doc.status !== "DRAFT") {
  throw new Error(`Cannot modify document in ${doc.status} status. Cancel first or create new.`);
}

// To re-edit: cancel the sent document, modify, then re-send
// Note: cancelling notifies all recipients
```

### Scenario 4: Invalid Field Position (400)

```typescript
// Error: field coordinates out of range
// pageX and pageY are PERCENTAGE-based (0-100), not pixel-based

// WRONG: pixel coordinates
await client.documentsFields.createV0(docId, {
  recipientId, type: "SIGNATURE",
  pageNumber: 1,
  pageX: 200,  // Invalid: > 100
  pageY: 600,  // Invalid: > 100
  pageWidth: 150, pageHeight: 50,
});

// CORRECT: percentage coordinates
await client.documentsFields.createV0(docId, {
  recipientId, type: "SIGNATURE",
  pageNumber: 1,
  pageX: 10,     // 10% from left edge
  pageY: 80,     // 80% from top edge
  pageWidth: 30, // 30% of page width
  pageHeight: 5, // 5% of page height
});
```

### Scenario 5: File Upload Errors (413)

```typescript
// Error: PDF too large for upload
// Cloud plans have per-document size limits

// Solution 1: Compress PDF before upload
import { PDFDocument } from "pdf-lib";
const pdfDoc = await PDFDocument.load(readFileSync("large-contract.pdf"));
const compressed = await pdfDoc.save({ useObjectStreams: true });
// Upload compressed version

// Solution 2: Check file size before upload
const MAX_SIZE_MB = 10; // Varies by plan
const fileSizeMB = readFileSync("contract.pdf").length / (1024 * 1024);
if (fileSizeMB > MAX_SIZE_MB) {
  throw new Error(`PDF is ${fileSizeMB.toFixed(1)}MB, max is ${MAX_SIZE_MB}MB`);
}
```

### Scenario 6: Webhook Not Receiving Events

```text
Checklist:
1. Webhook URL uses HTTPS (HTTP is rejected)
2. Webhook is enabled in Team Settings > Webhooks
3. Correct events are selected (document.completed, etc.)
4. Your endpoint returns 200 within 10 seconds
5. If using ngrok: tunnel is active and URL matches dashboard config
6. Check X-Documenso-Secret header matches your stored secret
```

### Scenario 7: SDK Type Mismatches

```typescript
// Error: argument type mismatch with SDK
// The SDK uses specific enum strings, not arbitrary values

// WRONG
await client.documentsRecipients.createV0(docId, {
  email: "signer@example.com",
  name: "Jane",
  role: "signer", // Lowercase fails
});

// CORRECT: use uppercase enum values
await client.documentsRecipients.createV0(docId, {
  email: "signer@example.com",
  name: "Jane",
  role: "SIGNER", // Must be uppercase: SIGNER, VIEWER, APPROVER, CC
});

// Field types are also uppercase: SIGNATURE, TEXT, DATE, NAME, EMAIL,
// INITIALS, NUMBER, CHECKBOX, DROPDOWN, RADIO, FREE_SIGNATURE
```

## Debugging Quick Commands

```bash
# Test API key
curl -s -w "\n%{http_code}" \
  -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  https://app.documenso.com/api/v1/documents?page=1&perPage=1

# Check self-hosted instance health
curl -s https://your-instance.com/api/health

# List documents to verify access
curl -s -H "Authorization: Bearer $DOCUMENSO_API_KEY" \
  "https://app.documenso.com/api/v1/documents?page=1&perPage=5" | jq '.documents[].title'
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `ERR_INVALID_URL` | Bad `serverURL` in SDK config | Include protocol and path: `https://host/api/v2` |
| `ECONNREFUSED` | Self-hosted instance down | Check Docker container status |
| `Module not found` | SDK not installed | Run `npm install @documenso/sdk-typescript` |
| Stale document data | Caching old state | Re-fetch document after status changes |

## Resources

- [Documenso API Reference](https://openapi.documenso.com/)
- [Status Page](https://status.documenso.com)
- [GitHub Issues](https://github.com/documenso/documenso/issues)
- [Documenso Discord](https://documenso.com/discord)

## Next Steps

For comprehensive debugging, see `documenso-debug-bundle`.
