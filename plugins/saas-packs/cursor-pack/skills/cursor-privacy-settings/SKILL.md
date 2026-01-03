---
name: cursor-privacy-settings
description: |
  Configure Cursor privacy and data handling settings. Triggers on "cursor privacy",
  "cursor data", "cursor security", "privacy mode", "cursor telemetry".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Privacy & Data Settings

## Privacy Mode

### Understanding Privacy Mode
```
Privacy Mode OFF (default):
- Full AI features enabled
- Code sent to AI providers for processing
- Best completions and suggestions
- Chat with full context

Privacy Mode ON:
- Limited AI features
- Code NOT sent to external AI
- Only local processing
- Reduced functionality
```

### Enabling Privacy Mode
```
Global:
Settings > Cursor > Privacy Mode > Enable

Per-workspace:
Add to .vscode/settings.json:
{
  "cursor.privacy.enabled": true
}
```

### When to Use Privacy Mode
```
Enable for:
- Proprietary algorithms
- Security-sensitive code
- Compliance requirements
- Client confidential work
- Pre-release features

Keep disabled for:
- Open source projects
- General development
- Learning/tutorials
- Public APIs
```

## Data Handling

### What Data is Processed
```
When Privacy Mode OFF:

Sent to AI:
- Code in context (selected/open files)
- Chat messages
- File contents for @-mentions
- Project structure (for indexing)

NOT sent:
- Full codebase (only indexed locally)
- Credentials (if properly excluded)
- Binary files
- Files in .cursorignore
```

### Data Retention
```
Cursor's data policy:
- Code not stored long-term
- Conversations not used for training (Business/Enterprise)
- Logs retained temporarily for debugging
- Indexing data stored locally only

AI Provider policies:
- OpenAI: No training on API data
- Anthropic: No training on API data
- Check current policies for specifics
```

## Sensitive File Exclusion

### .cursorignore for Security
```gitignore
# .cursorignore

# Environment and secrets
.env*
*.env
.env.local
.env.production

# Credentials
*.pem
*.key
*.p12
*.pfx
*.crt
id_rsa
id_ed25519
credentials.json
serviceAccount.json

# Config with secrets
config/production.json
config/secrets.yaml
secrets/

# API keys and tokens
.npmrc
.pypirc
.docker/config.json

# Database
*.sql
*.dump
*.sqlite
```

### Code-Level Exclusions
```typescript
// Mark sections to skip
// @cursor-ignore-start
const SECRET_KEY = "actual-secret-here";
const API_TOKEN = "sensitive-token";
// @cursor-ignore-end

// Or use environment variables (recommended)
const SECRET_KEY = process.env.SECRET_KEY;
```

## Telemetry Settings

### Cursor Telemetry
```json
// settings.json
{
  // Disable all telemetry
  "telemetry.telemetryLevel": "off",

  // Cursor-specific
  "cursor.telemetry.enabled": false,

  // Crash reports
  "cursor.telemetry.crashReports": false
}
```

### What Telemetry Collects
```
When enabled:
- Usage patterns (anonymized)
- Feature adoption metrics
- Crash reports
- Performance data

When disabled:
- No data collected
- Some features may be limited
- Can't contribute to improvements
```

## Enterprise Privacy Controls

### Organization Policies
```
Business/Enterprise admins can:
- Enforce Privacy Mode globally
- Set default model restrictions
- Configure data retention
- Audit usage patterns
- Require SSO/2FA
```

### Compliance Features
```
SOC 2 compliance:
- Audit logs available
- Access controls
- Encryption at rest and transit
- Regular security audits

GDPR compliance:
- Data processing agreements
- Right to deletion
- Data portability
- Purpose limitation
```

## Network Security

### Firewall Configuration
```
Required endpoints for Cursor:

Cursor services:
- api.cursor.com
- auth.cursor.com
- telemetry.cursor.com (optional)

AI providers:
- api.openai.com
- api.anthropic.com
- api.azure.com (if using Azure)

VS Code/Extensions:
- marketplace.visualstudio.com
- update.code.visualstudio.com
```

### Proxy Configuration
```json
// settings.json
{
  // HTTP proxy
  "http.proxy": "http://proxy.company.com:8080",

  // Proxy authorization
  "http.proxyAuthorization": "Basic base64credentials",

  // Strict SSL
  "http.proxyStrictSSL": true
}
```

## Local Data Storage

### Where Data is Stored
```bash
# Local Cursor data locations

macOS:
~/Library/Application Support/Cursor/
~/Library/Caches/Cursor/

Linux:
~/.config/Cursor/
~/.cache/Cursor/

Windows:
%APPDATA%\Cursor\
%LOCALAPPDATA%\Cursor\

# Index location
~/.cursor/index/
```

### Clearing Local Data
```bash
# Clear cache only
rm -rf ~/Library/Caches/Cursor/

# Clear all local data (reset)
rm -rf ~/Library/Application\ Support/Cursor/

# Clear just the index
rm -rf ~/.cursor/index/
```

## API Key Security

### Using Own API Keys
```json
// Secure storage of API keys
{
  // Use environment variables
  "cursor.openai.apiKey": "${OPENAI_API_KEY}",
  "cursor.anthropic.apiKey": "${ANTHROPIC_API_KEY}"
}
```

### Key Management Best Practices
```
1. Use environment variables, not hardcoded keys
2. Rotate keys periodically
3. Use least-privilege API keys
4. Monitor API usage for anomalies
5. Revoke keys immediately if compromised
```

## Privacy Checklist

### For Sensitive Projects
```
[ ] Privacy Mode enabled
[ ] .cursorignore configured
[ ] Environment files excluded
[ ] Credentials not in code
[ ] API keys from env vars
[ ] Telemetry disabled
[ ] Audit team access
[ ] Document data handling
```

### Regular Audit
```
Monthly:
[ ] Review .cursorignore coverage
[ ] Check for exposed secrets
[ ] Audit team member access
[ ] Review API key usage
[ ] Update security settings

Quarterly:
[ ] Full security review
[ ] Update documentation
[ ] Team training refresh
[ ] Policy updates
```

## Incident Response

### If Data Exposure Suspected
```
1. Immediately:
   - Enable Privacy Mode
   - Rotate affected credentials
   - Document the incident

2. Investigate:
   - Review what was exposed
   - Check AI provider logs (if available)
   - Assess impact

3. Remediate:
   - Update .cursorignore
   - Improve processes
   - Notify stakeholders if required
```
