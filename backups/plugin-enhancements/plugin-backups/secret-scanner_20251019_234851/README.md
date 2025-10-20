# Secret Scanner Plugin

Scan codebase for exposed secrets, API keys, passwords, and sensitive credentials with pattern matching and entropy analysis.

## Features

- **Multi-Platform API Keys** - AWS, GCP, Azure, Stripe, GitHub, etc.
- **Pattern Matching** - Known secret formats
- **Entropy Analysis** - Detect random strings that may be secrets
- **Git History Scanning** - Find secrets in commit history
- **Comprehensive Reporting** - File locations and remediation steps
- **Pre-commit Integration** - Prevent secret commits

## Installation

```bash
/plugin install secret-scanner@claude-code-plugins-plus
```

## Usage

```bash
# Scan current directory
/scan-secrets

# Or use shortcut
/secrets
```

## What It Detects

### API Keys & Tokens
- AWS Access Keys
- Google API Keys
- Azure Storage Keys
- Stripe API Keys
- GitHub Personal Access Tokens
- Slack Tokens
- Twilio API Keys
- SendGrid API Keys
- Mailgun API Keys

### Credentials
- Database passwords
- SMTP credentials
- FTP credentials
- SSH private keys
- PGP private keys

### Tokens
- OAuth tokens
- JWT tokens
- Session tokens
- Bearer tokens

### High-Entropy Strings
- Base64-encoded secrets
- Hexadecimal keys
- Random-looking strings (>4.5 entropy)

## Example Report

```
SECRET SCAN REPORT
==================
Scan Date: 2025-10-11
Secrets Found: 4

CRITICAL SECRETS
----------------

1. AWS Access Key Exposed
   File: src/config/aws.js:12
   Pattern: AKIA[0-9A-Z]{16}
   Value: AKIA****************WXYZ (masked)

   Immediate Actions:
   1. Revoke this key in AWS IAM Console
   2. Generate new access key
   3. Store in environment variable or AWS Secrets Manager
   4. Remove from git history:
      git filter-branch --force --index-filter \
        'git rm --cached --ignore-unmatch src/config/aws.js' \
        --prune-empty --tag-name-filter cat -- --all

2. Database Password Hardcoded
   File: config/database.yml:15
   Pattern: password: ********

   Remediation:
   Use environment variables:
   password: <%= ENV['DB_PASSWORD'] %>

3. Private SSH Key
   File: deploy/id_rsa:1
   Pattern: -----BEGIN RSA PRIVATE KEY-----

   Immediate Actions:
   1. Remove key from repository
   2. Revoke key on all servers
   3. Generate new SSH key pair
   4. Add to .gitignore: deploy/*.pem, deploy/id_rsa

4. High-Entropy String (Potential Secret)
   File: src/utils/crypto.js:45
   Entropy: 4.8 bits
   Value: 3kx9f2nv8q1m4p7r... (base64)

   Review Required:
   Verify if this is a secret or legitimate code
```

## Remediation Guide

### For Exposed API Keys
```bash
# 1. Revoke the exposed key immediately
# (Use provider's console/CLI)

# 2. Remove from current files
# Replace with environment variable
export API_KEY="new-key-here"

# 3. Remove from git history
git filter-repo --path config/keys.js --invert-paths

# 4. Add to .gitignore
echo "config/keys.js" >> .gitignore
```

### For Configuration Files
```bash
# Create template file
cp .env .env.example
# Remove sensitive values from .env.example

# Add .env to .gitignore
echo ".env" >> .gitignore

# Document required variables
cat > .env.example << EOF
# Required environment variables
API_KEY=your_api_key_here
DATABASE_URL=your_database_url_here
EOF
```

## Best Practices

1. **Prevention**
   - Use environment variables
   - Implement pre-commit hooks
   - Use secret management tools (Vault, AWS Secrets Manager)
   - Review code before committing

2. **Detection**
   - Run scans regularly
   - Scan git history periodically
   - Monitor CI/CD logs
   - Enable secret scanning in GitHub/GitLab

3. **Response**
   - Rotate exposed secrets immediately
   - Remove from git history
   - Update documentation
   - Notify security team

4. **Secret Management**
   - Use HashiCorp Vault
   - Use cloud provider secret managers
   - Use encrypted configuration
   - Implement proper access controls

## Pre-commit Hook

Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
if /plugin secret-scanner | grep -q "CRITICAL"; then
    echo "ERROR: Secrets detected! Commit blocked."
    exit 1
fi
```

## Requirements

- Read access to codebase
- Read access to git history
- Write access for remediation scripts

## License

MIT License - See LICENSE file for details
