---
name: windsurf-data-handling
description: |
  Control what code and data Windsurf AI can access and process in your workspace.
  Use when handling sensitive data, implementing data exclusion patterns,
  or ensuring compliance with privacy regulations in Windsurf environments.
  Trigger with phrases like "windsurf data privacy", "windsurf PII",
  "windsurf GDPR", "windsurf compliance", "codeium data", "windsurf telemetry".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, windsurf, privacy, compliance, data-handling]

---
# Windsurf Data Handling

## Overview
Control what code and data Windsurf's AI (Cascade, Supercomplete) can access. Covers file exclusion patterns, telemetry controls, Codeium's data processing model, and compliance configuration for regulated environments.

## Prerequisites
- Windsurf IDE installed
- Understanding of Codeium's data processing model
- Identified sensitive files and directories in workspace

## Instructions

### Step 1: Understand Codeium's Data Model

```yaml
# What happens with your code in Windsurf
data_flow:
  indexed_locally:
    what: "File contents, structure, dependencies"
    where: "Local machine only"
    purpose: "Supercomplete context, Cascade awareness"
    retention: "Persists until re-indexed"

  sent_to_cloud:
    what: "Cascade prompts, code snippets around cursor"
    where: "Codeium cloud (or self-hosted for Enterprise)"
    purpose: "AI model inference"
    retention: "Zero-data retention for ALL paid plans"

  never_processed:
    what: "Files in .codeiumignore, .gitignore, node_modules"
    where: "N/A"
    purpose: "N/A"

  compliance:
    certifications: ["SOC 2 Type II", "FedRAMP High"]
    hipaa: "BAA available for Enterprise customers"
    data_retention: "Zero for paid plans, configurable for Enterprise"
    deployment: "Cloud, Hybrid, or Self-Hosted options"
```

### Step 2: Configure .codeiumignore for Data Protection

```gitignore
# .codeiumignore — files Windsurf AI will NEVER see or index
# Uses gitignore syntax. Default: .gitignore and node_modules excluded.

# ===== SECRETS =====
.env
.env.*
.env.local
credentials.json
serviceAccountKey.json
*.pem
*.key
*.p12
*.pfx
.aws/
.gcloud/
.azure/
vault-config.*

# ===== CUSTOMER DATA =====
data/customers/
data/exports/
data/backups/
*.sql
*.sql.gz
*.dump
fixtures/production-*

# ===== INFRASTRUCTURE SECRETS =====
terraform.tfstate
terraform.tfstate.backup
*.tfvars
*.auto.tfvars
ansible/vault*

# ===== COMPLIANCE BOUNDARIES =====
# PCI zone — credit card processing code
src/pci/

# HIPAA zone — health data processing
src/hipaa/

# Financial data
reports/financial/
```

### Step 3: Disable Telemetry (Regulated Environments)

```json
// settings.json — maximum privacy configuration
{
  "codeium.enableTelemetry": false,
  "codeium.enableSnippetTelemetry": false,
  "telemetry.telemetryLevel": "off",
  "update.showReleaseNotes": false
}
```

### Step 4: Configure Autocomplete Data Boundaries

```json
// Disable Supercomplete for sensitive file types
{
  "codeium.autocomplete.languages": {
    "plaintext": false,
    "env": false,
    "dotenv": false,
    "properties": false,
    "ini": false,
    "yaml": false,
    "json": false
  }
}
```

**Rationale:** YAML and JSON files often contain configuration with secrets. Disabling Supercomplete for these types prevents the AI from seeing or suggesting content based on config files.

### Step 5: Safe Cascade Usage with Sensitive Code

```markdown
## Rules for using Cascade in regulated codebases

1. NEVER paste secrets into Cascade chat
   - BAD: "My API key is sk-abc123, why isn't it working?"
   - GOOD: "I'm getting auth errors. The key is set in .env as API_KEY."

2. NEVER ask Cascade to read excluded files
   - BAD: "Read .env and tell me what's configured"
   - GOOD: "What environment variables does src/config.ts expect?"

3. Use .windsurfrules to enforce safety patterns
   - "Always use process.env for secrets, never hardcode"
   - "Never log PII fields: email, phone, ssn, creditCard"

4. Mark compliance boundaries in .windsurfrules
   - "Files in src/pci/ handle credit card data — extra review required"
   - "Files in src/hipaa/ handle health data — never log patient info"
```

### Step 6: Enterprise Self-Hosted Deployment

For maximum data control:

```yaml
# Enterprise deployment options
deployment_modes:
  cloud:
    data_flow: "Code snippets → Codeium cloud → AI response"
    retention: "Zero-data retention (default for paid plans)"
    suitable_for: "Most teams"

  hybrid:
    data_flow: "Code stays on-prem, only prompts sent to cloud"
    retention: "Configurable"
    suitable_for: "Teams with data residency requirements"

  self_hosted:
    data_flow: "Everything on-prem or in your cloud"
    retention: "You control"
    suitable_for: "Highly regulated (finance, healthcare, government)"
    requires: "Enterprise plan + infrastructure team"
```

## Data Privacy Audit Checklist

- [ ] `.codeiumignore` covers all secret files and customer data
- [ ] Telemetry disabled (if required by policy)
- [ ] Autocomplete disabled for secret-containing file types
- [ ] `.windsurfrules` includes data handling coding standards
- [ ] Team trained: never paste secrets into Cascade
- [ ] Enterprise: deployment mode matches compliance requirements
- [ ] Enterprise: SSO configured, personal accounts blocked
- [ ] Regular audit: verify no new sensitive files outside ignore patterns

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| AI suggests hardcoded secrets | Secret was in indexed file | Add to `.codeiumignore`, rotate secret |
| PII appears in AI suggestions | Customer data in indexed directory | Exclude data directories |
| Telemetry still sending | Setting not applied | Verify in Settings UI, restart Windsurf |
| Compliance audit finding | Missing ignore patterns | Audit with `find` for exposed file types |

## Examples

### Quick Privacy Audit
```bash
set -euo pipefail
echo "=== Windsurf Data Privacy Audit ==="
echo "Has .codeiumignore: $([ -f .codeiumignore ] && echo 'YES' || echo 'NO')"
echo "Potential exposed secrets:"
find . -type f \
  -not -path '*/node_modules/*' -not -path '*/.git/*' \
  \( -name '*.env*' -o -name '*.key' -o -name '*.pem' -o -name 'credentials*' \) \
  2>/dev/null | while read f; do
    grep -q "$(basename "$f")" .codeiumignore 2>/dev/null && echo "  $f: PROTECTED" || echo "  $f: EXPOSED"
  done
```

## Resources
- [Codeium Privacy Policy](https://codeium.com/privacy-policy)
- [Windsurf Security](https://windsurf.com/security)
- [Windsurf Ignore Docs](https://docs.windsurf.com/context-awareness/windsurf-ignore)

## Next Steps
For enterprise access controls, see `windsurf-enterprise-rbac`.
