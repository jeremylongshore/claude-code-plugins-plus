---
name: apollo-security-basics
description: |
  Apply Apollo.io API security best practices.
  Use when securing Apollo integrations, managing API keys,
  or implementing secure data handling.
  Trigger with phrases like "apollo security", "secure apollo api",
  "apollo api key security", "apollo data protection".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, api, security]

---
# Apollo Security Basics

## Overview
Security best practices for Apollo.io API integrations. Apollo API keys grant broad access to 275M+ contacts — a leaked key is a serious incident. This covers key management, PII redaction, data access controls, key rotation, and audit procedures.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+

## Instructions

### Step 1: Secure API Key Storage
Apollo supports two key types with different risk profiles:
- **Standard key**: search + enrichment only (lower risk)
- **Master key**: full CRM access including delete (highest risk)

```typescript
// NEVER: const API_KEY = 'abc123';  // hardcoded
// NEVER: params: { api_key: key }   // query string (logged in server access logs)

// ALWAYS: x-api-key header + env var or secret manager
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

async function getApiKey(): Promise<string> {
  // Dev/staging: environment variable
  if (process.env.APOLLO_API_KEY) return process.env.APOLLO_API_KEY;

  // Production: GCP Secret Manager
  const client = new SecretManagerServiceClient();
  const [version] = await client.accessSecretVersion({
    name: 'projects/my-project/secrets/apollo-api-key/versions/latest',
  });
  return version.payload?.data?.toString() ?? '';
}
```

```bash
# .gitignore — prevent accidental commits
.env
.env.local
.env.*.local
*.pem
secrets/
```

### Step 2: PII Redaction for Logging
Apollo responses contain emails, phone numbers, and LinkedIn profiles. Never log raw responses in production.

```typescript
// src/apollo/redact.ts
const PII_PATTERNS: [RegExp, string][] = [
  [/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b/gi, '[EMAIL]'],
  [/\b\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b/g, '[PHONE]'],
  [/x-api-key[:\s]+["']?[\w-]+["']?/gi, 'x-api-key: [REDACTED]'],
  [/linkedin\.com\/in\/[^\s"',]+/gi, 'linkedin.com/in/[REDACTED]'],
];

export function redactPII(text: string): string {
  let result = text;
  for (const [pattern, replacement] of PII_PATTERNS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// Attach as axios interceptor
client.interceptors.response.use((response) => {
  if (process.env.NODE_ENV === 'production') {
    // Never log raw Apollo response data in production
    console.log(`[Apollo] ${response.status} ${response.config.url}`);
  } else {
    console.log('[Apollo]', redactPII(JSON.stringify(response.data).slice(0, 500)));
  }
  return response;
});
```

### Step 3: Use Minimal Key Permissions
```typescript
// src/apollo/scoped-client.ts
// Use standard keys for read-only operations, master keys only where needed

export function createReadOnlyClient() {
  return axios.create({
    baseURL: 'https://api.apollo.io/api/v1',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.APOLLO_STANDARD_KEY!,  // search + enrich only
    },
  });
}

export function createFullAccessClient() {
  return axios.create({
    baseURL: 'https://api.apollo.io/api/v1',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': process.env.APOLLO_MASTER_KEY!,  // full CRM access
    },
  });
}
```

### Step 4: API Key Rotation Procedure
```typescript
async function rotateApiKey() {
  // 1. Generate new key in Apollo Dashboard (Settings > Integrations > API Keys)
  const newKey = process.env.APOLLO_API_KEY_NEW;
  const oldKey = process.env.APOLLO_API_KEY;

  // 2. Verify new key works
  try {
    const resp = await axios.get('https://api.apollo.io/api/v1/auth/health', {
      headers: { 'x-api-key': newKey! },
    });
    if (!resp.data.is_logged_in) throw new Error('New key failed auth check');
    console.log('New API key verified');
  } catch {
    console.error('New API key invalid — aborting rotation');
    return;
  }

  // 3. Update secret manager / env vars with new key
  // 4. Deploy with new key
  // 5. Revoke old key in Apollo Dashboard
  console.log('Rotation steps: update secrets -> deploy -> revoke old key in dashboard');
}
```

### Step 5: Security Audit Script
```typescript
async function runSecurityAudit() {
  const checks: Array<{ name: string; pass: boolean; detail: string }> = [];

  // 1. API key not in source code
  const { execSync } = await import('child_process');
  try {
    execSync('grep -rn "x-api-key.*[a-zA-Z0-9]\\{20,\\}" src/ --include="*.ts"', { stdio: 'pipe' });
    checks.push({ name: 'No hardcoded keys', pass: false, detail: 'Hardcoded key found in source!' });
  } catch {
    checks.push({ name: 'No hardcoded keys', pass: true, detail: 'OK' });
  }

  // 2. HTTPS enforced
  checks.push({
    name: 'HTTPS only',
    pass: !process.env.APOLLO_BASE_URL || process.env.APOLLO_BASE_URL.startsWith('https://'),
    detail: 'Base URL uses HTTPS',
  });

  // 3. .env is gitignored
  const gitCheck = execSync('git check-ignore .env 2>/dev/null || echo NOT').toString().trim();
  checks.push({ name: '.env gitignored', pass: gitCheck !== 'NOT', detail: gitCheck !== 'NOT' ? 'OK' : 'ADD .env to .gitignore' });

  // 4. Header auth (not query param)
  try {
    execSync('grep -rn "api_key.*=" src/ --include="*.ts" | grep -v "x-api-key"', { stdio: 'pipe' });
    checks.push({ name: 'Header auth only', pass: false, detail: 'Found api_key in query params — use x-api-key header' });
  } catch {
    checks.push({ name: 'Header auth only', pass: true, detail: 'OK' });
  }

  for (const c of checks) console.log(`${c.pass ? 'PASS' : 'FAIL'} ${c.name}: ${c.detail}`);
}
```

## Output
- Secure API key loading from env vars or GCP Secret Manager
- PII redaction utility for emails, phones, API keys, and LinkedIn URLs
- Scoped clients: read-only (standard key) vs full-access (master key)
- Key rotation procedure with verification
- Automated security audit checking for hardcoded keys and header auth

## Error Handling
| Issue | Mitigation |
|-------|------------|
| API key committed to git | Rotate immediately, revoke old key in Apollo dashboard |
| PII in log files | Enable `redactPII` interceptor, review log retention |
| Using `api_key` query param | Switch to `x-api-key` header — query params appear in server logs |
| Master key used everywhere | Split into standard + master keys, use minimal permissions |

## Resources
- [Apollo Security Practices](https://www.apollo.io/security)
- [Create API Keys](https://docs.apollo.io/docs/create-api-key)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)

## Next Steps
Proceed to `apollo-prod-checklist` for production deployment.
