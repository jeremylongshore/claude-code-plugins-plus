---
name: vercel-policy-guardrails
description: |
  Implement lint rules, CI policy checks, and automated guardrails for Vercel projects.
  Use when setting up code quality rules, preventing secret exposure,
  or enforcing deployment policies for Vercel applications.
  Trigger with phrases like "vercel policy", "vercel lint",
  "vercel guardrails", "vercel best practices check", "vercel secret scan".
allowed-tools: Read, Write, Edit, Bash(npx:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vercel, policy, linting, security]

---
# Vercel Policy Guardrails

## Overview
Protect against common Vercel failure modes with automated guardrails: ESLint rules preventing secret exposure in client bundles, pre-commit hooks scanning for credentials, CI checks validating vercel.json and edge runtime compatibility, and runtime middleware enforcing auth on protected routes.

## Prerequisites
- ESLint configured in project
- Git hooks infrastructure (husky or lefthook)
- CI/CD pipeline (GitHub Actions or similar)
- TypeScript for type enforcement

## Instructions

### Step 1: ESLint Rules — Prevent Secret Exposure
```javascript
// .eslintrc.js — custom rules for Vercel projects
module.exports = {
  rules: {
    // Prevent using NEXT_PUBLIC_ prefix for sensitive variables
    'no-restricted-syntax': [
      'error',
      {
        selector: 'MemberExpression[object.property.name="env"][property.name=/^NEXT_PUBLIC_(SECRET|KEY|TOKEN|PASSWORD|PRIVATE)/]',
        message: 'Do not prefix secrets with NEXT_PUBLIC_ — they will be exposed in the client bundle',
      },
    ],
  },
  overrides: [
    {
      // Edge runtime files — prevent Node.js API usage
      files: ['**/edge-*.ts', '**/middleware.ts'],
      rules: {
        'no-restricted-imports': [
          'error',
          {
            paths: [
              { name: 'fs', message: 'fs is not available in Edge Runtime. Use fetch or Vercel Blob.' },
              { name: 'path', message: 'path is not available in Edge Runtime. Use URL API.' },
              { name: 'crypto', message: 'Use globalThis.crypto (Web Crypto API) in Edge Runtime.' },
              { name: 'child_process', message: 'child_process is not available in Edge Runtime.' },
              { name: 'net', message: 'net is not available in Edge Runtime.' },
            ],
          },
        ],
      },
    },
  ],
};
```

### Step 2: Pre-Commit Hook — Credential Scanning
```bash
# Install husky
npm install --save-dev husky
npx husky init
```

```bash
#!/usr/bin/env bash
# .husky/pre-commit
set -euo pipefail

# Scan staged files for credentials
PATTERNS=(
  'VERCEL_TOKEN\s*[:=]\s*\S+'
  'vercel_[a-zA-Z]*_token\s*[:=]\s*\S+'
  'sk_live_[a-zA-Z0-9]+'
  'NEXT_PUBLIC_.*SECRET'
  'api\.vercel\.com.*Bearer\s+[a-zA-Z0-9]+'
)

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
FOUND=0

for file in $STAGED_FILES; do
  for pattern in "${PATTERNS[@]}"; do
    if grep -qEi "$pattern" "$file" 2>/dev/null; then
      echo "ERROR: Potential credential found in $file"
      echo "  Pattern: $pattern"
      FOUND=1
    fi
  done
done

if [ $FOUND -ne 0 ]; then
  echo ""
  echo "Commit blocked: Remove credentials and use environment variables."
  echo "See: vercel env add <KEY> <environment>"
  exit 1
fi
```

### Step 3: CI Policy Check — vercel.json Validation
```yaml
# .github/workflows/vercel-policy.yml
name: Vercel Policy Checks
on: [pull_request]

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }

      - name: Validate vercel.json schema
        run: |
          if [ -f vercel.json ]; then
            node -e "
              const config = require('./vercel.json');
              const errors = [];

              // Check for deprecated builds property
              if (config.builds) {
                errors.push('vercel.json uses deprecated \"builds\" property — use \"functions\" instead');
              }

              // Check compressHTML (iOS Safari issue)
              if (config.compressHTML === true) {
                errors.push('compressHTML should be disabled — causes iOS Safari rendering issues');
              }

              // Check for hardcoded secrets in headers
              const headerStr = JSON.stringify(config.headers ?? []);
              if (/Bearer\s+[a-zA-Z0-9]{20,}/.test(headerStr)) {
                errors.push('Hardcoded token found in vercel.json headers');
              }

              if (errors.length > 0) {
                console.error('Policy violations:');
                errors.forEach(e => console.error('  - ' + e));
                process.exit(1);
              }
              console.log('vercel.json policy checks passed');
            "
          fi

      - name: Check edge runtime compatibility
        run: |
          # Find files with edge runtime declaration
          for file in $(grep -rl "runtime.*=.*'edge'" src/ api/ 2>/dev/null || true); do
            echo "Checking edge compatibility: $file"
            # Check for Node.js-only imports
            if grep -E "require\(['\"]fs['\"]|from ['\"]fs['\"]|from ['\"]path['\"]|from ['\"]crypto['\"]" "$file"; then
              echo "ERROR: $file uses Node.js APIs incompatible with Edge Runtime"
              exit 1
            fi
          done
          echo "Edge runtime compatibility checks passed"

      - name: Check bundle size budget
        run: |
          npm ci
          npm run build
          # Check output size
          TOTAL=$(du -sb .next/ 2>/dev/null | cut -f1 || echo 0)
          MAX=$((250 * 1024 * 1024))  # 250MB
          if [ "$TOTAL" -gt "$MAX" ]; then
            echo "ERROR: Build output ($TOTAL bytes) exceeds budget ($MAX bytes)"
            exit 1
          fi
          echo "Bundle size within budget: $TOTAL bytes"
```

