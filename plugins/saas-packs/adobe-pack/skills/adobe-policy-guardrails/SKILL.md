---
name: adobe-policy-guardrails
description: |
  Implement Adobe-specific lint rules, CI policy checks, and runtime guardrails
  covering credential scanning (p8_ patterns), Firefly content policy pre-screening,
  PDF Services quota enforcement, and OAuth scope validation.
  Trigger with phrases like "adobe policy", "adobe lint",
  "adobe guardrails", "adobe eslint", "adobe content policy".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, adobe]
compatible-with: claude-code
---

# Adobe Policy & Guardrails

## Overview

Automated policy enforcement for Adobe integrations: credential pattern scanning (Adobe OAuth secrets use `p8_` prefix), Firefly content policy pre-screening, PDF Services quota guardrails, and OAuth scope validation.

## Prerequisites

- ESLint configured in project
- CI/CD pipeline (GitHub Actions)
- Understanding of Adobe credential patterns

## Instructions

### Guardrail 1: Adobe Credential Pattern Scanner

Adobe OAuth Server-to-Server secrets follow the `p8_` prefix pattern:

```yaml
# .github/workflows/adobe-security.yml
name: Adobe Security Scan
on: [push, pull_request]
jobs:
  credential-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Scan for Adobe credential patterns
        run: |
          EXIT_CODE=0

          # Adobe OAuth client secrets (p8_ prefix)
          if grep -rE "p8_[A-Za-z0-9_-]{20,}" --include="*.ts" --include="*.js" --include="*.py" --include="*.json" --include="*.yaml" --include="*.yml" . 2>/dev/null | grep -v node_modules | grep -v '.git'; then
            echo "::error::Adobe client_secret pattern (p8_) found in source code"
            EXIT_CODE=1
          fi

          # Adobe IMS access tokens (JWT format)
          if grep -rE "eyJ[A-Za-z0-9_-]{100,}\.[A-Za-z0-9_-]{100,}" --include="*.ts" --include="*.js" . 2>/dev/null | grep -v node_modules | grep -v '.git' | grep -v '\.test\.' | grep -v '__mock'; then
            echo "::warning::Potential Adobe access token found in source (may be test fixture)"
          fi

          # Org IDs (format: HEXSTRING@AdobeOrg)
          if grep -rE "[A-F0-9]{24}@AdobeOrg" --include="*.ts" --include="*.js" --include="*.json" . 2>/dev/null | grep -v node_modules | grep -v '.git' | grep -v '.env.example'; then
            echo "::warning::Adobe Org ID found in source — consider using env var"
          fi

          exit $EXIT_CODE
```

### Guardrail 2: Firefly Content Policy Pre-Screener

```typescript
// src/adobe/guardrails/content-policy.ts
// Pre-screen prompts before sending to Firefly API to avoid wasted credits

interface ContentPolicyResult {
  allowed: boolean;
  violations: string[];
  suggestions: string[];
}

const CONTENT_RULES = [
  {
    name: 'real-people',
    pattern: /\b(photo of|portrait of|picture of)\s+(a\s+)?(real|actual|specific)\s+(person|man|woman|child)/i,
    message: 'Firefly cannot generate images of specific real people',
    suggestion: 'Use generic descriptions like "a professional in a business suit"',
  },
  {
    name: 'trademarks',
    pattern: /\b(nike|adidas|apple|google|microsoft|disney|marvel|coca.?cola|pepsi|starbucks|mcdonalds)\b/i,
    message: 'Firefly will reject prompts containing brand trademarks',
    suggestion: 'Use generic descriptions like "athletic shoes" or "tech company logo style"',
  },
  {
    name: 'explicit-content',
    pattern: /\b(nude|naked|explicit|pornograph|gore|violent|bloody|graphic death)\b/i,
    message: 'Firefly rejects explicit or violent content',
    suggestion: 'Use appropriate imagery descriptions',
  },
  {
    name: 'celebrity',
    pattern: /\b(celebrity|famous|actor|actress|politician|president|singer|musician)\s+(name|like|resembling)/i,
    message: 'Firefly cannot generate images of identifiable celebrities',
    suggestion: 'Describe the style or aesthetic without naming individuals',
  },
];

export function screenFireflyPrompt(prompt: string): ContentPolicyResult {
  const violations: string[] = [];
  const suggestions: string[] = [];

  for (const rule of CONTENT_RULES) {
    if (rule.pattern.test(prompt)) {
      violations.push(`[${rule.name}] ${rule.message}`);
      suggestions.push(rule.suggestion);
    }
  }

  return {
    allowed: violations.length === 0,
    violations,
    suggestions,
  };
}

// Usage in API layer
export function guardFireflyPrompt(prompt: string): void {
  const result = screenFireflyPrompt(prompt);
  if (!result.allowed) {
    throw new Error(
      `Firefly content policy pre-check failed:\n` +
      result.violations.join('\n') +
      '\n\nSuggestions:\n' +
      result.suggestions.join('\n')
    );
  }
}
```

