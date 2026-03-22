---
name: replit-policy-guardrails
description: |
  Enforce security and resource policies for Replit-hosted apps: secrets exposure prevention,
  resource limits, deployment visibility, and database access controls.
  Use when hardening a Replit app for production, auditing security posture,
  or setting up guardrails for team development.
  Trigger with phrases like "replit policy", "replit guardrails",
  "replit security audit", "replit hardening", "replit best practices check".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, security, policy]

---
# Replit Policy Guardrails

## Overview
Policy enforcement for Replit-hosted applications. Replit's public-by-default Repls, shared hosting, and resource limits require specific guardrails around secrets exposure, resource consumption, deployment security, and endpoint protection.

## Prerequisites
- Replit account with Deployment access
- Understanding of Replit's security model
- Awareness of Replit's Terms of Service

## Instructions

### Step 1: Secrets Exposure Prevention
Replit Repls are **public by default** on free plans. Source code is visible to anyone.

```python
# CRITICAL POLICY: Never hardcode secrets in source files

# BAD — visible to anyone viewing your Repl
API_KEY = "sk-live-abc123"
DB_PASSWORD = "p@ssw0rd"

# GOOD — use Replit Secrets (AES-256 encrypted)
import os

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY not set. Add it in the Secrets tab (lock icon).")

# Startup validation — fail fast if secrets missing
REQUIRED_SECRETS = ["API_KEY", "DATABASE_URL", "JWT_SECRET"]
missing = [s for s in REQUIRED_SECRETS if not os.environ.get(s)]
if missing:
    raise RuntimeError(f"Missing required secrets: {missing}")
```

**Automated secret detection:**
```typescript
// Pre-deploy check script: scripts/check-secrets.ts
import { readFileSync, readdirSync, statSync } from 'fs';
import { join } from 'path';

const SECRET_PATTERNS = [
  /sk[-_](?:live|test)[-_]\w{20,}/,     // API keys
  /(?:password|passwd|pwd)\s*[:=]\s*['"][^'"]+['"]/i,
  /(?:secret|token)\s*[:=]\s*['"][^'"]{10,}['"]/i,
  /-----BEGIN (?:RSA |EC )?PRIVATE KEY-----/,
  /eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+/,  // JWT tokens
];

function scanFile(filepath: string): string[] {
  const content = readFileSync(filepath, 'utf-8');
  const issues: string[] = [];

  SECRET_PATTERNS.forEach((pattern, i) => {
    if (pattern.test(content)) {
      issues.push(`${filepath}: potential secret found (pattern ${i})`);
    }
  });

  return issues;
}

function scanDirectory(dir: string): string[] {
  const issues: string[] = [];
  const entries = readdirSync(dir);

  for (const entry of entries) {
    if (['.git', 'node_modules', '.cache', 'dist'].includes(entry)) continue;
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) {
      issues.push(...scanDirectory(path));
    } else if (/\.(ts|js|py|json|env|yaml|yml|toml)$/.test(entry)) {
      issues.push(...scanFile(path));
    }
  }

  return issues;
}

const issues = scanDirectory('.');
if (issues.length > 0) {
  console.error('SECRET SCAN FAILED:');
  issues.forEach(i => console.error(`  ${i}`));
  process.exit(1);
}
console.log('Secret scan passed: no hardcoded secrets found.');
```

### Step 2: Resource Usage Guards
Replit containers have CPU and memory limits. Guard against runaway processes.

```python
import resource
import signal
import os

# Set memory limit (match your deployment tier)
MEMORY_LIMIT_MB = int(os.environ.get("MEMORY_LIMIT_MB", "512"))
resource.setrlimit(
    resource.RLIMIT_AS,
    (MEMORY_LIMIT_MB * 1024 * 1024, MEMORY_LIMIT_MB * 1024 * 1024)
)

# Per-request CPU timeout
def timeout_handler(signum, frame):
    raise TimeoutError("Request exceeded CPU time limit")

signal.signal(signal.SIGALRM, timeout_handler)

@app.route('/process')
def process_request():
    signal.alarm(30)  # 30 second max
    try:
        result = heavy_computation()
        return jsonify(result)
    except TimeoutError:
        return jsonify({"error": "Request timed out"}), 504
    finally:
        signal.alarm(0)
```

