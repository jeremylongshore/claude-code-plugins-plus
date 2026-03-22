---
name: langfuse-security-basics
description: |
  Implement Langfuse security best practices for API keys and data privacy.
  Use when securing Langfuse integration, protecting API keys,
  or implementing data privacy controls for LLM observability.
  Trigger with phrases like "langfuse security", "langfuse API key security",
  "langfuse data privacy", "secure langfuse", "langfuse PII".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langfuse, api, security, observability]

---
# Langfuse Security Basics

## Overview
Security practices for Langfuse LLM observability: credential management, PII scrubbing before tracing, self-hosted hardening, data retention, and secret scanning.

## Prerequisites
- Langfuse instance (cloud or self-hosted)
- API keys provisioned
- Understanding of data privacy requirements (GDPR, SOC2, HIPAA)

## Instructions

### Step 1: Credential Security

Langfuse uses two keys with different security profiles:

```typescript
// Startup validation -- catch misconfigurations early
function validateLangfuseCredentials() {
  const publicKey = process.env.LANGFUSE_PUBLIC_KEY;
  const secretKey = process.env.LANGFUSE_SECRET_KEY;

  if (!publicKey || !secretKey) {
    throw new Error("LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required");
  }

  // Catch key swap (common mistake)
  if (secretKey.startsWith("pk-lf-")) {
    throw new Error("LANGFUSE_SECRET_KEY contains a public key (pk-lf-). Keys are swapped.");
  }

  if (publicKey.startsWith("sk-lf-")) {
    throw new Error("LANGFUSE_PUBLIC_KEY contains a secret key (sk-lf-). Keys are swapped.");
  }

  return { publicKey, secretKey };
}

// Use validated credentials
const { publicKey, secretKey } = validateLangfuseCredentials();
```

**Key security rules:**
- Public key (`pk-lf-...`): Identifies the project. Safe in client-side code.
- Secret key (`sk-lf-...`): Grants write access. **Server-side only.**
- Store in environment variables or secret manager -- never in source code.
- Rotate keys immediately if exposed in logs, git, or error reports.

### Step 2: PII Scrubbing Before Tracing

Langfuse stores everything you send. Scrub PII from inputs and outputs before tracing.

```typescript
// src/lib/pii-scrubber.ts

const PII_PATTERNS: Array<{ regex: RegExp; replacement: string }> = [
  { regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b/gi, replacement: "[EMAIL]" },
  { regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, replacement: "[PHONE]" },
  { regex: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: "[SSN]" },
  { regex: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, replacement: "[CARD]" },
  { regex: /\b(?:sk|pk)-[a-zA-Z0-9_-]{20,}\b/g, replacement: "[API_KEY]" },
];

export function scrubPII(text: string): string {
  let scrubbed = text;
  for (const { regex, replacement } of PII_PATTERNS) {
    scrubbed = scrubbed.replace(regex, replacement);
  }
  return scrubbed;
}

export function scrubObject(obj: any): any {
  if (typeof obj === "string") return scrubPII(obj);
  if (Array.isArray(obj)) return obj.map(scrubObject);
  if (typeof obj === "object" && obj !== null) {
    const result: Record<string, any> = {};
    for (const [key, value] of Object.entries(obj)) {
      result[key] = scrubObject(value);
    }
    return result;
  }
  return obj;
}
```

```typescript
// Usage with tracing
import { observe, updateActiveObservation } from "@langfuse/tracing";
import { scrubPII, scrubObject } from "./lib/pii-scrubber";

const tracedChat = observe(async (userMessage: string) => {
  // Scrub input before tracing
  updateActiveObservation({ input: scrubPII(userMessage) });

  // Send original to LLM (unscrubbed)
  const response = await callLLM(userMessage);

  // Scrub output before tracing
  updateActiveObservation({ output: scrubPII(response) });
  return response;
});
```

### Step 3: Self-Hosted Hardening

```yaml
# docker-compose.yml -- production-hardened
services:
  langfuse:
    image: langfuse/langfuse:latest
    environment:
      # Disable open registration
      - AUTH_DISABLE_SIGNUP=true
      # Enforce SSO for your domain
      - AUTH_DOMAINS_WITH_SSO_ENFORCEMENT=company.com
      # Least-privilege default role
      - LANGFUSE_DEFAULT_PROJECT_ROLE=VIEWER
      # Encrypt data at rest
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      # Data retention (days)
      - LANGFUSE_RETENTION_DAYS=90
      # Database
      - DATABASE_URL=${DATABASE_URL}
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - SALT=${SALT}
```

### Step 4: Git Secret Scanning

Prevent Langfuse keys from being committed:

```bash
# .gitignore
.env
.env.local
.env.production
```

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for Langfuse keys
        run: |
          if grep -rn "sk-lf-[a-zA-Z0-9]" --include="*.ts" --include="*.js" --include="*.py" .; then
            echo "ERROR: Secret key found in source code!"
            exit 1
          fi
```

### Step 5: Scoped API Keys and Least Privilege

```typescript
// Create separate API keys per service/environment
// In Langfuse dashboard: Settings > API Keys

// Backend API service -- full write access
// LANGFUSE_SECRET_KEY=sk-lf-backend-...

// Analytics worker -- read-only access
// Use Langfuse API with read-only key
// LANGFUSE_SECRET_KEY=sk-lf-readonly-...

// CI/CD pipeline -- scoped to test project
// LANGFUSE_SECRET_KEY=sk-lf-ci-test-...
// LANGFUSE_PUBLIC_KEY=pk-lf-ci-test-...
```

## Security Checklist

| Category | Check | Status |
|----------|-------|--------|
| Credentials | Secret key in env vars / secret manager only | |
| Credentials | Keys validated at startup (no swap) | |
| Credentials | .env files in .gitignore | |
| Data Privacy | PII scrubbed from trace inputs/outputs | |
| Data Privacy | Retention policy configured | |
| Self-Hosted | Signup disabled, SSO enforced | |
| Self-Hosted | Encryption key set for data at rest | |
| CI/CD | Secret scanning in pipeline | |
| Access | Least-privilege roles per team member | |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII in traces | Not scrubbing before trace | Apply `scrubPII()` to all inputs/outputs |
| Secret key leaked | Key in source code | Rotate immediately, add secret scanning |
| Unauthorized access | Default roles too permissive | Set `LANGFUSE_DEFAULT_PROJECT_ROLE=VIEWER` |
| Data accumulation | No retention policy | Set `LANGFUSE_RETENTION_DAYS` |

## Resources
- [Langfuse Data Security](https://langfuse.com/docs/data-security-privacy)
- [Self-Hosting Configuration](https://langfuse.com/self-hosting/configuration)
- [Headless Initialization](https://langfuse.com/self-hosting/administration/headless-initialization)
