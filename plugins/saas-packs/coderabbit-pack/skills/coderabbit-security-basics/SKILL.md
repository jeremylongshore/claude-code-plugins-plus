---
name: coderabbit-security-basics
description: |
  Configure CodeRabbit for security-focused code review with secret detection and vulnerability scanning.
  Use when setting up security review rules, configuring secret detection in PRs,
  or hardening CodeRabbit configuration for compliance requirements.
  Trigger with phrases like "coderabbit security", "coderabbit secrets",
  "secure coderabbit", "coderabbit vulnerability detection", "coderabbit security review".
allowed-tools: Read, Write, Edit, Bash(gh:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, coderabbit, security, secrets, compliance]

---
# CodeRabbit Security Basics

## Overview
Configure CodeRabbit to catch security vulnerabilities, hardcoded secrets, and insecure patterns in pull requests. CodeRabbit's AI review can detect security issues that static analysis tools miss because it understands code context and intent. This skill covers security-focused configuration, secret detection instructions, and compliance-oriented review policies.

## Prerequisites
- CodeRabbit installed on repository
- `.coderabbit.yaml` in repository root
- Understanding of security requirements for your codebase

## Security Coverage
| Category | CodeRabbit Detection | Complementary Tool |
|----------|--------------------|--------------------|
| Hardcoded secrets | Path instructions + AI detection | GitHub Secret Scanning, GitLeaks |
| SQL injection | Path instructions for DB code | SonarCloud, Semgrep |
| XSS vulnerabilities | Path instructions for frontend | ESLint security plugins |
| Auth bypass | Path instructions for auth code | Manual review |
| Insecure dependencies | Limited (reviews import patterns) | Dependabot, Renovate |
| OWASP Top 10 | Path instructions covering each risk | Dedicated SAST tools |

## Instructions

### Step 1: Configure Security-Focused Review
```yaml
# .coderabbit.yaml - Security-hardened configuration
language: "en-US"

reviews:
  profile: "assertive"
  request_changes_workflow: true    # Block merge on security findings

  auto_review:
    enabled: true
    drafts: false
    base_branches: [main, develop]

  # Exclude secrets files from AI processing
  path_filters:
    - "!**/.env*"
    - "!**/credentials*"
    - "!**/secrets*"
    - "!**/*.pem"
    - "!**/*.key"
    - "!**/*.p12"
    - "!**/*.pfx"
    - "!**/serviceAccountKey*"
    - "!**/terraform.tfstate*"
    - "!**/*.tfvars"
    - "!**/*.lock"
    - "!dist/**"
    - "!vendor/**"

  path_instructions:
    # Global security rules
    - path: "**"
      instructions: |
        SECURITY REVIEW: Flag any of these as HIGH severity:
        - Hardcoded API keys, tokens, passwords, or connection strings
        - AWS access keys (AKIA...), GCP service account keys
        - Private keys or certificates in source code
        - JWT secrets or signing keys
        - Database credentials in code (not env vars)
        - Webhook URLs with tokens in query parameters
        - Disabled SSL/TLS verification
        - eval() or equivalent dynamic code execution

    # API security
    - path: "src/api/**"
      instructions: |
        API security checks:
        - Input validation: all request parameters validated before use
        - Authentication: auth middleware on all non-public endpoints
        - Authorization: proper role/permission checks
        - Rate limiting: endpoints have rate limits configured
        - Error responses: no stack traces or internal details exposed
        - CORS: properly configured, not wildcard (*)
        - SQL injection: parameterized queries only, no string concat

    # Authentication code
    - path: "src/auth/**"
      instructions: |
        CRITICAL SECURITY PATH. Review for:
        - Password hashing: bcrypt or argon2 ONLY (flag MD5, SHA-1, SHA-256)
        - Token expiry: access tokens < 1 hour, refresh tokens < 30 days
        - Session fixation: new session ID after authentication
        - CSRF protection: anti-CSRF tokens on state-changing operations
        - Brute force protection: account lockout or rate limiting on login
        - No timing attacks in comparison (use constant-time comparison)

    # Database code
    - path: "src/db/**"
      instructions: |
        Database security checks:
        - Parameterized queries ONLY (flag any string concatenation in SQL)
        - No sensitive data in error messages (e.g., full query text)
        - Connection strings from env vars (not hardcoded)
        - Principle of least privilege for DB user accounts
        - Transactions for multi-step operations

    # CI/CD pipelines
    - path: ".github/workflows/**"
      instructions: |
        CI/CD security checks:
        - Pin ALL action versions to SHA commit hash (not tags)
        - No secrets in step names, echo statements, or log output
        - Include timeout-minutes on all jobs
        - Use OIDC for cloud provider auth (not long-lived keys)
        - No curl | sh patterns (supply chain risk)
        - Restrict workflow permissions to minimum required

    # Infrastructure as code
    - path: "**/*.tf"
      instructions: |
        Terraform security:
        - No hardcoded credentials or access keys
        - S3 buckets: encryption enabled, public access blocked
        - Security groups: no 0.0.0.0/0 ingress except port 443
        - RDS/databases: encryption at rest enabled, no public access
        - IAM roles: least privilege, no wildcard (*) actions

    # Docker
    - path: "**/Dockerfile"
      instructions: |
        Container security:
        - No secrets in ENV or ARG instructions
        - Use specific image tags (not :latest)
        - Run as non-root user (USER instruction)
        - Multi-stage builds to reduce attack surface
        - No sensitive files copied into image

chat:
  auto_reply: true
```

