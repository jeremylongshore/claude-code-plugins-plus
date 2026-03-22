---
name: webflow-data-handling
description: |
  Implement Webflow data handling — CMS content delivery patterns, PII redaction in
  form submissions, GDPR/CCPA compliance for ecommerce data, and data retention policies.
  Trigger with phrases like "webflow data", "webflow PII", "webflow GDPR",
  "webflow data retention", "webflow privacy", "webflow CCPA", "webflow forms data".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Data Handling

## Overview

Handle sensitive data correctly when working with the Webflow Data API v2. Covers
PII in form submissions, ecommerce customer data, CMS content classification,
GDPR/CCPA compliance patterns, and data retention policies.

## Prerequisites

- Understanding of GDPR/CCPA requirements
- Webflow API token with `forms:read`, `ecommerce:read` scopes
- Database for audit logging
- Scheduled job infrastructure for data cleanup

## Webflow Data Classification

| Source | Data Type | PII Risk | Handling |
|--------|-----------|----------|----------|
| Form submissions | Email, name, phone, message | High | Encrypt at rest, redact in logs |
| Ecommerce orders | Name, email, address, payment | High | Never log, minimal retention |
| CMS items | Blog posts, team bios, products | Low-Medium | May contain names/photos |
| Site analytics | Page views, sessions | Low | Aggregate when possible |
| API tokens | Access credentials | Critical | Never log, rotate quarterly |

## Instructions

### Step 1: PII Detection in Form Submissions

```typescript
const PII_PATTERNS = [
  { type: "email", regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: "phone", regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: "ssn", regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: "credit_card", regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
];

function detectPII(text: string): Array<{ type: string; found: boolean }> {
  return PII_PATTERNS.map(p => ({
    type: p.type,
    found: p.regex.test(text),
  })).filter(r => r.found);
}

// Scan form submissions for PII before logging
async function processFormSubmission(formId: string) {
  const { formSubmissions } = await webflow.forms.listSubmissions(formId);

  for (const sub of formSubmissions || []) {
    const rawData = JSON.stringify(sub.formData);
    const piiFindings = detectPII(rawData);

    if (piiFindings.length > 0) {
      console.warn(`PII detected in submission ${sub.id}: ${piiFindings.map(f => f.type).join(", ")}`);
      // Log redacted version only
      console.log("Form data:", redactPII(sub.formData || {}));
    }
  }
}
```

### Step 2: PII Redaction

```typescript
function redactPII(data: Record<string, any>): Record<string, any> {
  const sensitiveFields = new Set([
    "email", "phone", "telephone", "mobile", "ssn",
    "password", "credit-card", "card-number", "address",
    "full-name", "first-name", "last-name",
  ]);

  const redacted: Record<string, any> = {};

  for (const [key, value] of Object.entries(data)) {
    const normalizedKey = key.toLowerCase().replace(/[\s_]/g, "-");

    if (sensitiveFields.has(normalizedKey)) {
      redacted[key] = "[REDACTED]";
    } else if (typeof value === "string") {
      // Redact inline PII patterns
      let cleaned = value;
      for (const pattern of PII_PATTERNS) {
        cleaned = cleaned.replace(pattern.regex, `[${pattern.type.toUpperCase()}_REDACTED]`);
      }
      redacted[key] = cleaned;
    } else {
      redacted[key] = value;
    }
  }

  return redacted;
}

// Usage in logging
async function logFormData(formData: Record<string, any>) {
  console.log("Form submission (redacted):", redactPII(formData));
}
```

### Step 3: Ecommerce Data Handling

```typescript
// Order data contains high-sensitivity PII
async function processOrder(siteId: string, orderId: string) {
  const order = await webflow.orders.get(siteId, orderId);

  // NEVER log full customer info
  const safeOrderLog = {
    orderId: order.orderId,
    status: order.status,
    itemCount: order.purchasedItems?.length,
    totalCents: order.customerPaid?.value,
    // Redact customer info
    customer: {
      hasEmail: !!order.customerInfo?.email,
      hasAddress: !!order.shippingAddress,
      // Never: order.customerInfo?.email
      // Never: order.shippingAddress?.addressLine1
    },
    createdAt: order.acceptedOn,
  };

  console.log("Order processed:", safeOrderLog);
}
```

### Step 4: GDPR — Data Subject Access Request (DSAR)

