---
name: ramp-reporting-compliance
description: |
  Execute Ramp secondary workflow: Reporting & Compliance.
  Use when generating monthly expense reports for accounting,
  or producing audit trails for compliance reviews.
  Trigger with phrases like "ramp financial report",
  "generate compliance report with ramp".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, ramp]
---

# Ramp Reporting & Compliance

## Overview
Generate financial reports, audit trails, and compliance documentation.
Required for SOX, tax filing, and financial audits.


## Prerequisites
- Completed `ramp-install-auth` setup
- Familiarity with `ramp-transaction-processing`
- Valid API credentials configured

## Instructions

### Step 1: Generate Report
```typescript
const report = await client.reports.create({
  type: 'expense_summary',
  period: { start: '2026-01-01', end: '2026-03-31' },
  groupBy: ['department', 'category'],
  includeReceipts: true,
});

```

### Step 2: Extract Audit Trail
```typescript
const auditLog = await client.audit.list({
  from: '2026-01-01',
  events: ['transaction.created', 'transaction.approved', 'card.issued'],
});
console.log(`${auditLog.total} audit events in period`);

```

### Step 3: Export Documentation
```typescript
const docs = await client.compliance.export({
  type: 'quarterly_review',
  period: 'Q1-2026',
  format: 'pdf',
});
fs.writeFileSync('Q1-2026-compliance.pdf', docs.data);

```

## Output
- Completed Reporting & Compliance execution

- Results from Ramp API

- Success confirmation or error details

## Error Handling
| Aspect | Transaction Processing | Reporting & Compliance |
|--------|------------|------------|
| Use Case | syncing expenses from corporate cards into accounting | generating monthly expense reports for accounting |
| Complexity | Medium | Medium |
| Performance | Standard | Report generation can take 10-60s for large datasets |

## Examples

### Complete Workflow
```typescript
async function quarterlyReport(quarter: string) {
  const report = await client.reports.create({ type: 'quarterly', period: quarter });
  const audit = await client.audit.list({ period: quarter });
  return { report, auditEventCount: audit.total };
}

```

### Error Recovery
```typescript
try {
  const report = await client.reports.create(params);
  return report;
} catch (err) {
  if (err.code === 'report_period_locked') {
    console.error('Period is closed for edits. Contact finance admin.');
  } else if (err.code === 'insufficient_permissions') {
    console.error('Need finance-admin role to generate this report type.');
  }
  throw err;
}

```

## Resources
- [Ramp Documentation](https://docs.ramp.com)
- [Ramp API Reference](https://docs.ramp.com/api)

## Next Steps
For common errors, see `ramp-common-errors`.