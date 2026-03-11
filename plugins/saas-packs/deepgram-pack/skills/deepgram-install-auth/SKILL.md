---
name: deepgram-install-auth
description: |
  Install and configure Deepgram SDK/CLI authentication.
  Use when setting up a new Deepgram integration, configuring API keys,
  or initializing Deepgram in your project.
  Trigger with phrases like "install deepgram", "setup deepgram",
  "deepgram auth", "configure deepgram API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Install & Auth

## Overview
Set up Deepgram SDK and configure authentication credentials for speech-to-text services.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Deepgram account with API access
- API key from Deepgram Console (https://console.deepgram.com)

## Instructions

### Step 1: Install SDK
```bash
set -euo pipefail
# Node.js
npm install @deepgram/sdk

# Python
pip install deepgram-sdk
```

### Step 2: Configure Authentication
```bash
# Set environment variable
export DEEPGRAM_API_KEY="your-api-key"

# Or create .env file
echo 'DEEPGRAM_API_KEY=your-api-key' >> .env
```

### Step 3: Verify Connection
```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY);
const { result, error } = await deepgram.manage.getProjects();
console.log(error ? 'Failed' : 'Connected successfully');
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variable or .env file with API key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Deepgram Console |
| 401 Unauthorized | API key not set | Check environment variable is exported |
| Network Error | Firewall blocking | Ensure outbound HTTPS to api.deepgram.com |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { createClient } from '@deepgram/sdk';

const deepgram = createClient(process.env.DEEPGRAM_API_KEY);

// Verify connection
async function verifyConnection() {
  const { result, error } = await deepgram.manage.getProjects();
  if (error) throw error;
  console.log('Projects:', result.projects);
}
```

### Python Setup
```python
from deepgram import DeepgramClient
import os

deepgram = DeepgramClient(os.environ.get('DEEPGRAM_API_KEY'))

# Verify connection
response = deepgram.manage.get_projects()
print(f"Projects: {response.projects}")
```

## Resources
- [Deepgram Documentation](https://developers.deepgram.com/docs)
- [Deepgram Console](https://console.deepgram.com)
- [Deepgram API Reference](https://developers.deepgram.com/reference)

## Next Steps
After successful auth, proceed to `deepgram-hello-world` for your first transcription.