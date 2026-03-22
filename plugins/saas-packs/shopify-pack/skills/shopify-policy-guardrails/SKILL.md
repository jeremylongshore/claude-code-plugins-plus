---
name: shopify-policy-guardrails
description: |
  Implement Shopify app policy enforcement with ESLint rules for API key detection,
  query cost budgets, and App Store compliance checks.
  Trigger with phrases like "shopify policy", "shopify lint",
  "shopify guardrails", "shopify compliance", "shopify eslint", "shopify app review".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ecommerce, shopify]
compatible-with: claude-code
---

# Shopify Policy & Guardrails

## Overview

Automated policy enforcement for Shopify apps: secret detection, query cost budgets, App Store compliance checks, and CI policy validation.

## Prerequisites

- ESLint configured in project
- Pre-commit hooks infrastructure
- CI/CD pipeline with GitHub Actions
- Shopify app with `shopify.app.toml`

## Instructions

### Step 1: Secret Detection Rules

```javascript
// eslint-rules/no-shopify-secrets.js
module.exports = {
  meta: {
    type: "problem",
    docs: { description: "Detect hardcoded Shopify tokens and secrets" },
    messages: {
      adminToken: "Hardcoded Shopify Admin API token detected (shpat_*)",
      apiSecret: "Potential Shopify API secret detected",
      storefrontToken: "Hardcoded Storefront API token detected",
    },
  },
  create(context) {
    return {
      Literal(node) {
        if (typeof node.value !== "string") return;
        const v = node.value;

        // Admin API access token: shpat_ + 32 hex chars
        if (/^shpat_[a-f0-9]{32}$/i.test(v)) {
          context.report({ node, messageId: "adminToken" });
        }
        // Storefront token: shpss_ pattern
        if (/^shpss_[a-f0-9]{32}$/i.test(v)) {
          context.report({ node, messageId: "storefrontToken" });
        }
        // Generic secret pattern (32+ hex that's clearly a token)
        if (/^[a-f0-9]{32,}$/i.test(v) && v.length === 32) {
          context.report({ node, messageId: "apiSecret" });
        }
      },
      TemplateLiteral(node) {
        for (const quasi of node.quasis) {
          if (/shpat_[a-f0-9]/i.test(quasi.value.raw)) {
            context.report({ node, messageId: "adminToken" });
          }
        }
      },
    };
  },
};
```

### Step 2: Query Cost Budget Enforcement

```typescript
// Enforce query cost budgets at build/test time
interface QueryCostBudget {
  maxFirstParam: number;        // Max items per page
  maxNestedDepth: number;       // Max nested connection depth
  maxEstimatedCost: number;     // Max estimated query cost
}

const BUDGET: QueryCostBudget = {
  maxFirstParam: 100,           // Never request more than 100 items
  maxNestedDepth: 3,            // No more than 3 levels of edges/node
  maxEstimatedCost: 500,        // Stay well under 1,000 point limit
};

function validateQueryCost(query: string): string[] {
  const violations: string[] = [];

  // Check `first:` parameter values
  const firstParams = query.matchAll(/first:\s*(\d+)/g);
  for (const match of firstParams) {
    if (parseInt(match[1]) > BUDGET.maxFirstParam) {
      violations.push(
        `first: ${match[1]} exceeds budget of ${BUDGET.maxFirstParam}`
      );
    }
  }

  // Check nesting depth (count "edges { node {" patterns)
  const depth = (query.match(/edges\s*\{/g) || []).length;
  if (depth > BUDGET.maxNestedDepth) {
    violations.push(
      `Nesting depth ${depth} exceeds budget of ${BUDGET.maxNestedDepth}`
    );
  }

  // Estimate cost: multiply all `first` values along nested path
  const firstValues = [...query.matchAll(/first:\s*(\d+)/g)].map((m) =>
    parseInt(m[1])
  );
  const estimatedCost = firstValues.reduce((a, b) => a * b, 1);
  if (estimatedCost > BUDGET.maxEstimatedCost) {
    violations.push(
      `Estimated cost ${estimatedCost} exceeds budget of ${BUDGET.maxEstimatedCost}`
    );
  }

  return violations;
}
```

### Step 3: Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: shopify-token-scan
        name: Scan for Shopify tokens
        language: system
        entry: bash -c '
          if git diff --cached --diff-filter=d | grep -E "shpat_[a-f0-9]{32}|shpss_[a-f0-9]{32}" ; then
            echo "ERROR: Shopify access token detected in staged changes"
            exit 1
          fi'
        pass_filenames: false

      - id: shopify-env-check
        name: Check .env not staged
        language: system
        entry: bash -c '
          if git diff --cached --name-only | grep -E "^\.env$|^\.env\.local$|^\.env\.production$" ; then
            echo "ERROR: .env file staged for commit"
            exit 1
          fi'
        pass_filenames: false
