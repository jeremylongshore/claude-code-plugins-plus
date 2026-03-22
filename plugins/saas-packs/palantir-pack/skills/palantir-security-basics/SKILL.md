---
name: palantir-security-basics
description: |
  Apply Palantir Foundry security best practices for credentials, scopes, and access control.
  Use when securing API tokens, implementing least privilege access,
  or auditing Foundry security configuration.
  Trigger with phrases like "palantir security", "foundry secrets",
  "secure palantir", "palantir API key security", "foundry scopes".
allowed-tools: Read, Write, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, security, oauth]
compatible-with: claude-code, codex, openclaw
---

# Palantir Security Basics

## Overview
Security best practices for Foundry API tokens, OAuth2 credentials, scope management, and secret rotation. Covers both personal access tokens (dev) and service user credentials (production).

## Prerequisites
- Foundry Developer Console access
- Understanding of OAuth2 scopes

## Instructions

### Step 1: Secure Credential Storage
```bash
# .env — NEVER commit to git
FOUNDRY_HOSTNAME=mycompany.palantirfoundry.com
FOUNDRY_CLIENT_ID=your-client-id
FOUNDRY_CLIENT_SECRET=your-client-secret

# .gitignore — ensure .env files are excluded
echo '.env' >> .gitignore
echo '.env.local' >> .gitignore
echo '.env.*.local' >> .gitignore
```

For production, use a secrets manager:
```bash
# AWS Secrets Manager
aws secretsmanager create-secret --name foundry/prod \
  --secret-string '{"client_id":"xxx","client_secret":"yyy","hostname":"zzz"}'

# Google Cloud Secret Manager
echo -n "your-client-secret" | gcloud secrets create foundry-client-secret --data-file=-

# HashiCorp Vault
vault kv put secret/foundry client_id=xxx client_secret=yyy
```

### Step 2: Apply Least Privilege Scopes
| Environment | Recommended Scopes | Rationale |
|-------------|-------------------|-----------|
| Development | `api:read-data` | Read-only prevents accidental mutations |
| Staging | `api:read-data`, `api:write-data` | Test writes in safe environment |
| Production | Only scopes your app actually needs | Minimize blast radius |

```python
# Production app that only reads Ontology objects:
auth = foundry.ConfidentialClientAuth(
    client_id=os.environ["FOUNDRY_CLIENT_ID"],
    client_secret=os.environ["FOUNDRY_CLIENT_SECRET"],
    hostname=os.environ["FOUNDRY_HOSTNAME"],
    scopes=["api:ontology-read"],  # Minimum viable scope
)
```

### Step 3: Rotate Credentials
```bash
# 1. Generate new credentials in Developer Console
# 2. Deploy new credentials alongside old ones
# 3. Verify new credentials work
python -c "
import os, foundry
auth = foundry.ConfidentialClientAuth(
    client_id=os.environ['NEW_CLIENT_ID'],
    client_secret=os.environ['NEW_CLIENT_SECRET'],
    hostname=os.environ['FOUNDRY_HOSTNAME'],
    scopes=['api:read-data'],
)
auth.sign_in_as_service_user()
print('New credentials verified')
"
# 4. Remove old credentials from Developer Console
# 5. Update environment variables to use new credentials only
```

### Step 4: Validate Tokens Are Not Exposed
```bash
# Scan for leaked credentials in git history
git log --all -p | grep -i "foundry_token\|foundry_client_secret" | head -5
# If found: rotate immediately, then use git-filter-repo to remove

# Pre-commit hook to prevent committing secrets
# .pre-commit-config.yaml
# - repo: https://github.com/Yelp/detect-secrets
#   hooks:
#   - id: detect-secrets
```

### Step 5: Security Checklist
- [ ] Credentials in environment variables or secrets manager (never in code)
- [ ] `.env` files listed in `.gitignore`
- [ ] Separate credentials per environment (dev/staging/prod)
- [ ] Minimum scopes per application
- [ ] Personal access tokens used only for development
- [ ] OAuth2 client credentials for all production workloads
- [ ] Credential rotation schedule (every 90 days)
- [ ] Pre-commit hooks to detect leaked secrets

## Output
- Securely stored credentials using secrets manager
- Least-privilege scopes per environment
- Rotation procedure documented and tested
- Pre-commit hooks preventing secret commits

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Exposed token in git | `detect-secrets` scan | Rotate immediately, scrub history |
| Overly broad scopes | Audit app permissions | Reduce to minimum needed |
| Stale credentials | Age > 90 days | Rotate on schedule |
| Shared credentials | Multiple users same token | Create per-user service users |

## Resources
- [Foundry Authentication](https://www.palantir.com/docs/foundry/api/general/overview/authentication)
- [Developer Console](https://www.palantir.com/docs/foundry/ontology-sdk/create-a-new-osdk)
- [detect-secrets](https://github.com/Yelp/detect-secrets)

## Next Steps
For production deployment, see `palantir-prod-checklist`.
