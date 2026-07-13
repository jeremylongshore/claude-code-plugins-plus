# Sensitive File Exclusion

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
