---
name: coderabbit-data-handling
description: |
  Implement CodeRabbit PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for CodeRabbit integrations.
  Trigger with phrases like "coderabbit data", "coderabbit PII",
  "coderabbit GDPR", "coderabbit data retention", "coderabbit privacy", "coderabbit CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# CodeRabbit Data Handling

## Overview
Manage code review data and sensitive patterns with CodeRabbit. Covers secret detection in PRs, sensitive file exclusion from AI review, review comment data retention, and configuring what code context gets sent to the AI engine.

## Prerequisites
- CodeRabbit installed on repository
- Understanding of sensitive file patterns
- Repository admin access for configuration
- Secret scanning tools awareness

## Instructions

### Step 1: Exclude Sensitive Files from Review
```yaml
# .coderabbit.yaml - Data handling configuration
reviews:
  path_filters:
    # Never send these to AI review
    - "!**/.env*"
    - "!**/credentials*"
    - "!**/secrets*"
    - "!**/*.pem"
    - "!**/*.key"
    - "!**/*.p12"
    - "!**/serviceAccountKey*"
    - "!**/terraform.tfstate*"
    - "!**/*.tfvars"

    # Exclude large generated files
    - "!**/package-lock.json"
    - "!**/pnpm-lock.yaml"
    - "!**/yarn.lock"
    - "!**/*.generated.*"
    - "!**/dist/**"
    - "!**/coverage/**"
```

### Step 2: Secret Detection Instructions
```yaml
# .coderabbit.yaml - Instruct AI to flag secrets
reviews:
  path_instructions:
    - path: "**"
      instructions: |
        CRITICAL: Flag any of these patterns as HIGH SEVERITY:
        - Hardcoded API keys, tokens, or passwords
        - AWS access keys (AKIA...)
        - Private keys or certificates
        - Database connection strings with credentials
        - JWT secrets or signing keys
        - Webhook URLs with tokens in query params

        If you find any secrets, add a comment:
        "SECURITY: Hardcoded secret detected. Move to environment variable."

    - path: "**/*.{yml,yaml}"
      instructions: |
        Check CI/CD files for:
        - Secrets logged in step names or echo statements
        - Unpinned GitHub Actions (use SHA, not tags)
        - Missing secret masking in outputs
```

### Step 3: Review Data Scope Management
```yaml
# Control what context CodeRabbit accesses
reviews:
  auto_review:
    enabled: true
    drafts: false   # Don't review draft PRs (may contain WIP secrets)
    base_branches:
      - "main"
      - "develop"
    ignore_title_keywords:
      - "WIP"
      - "DO NOT REVIEW"
      - "DRAFT"

  # Limit file types reviewed
  path_filters:
    # Only review source code, not data
    - "+src/**"
    - "+lib/**"
    - "+app/**"
    - "+tests/**"
    - "+.github/**"
    - "!**/*.csv"
    - "!**/*.json"      # Exclude data files
    - "!**/fixtures/**"  # Exclude test fixtures with sample data
    - "!**/seeds/**"     # Exclude database seeds
```

### Step 4: Sensitive Code Pattern Detection
```yaml
# .coderabbit.yaml - Custom pattern detection
reviews:
  path_instructions:
    - path: "src/db/**"
      instructions: |
        Review database code for:
        - SQL injection vulnerabilities (string concatenation in queries)
        - Unparameterized queries
        - PII logged in error messages
        - Missing data sanitization on inputs

    - path: "src/api/**"
      instructions: |
        Review API endpoints for:
        - User input not validated before processing
        - Sensitive data in response bodies (passwords, tokens)
        - Missing authentication checks
        - Overly permissive CORS configuration
        - PII in URL parameters (should be POST body instead)

    - path: "src/auth/**"
      instructions: |
        SECURITY-CRITICAL PATH. Review for:
        - Token expiry configuration
        - Password hashing (must use bcrypt/argon2, never MD5/SHA)
        - Session fixation vulnerabilities
        - CSRF protection
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret in reviewed PR | Not in exclusion list | Add pattern to path_filters |
| Large diff reviewed | Generated code included | Exclude generated file paths |
| Sensitive fixture data | Test data has real PII | Exclude fixtures directory |
| Review on draft PR | drafts setting enabled | Set `drafts: false` |

## Examples

### Minimal Secure Configuration
```yaml
# .coderabbit.yaml - Security-focused setup
reviews:
  auto_review:
    enabled: true
    drafts: false
  path_filters:
    - "!**/.env*"
    - "!**/*.key"
    - "!**/*.pem"
    - "!**/secrets/**"
  path_instructions:
    - path: "**"
      instructions: "Flag any hardcoded secrets, API keys, or credentials."
```

## Resources
- [CodeRabbit Configuration](https://docs.coderabbit.ai/configuration)
- [CodeRabbit Path Filters](https://docs.coderabbit.ai/guides/review-instructions)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale