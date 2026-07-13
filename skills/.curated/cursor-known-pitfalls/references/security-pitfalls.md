# Security Pitfalls

## Security Pitfalls

### Exposing Secrets

```
PITFALL:
AI context includes sensitive data.
Secrets sent to AI providers.

SOLUTION:
- Use .cursorignore for .env files
- Use environment variables
- Enable Privacy Mode for sensitive code
- Never hardcode credentials
```

### Trusting AI for Security Code

```
PITFALL:
AI-generated auth/crypto code may have flaws.
Security vulnerabilities in generated code.

SOLUTION:
- Extra review for security code
- Use established libraries
- Security review by human expert
- Test with security tools
```

### API Keys in Settings

```
PITFALL:
Storing API keys in settings.json.
Keys visible in plaintext.

SOLUTION:
- Use environment variables
- Use secrets managers
- Never commit keys to repo
- Rotate keys if exposed
```
