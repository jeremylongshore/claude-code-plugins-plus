---
name: adobe-data-handling
description: |
  Implement data handling for Adobe APIs including PII redaction in logs,
  Firefly content policy compliance, PDF document data classification,
  and GDPR/CCPA data subject access requests via Adobe Privacy Service.
  Trigger with phrases like "adobe data", "adobe PII",
  "adobe GDPR", "adobe data retention", "adobe privacy", "adobe content policy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Data Handling

## Overview

Handle sensitive data correctly when integrating with Adobe APIs. Key concerns include Firefly content policy compliance, PII in PDF extraction results, credential redaction in logs, and GDPR/CCPA compliance using Adobe Privacy Service API.

## Prerequisites

- Understanding of your data classification requirements
- Adobe SDK with appropriate API access
- Database for audit logging
- Familiarity with GDPR/CCPA obligations

## Instructions

### Step 1: Data Classification for Adobe API Data

| Category | Examples | Handling |
|----------|----------|----------|
| **Credentials** | `client_secret`, access tokens | Never log; rotate regularly |
| **User Content** | Uploaded images, PDFs | Encrypt at rest; delete per retention policy |
| **Generated Content** | Firefly outputs, processed PDFs | Time-limited URLs (24h); cache intentionally |
| **Extraction Results** | PDF text, tables, structured data | May contain PII; scan and redact |
| **API Metadata** | Job IDs, request IDs, timestamps | Safe to log; useful for debugging |

### Step 2: PII Detection in PDF Extraction Results

PDF Extract API returns raw text that may contain customer PII:

```typescript
// src/adobe/pii-scanner.ts
const PII_PATTERNS = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'ssn', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: 'credit_card', regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
];

interface PiiFinding {
  type: string;
  count: number;
  // Never store the actual PII value
}

export function scanForPii(text: string): PiiFinding[] {
  return PII_PATTERNS
    .map(pattern => {
      const matches = text.matchAll(pattern.regex);
      const count = [...matches].length;
      return count > 0 ? { type: pattern.type, count } : null;
    })
    .filter(Boolean) as PiiFinding[];
}

export function redactPii(text: string): string {
  let redacted = text;
  for (const pattern of PII_PATTERNS) {
    redacted = redacted.replace(pattern.regex, `[REDACTED-${pattern.type.toUpperCase()}]`);
  }
  return redacted;
}

// Usage after PDF extraction
const extracted = await extractPdfContent('customer-form.pdf');
const piiFindings = scanForPii(extracted.text);

if (piiFindings.length > 0) {
  console.warn('PII detected in extraction:', piiFindings);
  // Store redacted version, or encrypt at rest
  const safeText = redactPii(extracted.text);
}
```

### Step 3: Firefly Content Policy Compliance

Firefly API has built-in content guardrails. Handle policy rejections gracefully:

```typescript
// src/adobe/content-policy.ts

// Pre-screen prompts before sending to Firefly
const BLOCKED_PATTERNS = [
  /\b(person|celebrity|actor|politician)\b/i,
  /\b(nike|apple|google|disney|marvel)\b/i, // Trademarks
  /\b(nude|explicit|violent|gore)\b/i,
];

export function validatePrompt(prompt: string): { valid: boolean; reason?: string } {
  for (const pattern of BLOCKED_PATTERNS) {
    if (pattern.test(prompt)) {
      return {
        valid: false,
        reason: `Prompt may violate Firefly content policy: matches "${pattern.source}"`,
      };
    }
  }
  return { valid: true };
}

// Handle Firefly content policy rejection
export function handleContentPolicyError(error: any): string {
  if (error.status === 400 && error.message?.includes('content policy')) {
    return 'Prompt rejected by Adobe Firefly content policy. ' +
      'Remove references to real people, trademarks, or explicit content.';
  }
  throw error;
}
```

### Step 4: Credential Redaction in Logs

```typescript
// src/adobe/safe-logger.ts
import pino from 'pino';

const logger = pino({
  name: 'adobe',
  redact: {
    paths: [
      'clientSecret',
      'client_secret',
      'access_token',
      'accessToken',
      'req.headers.authorization',
      'req.headers["x-api-key"]',
    ],
    censor: '[REDACTED]',
  },
});

// Safe request logging — only log metadata, never credentials
export function logAdobeRequest(entry: {
  api: string;
  operation: string;
  durationMs: number;
  httpStatus: number;
  jobId?: string;
  requestId?: string;  // From x-request-id response header
}) {
  logger.info(entry, `adobe.${entry.api}.${entry.operation}`);
}
```

### Step 5: GDPR/CCPA — Adobe Privacy Service API

Adobe provides a Privacy Service API for data subject access and deletion requests:

```typescript
// GDPR Data Subject Access Request
export async function submitPrivacyRequest(
  userId: string,
  requestType: 'access' | 'delete'
): Promise<{ jobId: string }> {
  const token = await getAccessToken();

  const response = await fetch(
    'https://platform.adobe.io/data/core/privacy/jobs',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-api-key': process.env.ADOBE_CLIENT_ID!,
        'x-gw-ims-org-id': process.env.ADOBE_IMS_ORG_ID!,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        companyContexts: [{
          namespace: 'imsOrgID',
          value: process.env.ADOBE_IMS_ORG_ID,
        }],
        users: [{
          key: userId,
          action: [requestType],
          userIDs: [{
            namespace: 'email',
            value: userId,
            type: 'standard',
          }],
        }],
        regulation: 'gdpr', // or 'ccpa'
      }),
    }
  );

  const result = await response.json();
  return { jobId: result.jobId };
}
```

### Data Retention Policy

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Firefly generated images | URLs expire 24h; cache intentionally | Adobe auto-expires |
| PDF extraction results | 30 days | Debugging |
| API access tokens | 24 hours (auto-expire) | Adobe IMS TTL |
| Error logs with request IDs | 90 days | Root cause analysis |
| Audit logs (who accessed what) | 7 years | Compliance |

## Output

- PII detection and redaction for PDF extraction results
- Firefly prompt pre-screening for content policy
- Credential redaction in all logs
- GDPR/CCPA data subject request support via Privacy Service API
- Data retention policy aligned with Adobe's auto-expiration

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII in extraction output | Raw PDF content | Apply redactPii() before storage |
| Firefly prompt rejected | Content policy | Pre-screen with validatePrompt() |
| Credentials in logs | Missing redaction | Configure pino redact paths |
| Privacy request failed | Missing org ID | Set `ADOBE_IMS_ORG_ID` env var |

## Resources

- [Adobe Privacy Service API](https://developer.adobe.com/experience-platform-apis/references/privacy-service/)
- [Firefly Content Policy](https://developer.adobe.com/firefly-services/docs/firefly-api/)
- [GDPR Developer Guide](https://gdpr.eu/developers/)

## Next Steps

For enterprise access control, see `adobe-enterprise-rbac`.
