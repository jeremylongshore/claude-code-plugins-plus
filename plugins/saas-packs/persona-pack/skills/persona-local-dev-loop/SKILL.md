---
name: persona-local-dev-loop
description: |
  Local development with Persona sandbox, ngrok for webhooks, mock verifications.
  Use when working with Persona identity verification.
  Trigger with phrases like "persona local-dev-loop", "persona local-dev-loop".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, verification]
compatible-with: claude-code, codex, openclaw
---

# persona local dev loop | sed 's/\b\(.\)/\u\1/g'

## Overview
Sandbox testing with test inquiry templates, ngrok tunnel for webhook testing, mock API responses for CI.

## Prerequisites
- Completed `persona-install-auth` setup
- Valid Persona API key (sandbox or production)

## Instructions

### Step 1: Set Up Sandbox Environment
```bash
set -euo pipefail
# Use sandbox API key for all development
echo 'PERSONA_API_KEY=persona_sandbox_xxxxxxxx' > .env
echo 'PERSONA_API_VERSION=2023-01-05' >> .env
```

### Step 2: Expose Local Webhooks with ngrok
```bash
# Terminal 1: Start your webhook server
npm run dev  # localhost:3000

# Terminal 2: Tunnel with ngrok
ngrok http 3000
# Copy the HTTPS URL and configure in Persona Dashboard > Webhooks
```

### Step 3: Create Test Inquiries
```python
import os, requests

HEADERS = {
    "Authorization": f"Bearer {os.environ['PERSONA_API_KEY']}",
    "Persona-Version": "2023-01-05",
}

# Create inquiry with sandbox template
resp = requests.post("https://withpersona.com/api/v1/inquiries", headers=HEADERS, json={
    "data": {
        "attributes": {
            "inquiry-template-id": "itmpl_YOUR_SANDBOX_TEMPLATE",
            "reference-id": f"test-{int(time.time())}",
        }
    }
})
print(f"Test inquiry: {resp.json()['data']['id']}")
```

### Step 4: Mock API Responses for CI
```typescript
import { vi } from 'vitest';

const mockPersonaApi = {
  createInquiry: vi.fn().mockResolvedValue({
    data: { id: 'inq_test_123', attributes: { status: 'created', 'session-token': 'tok_xxx' } },
  }),
  getInquiry: vi.fn().mockResolvedValue({
    data: { id: 'inq_test_123', attributes: { status: 'completed' } },
  }),
};
```

## Output
- Sandbox environment configured for development
- ngrok tunnel for webhook testing
- Test inquiry creation workflow
- Mock API responses for unit tests

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Webhook not received | ngrok URL not configured | Update webhook URL in Dashboard |
| Sandbox key rejected | Using production key | Verify key starts with `persona_sandbox_` |
| Template not found | Wrong environment | Templates are per-environment |

## Resources
- [Persona API Quickstart](https://docs.withpersona.com/api-quickstart-tutorial)
- [ngrok Documentation](https://ngrok.com/docs)

## Next Steps
Apply SDK patterns: `persona-sdk-patterns`
