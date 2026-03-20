---
name: maintainx-security-basics
description: |
  Configure MaintainX API security, credential management, and access control.
  Use when securing API keys, implementing access controls,
  or hardening your MaintainX integration.
  Trigger with phrases like "maintainx security", "maintainx api key security",
  "secure maintainx", "maintainx credentials", "maintainx access control".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# MaintainX Security Basics

## Overview
Secure your MaintainX integration with proper credential management, input validation, audit logging, and key rotation procedures.

## Prerequisites
- MaintainX account with admin access
- Node.js 18+
- Familiarity with environment variables and secret management

## Instructions

### Step 1: Secure Credential Storage

Never hardcode API keys. Use environment variables or a secret manager.

```bash
# .env (never committed to git)
MAINTAINX_API_KEY=mx-prod-key-here

# .gitignore
.env
.env.*
*.key
```

```typescript
// src/config.ts - load and validate credentials
import 'dotenv/config';

const REQUIRED_VARS = ['MAINTAINX_API_KEY'] as const;

export function validateEnv() {
  const missing = REQUIRED_VARS.filter((v) => !process.env[v]);
  if (missing.length > 0) {
    throw new Error(`Missing required env vars: ${missing.join(', ')}`);
  }
}

validateEnv();
export const API_KEY = process.env.MAINTAINX_API_KEY!;
```

### Step 2: Git Hook to Prevent Secret Commits

```bash
# Install pre-commit hook
cat > .git/hooks/pre-commit << 'HOOK'
#!/bin/bash
# Block commits containing API keys
if git diff --cached --diff-filter=ACMR | grep -qiE '(MAINTAINX_API_KEY|Bearer mx-)'; then
  echo "ERROR: Potential MaintainX API key detected in staged files."
  echo "Remove secrets before committing."
  exit 1
fi
HOOK
chmod +x .git/hooks/pre-commit
```

Or use `gitleaks`:
```bash
npx gitleaks detect --source . --no-git
```

### Step 3: Input Validation

Validate all user input before sending to the MaintainX API:

```typescript
// src/validation.ts
import { z } from 'zod';

const WorkOrderInput = z.object({
  title: z.string().min(1).max(500),
  description: z.string().max(5000).optional(),
  priority: z.enum(['NONE', 'LOW', 'MEDIUM', 'HIGH']).default('NONE'),
  status: z.enum(['OPEN', 'IN_PROGRESS', 'ON_HOLD', 'COMPLETED', 'CLOSED']).default('OPEN'),
  assignees: z.array(z.object({
    type: z.enum(['USER', 'TEAM']),
    id: z.number().positive(),
  })).optional(),
  assetId: z.number().positive().optional(),
  locationId: z.number().positive().optional(),
  dueDate: z.string().datetime().optional(),
});

export function validateWorkOrder(input: unknown) {
  return WorkOrderInput.parse(input);
}

// Usage
try {
  const validated = validateWorkOrder(userInput);
  await client.createWorkOrder(validated);
} catch (err) {
  if (err instanceof z.ZodError) {
    console.error('Validation failed:', err.issues);
  }
}
```

### Step 4: Audit Logging

```typescript
// src/audit-logger.ts
interface AuditEntry {
  timestamp: string;
  action: string;
  resource: string;
  resourceId?: number;
  userId: string;
  ip?: string;
  result: 'success' | 'failure';
  details?: string;
}

class AuditLogger {
  private entries: AuditEntry[] = [];

  log(entry: Omit<AuditEntry, 'timestamp'>) {
    const full: AuditEntry = { ...entry, timestamp: new Date().toISOString() };
    this.entries.push(full);
    // Structured JSON for log aggregation (ELK, CloudWatch, etc.)
    console.log(JSON.stringify({ type: 'audit', ...full }));
  }
}

export const audit = new AuditLogger();

// Usage in API wrapper
async function createWorkOrderAudited(client: MaintainXClient, input: any, userId: string) {
  try {
    const wo = await client.createWorkOrder(input);
    audit.log({
      action: 'workorder.create',
      resource: 'workorder',
      resourceId: wo.id,
      userId,
      result: 'success',
    });
    return wo;
  } catch (err: any) {
    audit.log({
      action: 'workorder.create',
      resource: 'workorder',
      userId,
      result: 'failure',
      details: err.message,
    });
    throw err;
  }
}
```

### Step 5: API Key Rotation

```typescript
// scripts/rotate-key.ts
// Run quarterly: npx tsx scripts/rotate-key.ts

async function rotateApiKey() {
  console.log('=== MaintainX API Key Rotation ===');
  console.log('1. Go to https://app.getmaintainx.com > Settings > Integrations');
  console.log('2. Click "Generate New Key"');
  console.log('3. Update the key in your secret manager / .env');
  console.log('4. Verify with: curl -s -o /dev/null -w "%{http_code}" \\');
  console.log('     https://api.getmaintainx.com/v1/users?limit=1 \\');
  console.log('     -H "Authorization: Bearer NEW_KEY"');
  console.log('5. Revoke the old key in MaintainX Settings');
  console.log('6. Update CI/CD secrets (GitHub Actions, GCP Secret Manager)');
  console.log('');
  console.log('Rotation schedule: every 90 days');
  console.log('Next rotation due:', new Date(Date.now() + 90 * 86400000).toISOString().split('T')[0]);
}

rotateApiKey();
```

## Output
- `.env` with API key, protected by `.gitignore`
- Pre-commit hook blocking secret leaks
- Zod-based input validation for all API inputs
- Structured audit logging for compliance
- Key rotation procedure with verification steps

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Key leaked to git | Committed `.env` or hardcoded key | Rotate immediately, add pre-commit hook |
| Validation errors | Invalid user input | Use Zod schema to validate before API calls |
| Audit gaps | Missing log entries | Wrap all API calls with audit logger |
| Stale key | Key not rotated in > 90 days | Follow rotation procedure in Step 5 |

## Resources
- [MaintainX Security](https://www.getmaintainx.com/security)
- [OWASP API Security Top 10](https://owasp.org/API-Security/)
- [gitleaks](https://github.com/gitleaks/gitleaks) -- Secret detection in git repos
- [Zod](https://zod.dev/) -- TypeScript-first schema validation

## Next Steps
For production deployment, see `maintainx-prod-checklist`.

## Examples

**Middleware for Express API that validates and audits**:

```typescript
function secureEndpoint(schema: z.ZodSchema) {
  return async (req: express.Request, res: express.Response, next: express.NextFunction) => {
    try {
      req.body = schema.parse(req.body);
      audit.log({
        action: req.method + ' ' + req.path,
        resource: req.path,
        userId: req.headers['x-user-id'] as string,
        result: 'success',
      });
      next();
    } catch (err) {
      res.status(400).json({ error: 'Validation failed', details: (err as z.ZodError).issues });
    }
  };
}
```