```

### Step 4: App Store Compliance Checker

```typescript
// scripts/check-app-compliance.ts
// Run before submitting to Shopify App Store

interface ComplianceCheck {
  name: string;
  required: boolean;
  check: () => Promise<boolean>;
}

const checks: ComplianceCheck[] = [
  {
    name: "GDPR webhook: customers/data_request",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return toml.includes("customers/data_request");
    },
  },
  {
    name: "GDPR webhook: customers/redact",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return toml.includes("customers/redact");
    },
  },
  {
    name: "GDPR webhook: shop/redact",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return toml.includes("shop/redact");
    },
  },
  {
    name: "No hardcoded tokens in source",
    required: true,
    check: async () => {
      const { execSync } = require("child_process");
      const result = execSync(
        'grep -rE "shpat_[a-f0-9]{32}" app/ --include="*.ts" --include="*.tsx" || true'
      ).toString();
      return result.trim() === "";
    },
  },
  {
    name: "CSP frame-ancestors header set",
    required: true,
    check: async () => {
      const files = await glob("app/**/*.ts");
      const hasCSP = files.some((f) => {
        const content = readFileSync(f, "utf-8");
        return content.includes("frame-ancestors");
      });
      return hasCSP;
    },
  },
  {
    name: "API version is not unstable",
    required: true,
    check: async () => {
      const toml = await readFile("shopify.app.toml", "utf-8");
      return !toml.includes('api_version = "unstable"');
    },
  },
];

async function runComplianceChecks(): Promise<void> {
  console.log("=== Shopify App Store Compliance Check ===\n");
  let passed = 0;
  let failed = 0;

  for (const check of checks) {
    const result = await check.check();
    const status = result ? "PASS" : check.required ? "FAIL" : "WARN";
    console.log(`${status}: ${check.name}`);
    result ? passed++ : failed++;
  }

  console.log(`\n${passed} passed, ${failed} failed`);
  if (failed > 0) process.exit(1);
}
```

### Step 5: CI Policy Pipeline

```yaml
# .github/workflows/shopify-policy.yml
name: Shopify Policy

on: [push, pull_request]

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for hardcoded Shopify tokens
        run: |
          if grep -rE "shpat_[a-f0-9]{32}|shpss_[a-f0-9]{32}" \
            --include="*.ts" --include="*.tsx" --include="*.js" \
            app/ src/ ; then
            echo "::error::Hardcoded Shopify tokens found!"
            exit 1
          fi

      - name: Check GDPR webhooks configured
        run: |
          for topic in "customers/data_request" "customers/redact" "shop/redact"; do
            if ! grep -q "$topic" shopify.app.toml; then
              echo "::error::Missing mandatory GDPR webhook: $topic"
              exit 1
            fi
          done
          echo "All GDPR webhooks configured"

      - name: Validate API version
        run: |
          VERSION=$(grep 'api_version' shopify.app.toml | head -1 | grep -oP '\d{4}-\d{2}')
          if [ "$VERSION" = "unstable" ]; then
            echo "::error::Cannot use unstable API version"
            exit 1
          fi
          echo "API version: $VERSION"
```

## Output

- ESLint rules catching hardcoded tokens
- Query cost budgets enforced
- Pre-commit hooks blocking secret leaks
- App Store compliance checker
- CI policy pipeline preventing violations

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| False positive on token | Base64 string matched | Narrow regex pattern |
| Query cost estimate wrong | Complex variable nesting | Use actual debug header in tests |
| Pre-commit bypassed | `--no-verify` flag | Enforce in CI as backup |
| App Store rejection | Missing GDPR webhook | Run compliance checker before submit |

## Examples

### Quick Policy Scan

```bash
# One-liner: check for token leaks in staged changes
git diff --cached | grep -E "shpat_|shpss_" && echo "TOKEN LEAK!" || echo "Clean"

# Check GDPR compliance
grep -c "customers/data_request\|customers/redact\|shop/redact" shopify.app.toml
# Should output: 3
```

## Resources

- [Shopify App Store Requirements](https://shopify.dev/docs/apps/launch/app-requirements)
- [ESLint Plugin Development](https://eslint.org/docs/latest/extend/plugins)
- [git-secrets](https://github.com/awslabs/git-secrets)

## Next Steps

For architecture blueprints, see `shopify-architecture-variants`.
