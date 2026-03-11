# Lindy Install Auth - Implementation Guide

# Lindy Install & Auth

## Overview
Set up Lindy AI SDK and configure authentication credentials for AI agent automation.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Lindy account with API access
- API key from Lindy dashboard (https://app.lindy.ai)

## Instructions

### Step 1: Install SDK
```bash
# Node.js
npm install @lindy-ai/sdk

# Python
pip install lindy-sdk
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export LINDY_API_KEY="your-api-key"

# Or create .env file
echo 'LINDY_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
import { Lindy } from '@lindy-ai/sdk';

const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });
const agents = await lindy.agents.list();
console.log(agents.length > 0 ? 'Connected!' : 'No agents yet');
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Lindy dashboard |
| Rate Limited | Exceeded quota | Check quota at https://app.lindy.ai |
| Network Error | Firewall blocking | Ensure outbound HTTPS allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { Lindy } from '@lindy-ai/sdk';

const lindy = new Lindy({
  apiKey: process.env.LINDY_API_KEY,
});

// Verify connection
const me = await lindy.users.me();
console.log(`Connected as: ${me.email}`);
```

### Python Setup
```python
from lindy import Lindy

client = Lindy(api_key=os.environ.get('LINDY_API_KEY'))

# Verify connection
me = client.users.me()
print(f"Connected as: {me.email}")
```

## Resources
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Dashboard](https://app.lindy.ai)
- [Lindy API Reference](https://docs.lindy.ai/api)

## Next Steps
After successful auth, proceed to `lindy-hello-world` for your first AI agent.
