---
name: persona-install-auth
description: |
  Install and configure Persona SDK/CLI authentication.
  Use when setting up a new Persona integration, configuring API keys,
  or initializing Persona in your project.
  Trigger with phrases like "install persona", "setup persona",
  "persona auth", "configure persona API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, persona]
---

# Persona Install & Auth

## Overview
Set up Persona SDK/CLI and configure authentication credentials.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Persona account with API access

- OAuth2 access token or personal API token from Persona settings


## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @persona/sdk

# Python
pip install persona
```

### Step 2: Configure Authentication

```bash
# Set environment variable
export PERSONA_API_KEY="your-api-key"

# Or create .env file
echo 'PERSONA_API_KEY=your-api-key' >> .env
```


### Step 3: Verify Connection
```typescript
const org = await client.organization.get();
console.log(`Connected: ${org.name} (${org.plan} plan)`);

```

## Output
- Installed SDK package in node_modules or site-packages

- Environment variable or .env file with API key
- Successful connection verification output


## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|

| Invalid API Key | Incorrect or expired key | Verify key in Persona dashboard |
| Rate Limited | Exceeded quota | Check quota at https://docs.persona.com |

| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { PersonaClient } from '@persona/sdk';

const client = new PersonaClient({

  apiKey: process.env.PERSONA_API_KEY,

});
```

### Python Setup
```python
from persona import PersonaClient

client = PersonaClient(

    api_key=os.environ.get('PERSONA_API_KEY')

)
```

## Resources
- [Persona Documentation](https://docs.persona.com)
- [Persona Dashboard](https://api.persona.com)
- [Persona Status](https://status.persona.com)

## Next Steps
After successful auth, proceed to `persona-hello-world` for your first API call.