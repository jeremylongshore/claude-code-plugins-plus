---
name: clay-policy-guardrails
description: |
  Implement credit spending limits, data privacy enforcement, and input validation guardrails for Clay pipelines.
  Use when enforcing spending caps, blocking PII enrichment,
  or adding pre-enrichment validation rules.
  Trigger with phrases like "clay policy", "clay guardrails", "clay spending limit",
  "clay data privacy rules", "clay validation", "clay controls".
allowed-tools: Read, Write, Edit, Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, clay-policy]

---
# Clay Policy Guardrails

## Overview

Policy enforcement and guardrails for Clay data enrichment pipelines. Clay processes personal and business data at scale, requiring strict controls around credit spending, data privacy compliance, input validation, and export restrictions.

## Prerequisites

- Clay integration in production or pre-production
- Understanding of GDPR/CCPA requirements
- Credit budget defined by management
- Data classification policy for your organization

## Instructions

### Step 1: Credit Spending Guardrails

```typescript
// src/clay/policies/credit-policy.ts
interface CreditPolicy {
  dailyLimit: number;
  perTableLimit: number;
  perBatchLimit: number;
  alertThresholdPct: number;
  hardStopEnabled: boolean;
}

const CREDIT_POLICIES: Record<string, CreditPolicy> = {
  conservative: {
    dailyLimit: 200,
    perTableLimit: 500,
    perBatchLimit: 100,
    alertThresholdPct: 70,
    hardStopEnabled: true,
  },
  standard: {
    dailyLimit: 500,
    perTableLimit: 2000,
    perBatchLimit: 500,
    alertThresholdPct: 80,
    hardStopEnabled: true,
  },
  aggressive: {
    dailyLimit: 2000,
    perTableLimit: 10000,
    perBatchLimit: 2000,
    alertThresholdPct: 90,
    hardStopEnabled: false, // Alert only, don't stop
  },
};

class CreditPolicyEnforcer {
  private dailyUsed = 0;
  private tableUsage = new Map<string, number>();

  constructor(private policy: CreditPolicy) {}

  checkBatch(tableId: string, rowCount: number, creditsPerRow: number): {
    allowed: boolean;
    reason?: string;
  } {
    const estimated = rowCount * creditsPerRow;

    // Batch limit
    if (estimated > this.policy.perBatchLimit) {
      return {
        allowed: false,
        reason: `Batch (${estimated} credits) exceeds per-batch limit (${this.policy.perBatchLimit}). Split into smaller batches.`,
      };
    }

    // Daily limit
    if (this.dailyUsed + estimated > this.policy.dailyLimit) {
      if (this.policy.hardStopEnabled) {
        return {
          allowed: false,
          reason: `Would exceed daily limit: ${this.dailyUsed} + ${estimated} > ${this.policy.dailyLimit}`,
        };
      }
      console.warn(`WARNING: Exceeding daily limit (${this.dailyUsed + estimated}/${this.policy.dailyLimit})`);
    }

    // Per-table limit
    const tableTotal = (this.tableUsage.get(tableId) || 0) + estimated;
    if (tableTotal > this.policy.perTableLimit) {
      return {
        allowed: false,
        reason: `Table ${tableId} would exceed limit: ${tableTotal} > ${this.policy.perTableLimit}`,
      };
    }

    // Alert threshold
    const dailyPct = ((this.dailyUsed + estimated) / this.policy.dailyLimit) * 100;
    if (dailyPct > this.policy.alertThresholdPct) {
      console.warn(`Credit alert: ${dailyPct.toFixed(0)}% of daily limit used`);
    }

    return { allowed: true };
  }

  recordUsage(tableId: string, credits: number) {
    this.dailyUsed += credits;
    this.tableUsage.set(tableId, (this.tableUsage.get(tableId) || 0) + credits);
  }
}
```

### Step 2: Data Privacy Guardrails

```typescript
// src/clay/policies/privacy-policy.ts

// Fields that should NEVER be enriched or stored
const BLOCKED_ENRICHMENT_FIELDS = new Set([
  'ssn', 'social_security', 'tax_id',
  'date_of_birth', 'dob', 'birthday',
  'home_address', 'home_phone',
  'personal_phone', 'personal_mobile',
  'bank_account', 'credit_card',
  'medical_history', 'health_records',
  'salary', 'compensation',
  'political_affiliation', 'religion',
  'ethnic_origin', 'sexual_orientation',
]);

// Fields that require explicit consent
const CONSENT_REQUIRED_FIELDS = new Set([
  'personal_email', 'phone_number', 'mobile_phone',
]);

interface PrivacyCheckResult {
  allowed: boolean;
  violations: string[];
  warnings: string[];
}

function checkPrivacy(
  fieldsToEnrich: string[],
  hasExplicitConsent: boolean = false,
): PrivacyCheckResult {
  const violations: string[] = [];
  const warnings: string[] = [];

  for (const field of fieldsToEnrich) {
    const normalized = field.toLowerCase().replace(/[\s-]/g, '_');

    if (BLOCKED_ENRICHMENT_FIELDS.has(normalized)) {
      violations.push(`BLOCKED: "${field}" is a restricted field (never enrich)`);
    }

    if (CONSENT_REQUIRED_FIELDS.has(normalized) && !hasExplicitConsent) {
      warnings.push(`CONSENT: "${field}" requires explicit consent to enrich`);
    }
  }

  return {
    allowed: violations.length === 0,
    violations,
    warnings,
  };
}
```

