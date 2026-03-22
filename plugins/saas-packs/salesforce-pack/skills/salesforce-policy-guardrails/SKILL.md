---
name: salesforce-policy-guardrails
description: |
  Implement Salesforce lint rules, SOQL injection prevention, and API usage guardrails.
  Use when enforcing Salesforce integration code quality, preventing SOQL injection,
  or configuring CI policy checks for Salesforce best practices.
  Trigger with phrases like "salesforce policy", "salesforce lint",
  "salesforce guardrails", "SOQL injection", "salesforce eslint", "salesforce code review".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Policy & Guardrails

## Overview
Automated policy enforcement for Salesforce integrations: SOQL injection prevention, API key leak detection, governor limit guardrails, and CI pipeline checks.

## Prerequisites
- ESLint configured in project
- jsforce TypeScript project
- CI/CD pipeline with policy checks
- Understanding of Salesforce security model

## Instructions

### Step 1: SOQL Injection Prevention

```typescript
// CRITICAL: Never concatenate user input into SOQL strings

// BAD — SOQL injection vulnerability
async function findAccount(name: string) {
  return conn.query(`SELECT Id FROM Account WHERE Name = '${name}'`);
  // User input: "'; DELETE FROM Account; --"
  // Result: SOQL injection (though Salesforce doesn't support DELETE via SOQL,
  //         user can still extract data with UNION-like techniques)
}

// GOOD — Escape special characters
function escapeSoql(value: string): string {
  return value
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/%/g, '\\%')
    .replace(/_/g, '\\_');
}

async function findAccountSafe(name: string) {
  const safeName = escapeSoql(name);
  return conn.query(`SELECT Id, Name FROM Account WHERE Name = '${safeName}'`);
}

// BEST — Use parameterized queries with jsforce
// jsforce doesn't have native parameterized SOQL, so always use escapeSoql()
// For Apex, use bind variables:
// [SELECT Id FROM Account WHERE Name = :accountName]
```

### Step 2: ESLint Rules for Salesforce

```javascript
// eslint-plugin-salesforce-integration/rules/no-soql-injection.js
module.exports = {
  meta: {
    type: 'problem',
    docs: { description: 'Prevent SOQL injection by detecting string concatenation in query calls' },
  },
  create(context) {
    return {
      CallExpression(node) {
        // Detect conn.query(`...${variable}...`)
        if (
          node.callee.property?.name === 'query' &&
          node.arguments[0]?.type === 'TemplateLiteral' &&
          node.arguments[0].expressions.length > 0
        ) {
          // Check if expressions use the escapeSoql wrapper
          for (const expr of node.arguments[0].expressions) {
            if (expr.type !== 'CallExpression' || expr.callee?.name !== 'escapeSoql') {
              context.report({
                node: expr,
                message: 'SOQL injection risk: wrap user input with escapeSoql(). Example: `WHERE Name = \'${escapeSoql(userInput)}\'`',
              });
            }
          }
        }
      },
    };
  },
};
```

### Step 3: Credential Leak Detection

```bash
#!/bin/bash
# pre-commit-salesforce-check.sh

# Detect Salesforce credential patterns in staged files
PATTERNS=(
  '00D[a-zA-Z0-9]{15}'           # Org ID (shouldn't be hardcoded)
  '005[a-zA-Z0-9]{15}'           # User ID (context-dependent)
  'force://[a-zA-Z0-9]+'         # Salesforce login token
  'SF_PASSWORD=.'                 # Password in code
  'SF_SECURITY_TOKEN=.'          # Security token in code
  'SF_CLIENT_SECRET=.'           # OAuth client secret in code
)

FOUND=0
for PATTERN in "${PATTERNS[@]}"; do
  if git diff --cached --name-only | xargs grep -l "$PATTERN" 2>/dev/null; then
    echo "ERROR: Possible Salesforce credential found: $PATTERN"
    FOUND=1
  fi
done

# Check for .env files being committed
if git diff --cached --name-only | grep -E '\.env$|\.env\.local$|\.env\.prod'; then
  echo "ERROR: .env file staged for commit"
  FOUND=1
fi

exit $FOUND
```

### Step 4: API Usage Guardrails

```typescript
// Runtime guardrails preventing API limit exhaustion

class SalesforceGuardrails {
  private callsThisMinute = 0;
  private lastReset = Date.now();
  private maxCallsPerMinute = 50; // Conservative limit

