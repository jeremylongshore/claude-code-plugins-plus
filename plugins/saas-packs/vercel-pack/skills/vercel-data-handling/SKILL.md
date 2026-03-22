---
name: vercel-data-handling
description: |
  Implement data handling, PII protection, and GDPR/CCPA compliance for Vercel deployments.
  Use when handling sensitive data in serverless functions, implementing data redaction,
  or ensuring privacy compliance on Vercel.
  Trigger with phrases like "vercel data", "vercel PII",
  "vercel GDPR", "vercel data retention", "vercel privacy", "vercel compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, compliance, privacy, security]

---
# Vercel Data Handling

## Overview
Handle sensitive data correctly on Vercel: PII redaction in logs, GDPR-compliant data processing in serverless functions, secure cookie management, and data residency configuration. Covers both what Vercel stores and what your application should protect.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- Vercel Pro or Enterprise (for data residency options)
- Logging infrastructure with PII awareness

## Instructions

### Step 1: Understand What Vercel Stores

| Data Type | Where | Retention | Control |
|-----------|-------|-----------|---------|
| Runtime logs | Vercel servers | 1hr (free), 30d (Plus) | Log drains |
| Build logs | Vercel servers | 30 days | Automatic |
| Analytics data | Vercel | Aggregated, no PII | Disable in dashboard |
| Deployment source | Vercel | Until deleted | Manual deletion |
| Environment variables | Vercel (encrypted) | Until deleted | Scoped access |

### Step 2: PII Redaction in Logs
```typescript
// lib/redact.ts — redact PII before logging
const PII_PATTERNS: [RegExp, string][] = [
  [/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, '[EMAIL]'],
  [/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE]'],
  [/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]'],
  [/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, '[CARD]'],
  [/\b(?:Bearer|token|key|secret|password)\s*[:=]\s*\S+/gi, '[CREDENTIAL]'],
];

export function redact(text: string): string {
  let result = text;
  for (const [pattern, replacement] of PII_PATTERNS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// Usage — always redact before console.log
import { redact } from '@/lib/redact';

export async function POST(request: Request) {
  const body = await request.json();
  console.log('Request received:', redact(JSON.stringify(body)));
  // Process safely...
}
```

### Step 3: GDPR-Compliant API Routes
```typescript
// api/users/[id]/route.ts — data subject request handlers
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';

// Right to Access (GDPR Art. 15)
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const user = await db.user.findUnique({
    where: { id: params.id },
    include: { posts: true, preferences: true },
  });

  if (!user) return NextResponse.json({ error: 'Not found' }, { status: 404 });

  return NextResponse.json({
    personalData: {
      name: user.name,
      email: user.email,
      createdAt: user.createdAt,
      posts: user.posts,
      preferences: user.preferences,
    },
    exportedAt: new Date().toISOString(),
  });
}

// Right to Erasure (GDPR Art. 17)
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // Soft delete — anonymize instead of hard delete for audit trail
  await db.user.update({
    where: { id: params.id },
    data: {
      email: `deleted-${params.id}@redacted.local`,
      name: '[DELETED]',
      deletedAt: new Date(),
    },
  });

  // Also delete from log drain provider if applicable
  console.log(`GDPR deletion completed for user ${params.id}`);
  return NextResponse.json({ deleted: true });
}
```

### Step 4: Secure Cookie Management
```typescript
// lib/cookies.ts — GDPR-aware cookie handling
import { cookies } from 'next/headers';

export function setSessionCookie(token: string): void {
  cookies().set('session', token, {
    httpOnly: true,       // Not accessible via JavaScript
    secure: true,         // HTTPS only
    sameSite: 'lax',      // CSRF protection
    maxAge: 60 * 60 * 24, // 24 hours
    path: '/',
  });
}

export function setConsentCookie(consent: Record<string, boolean>): void {
  cookies().set('consent', JSON.stringify(consent), {
    httpOnly: false,  // Needs client-side access
    secure: true,
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 365, // 1 year
    path: '/',
  });
}

// Middleware — block analytics if consent not given
export function middleware(request: Request) {
  const consent = request.headers.get('cookie')?.includes('consent');
  if (!consent) {
    // Strip analytics query params, skip tracking middleware
  }
}
```

### Step 5: Data Residency Configuration
Vercel allows configuring where your serverless functions execute:

```json
// vercel.json — restrict function execution to EU regions
{
  "regions": ["cdg1", "lhr1"],
  "functions": {
    "api/**/*.ts": {
      "regions": ["cdg1"]
    }
  }
}
```

EU regions for GDPR data residency:
| Region | Location | Code |
|--------|----------|------|
| Paris | France | `cdg1` |
| London | UK | `lhr1` |
| Frankfurt | Germany | `fra1` |

### Step 6: Audit Logging
```typescript
// lib/audit-log.ts — track data access for compliance
interface AuditEntry {
  action: 'read' | 'create' | 'update' | 'delete' | 'export';
  resource: string;
  resourceId: string;
  userId: string;
  ip: string;
  timestamp: string;
}

export async function auditLog(entry: Omit<AuditEntry, 'timestamp'>): Promise<void> {
  const record: AuditEntry = {
    ...entry,
    timestamp: new Date().toISOString(),
  };

  // Write to database audit table
  await db.auditLog.create({ data: record });

  // Also log for log drain capture (structured JSON)
  console.log(JSON.stringify({ type: 'audit', ...record }));
}

// Usage in API route:
export async function GET(request: NextRequest) {
  await auditLog({
    action: 'read',
    resource: 'user',
    resourceId: params.id,
    userId: session.userId,
    ip: request.headers.get('x-forwarded-for') ?? 'unknown',
  });
}
```

## Data Classification Guide

| Category | Examples | Handling on Vercel |
|----------|----------|-------------------|
| PII | Email, name, phone, IP | Redact from logs, encrypt at rest |
| Secrets | API keys, tokens, passwords | Use `type: sensitive` env vars, never log |
| Financial | Card numbers, bank info | Never process in functions — use Stripe/payment provider |
| Health | Medical records | Requires BAA — contact Vercel Enterprise |
| Business | Metrics, usage stats | Aggregate before logging |

## Output
- PII redaction applied to all log output
- GDPR data subject request endpoints implemented
- Secure cookie handling with consent management
- Data residency configured via function regions
- Audit logging for compliance trail

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| PII in Vercel logs | Not redacting before console.log | Use `redact()` wrapper on all log calls |
| GDPR data request timeout | Large data export in function | Paginate or use background processing |
| Cookies not secure | Missing `secure: true` flag | Always set httpOnly and secure flags |
| Function running in wrong region | Region not set in vercel.json | Specify `regions` per function |

## Resources
- [Vercel Privacy Policy](https://vercel.com/legal/privacy-policy)
- [Vercel Data Processing Agreement](https://vercel.com/legal/dpa)
- [GDPR Overview](https://gdpr.eu/)
- [Vercel Function Regions](https://vercel.com/docs/functions/configuring-functions)
- [Vercel Security](https://vercel.com/security)

## Next Steps
For enterprise RBAC, see `vercel-enterprise-rbac`.
