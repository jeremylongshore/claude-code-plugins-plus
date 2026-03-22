---
name: windsurf-security-basics
description: |
  Apply Windsurf security best practices for workspace isolation, data privacy, and secret protection.
  Use when securing sensitive code from AI indexing, configuring telemetry,
  or auditing Windsurf security posture.
  Trigger with phrases like "windsurf security", "windsurf secrets",
  "windsurf privacy", "windsurf data protection", "codeiumignore".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, security, privacy, compliance]

---
# Windsurf Security Basics

## Overview
Security best practices for Windsurf AI IDE: controlling what code Cascade can see, preventing secrets from leaking into AI context, managing telemetry, and configuring workspace isolation for regulated environments.

## Prerequisites
- Windsurf installed
- Understanding of Codeium's data processing model
- Repository with identified sensitive files

## Instructions

### Step 1: Exclude Secrets from AI Indexing

Create `.codeiumignore` at project root (gitignore syntax):

```gitignore
# .codeiumignore — files Codeium/Windsurf will NEVER index or read

# Secrets and credentials
.env
.env.*
.env.local
credentials.json
serviceAccountKey.json
*.pem
*.key
*.p12
*.pfx

# Cloud provider configs
.aws/
.gcloud/
.azure/

# Infrastructure secrets
terraform.tfstate
terraform.tfstate.backup
*.tfvars
vault-config.*

# Customer data
data/customers/
exports/
backups/
*.sql.gz
```

**Default exclusions (automatic):** Files in `.gitignore`, `node_modules/`, hidden directories (`.` prefix).

**Enterprise:** Place a global `.codeiumignore` at `~/.codeium/` for org-wide exclusions.

### Step 2: Disable Telemetry (If Required)

```json
// Windsurf Settings (settings.json)
{
  "codeium.enableTelemetry": false,
  "codeium.enableSnippetTelemetry": false,
  "telemetry.telemetryLevel": "off"
}
```

### Step 3: Configure AI Autocomplete Exclusions

Disable Supercomplete for file types that commonly contain secrets:

```json
{
  "codeium.autocomplete.languages": {
    "plaintext": false,
    "env": false,
    "dotenv": false,
    "properties": false,
    "ini": false
  }
}
```

### Step 4: Create Security-Focused .windsurfrules

```markdown
<!-- .windsurfrules - security section -->

## Security Requirements
- Never suggest hardcoded secrets, API keys, or passwords in code
- Always use environment variables via process.env for secrets
- Never log PII (email, phone, SSN, credit card numbers)
- Use parameterized queries for all database operations
- Never suggest wildcard CORS origins in production code
- All user input must be validated before processing
- Use constant-time comparison for secret/token validation
```

### Step 5: Audit AI Workspace Access

```bash
#!/bin/bash
set -euo pipefail
echo "=== Windsurf Security Audit ==="

# Check if .codeiumignore exists
if [ ! -f .codeiumignore ]; then
  echo "WARNING: No .codeiumignore — AI can index all non-gitignored files"
fi

# Check for secrets that AI could index
echo "--- Potentially exposed secret files ---"
find . -type f \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  \( -name '*.env*' -o -name '*.key' -o -name '*.pem' \
  -o -name 'credentials*' -o -name '*secret*' \
  -o -name '*.tfvars' -o -name 'serviceAccount*' \) \
  2>/dev/null | head -20

# Check if found files are in .codeiumignore
echo "--- Verify all above files are excluded ---"
```

### Step 6: Windsurf Data Processing Model

```yaml
# What Windsurf/Codeium processes:
data_processing:
  indexed_locally:
    - File contents for Supercomplete context
    - Codebase structure for Cascade awareness
    stored: "Local machine only (not sent to cloud for indexing)"

  sent_to_cloud:
    - Cascade prompts (for AI model inference)
    - Code snippets around cursor (for Supercomplete)
    stored: "Zero-data retention for paid plans"

  never_processed:
    - Files in .codeiumignore
    - Files in .gitignore (by default)
    - Files in node_modules/

  compliance:
    - SOC 2 Type II certified
    - FedRAMP High accredited
    - HIPAA BAA available (Enterprise)
    - Zero-data retention on paid plans
```

## Security Checklist

- [ ] `.codeiumignore` exists with secret file patterns
- [ ] `.env` files excluded from AI indexing
- [ ] `.windsurfrules` includes security coding standards
- [ ] Telemetry disabled (if required by policy)
- [ ] Autocomplete disabled for secret-containing file types
- [ ] No competing AI extensions installed (data exposure risk)
- [ ] Team members trained on "never paste secrets into Cascade chat"
- [ ] Enterprise: SSO configured, personal accounts blocked

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Secret in Cascade suggestion | Appears in AI output | Add source file to `.codeiumignore`, rotate secret |
| AI indexing .env files | Check `.codeiumignore` | Add `.env*` pattern |
| Telemetry sending code | Policy audit | Disable all telemetry settings |
| Dev pastes secret in chat | Cannot detect after the fact | Training + enterprise data retention = 0 |

## Examples

### Enterprise .codeiumignore
```gitignore
# ~/.codeium/.codeiumignore (global, all workspaces)
*.pem
*.key
*.p12
*.env*
**/secrets/**
**/credentials/**
terraform.tfstate*
*.tfvars
```

### Quick Privacy Check
```bash
# Verify critical files are excluded
echo ".env" | while read f; do
  [ -f "$f" ] && grep -q "\.env" .codeiumignore 2>/dev/null && echo "$f: PROTECTED" || echo "$f: EXPOSED"
done
```

## Resources
- [Windsurf Security](https://windsurf.com/security)
- [Codeium Privacy Policy](https://codeium.com/privacy-policy)
- [Windsurf Ignore Docs](https://docs.windsurf.com/context-awareness/windsurf-ignore)

## Next Steps
For production deployment, see `windsurf-prod-checklist`.