  async guard(operation: string, estimatedCalls: number = 1): Promise<void> {
    // Reset counter every minute
    if (Date.now() - this.lastReset > 60000) {
      this.callsThisMinute = 0;
      this.lastReset = Date.now();
    }

    // Per-minute throttle (prevent burst)
    if (this.callsThisMinute + estimatedCalls > this.maxCallsPerMinute) {
      const waitMs = 60000 - (Date.now() - this.lastReset);
      console.warn(`SF guardrail: throttling ${operation}, waiting ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
      this.callsThisMinute = 0;
      this.lastReset = Date.now();
    }

    // Check daily limit before proceeding
    const conn = await getConnection();
    const limits = await conn.request('/services/data/v59.0/limits/');
    const usagePercent = (limits.DailyApiRequests.Max - limits.DailyApiRequests.Remaining) / limits.DailyApiRequests.Max;

    if (usagePercent > 0.95) {
      throw new Error(`SF guardrail: API usage at ${(usagePercent * 100).toFixed(1)}% — blocking ${operation}`);
    }

    if (usagePercent > 0.80) {
      console.warn(`SF guardrail: API usage at ${(usagePercent * 100).toFixed(1)}%`);
    }

    this.callsThisMinute += estimatedCalls;
  }
}
```

### Step 5: CI Policy Checks

```yaml
# .github/workflows/salesforce-policy.yml
name: Salesforce Policy Check

on: [push, pull_request]

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Check for SOQL injection risks
        run: |
          # Detect raw string interpolation in .query() calls
          if grep -rn "\.query(\`.*\$\{" --include="*.ts" --include="*.js" src/ | grep -v "escapeSoql"; then
            echo "ERROR: Possible SOQL injection — wrap user input with escapeSoql()"
            exit 1
          fi

      - name: Check for hardcoded credentials
        run: |
          if grep -rE "(SF_PASSWORD|SF_SECURITY_TOKEN|SF_CLIENT_SECRET)\s*=" --include="*.ts" --include="*.js" src/; then
            echo "ERROR: Hardcoded Salesforce credentials found"
            exit 1
          fi

      - name: Check for production org IDs
        run: |
          if grep -rE "00D[a-zA-Z0-9]{15}" --include="*.ts" --include="*.js" --include="*.json" src/; then
            echo "WARNING: Hardcoded Salesforce Org ID found — use environment variables"
          fi

      - name: Verify .gitignore includes sensitive files
        run: |
          for pattern in ".env" ".env.local" "server.key" "*.pem"; do
            if ! grep -q "$pattern" .gitignore; then
              echo "ERROR: .gitignore missing '$pattern'"
              exit 1
            fi
          done
```

### Step 6: SOQL Best Practices Enforcement

```typescript
// Automated SOQL quality checks
function validateSoql(soql: string): { valid: boolean; warnings: string[] } {
  const warnings: string[] = [];

  // Warn on SELECT FIELDS(ALL) — performance anti-pattern
  if (soql.includes('FIELDS(ALL)')) {
    warnings.push('Avoid FIELDS(ALL) — select only needed fields');
  }

  // Warn on missing LIMIT
  if (!soql.toUpperCase().includes('LIMIT') && !soql.toUpperCase().includes('COUNT(')) {
    warnings.push('Missing LIMIT clause — add LIMIT to prevent hitting 50K row limit');
  }

  // Warn on LIKE with leading wildcard
  if (/LIKE\s+'%/.test(soql)) {
    warnings.push("Leading wildcard in LIKE '%...' causes full table scan");
  }

  // Warn on missing WHERE clause
  if (!soql.toUpperCase().includes('WHERE') && !soql.toUpperCase().includes('LIMIT 1')) {
    warnings.push('No WHERE clause — query may return too many rows');
  }

  return { valid: warnings.length === 0, warnings };
}
```

## Output
- SOQL injection prevention with escape function
- ESLint rule detecting injection risks
- Pre-commit hook blocking credential leaks
- Runtime API usage guardrails
- CI pipeline policy checks

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| ESLint rule false positive | escapeSoql used but not detected | Update rule to check function name |
| Guardrail blocks valid request | Threshold too low | Tune per-minute and daily thresholds |
| Pre-commit hook slow | Too many files | Use `lint-staged` for incremental checks |
| SOQL injection detected | String concatenation | Apply escapeSoql() wrapper |

## Resources
- [SOQL Injection](https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/pages_security_tips_soql_injection.htm)
- [Salesforce Security Guide](https://developer.salesforce.com/docs/atlas.en-us.securityImplGuide.meta/securityImplGuide/)
- [ESLint Plugin Development](https://eslint.org/docs/latest/extend/plugins)

## Next Steps
For architecture blueprints, see `salesforce-architecture-variants`.
