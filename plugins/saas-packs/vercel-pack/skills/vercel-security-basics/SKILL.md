---
name: vercel-security-basics
description: |
  Apply Vercel security best practices for secrets, headers, and access control.
  Use when securing API keys, configuring security headers,
  or auditing Vercel security configuration.
  Trigger with phrases like "vercel security", "vercel secrets",
  "secure vercel", "vercel headers", "vercel CSP".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, security, headers, secrets]

---
# Vercel Security Basics

## Overview
Secure Vercel deployments with proper secret management, security headers, deployment protection, and access token hygiene. Covers environment variable scoping, Content Security Policy, and preventing common secret exposure patterns.

## Prerequisites
- Vercel CLI installed and authenticated
- Access to Vercel dashboard
- Understanding of HTTP security headers

## Instructions

### Step 1: Secret Management with Environment Variables
```bash
# Add secrets scoped to specific environments
vercel env add DATABASE_URL production
vercel env add DATABASE_URL preview
vercel env add DATABASE_URL development

# Use 'sensitive' type — values hidden in dashboard and logs
vercel env add API_SECRET production --sensitive

# Via REST API
curl -X POST "https://api.vercel.com/v9/projects/my-app/env" \
  -H "Authorization: Bearer $VERCEL_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "API_SECRET",
    "value": "sk-secret-value",
    "type": "sensitive",
    "target": ["production"]
  }'
```

**Critical rule:** Never prefix secrets with `NEXT_PUBLIC_`. Variables starting with `NEXT_PUBLIC_` are inlined into the client JavaScript bundle and visible to anyone.

### Step 2: Security Headers via vercel.json
```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
        { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=()" },
        {
          "key": "Strict-Transport-Security",
          "value": "max-age=63072000; includeSubDomains; preload"
        },
        {
          "key": "Content-Security-Policy",
          "value": "default-src 'self'; script-src 'self' 'unsafe-inline' https://vercel.live; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com; connect-src 'self' https://api.vercel.com"
        }
      ]
    }
  ]
}
```

### Step 3: Security Headers via Edge Middleware
```typescript
// middleware.ts
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const response = NextResponse.next();

  // Security headers
  response.headers.set('X-Content-Type-Options', 'nosniff');
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  response.headers.set(
    'Strict-Transport-Security',
    'max-age=63072000; includeSubDomains; preload'
  );

  // Remove server version headers
  response.headers.delete('X-Powered-By');

  return response;
}
```

### Step 4: Deployment Protection
```json
// vercel.json
{
  "deploymentProtection": {
    "preview": "vercel-authentication",
    "optedOutFrom": []
  }
}
```

Protection options:
- **`vercel-authentication`** — requires Vercel team login to view preview deploys
- **`standard-protection`** — uses bypass header for automation
- **Deployment Protection Bypass** — for CI/CD and health checks:

```bash
# Generate a bypass secret in Vercel dashboard > Settings > Deployment Protection
# Use in CI with:
curl -H "x-vercel-protection-bypass: your-bypass-secret" \
  https://my-app-preview.vercel.app/api/health
```

### Step 5: Access Token Best Practices
```bash
# Create scoped tokens — restrict to one team and project
# Settings > Tokens > Create Token:
# - Scope: Team → your-team
# - Expiration: 90 days (for CI)
# - Permissions: Deployment-only (no team admin)

# Rotate tokens on a schedule
# In CI (GitHub Actions):
# Store as GitHub Secret: VERCEL_TOKEN
# Set expiry alerts in your calendar
```

Token security rules:
1. Never commit tokens to git — use `.env.local` or CI secrets
2. Scope tokens to the minimum required permissions
3. Set expiration dates (90 days for CI, 30 days for dev)
4. Rotate immediately if exposed
5. Use separate tokens per environment/pipeline

### Step 6: API Route Authentication
```typescript
// api/protected.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  // Verify API key from header
  const apiKey = req.headers['x-api-key'];
  if (!apiKey || apiKey !== process.env.INTERNAL_API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  // Verify origin for CORS
  const origin = req.headers.origin;
  const allowedOrigins = (process.env.ALLOWED_ORIGINS ?? '').split(',');
  if (origin && !allowedOrigins.includes(origin)) {
    return res.status(403).json({ error: 'Forbidden origin' });
  }

  res.json({ data: 'protected content' });
}
```

## Security Checklist

| Check | Status |
|-------|--------|
| No secrets in `NEXT_PUBLIC_*` variables | Required |
| Sensitive env vars use `type: sensitive` | Required |
| Security headers configured | Required |
| HSTS enabled with preload | Recommended |
| Preview deployments protected | Recommended |
| Access tokens scoped and rotated | Required |
| CSP configured for your domains | Recommended |
| `.env.local` in `.gitignore` | Required |

## Output
- Environment variables properly scoped and typed as sensitive
- Security headers applied to all responses
- Deployment protection enabled for preview URLs
- Access tokens scoped with expiration dates

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Secret visible in client bundle | Prefixed with `NEXT_PUBLIC_` | Remove prefix, redeploy, rotate the secret |
| CSP blocking resources | Policy too restrictive | Add the blocked domain to the relevant directive |
| Preview accessible without auth | Deployment protection disabled | Enable in vercel.json or dashboard |
| Token expired | Past expiration date | Generate new token, update CI secrets |

## Resources
- [Vercel Security](https://vercel.com/docs/security)
- [Deployment Protection](https://vercel.com/docs/security/deployment-protection)
- [Environment Variables](https://vercel.com/docs/environment-variables)
- [Security Headers](https://vercel.com/docs/headers)
- [Access Tokens](https://vercel.com/docs/rest-api#creating-an-access-token)

## Next Steps
For production deployment checklist, see `vercel-prod-checklist`.