### Step 4: Env Var Documentation Guard
```bash
#!/usr/bin/env bash
# scripts/check-env-docs.sh — ensure .env.example stays in sync
set -euo pipefail

# Extract env vars used in code
CODE_VARS=$(grep -roh 'process\.env\.\w\+' src/ api/ 2>/dev/null \
  | sed 's/process\.env\.//' \
  | sort -u)

# Extract vars documented in .env.example
if [ ! -f .env.example ]; then
  echo "ERROR: .env.example file missing"
  exit 1
fi

DOC_VARS=$(grep -oE '^\w+=' .env.example | sed 's/=//' | sort -u)

# Find undocumented vars
MISSING=$(comm -23 <(echo "$CODE_VARS") <(echo "$DOC_VARS"))
if [ -n "$MISSING" ]; then
  echo "ERROR: Undocumented environment variables:"
  echo "$MISSING" | sed 's/^/  /'
  echo "Add these to .env.example"
  exit 1
fi

echo "All environment variables documented"
```

### Step 5: Runtime Auth Middleware Guard
```typescript
// middleware.ts — enforce that protected routes always require auth
import { NextRequest, NextResponse } from 'next/server';

// Routes that MUST require authentication
const PROTECTED_PATTERNS = [
  /^\/api\/admin/,
  /^\/api\/users/,
  /^\/dashboard/,
  /^\/settings/,
];

// Routes explicitly allowed without auth
const PUBLIC_PATTERNS = [
  /^\/api\/health/,
  /^\/api\/webhooks/,
  /^\/$/, // homepage
  /^\/login/,
  /^\/signup/,
];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED_PATTERNS.some(p => p.test(pathname));
  const isPublic = PUBLIC_PATTERNS.some(p => p.test(pathname));

  if (isProtected && !isPublic) {
    const token = request.cookies.get('session')?.value;
    if (!token) {
      if (pathname.startsWith('/api/')) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
      }
      return NextResponse.redirect(new URL('/login', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};
```

### Step 6: Deployment Freeze Guard
```bash
#!/usr/bin/env bash
# scripts/check-deploy-freeze.sh — prevent production deploys during freeze windows
set -euo pipefail

# Check if we're in a deployment freeze window
HOUR=$(date -u +%H)
DAY=$(date -u +%u)  # 1=Monday, 7=Sunday

# No deploys on weekends
if [ "$DAY" -gt 5 ]; then
  echo "BLOCKED: No production deploys on weekends"
  exit 1
fi

# No deploys after 4pm UTC (Friday especially)
if [ "$DAY" -eq 5 ] && [ "$HOUR" -ge 16 ]; then
  echo "BLOCKED: No production deploys after 4pm UTC on Fridays"
  exit 1
fi

echo "Deploy allowed"
```

## Guardrails Summary

| Guardrail | Enforcement Point | Prevents |
|-----------|-------------------|----------|
| Secret prefix lint | ESLint (editor + CI) | Client bundle secret exposure |
| Edge runtime lint | ESLint (editor + CI) | Node.js APIs in edge functions |
| Credential scan | Pre-commit hook | Secrets in version control |
| vercel.json validation | CI | Deprecated config, hardcoded tokens |
| Env var documentation | CI | Missing .env.example entries |
| Auth middleware | Runtime | Unprotected routes |
| Deploy freeze | CI | Weekend/late deploys |

## Output
- ESLint rules preventing secret exposure and edge runtime violations
- Pre-commit hooks blocking credentials from entering git
- CI policy checks validating configuration and compatibility
- Runtime middleware enforcing authentication on protected routes
- Deployment freeze windows preventing risky deploys

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| ESLint rule false positive | Variable name matches pattern | Add `// eslint-disable-next-line` with justification |
| Pre-commit hook blocks valid commit | Pattern too broad | Narrow the regex or add allowlist |
| CI edge check false positive | Dead import | Remove unused import |
| Deploy freeze too restrictive | Urgent hotfix needed | Use `--force` flag with team approval |

## Resources
- [ESLint Custom Rules](https://eslint.org/docs/latest/extend/plugins)
- [Husky Documentation](https://typicode.github.io/husky/)
- [Vercel Project Configuration](https://vercel.com/docs/project-configuration)
- [Edge Runtime API](https://vercel.com/docs/functions/runtimes/edge)

## Next Steps
For architecture variants, see `vercel-architecture-variants`.
