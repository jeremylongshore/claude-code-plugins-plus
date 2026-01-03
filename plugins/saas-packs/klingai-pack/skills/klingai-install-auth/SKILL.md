---
name: klingai-install-auth
description: |
  Set up Kling AI API authentication and configure API keys. Use when starting a new Kling AI
  integration or troubleshooting auth issues. Trigger with phrases like 'kling ai setup',
  'klingai api key', 'kling ai authentication', 'configure klingai'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Kling AI Installation & Authentication

## Overview

This skill guides you through obtaining and configuring Kling AI API credentials for video generation, setting up environment variables, and verifying your authentication is working correctly.

## Prerequisites

- Kling AI account (sign up at klingai.com)
- Python 3.8+ or Node.js 18+
- HTTP client library (requests, axios, or fetch)

## Instructions

Follow these steps to set up Kling AI authentication:

1. **Create Account**: Sign up at https://klingai.com
2. **Access API Settings**: Navigate to your account settings > API
3. **Generate API Key**: Create a new API key for your application
4. **Configure Environment**: Set up your environment variables
5. **Verify Setup**: Test your authentication with a simple request

## Getting Your API Key

### Create Account
```
1. Go to https://klingai.com
2. Sign up with email or phone
3. Verify your account
4. Navigate to API settings
```

### Generate API Key
```
1. Go to account settings > API Keys
2. Click "Create New Key"
3. Name your key (e.g., "production", "development")
4. Copy key immediately (only shown once)
5. Store securely
```

## Authentication Methods

### Bearer Token Authentication
```bash
curl -X POST https://api.klingai.com/v1/videos/text2video \
  -H "Authorization: Bearer $KLINGAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A cat playing piano",
    "duration": 5
  }'
```

### API Key Header
```bash
curl -X POST https://api.klingai.com/v1/videos/text2video \
  -H "X-API-Key: $KLINGAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A sunset over mountains",
    "duration": 5
  }'
```

## Environment Setup

### Environment Variables
```bash
# .env file
KLINGAI_API_KEY=your-api-key-here
KLINGAI_BASE_URL=https://api.klingai.com/v1

# Shell export
export KLINGAI_API_KEY="your-api-key-here"
```

### Python Setup
```python
import os
import requests

KLINGAI_API_KEY = os.environ.get("KLINGAI_API_KEY")
KLINGAI_BASE_URL = "https://api.klingai.com/v1"

headers = {
    "Authorization": f"Bearer {KLINGAI_API_KEY}",
    "Content-Type": "application/json"
}

def create_video(prompt: str, duration: int = 5):
    response = requests.post(
        f"{KLINGAI_BASE_URL}/videos/text2video",
        headers=headers,
        json={"prompt": prompt, "duration": duration}
    )
    return response.json()
```

### TypeScript/Node Setup
```typescript
import axios from 'axios';

const KLINGAI_API_KEY = process.env.KLINGAI_API_KEY;
const KLINGAI_BASE_URL = 'https://api.klingai.com/v1';

const klingaiClient = axios.create({
  baseURL: KLINGAI_BASE_URL,
  headers: {
    'Authorization': `Bearer ${KLINGAI_API_KEY}`,
    'Content-Type': 'application/json'
  }
});

async function createVideo(prompt: string, duration: number = 5) {
  const response = await klingaiClient.post('/videos/text2video', {
    prompt,
    duration
  });
  return response.data;
}
```

## API Key Best Practices

### Security
```
DO:
- Store in environment variables
- Use secrets manager in production
- Rotate keys periodically
- Use separate keys per environment

DON'T:
- Hardcode in source code
- Commit to version control
- Share keys between apps
- Log API keys
```

### Key Management
```
Development: dev-key with usage monitoring
Staging: staging-key with moderate limits
Production: prod-key with alerts

Rotation schedule:
- Development: When needed
- Production: Every 90 days
- After any suspected exposure: Immediately
```

## Verifying Setup

### Test Request
```python
import requests
import os

def verify_setup():
    response = requests.get(
        "https://api.klingai.com/v1/account",
        headers={"Authorization": f"Bearer {os.environ['KLINGAI_API_KEY']}"}
    )
    if response.status_code == 200:
        print("✓ Authentication successful")
        print(f"  Credits: {response.json().get('credits', 'N/A')}")
    else:
        print(f"✗ Authentication failed: {response.status_code}")
        print(f"  Error: {response.text}")

verify_setup()
```

### Check Account Status
```bash
curl https://api.klingai.com/v1/account \
  -H "Authorization: Bearer $KLINGAI_API_KEY"
```

## Troubleshooting

### "Invalid API Key"
```
Checklist:
[ ] Key is correctly copied (no extra spaces)
[ ] Using correct authorization header
[ ] Key hasn't been revoked
[ ] Account is active and verified
```

### "Insufficient Credits"
```
Solutions:
1. Check credit balance at klingai.com
2. Purchase additional credits
3. Wait for free tier refresh
```

## Output

Successful execution produces:
- Working Kling AI API authentication
- Verified API connectivity
- Account status and credit information

## Error Handling

Common errors and solutions:
1. **401 Unauthorized**: Check API key format and validity
2. **403 Forbidden**: Verify account is active and has API access
3. **429 Rate Limited**: Implement exponential backoff
4. **500 Server Error**: Retry with backoff, check Kling AI status

## Examples

See code examples in sections above for complete, runnable implementations.

## Resources

- [Kling AI Documentation](https://docs.klingai.com/)
- [Kling AI API Reference](https://docs.klingai.com/api)
- [Kling AI Dashboard](https://klingai.com/dashboard)