### Guardrail 3: PDF Services Quota Enforcement

```typescript
// src/adobe/guardrails/pdf-quota.ts
// Enforce PDF Services monthly transaction limits

class PdfQuotaGuard {
  private monthlyLimit: number;
  private transactionsUsed: number = 0;
  private monthStart: Date;

  constructor(tier: 'free' | 'paid' = 'free') {
    this.monthlyLimit = tier === 'free' ? 500 : Infinity;
    this.monthStart = new Date(new Date().getFullYear(), new Date().getMonth(), 1);
  }

  check(): { allowed: boolean; remaining: number; warning: boolean } {
    // Reset counter on new month
    const now = new Date();
    if (now.getMonth() !== this.monthStart.getMonth()) {
      this.transactionsUsed = 0;
      this.monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    }

    const remaining = this.monthlyLimit - this.transactionsUsed;
    return {
      allowed: remaining > 0,
      remaining,
      warning: remaining < this.monthlyLimit * 0.2,
    };
  }

  record(): void {
    const status = this.check();
    if (!status.allowed) {
      throw new Error(`PDF Services quota exhausted (${this.monthlyLimit} transactions/month)`);
    }
    this.transactionsUsed++;
    if (status.warning) {
      console.warn(`PDF Services: ${status.remaining - 1} transactions remaining this month`);
    }
  }
}

export const pdfQuota = new PdfQuotaGuard(
  process.env.ADOBE_PDF_TIER === 'paid' ? 'paid' : 'free'
);
```

### Guardrail 4: OAuth Scope Validation

```typescript
// Verify that the requested scopes match what the environment should use
function validateAdobeScopes(scopes: string, environment: string): void {
  const scopeList = scopes.split(',').map(s => s.trim());

  // Development should only have minimal scopes
  if (environment === 'development') {
    const prodOnlyScopes = ['ff_apis'];
    const violations = scopeList.filter(s => prodOnlyScopes.includes(s));
    if (violations.length > 0) {
      console.warn(`Adobe scope warning: ${violations.join(', ')} should not be in development`);
    }
  }

  // Required scopes that should always be present
  const required = ['openid', 'AdobeID'];
  const missing = required.filter(s => !scopeList.includes(s));
  if (missing.length > 0) {
    throw new Error(`Adobe required scopes missing: ${missing.join(', ')}`);
  }
}
```

### Guardrail 5: Runtime Operation Guard

```typescript
// Prevent dangerous operations based on environment
const BLOCKED_IN_PROD: Record<string, string> = {
  'delete-all-assets': 'Mass deletion blocked in production',
  'reset-quota-counter': 'Quota reset blocked in production',
  'use-test-credentials': 'Test credentials blocked in production',
};

function guardAdobeOperation(operation: string): void {
  const isProd = process.env.NODE_ENV === 'production';
  if (isProd && BLOCKED_IN_PROD[operation]) {
    throw new Error(`BLOCKED: ${BLOCKED_IN_PROD[operation]}`);
  }
}
```

## Output

- CI secret scanning for Adobe credential patterns (`p8_`, JWTs, Org IDs)
- Firefly prompt pre-screening avoiding wasted credits on policy violations
- PDF Services quota enforcement with monthly tracking
- OAuth scope validation per environment
- Runtime operation guards for production safety

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret scan false positive | Test fixture contains pattern | Exclude test dirs from scan |
| Prompt wrongly rejected | Pattern too broad | Refine regex; allow legitimate uses |
| Quota counter reset | Server restart | Persist counter in Redis/DB |
| Scope validation fails | Wrong env var | Check `NODE_ENV` and `ADOBE_SCOPES` |

## Resources

- [Firefly Content Policy](https://developer.adobe.com/firefly-services/docs/firefly-api/)
- [PDF Services Pricing](https://developer.adobe.com/document-services/pricing/main/)
- [OAuth Server-to-Server Scopes](https://developer.adobe.com/developer-console/docs/guides/authentication/ServerToServerAuthentication/implementation)

## Next Steps

For architecture blueprints, see `adobe-architecture-variants`.
