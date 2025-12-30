---
name: openrouter-install-auth
description: |
  Set up OpenRouter API authentication and keys. Triggers on "openrouter setup",
  "openrouter api key", "openrouter authentication", "configure openrouter".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# OpenRouter Installation & Authentication

## Getting Your API Key

### Create Account
```
1. Go to https://openrouter.ai
2. Sign up with email or OAuth (Google, GitHub)
3. Verify email if required
4. Navigate to https://openrouter.ai/keys
```

### Generate API Key
```
1. Click "Create Key"
2. Name your key (e.g., "production", "development")
3. Set optional credit limit
4. Copy key immediately (only shown once)
5. Store securely
```

## Authentication Methods

### Bearer Token (Recommended)
```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### HTTP-Referer Header (Optional)
```bash
# For app identification and rankings
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "HTTP-Referer: https://your-app.com" \
  -H "X-Title: Your App Name" \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-4-turbo", "messages": [...]}'
```

## Environment Setup

### Environment Variables
```bash
# .env file
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# Shell export
export OPENROUTER_API_KEY="sk-or-v1-..."
```

### Python Setup
```python
import os
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)
```

### TypeScript/Node Setup
```typescript
import OpenAI from 'openai';

const openrouter = new OpenAI({
  baseURL: 'https://openrouter.ai/api/v1',
  apiKey: process.env.OPENROUTER_API_KEY,
  defaultHeaders: {
    'HTTP-Referer': 'https://your-app.com',
    'X-Title': 'Your App Name',
  },
});
```

## API Key Best Practices

### Security
```
DO:
- Store in environment variables
- Use secrets manager in production
- Rotate keys periodically
- Set credit limits on keys
- Use separate keys per environment

DON'T:
- Hardcode in source code
- Commit to version control
- Share keys between apps
- Use production keys in development
```

### Key Management
```
Development: dev-key with low credit limit
Staging: staging-key with moderate limit
Production: prod-key with monitoring

Rotation schedule:
- Development: When needed
- Production: Every 90 days
- After any suspected exposure: Immediately
```

## Verifying Setup

### Test Request
```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Check Credits
```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Response
```json
{
  "data": {
    "label": "my-key",
    "limit": 100.0,
    "usage": 5.23,
    "limit_remaining": 94.77
  }
}
```

## Troubleshooting

### "Invalid API Key"
```
Checklist:
[ ] Key starts with "sk-or-"
[ ] No extra whitespace
[ ] Key hasn't been revoked
[ ] Using correct header format
```

### "Insufficient Credits"
```
Solutions:
1. Add credits at openrouter.ai/credits
2. Check key-specific limit
3. Verify usage at openrouter.ai/activity
```

### "Rate Limited"
```
Solutions:
1. Implement exponential backoff
2. Check rate limit headers
3. Consider upgrading plan
4. Distribute across multiple keys
```

## Credit System

### Adding Credits
```
1. Go to openrouter.ai/credits
2. Choose amount ($5, $20, $100, custom)
3. Pay via Stripe
4. Credits available immediately
```

### Credit Limits per Key
```
Set limits to prevent unexpected charges:
- Development keys: $5-10
- Staging keys: $20-50
- Production keys: Based on budget
```

### Monitoring Usage
```
Dashboard: openrouter.ai/activity
- Per-request costs
- Model breakdown
- Daily/weekly/monthly trends
```