### Step 3: Input Validation Guardrails

```typescript
// src/clay/policies/input-validation.ts

const PERSONAL_EMAIL_DOMAINS = new Set([
  'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'icloud.com',
  'aol.com', 'protonmail.com', 'mail.com', 'yandex.com', 'gmx.com',
]);

const DISPOSABLE_EMAIL_DOMAINS = new Set([
  'tempmail.com', 'guerrillamail.com', 'throwaway.email', 'yopmail.com',
  'mailinator.com', '10minutemail.com', 'trashmail.com',
]);

interface ValidationResult {
  valid: Record<string, unknown>[];
  rejected: { row: Record<string, unknown>; reason: string }[];
  stats: {
    total: number;
    valid: number;
    invalidDomain: number;
    personalDomain: number;
    disposableDomain: number;
    missingRequiredField: number;
    duplicates: number;
  };
}

function validateBatch(
  rows: Record<string, unknown>[],
  requiredFields: string[] = ['domain'],
): ValidationResult {
  const seen = new Set<string>();
  const stats = {
    total: rows.length, valid: 0, invalidDomain: 0,
    personalDomain: 0, disposableDomain: 0, missingRequiredField: 0, duplicates: 0,
  };
  const valid: Record<string, unknown>[] = [];
  const rejected: { row: Record<string, unknown>; reason: string }[] = [];

  for (const row of rows) {
    // Required fields check
    const missing = requiredFields.filter(f => !row[f]);
    if (missing.length > 0) {
      rejected.push({ row, reason: `Missing required: ${missing.join(', ')}` });
      stats.missingRequiredField++;
      continue;
    }

    const domain = String(row.domain || '').toLowerCase().trim();

    // Domain validation
    if (!domain.includes('.') || domain.length < 4) {
      rejected.push({ row, reason: `Invalid domain: "${domain}"` });
      stats.invalidDomain++;
      continue;
    }

    // Personal domain filter
    if (PERSONAL_EMAIL_DOMAINS.has(domain)) {
      rejected.push({ row, reason: `Personal email domain: ${domain}` });
      stats.personalDomain++;
      continue;
    }

    // Disposable domain filter
    if (DISPOSABLE_EMAIL_DOMAINS.has(domain)) {
      rejected.push({ row, reason: `Disposable email domain: ${domain}` });
      stats.disposableDomain++;
      continue;
    }

    // Deduplication
    const key = `${domain}:${String(row.first_name || '').toLowerCase()}:${String(row.last_name || '').toLowerCase()}`;
    if (seen.has(key)) {
      stats.duplicates++;
      continue;
    }
    seen.add(key);

    valid.push({ ...row, domain });
    stats.valid++;
  }

  return { valid, rejected, stats };
}
```

### Step 4: Export Restrictions

```typescript
// src/clay/policies/export-policy.ts
type ExportDestination = 'crm' | 'outreach' | 'analytics' | 'csv';

const EXPORT_RULES: Record<ExportDestination, {
  allowedFields: string[];
  blockedFields: string[];
  requiresApproval: boolean;
}> = {
  crm: {
    allowedFields: ['email', 'first_name', 'last_name', 'company_name', 'job_title', 'icp_score'],
    blockedFields: ['personal_email', 'home_address'],
    requiresApproval: false,
  },
  outreach: {
    allowedFields: ['email', 'first_name', 'company_name', 'personalized_opener'],
    blockedFields: ['phone_number', 'linkedin_url', 'personal_email'],
    requiresApproval: false,
  },
  analytics: {
    allowedFields: ['company_name', 'industry', 'employee_count', 'icp_score'],
    blockedFields: ['email', 'first_name', 'last_name', 'phone_number'],
    requiresApproval: false,
  },
  csv: {
    allowedFields: ['*'], // All fields
    blockedFields: ['personal_email', 'home_address', 'ssn'],
    requiresApproval: true, // Requires manager approval for CSV export
  },
};

function filterForExport(
  rows: Record<string, unknown>[],
  destination: ExportDestination,
): Record<string, unknown>[] {
  const rules = EXPORT_RULES[destination];

  return rows.map(row => {
    const filtered: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(row)) {
      if (rules.blockedFields.includes(key)) continue;
      if (rules.allowedFields[0] !== '*' && !rules.allowedFields.includes(key)) continue;
      filtered[key] = value;
    }
    return filtered;
  });
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Credit overrun | No spending limits enforced | Implement credit policy enforcer |
| PII enrichment violation | No privacy checks | Add blocked field validation |
| Wasted credits on bad data | No input validation | Pre-validate all batches |
| Unauthorized data export | No export restrictions | Implement per-destination field filtering |

## Resources

- [GDPR Official Text](https://gdpr.eu/what-is-gdpr/)
- [CCPA Requirements](https://oag.ca.gov/privacy/ccpa)
- [Clay Community](https://community.clay.com)

## Next Steps

For architecture patterns at scale, see `clay-architecture-variants`.
