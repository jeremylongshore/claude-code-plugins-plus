---
description: Scan for exposed secrets and credentials in codebase
shortcut: secrets
---

# Secret Scanner

Scan codebase for exposed secrets, API keys, passwords, tokens, and sensitive credentials that should not be committed to version control.

## Detection Methods

1. **Pattern Matching**
   - API keys (AWS, Google, Azure, Stripe, etc.)
   - Private keys (RSA, SSH, PGP)
   - Database credentials
   - OAuth tokens
   - JWT tokens
   - Passwords in configuration files

2. **Entropy Analysis**
   - High-entropy strings (base64, hex)
   - Random-looking strings that may be secrets
   - Cryptographic keys

3. **Common Mistakes**
   - Hardcoded credentials in source code
   - Credentials in commit history
   - Secrets in configuration files
   - Environment variables committed to repo
   - Backup files containing secrets

4. **File Type Analysis**
   - .env files
   - Configuration files
   - Shell scripts
   - Docker files
   - CI/CD configuration

## Report Output

Generate detailed secret exposure report with:
- Location of each secret (file, line number)
- Type of secret detected
- Severity level (Critical, High, Medium)
- Remediation steps
- Git history scan results

## Immediate Actions

For exposed secrets:
1. **Rotate immediately** - Revoke and regenerate
2. **Remove from git history** - Use git-filter-branch or BFG
3. **Update .gitignore** - Prevent future commits
4. **Use secret management** - HashiCorp Vault, AWS Secrets Manager
5. **Enable pre-commit hooks** - Prevent secret commits

## Best Practices

- Never commit secrets to version control
- Use environment variables
- Use secret management tools
- Enable pre-commit secret scanning
- Rotate secrets regularly
- Audit git history periodically
