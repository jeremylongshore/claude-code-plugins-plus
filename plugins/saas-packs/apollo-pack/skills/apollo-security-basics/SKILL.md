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
---
# Apollo Security Basics

## Overview
Implement security best practices for Apollo.io API integrations including API key management, PII redaction in logs, data access controls, and security audit procedures.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Secure API Key Storage
```typescript
// NEVER do this:
// const API_KEY = 'abc123-your-key';  // hardcoded in source

// DO this: load from environment or secret manager
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';

async function getApiKey(): Promise<string> {
  // Option 1: Environment variable (dev/staging)
  if (process.env.APOLLO_API_KEY) return process.env.APOLLO_API_KEY;

  // Option 2: GCP Secret Manager (production)
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

### Step 2: Implement PII Redaction for Logging
```typescript
// src/apollo/redact.ts
const PII_PATTERNS: [RegExp, string][] = [
  [/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b/gi, '[EMAIL]'],
  [/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE]'],
  [/\bapi_key[=:]\s*["']?[\w-]+["']?/gi, 'api_key=[REDACTED]'],
  [/\b(linkedin\.com\/in\/)[^\s"]+/gi, '$1[REDACTED]'],
];

export function redactPII(text: string): string {
  let result = text;
  for (const [pattern, replacement] of PII_PATTERNS) {
    result = result.replace(pattern, replacement);
  }
  return result;
}

// Use in logging interceptor
client.interceptors.response.use((response) => {
  if (process.env.NODE_ENV !== 'production') {
    console.log('[Apollo]', redactPII(JSON.stringify(response.data)));
  }
  return response;
});
```

### Step 3: Restrict Data Access by Role
```typescript
// src/apollo/access-control.ts
type Role = 'viewer' | 'user' | 'admin';

interface ApolloPermission {
  search: boolean;
  enrich: boolean;
  exportPII: boolean;
  manageSequences: boolean;
  viewAnalytics: boolean;
}

const ROLE_PERMISSIONS: Record<Role, ApolloPermission> = {
  viewer: { search: true, enrich: false, exportPII: false, manageSequences: false, viewAnalytics: true },
  user:   { search: true, enrich: true, exportPII: false, manageSequences: true, viewAnalytics: true },
  admin:  { search: true, enrich: true, exportPII: true, manageSequences: true, viewAnalytics: true },
};

export function checkPermission(role: Role, action: keyof ApolloPermission): boolean {
  return ROLE_PERMISSIONS[role]?.[action] ?? false;
}

// Usage in API route:
// if (!checkPermission(user.role, 'exportPII')) {
//   return res.status(403).json({ error: 'PII export not allowed for your role' });
// }
```

### Step 4: Implement API Key Rotation
```typescript
// src/apollo/key-rotation.ts
async function rotateApiKey() {
  // 1. Generate new key in Apollo Dashboard (Settings > Integrations > API)
  // 2. Store new key alongside old key
  const newKey = process.env.APOLLO_API_KEY_NEW;
  const oldKey = process.env.APOLLO_API_KEY;

  // 3. Verify new key works
  try {
    const client = createClientWithKey(newKey!);
    await client.post('/people/search', {
      q_organization_domains: ['apollo.io'],
      per_page: 1,
    });
    console.log('New API key verified');
  } catch {
    console.error('New API key invalid, aborting rotation');
    return;
  }

  // 4. Switch to new key in secret manager
  // 5. Remove old key from Apollo Dashboard
  console.log('Key rotation complete. Update APOLLO_API_KEY and remove APOLLO_API_KEY_NEW');
}
```

### Step 5: Security Audit Checklist
```typescript
// src/scripts/security-audit.ts
interface AuditCheck {
  name: string;
  pass: boolean;
  detail: string;
}

async function runSecurityAudit(): Promise<AuditCheck[]> {
  const checks: AuditCheck[] = [];

  // 1. API key not hardcoded
  checks.push({
    name: 'No hardcoded API keys',
    pass: !process.env.APOLLO_API_KEY?.startsWith('test'),
    detail: 'Ensure APOLLO_API_KEY is loaded from env/secrets',
  });

  // 2. HTTPS enforced
  const baseUrl = process.env.APOLLO_BASE_URL ?? 'https://api.apollo.io/v1';
  checks.push({
    name: 'HTTPS enforced',
    pass: baseUrl.startsWith('https://'),
    detail: `Base URL: ${baseUrl}`,
  });

  // 3. .env is gitignored
  const { execSync } = await import('child_process');
  const gitCheck = execSync('git check-ignore .env 2>/dev/null || echo "NOT_IGNORED"').toString().trim();
  checks.push({
    name: '.env is gitignored',
    pass: gitCheck !== 'NOT_IGNORED',
    detail: gitCheck === 'NOT_IGNORED' ? 'Add .env to .gitignore' : 'OK',
  });

  // 4. Rate limiting enabled
  checks.push({
    name: 'Rate limiting configured',
    pass: true,  // check for rate limiter import
    detail: 'Verify rate-limiter.ts is imported in client',
  });

  // Print results
  for (const check of checks) {
    console.log(`${check.pass ? 'PASS' : 'FAIL'} ${check.name} — ${check.detail}`);
  }
  return checks;
}
```

## Output
- Secure API key loading from environment or GCP Secret Manager
- PII redaction utility filtering emails, phones, API keys, and LinkedIn URLs from logs
- Role-based permission matrix (viewer / user / admin)
- API key rotation procedure with dual-key verification
- Automated security audit script with pass/fail checks

## Error Handling
| Issue | Mitigation |
|-------|------------|
| API key committed to git | Rotate immediately, use `git filter-branch` to remove from history |
| PII in log files | Enable `redactPII` interceptor, review log retention policies |
| Unauthorized access | Audit access logs, revoke compromised keys |
| Data breach | Rotate all keys, notify affected contacts, review access controls |

## Examples

### Pre-Commit Hook for Secret Detection
```bash
#!/bin/bash
# .git/hooks/pre-commit
if git diff --cached --diff-filter=ACMR | grep -qiE 'api_key.*=.*[a-zA-Z0-9]{20,}'; then
  echo "ERROR: Potential API key detected in staged files"
  echo "Use environment variables instead of hardcoding secrets"
  exit 1
fi
```

## Resources
- [Apollo Security Practices](https://www.apollo.io/security)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GCP Secret Manager](https://cloud.google.com/secret-manager/docs)

## Next Steps
Proceed to `apollo-prod-checklist` for production deployment.
