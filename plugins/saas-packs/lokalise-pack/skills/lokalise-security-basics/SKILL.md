---
name: lokalise-security-basics
description: |
  Apply Lokalise security best practices for API tokens and access control.
  Use when securing API tokens, implementing least privilege access,
  or auditing Lokalise security configuration.
  Trigger with phrases like "lokalise security", "lokalise secrets",
  "secure lokalise", "lokalise API token security".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lokalise, api, security, audit]

---
# Lokalise Security Basics

## Overview
Security practices for Lokalise integrations: API token management with scoped permissions, translation content sanitization, CI/CD secret handling, webhook secret verification, and audit logging. Lokalise handles translation strings that may contain user-facing content, interpolation variables, and occasionally PII embedded in keys or values.

## Prerequisites
- Lokalise API token provisioned (admin token for audit, scoped tokens for operations)
- Understanding of Lokalise token permission model (read-only vs read-write)
- Secret management infrastructure (GitHub Secrets, AWS Secrets Manager, GCP Secret Manager, or Vault)

## Instructions

### Step 1: Token Scope Management

Lokalise API tokens are either read-only or read-write. Create separate tokens per use case to enforce least privilege.

```typescript
import { LokaliseApi } from "@lokalise/node-api";

// Token strategy: separate tokens per context
const TOKENS = {
  // CI download pipeline — read-only token
  ciDownload: process.env.LOKALISE_READ_TOKEN,
  // CI upload pipeline — read-write token
  ciUpload: process.env.LOKALISE_WRITE_TOKEN,
  // Admin operations (contributor management, webhooks) — admin token
  admin: process.env.LOKALISE_ADMIN_TOKEN,
} as const;

function getClient(scope: keyof typeof TOKENS): LokaliseApi {
  const token = TOKENS[scope];
  if (!token) {
    throw new Error(
      `LOKALISE_${scope.toUpperCase()}_TOKEN not set. ` +
      `Generate at https://app.lokalise.com/profile#apitokens`
    );
  }
  return new LokaliseApi({ apiKey: token, enableCompression: true });
}

// Download translations — uses read-only token
const readClient = getClient("ciDownload");
const bundle = await readClient.files().download(projectId, {
  format: "json",
  original_filenames: false,
  bundle_structure: "%LANG_ISO%.json",
});
```

### Step 2: Validate Translation Content

Translation strings may contain interpolation variables, HTML, or user-generated content. Validate before rendering.

```typescript
interface ValidationIssue {
  key: string;
  severity: "critical" | "warning";
  message: string;
}

function validateTranslation(key: string, value: string): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  // XSS: Check for script injection in translations
  if (/<script|javascript:|on\w+=/i.test(value)) {
    issues.push({ key, severity: "critical", message: "Potential XSS payload" });
  }

  // Credential leak: Check for secrets in translation values
  if (/(api_key|password|secret|token)\s*[:=]/i.test(value)) {
    issues.push({ key, severity: "critical", message: "Possible credential in value" });
  }

  // Placeholder integrity: Ensure ICU/i18next placeholders are well-formed
  const placeholders = value.match(/\{[^}]+\}|\{\{[^}]+\}\}/g) ?? [];
  for (const p of placeholders) {
    if (/[<>'"]/.test(p)) {
      issues.push({ key, severity: "warning", message: `Suspicious placeholder: ${p}` });
    }
  }

  return issues;
}

// Validate all translations after download
import { readFileSync } from "fs";

function auditTranslationFile(filePath: string): ValidationIssue[] {
  const data: Record<string, string> = JSON.parse(
    readFileSync(filePath, "utf-8")
  );
  return Object.entries(data).flatMap(([key, value]) =>
    validateTranslation(key, value)
  );
}

const issues = auditTranslationFile("./src/locales/de.json");
const critical = issues.filter((i) => i.severity === "critical");
if (critical.length > 0) {
  console.error("CRITICAL security issues found in translations:");
  critical.forEach((i) => console.error(`  ${i.key}: ${i.message}`));
  process.exit(1);
}
```

### Step 3: Webhook Secret Verification

Lokalise sends a random alphanumeric secret in the `X-Secret` header. Always verify it.

```typescript
import express from "express";

const WEBHOOK_SECRET = process.env.LOKALISE_WEBHOOK_SECRET!;

