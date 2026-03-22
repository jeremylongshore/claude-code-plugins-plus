---
name: appfolio-security-basics
description: |
  Secure AppFolio API credentials and tenant data.
  Trigger: "appfolio security".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio security basics | sed 's/\b\(.\)/\u\1/g'

## Security Checklist
- [ ] API credentials in secret manager (not .env in production)
- [ ] HTTPS enforced for all API calls
- [ ] Tenant PII logged only when necessary
- [ ] API credentials rotated periodically
- [ ] Access scoped to minimum required endpoints

## Secure Client Configuration
```typescript
import https from "https";
import axios from "axios";

const secureClient = axios.create({
  baseURL: process.env.APPFOLIO_BASE_URL,
  auth: { username: process.env.APPFOLIO_CLIENT_ID!, password: process.env.APPFOLIO_CLIENT_SECRET! },
  httpsAgent: new https.Agent({ minVersion: "TLSv1.2", rejectUnauthorized: true }),
});
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
