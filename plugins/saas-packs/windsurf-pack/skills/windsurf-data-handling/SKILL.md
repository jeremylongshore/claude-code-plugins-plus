---
name: windsurf-data-handling
description: |
  Implement Windsurf PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Windsurf integrations.
  Trigger with phrases like "windsurf data", "windsurf PII",
  "windsurf GDPR", "windsurf data retention", "windsurf privacy", "windsurf CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Windsurf Data Handling

## Overview
Control what code and data Windsurf (Codeium) Cascade AI can access in your workspace. Covers file exclusion patterns, sensitive content filtering, telemetry management, and workspace privacy configuration.

## Prerequisites
- Windsurf IDE installed
- Understanding of Codeium data processing
- Repository with sensitive files identified
- Team agreement on AI data boundaries

## Instructions

### Step 1: Exclude Sensitive Files from AI Indexing
```json
// .windsurf/settings.json - Privacy configuration
{
  "codeium.indexing.excludePatterns": [
    "**/.env*",
    "**/credentials*",
    "**/secrets/**",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/serviceAccountKey*",
    "**/.aws/**",
    "**/.gcloud/**",
    "**/terraform.tfstate*",
    "**/*.tfvars",
    "**/vault-config*"
  ],
  "codeium.indexing.maxFileSize": 524288,
  "codeium.enableTelemetry": false
}
```

### Step 2: Create Workspace Ignore File
```gitignore
# .codeiumignore - Files Codeium/Windsurf will never process
# Similar to .gitignore syntax

# Secrets and credentials
.env
.env.*
credentials.json
serviceAccountKey.json
*.pem
*.key
*.p12

# Customer data
data/customers/**
exports/**
backups/**

# Sensitive configuration
config/production.json
config/secrets.yaml

# Large binary files (waste of indexing)
*.zip
*.tar.gz
*.sqlite
*.db
```

### Step 3: Environment Variable Safety
```typescript
// Prevent secrets from appearing in Cascade suggestions
// .windsurf/patterns.md

/**
 * IMPORTANT: Environment Variable Patterns
 *
 * When Cascade suggests code with environment variables:
 * - Always use process.env.VARIABLE_NAME, never hardcode values
 * - For local development, use .env files (which are excluded from AI)
 * - Never paste actual secret values into Cascade chat
 *
 * Safe pattern:
 * ```
 * const apiKey = process.env.API_KEY!;
 * ```
 *
 * Unsafe pattern (never do this):
 * ```
 * const apiKey = "sk-abc123..."; // NEVER
 * ```
 */
```

### Step 4: Telemetry and Data Controls
```json
// .windsurf/settings.json - Telemetry controls
{
  "codeium.enableTelemetry": false,
  "codeium.enableSnippetTelemetry": false,
  "telemetry.telemetryLevel": "off",

  "codeium.autocomplete": {
    "enable": true,
    "languages": {
      "plaintext": false,
      "markdown": false,
      "json": false,
      "yaml": false,
      "env": false
    }
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secret in AI suggestion | Secret was in indexed file | Add to `.codeiumignore` |
| Large file slowing AI | Binary indexed | Add file extension to exclude patterns |
| Telemetry sending data | Not disabled | Set `enableTelemetry: false` |
| AI suggests hardcoded key | No workspace rules | Add patterns about env vars to rules file |

## Examples

### Quick Privacy Audit
```bash
# Check what files Windsurf would index
find . -type f \
  -not -path '*/node_modules/*' \
  -not -path '*/.git/*' \
  -name '*.env*' -o -name '*.key' -o -name '*.pem' \
  | head -20
# All found files should be in .codeiumignore
```

## Resources
- [Codeium Privacy Policy](https://codeium.com/privacy-policy)
- [Windsurf Configuration](https://docs.windsurf.com/configuration)