### Step 2: Secret Detection with GitHub Integration
```yaml
# .github/workflows/security-review.yml
name: Security Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Scan for secrets in PR diff
        run: |
          # Check PR diff for common secret patterns
          DIFF=$(git diff origin/${{ github.base_ref }}...HEAD)
          PATTERNS=(
            "AKIA[0-9A-Z]{16}"           # AWS access key
            "(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"][^'\"]{16,}"   # API keys
            "(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}"   # Passwords
            "ghp_[a-zA-Z0-9]{36}"         # GitHub PAT
            "sk-[a-zA-Z0-9]{48}"          # OpenAI key
            "-----BEGIN.*PRIVATE KEY"     # Private keys
          )

          FOUND=0
          for PATTERN in "${PATTERNS[@]}"; do
            if echo "$DIFF" | grep -qP "$PATTERN"; then
              echo "::error::Potential secret found matching pattern: $PATTERN"
              FOUND=1
            fi
          done

          if [ "$FOUND" -eq 1 ]; then
            echo "::error::Secret-like patterns detected in PR. Review before merging."
            exit 1
          fi
```

### Step 3: Security Review Learnings
```markdown
# Train CodeRabbit to catch your team's specific security patterns:

# In a PR comment, reply to a CodeRabbit review:
"Good catch! We always want to flag missing CSRF tokens in POST handlers."

"We use Helmet.js for security headers. If you see an Express route
without `app.use(helmet())`, flag it as a security issue."

"In this project, all database queries must go through the QueryBuilder class.
Direct SQL strings are a security violation."

# These learnings persist across PRs and repos in the organization.
```

### Step 4: Security Audit Script
```bash
set -euo pipefail
echo "=== CodeRabbit Security Configuration Audit ==="

# Check .coderabbit.yaml for security settings
if [ -f .coderabbit.yaml ]; then
  python3 -c "
import yaml

config = yaml.safe_load(open('.coderabbit.yaml'))
reviews = config.get('reviews', {})
path_filters = reviews.get('path_filters', [])
path_instructions = reviews.get('path_instructions', [])

# Check if sensitive files are excluded
sensitive_patterns = ['.env', '.pem', '.key', 'credentials', 'secrets', 'tfstate', 'tfvars']
excluded = [p for p in path_filters if any(s in p for s in sensitive_patterns)]
print(f'Sensitive file exclusions: {len(excluded)}/{len(sensitive_patterns)} patterns')

# Check if security instructions exist
security_keywords = ['security', 'injection', 'credential', 'secret', 'auth', 'password']
has_security = any(
    any(kw in str(pi.get('instructions', '')).lower() for kw in security_keywords)
    for pi in path_instructions
)
print(f'Security path_instructions: {\"YES\" if has_security else \"MISSING\"} ')

# Check if request_changes_workflow blocks on issues
blocks = reviews.get('request_changes_workflow', False)
print(f'Blocks merge on issues: {\"YES\" if blocks else \"NO (consider enabling)\"}')

# Check auto_review settings
auto = reviews.get('auto_review', {})
print(f'Drafts reviewed: {\"YES (risky)\" if auto.get(\"drafts\", True) else \"NO (good)\"}')
" 2>&1
else
  echo "WARNING: .coderabbit.yaml not found"
fi
```

## Output
- Security-focused `.coderabbit.yaml` with path instructions for critical code areas
- Secret detection patterns in CI pipeline
- CodeRabbit learnings trained for team-specific security rules
- Security configuration audit script
- Merge blocking enabled for security findings

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secrets not flagged | No security path_instructions | Add global `**` instruction for secret patterns |
| False positive on test data | Test fixtures contain mock secrets | Add `!**/fixtures/**` to path_filters |
| Security finding ignored | `request_changes_workflow: false` | Set to `true` to block merge |
| Too many security comments | Overly broad instructions | Focus instructions on specific paths |
| Secret in reviewed diff | File not in exclusion list | Add pattern to path_filters |

## Resources
- [CodeRabbit Configuration](https://docs.coderabbit.ai/reference/configuration)
- [CodeRabbit Path Instructions](https://docs.coderabbit.ai/guides/review-instructions)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)

## Next Steps
For production deployment, see `coderabbit-prod-checklist`.