function verifyWebhookSecret(
  req: express.Request,
  res: express.Response,
  next: express.NextFunction
): void {
  const secret = req.headers["x-secret"] as string | undefined;

  if (!secret || secret !== WEBHOOK_SECRET) {
    console.error("Webhook secret verification failed", {
      ip: req.ip,
      path: req.path,
      hasSecret: !!secret,
    });
    res.status(401).json({ error: "Invalid webhook secret" });
    return;
  }
  next();
}
```

### Step 4: CI/CD Token Security

```yaml
# GitHub Actions: use repository secrets, never hardcode tokens
name: Sync Translations
on:
  push:
    branches: [main]
    paths: ['src/locales/en.json']

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Pull translations
        env:
          LOKALISE_API_TOKEN: ${{ secrets.LOKALISE_READ_TOKEN }}
          LOKALISE_PROJECT_ID: ${{ vars.LOKALISE_PROJECT_ID }}
        run: |
          # Token is masked in logs by GitHub Actions
          lokalise2 file download \
            --token "$LOKALISE_API_TOKEN" \
            --project-id "$LOKALISE_PROJECT_ID" \
            --format json \
            --original-filenames=false \
            --bundle-structure "%LANG_ISO%.json" \
            --unzip-to ./src/locales/
```

### Step 5: Scan for Hardcoded Tokens

```bash
#!/bin/bash
# scripts/scan-secrets.sh — Run in CI or as pre-commit hook
set -euo pipefail

echo "=== Lokalise Token Security Scan ==="

# Check for hardcoded tokens in source files
HARDCODED=$(grep -rn "X-Api-Token\|apiKey.*['\"][a-f0-9]\{32,\}" \
  --include="*.ts" --include="*.js" --include="*.json" --include="*.yml" \
  src/ .github/ 2>/dev/null \
  | grep -v node_modules \
  | grep -v "process.env\|secrets\.\|vars\.\|\${{" || true)

if [[ -n "$HARDCODED" ]]; then
  echo "FAIL: Potential hardcoded token found:"
  echo "$HARDCODED"
  exit 1
fi

# Verify .env files are gitignored
if ! grep -q "\.env" .gitignore 2>/dev/null; then
  echo "WARN: .env not in .gitignore — add it immediately"
fi

# Check git history for leaked tokens
HISTORY_LEAK=$(git log --all -p --diff-filter=A -- '*.env' '*.env.*' 2>/dev/null \
  | grep -i "LOKALISE_API_TOKEN=" | head -3 || true)

if [[ -n "$HISTORY_LEAK" ]]; then
  echo "CRITICAL: Token found in git history. Rotate immediately."
  echo "  Use 'git filter-repo' to remove, then rotate the token."
  exit 1
fi

echo "PASS: No hardcoded tokens detected"
```

### Step 6: Audit Translation Changes

```typescript
interface TranslationAuditEntry {
  timestamp: string;
  projectId: string;
  key: string;
  locale: string;
  userId: string;
  action: "create" | "update" | "delete";
  // Never log actual content — may contain PII
  oldLength: number;
  newLength: number;
}

function logTranslationChange(entry: TranslationAuditEntry): void {
  // Ship to your logging backend (Datadog, CloudWatch, etc.)
  console.log(JSON.stringify({
    level: "info",
    event: "translation_change",
    ...entry,
  }));
}
```

## Output
- Scoped token configuration with separate read/write/admin tokens
- Translation content validator catching XSS, credential leaks, and malformed placeholders
- Webhook secret verification middleware for Express
- CI/CD workflow using repository secrets with masked output
- Pre-commit/CI scan script for hardcoded tokens
- Audit logging for translation changes (PII-safe)

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Token leaked in CI logs | Token in command output | Use env variables; GitHub Actions auto-masks secrets |
| XSS via translations | Unsanitized translation rendered as HTML | Validate with `validateTranslation()` before use |
| Overprivileged access | Using admin token for read-only operations | Create scoped tokens per use case |
| Unauthorized changes | No audit trail | Register webhook for `project.translation.updated` events |
| Token in git history | Committed .env file | Rotate token immediately, use `git filter-repo` to scrub |

## Resources
- [Lokalise API Authentication](https://developers.lokalise.com/reference/api-authentication)
- [Lokalise Security](https://lokalise.com/security)
- [Webhook Events Reference](https://developers.lokalise.com/docs/webhook-events)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)

## Next Steps
For enterprise-level access control with SSO and contributor groups, see `lokalise-enterprise-rbac`.