```typescript
// Node.js: memory and request size limits
app.use(express.json({ limit: '1mb' }));  // Prevent payload bombs
app.use(express.urlencoded({ limit: '1mb', extended: true }));

// Monitor and alert on high memory
setInterval(() => {
  const heapMB = Math.round(process.memoryUsage().heapUsed / 1024 / 1024);
  if (heapMB > 400) {  // Approaching 512MB limit
    console.warn(`HIGH MEMORY: ${heapMB}MB — consider restart`);
  }
}, 30000);
```

### Step 3: Endpoint Protection
```typescript
// Protect all data endpoints with authentication
import { Request, Response, NextFunction } from 'express';

function requireAuth(req: Request, res: Response, next: NextFunction) {
  const userId = req.headers['x-replit-user-id'];
  if (!userId) {
    return res.status(401).json({ error: 'Authentication required' });
  }
  next();
}

// Apply to all API routes
app.use('/api', requireAuth);

// Admin-only routes: check specific user IDs or roles
function requireAdmin(req: Request, res: Response, next: NextFunction) {
  const userId = req.headers['x-replit-user-id'] as string;
  const adminIds = (process.env.ADMIN_USER_IDS || '').split(',');

  if (!adminIds.includes(userId)) {
    return res.status(403).json({ error: 'Admin access required' });
  }
  next();
}

app.use('/admin', requireAuth, requireAdmin);
```

### Step 4: Deployment Visibility Controls
```typescript
// Validate deployment configuration at startup
function validateDeploymentSecurity() {
  const warnings: string[] = [];

  // Check if running as Deployment vs Repl
  if (!process.env.REPL_DEPLOYMENT && process.env.NODE_ENV === 'production') {
    warnings.push('WARNING: Production NODE_ENV but not a Deployment. Container may sleep.');
  }

  // Check debug mode
  if (process.env.DEBUG && process.env.NODE_ENV === 'production') {
    warnings.push('WARNING: DEBUG enabled in production');
  }

  // Check CORS
  if (process.env.CORS_ORIGIN === '*' && process.env.NODE_ENV === 'production') {
    warnings.push('WARNING: CORS allows all origins in production');
  }

  if (warnings.length) {
    warnings.forEach(w => console.warn(w));
  }

  return { secure: warnings.length === 0, warnings };
}

// Run at startup
const security = validateDeploymentSecurity();
if (!security.secure) {
  console.warn('Security warnings detected. Review before production deployment.');
}
```

### Step 5: Security Audit Checklist
```markdown
## Replit Security Audit

### Secrets (Critical)
- [ ] No API keys in source code
- [ ] All secrets in Replit Secrets tab
- [ ] Startup validates required secrets
- [ ] Secret Scanner warnings addressed

### Access Control
- [ ] All data endpoints require authentication
- [ ] Admin routes have role-based access
- [ ] Rate limiting on public endpoints
- [ ] CORS configured for specific origins

### Data Protection
- [ ] Parameterized SQL queries (no string concatenation)
- [ ] Input validation on all user data
- [ ] Error responses don't expose internals
- [ ] Logs don't contain PII or secrets

### Deployment
- [ ] Production uses Deployments (not Repl "Run")
- [ ] NODE_ENV set to "production"
- [ ] Health endpoint doesn't expose secrets
- [ ] Custom domain has SSL (auto-provisioned)

### Resources
- [ ] Memory limits appropriate for tier
- [ ] Request size limits configured
- [ ] Per-request timeout enforced
- [ ] Payload size validation
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret leaked in code | Not using Secrets tab | Rotate key, move to Secrets |
| OOM kill | No memory limits | Set resource limits, monitor usage |
| Unauthorized data access | Missing auth middleware | Add requireAuth to all /api routes |
| Debug info in production | Debug mode not disabled | Check NODE_ENV and DEBUG env vars |

## Resources
- [Replit Secrets](https://docs.replit.com/replit-workspace/workspace-features/secrets)
- [Replit Security](https://replit.com/products/security)
- [Secure Vibe Coding](https://blog.replit.com/16-ways-to-vibe-code-securely)
- [Secret Scanner](https://blog.replit.com/secret-scanner)

## Next Steps
For architecture patterns, see `replit-architecture-variants`.