```typescript
interface DataExport {
  source: string;
  exportedAt: string;
  requestedBy: string;
  data: {
    formSubmissions: Array<{ formName: string; submittedAt: string; data: Record<string, any> }>;
    orders: Array<{ orderId: string; status: string; total: number; items: string[] }>;
  };
}

async function exportUserData(siteId: string, userEmail: string): Promise<DataExport> {
  const exportData: DataExport = {
    source: "Webflow",
    exportedAt: new Date().toISOString(),
    requestedBy: userEmail,
    data: { formSubmissions: [], orders: [] },
  };

  // 1. Find form submissions by email
  const { forms } = await webflow.forms.list(siteId);
  for (const form of forms || []) {
    const { formSubmissions } = await webflow.forms.listSubmissions(form.id!);
    for (const sub of formSubmissions || []) {
      const formData = sub.formData || {};
      // Check all fields for matching email
      const hasEmail = Object.values(formData).some(
        v => typeof v === "string" && v.toLowerCase() === userEmail.toLowerCase()
      );
      if (hasEmail) {
        exportData.data.formSubmissions.push({
          formName: form.displayName!,
          submittedAt: sub.submittedAt!,
          data: formData,
        });
      }
    }
  }

  // 2. Find orders by email
  const { orders } = await webflow.orders.list(siteId);
  for (const order of orders || []) {
    if (order.customerInfo?.email?.toLowerCase() === userEmail.toLowerCase()) {
      exportData.data.orders.push({
        orderId: order.orderId!,
        status: order.status!,
        total: (order.customerPaid?.value || 0) / 100,
        items: order.purchasedItems?.map(i => i.productName || "Unknown") || [],
      });
    }
  }

  return exportData;
}
```

### Step 5: GDPR — Right to Deletion

```typescript
async function deleteUserData(
  siteId: string,
  userEmail: string
): Promise<{ deleted: string[]; retained: string[] }> {
  const result = { deleted: [] as string[], retained: [] as string[] };

  // Note: Webflow API does not currently support deleting form submissions
  // via API. You must delete them through the Webflow dashboard.
  // However, you can delete your local copies:

  // 1. Delete local form submission copies
  await db.formSubmissions.deleteMany({ email: userEmail, source: "webflow" });
  result.deleted.push("Local form submission copies");

  // 2. Delete local order copies (keep anonymized for accounting)
  await db.orders.updateMany(
    { email: userEmail, source: "webflow" },
    { $set: { email: "[DELETED]", name: "[DELETED]", address: "[DELETED]" } }
  );
  result.retained.push("Anonymized order records (legal requirement)");

  // 3. Audit log (required — never delete audit logs)
  await db.auditLog.insertOne({
    action: "GDPR_DELETION",
    email: userEmail,
    service: "webflow",
    timestamp: new Date(),
    deletedSources: result.deleted,
    retainedSources: result.retained,
  });
  result.retained.push("Audit log entry");

  return result;
}
```

### Step 6: Data Retention Policy

| Data Type | Retention | Reason | Auto-Cleanup |
|-----------|-----------|--------|--------------|
| Form submissions | 90 days | Business need | Yes |
| Order records | 7 years | Tax/accounting | No |
| API call logs | 30 days | Debugging | Yes |
| Error logs | 90 days | Root cause analysis | Yes |
| Audit logs | 7 years | Compliance | No |
| Cached CMS content | 24 hours | Performance | Yes (TTL) |

```typescript
async function cleanupExpiredData() {
  const now = new Date();

  // Delete form submissions older than 90 days
  const formCutoff = new Date(now);
  formCutoff.setDate(formCutoff.getDate() - 90);
  await db.formSubmissions.deleteMany({
    source: "webflow",
    createdAt: { $lt: formCutoff },
    type: { $nin: ["audit", "compliance"] },
  });

  // Delete API logs older than 30 days
  const logCutoff = new Date(now);
  logCutoff.setDate(logCutoff.getDate() - 30);
  await db.apiLogs.deleteMany({
    service: "webflow",
    createdAt: { $lt: logCutoff },
  });

  console.log("Data cleanup completed");
}

// Schedule daily at 3 AM
// cron: "0 3 * * *"
```

## Output

- PII detection for form submissions and order data
- Redaction layer for logging sensitive Webflow data
- GDPR DSAR export (forms + orders by email)
- Right to deletion with audit trail
- Data retention policy with automated cleanup

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII in logs | Missing redaction wrapper | Wrap all logging with `redactPII()` |
| DSAR incomplete | Not scanning all forms | Iterate all forms in site |
| Deletion failed | No API for form deletion | Delete via Webflow dashboard |
| Audit gap | Missing log entries | Ensure audit logging in all deletion paths |

## Resources

- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [CCPA Compliance](https://oag.ca.gov/privacy/ccpa)
- [Webflow Forms API](https://developers.webflow.com/data/reference/forms)
- [Webflow Orders API](https://developers.webflow.com/data/reference/ecommerce)

## Next Steps

For enterprise access control, see `webflow-enterprise-rbac`.
