---
name: replit-security-basics
description: |
  Apply Replit security best practices: Secrets management, REPL_IDENTITY tokens, Auth headers, and public Repl safety.
  Use when securing API keys, validating request identity,
  or auditing Replit security configuration.
  Trigger with phrases like "replit security", "replit secrets",
  "secure replit", "replit public safety", "replit identity token".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, security, secrets, audit]

---
# Replit Security Basics

## Overview
Security best practices for Replit: Secrets (AES-256 encrypted env vars), REPL_IDENTITY token verification, Auth header trust model, public Repl exposure risks, and Secret Scanner protection.

## Prerequisites
- Replit account with Workspace access
- Understanding of environment variables
- Deployed app (for Auth security)

## Instructions

### Step 1: Secrets Management
Replit Secrets are AES-256 encrypted at rest with TLS in transit. Keys rotate regularly. Two scopes:

```markdown
App-level secrets: Specific to one Repl (lock icon in sidebar)
Account-level secrets: Apply across all your Repls (Account Settings > Secrets)
```

```typescript
// Validate all required secrets at startup — fail fast
const REQUIRED = ['DATABASE_URL', 'JWT_SECRET', 'API_KEY'];
const missing = REQUIRED.filter(k => !process.env[k]);
if (missing.length) {
  console.error(`Missing secrets: ${missing.join(', ')}`);
  console.error('Add them in the Secrets tab (lock icon in sidebar)');
  process.exit(1);
}
```

**Secret Scanner**: Replit detects when you paste API keys into code files and warns you to store them as Secrets instead. Never dismiss this warning.

### Step 2: Public Repl Safety
Replit Repls are **public by default** on free plans. Your source code is visible to anyone.

```python
# CRITICAL: Never hardcode secrets in source files
# BAD — visible to anyone who views your Repl
API_KEY = "sk-live-abc123"  # exposed!

# GOOD — use Replit Secrets
import os
API_KEY = os.environ.get("API_KEY")
```

```gitignore
# .gitignore (also applies if you connect Repl to GitHub)
.env
.env.local
*.pem
*.key
```

### Step 3: REPL_IDENTITY Token Verification
Every Repl gets a `REPL_IDENTITY` environment variable — a PASETO token signed by Replit infrastructure. Use it for service-to-service authentication between Repls.

```typescript
// Verify a request came from a specific Repl
import { verify } from '@replit/repl-auth';

function verifyReplIdentity(identityToken: string): boolean {
  try {
    // REPL_PUBKEYS contains the ED25519 public key (base64-encoded)
    const pubkeys = JSON.parse(process.env.REPL_PUBKEYS || '{}');
    const payload = verify(identityToken, pubkeys);
    // payload contains: replId, user, slug, aud
    return !!payload;
  } catch {
    return false;
  }
}

// Use in middleware for Repl-to-Repl calls
app.post('/internal/api', (req, res) => {
  const identity = req.headers['x-repl-identity'] as string;
  if (!verifyReplIdentity(identity)) {
    return res.status(403).json({ error: 'Invalid Repl identity' });
  }
  // Process trusted request
});
```

### Step 4: Auth Header Trust Model
Replit Auth headers (`X-Replit-User-*`) are injected by Replit's proxy. They can be trusted on deployed apps but NOT on external networks.

```typescript
// Auth headers to read (set by Replit proxy)
const AUTH_HEADERS = [
  'x-replit-user-id',           // Unique user ID
  'x-replit-user-name',         // Username
  'x-replit-user-bio',          // User bio
  'x-replit-user-url',          // Profile URL
  'x-replit-user-profile-image',// Avatar URL
  'x-replit-user-roles',        // Comma-separated roles
  'x-replit-user-teams',        // Team memberships
] as const;

// IMPORTANT: Only trust these headers on *.replit.app or *.replit.dev domains
// If your app is also accessible via a custom domain without Replit proxy,
// an attacker could spoof these headers
function isSecureContext(): boolean {
  return !!process.env.REPL_SLUG; // Running on Replit
}
```

### Step 5: Database Security
```typescript
// PostgreSQL: connection string is secure by default on newer Replit databases
// Even if DATABASE_URL is leaked, it cannot be used outside your Repl

// However, always use parameterized queries
// BAD — SQL injection
const result = await pool.query(`SELECT * FROM users WHERE name = '${name}'`);

// GOOD — parameterized
const result = await pool.query('SELECT * FROM users WHERE name = $1', [name]);

// Replit KV Database: accessible only within the Repl
// No external access possible — REPLIT_DB_URL is internal only
```

### Step 6: Security Checklist
```markdown
## Replit Security Audit Checklist

### Secrets
- [ ] All API keys stored in Replit Secrets (never in code)
- [ ] Required secrets validated at startup
- [ ] No secrets in console.log() or error responses
- [ ] Secret Scanner warnings not dismissed

### Access
- [ ] Repl visibility appropriate (public vs private)
- [ ] Auth headers validated on protected routes
- [ ] Database queries use parameterized statements
- [ ] Error responses don't expose stack traces in production

### Deployment
- [ ] Production uses Deployments (not just "Run")
- [ ] Custom domains have SSL (auto-provisioned by Replit)
- [ ] Health endpoint doesn't expose sensitive info
- [ ] NODE_ENV set to "production" in deployment config

### Team
- [ ] Roles assigned with least privilege
- [ ] Inactive members removed (seat audit)
- [ ] SSO enforced (Enterprise)
- [ ] Deployment permissions restricted to admins
```

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Secret in source code | Secret Scanner alert | Move to Secrets tab immediately |
| Public Repl with secrets | Code review | Make Repl private or use Secrets |
| Auth header spoofing | Custom domain without proxy | Only trust headers on Replit domains |
| SQL injection | Code audit | Use parameterized queries exclusively |
| Stack trace exposure | Error handler review | Catch all errors, return safe messages |

## Resources
- [Replit Secrets](https://docs.replit.com/replit-workspace/workspace-features/secrets)
- [Replit Security](https://replit.com/products/security)
- [Repl Identity (PASETO)](https://blog.replit.com/repl-identity)
- [Secure Vibe Coding](https://blog.replit.com/16-ways-to-vibe-code-securely)

## Next Steps
For production deployment, see `replit-prod-checklist`.
