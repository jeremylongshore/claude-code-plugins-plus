---
name: wispr-install-auth
description: |
  Wispr Flow install auth for voice-to-text API integration.
  Use when integrating Wispr Flow dictation, WebSocket streaming,
  or building voice-powered applications.
  Trigger: "wispr install auth".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, voice, dictation, wispr]
compatible-with: claude-code
---

# Wispr Flow Install & Auth

## Overview

Configure Wispr Flow API for voice-to-text transcription. Supports WebSocket (recommended, lower latency) and REST endpoints. Auth via API key (backend) or access tokens (client-side).

## Prerequisites

- Wispr Flow API access from [wisprflow.ai/developers](https://wisprflow.ai/developers)
- API key from developer dashboard
- Node.js 18+ or Python 3.8+

## Instructions

### Step 1: Configure API Key

```bash
# .env
WISPR_API_KEY=your-api-key-here
WISPR_API_URL=https://api.wisprflow.ai
```

### Step 2: WebSocket Connection (Recommended)

```typescript
const ws = new WebSocket('wss://api.wisprflow.ai/api/v1/ws', {
  headers: { Authorization: `Bearer ${process.env.WISPR_API_KEY}` },
});

ws.on('open', () => {
  // Send context for better transcription
  ws.send(JSON.stringify({
    type: 'config',
    context: { app: 'code-editor', language: 'en' },
  }));
  console.log('Connected to Wispr Flow');
});

ws.on('message', (data) => {
  const result = JSON.parse(data.toString());
  if (result.type === 'transcription') {
    console.log(`Transcript: ${result.text}`);
  }
});
```

### Step 3: REST API (Simpler, Higher Latency)

```python
import requests, os

response = requests.post(
    f"{os.environ['WISPR_API_URL']}/api/v1/transcribe",
    headers={"Authorization": f"Bearer {os.environ['WISPR_API_KEY']}"},
    files={"audio": open("recording.wav", "rb")},
    data={"language": "en"},
)
print(f"Transcript: {response.json()['text']}")
```

### Step 4: Generate Client Access Token

```typescript
// Backend: generate short-lived token for client use
const response = await fetch('https://api.wisprflow.ai/api/v1/auth/token', {
  method: 'POST',
  headers: {
    Authorization: `Bearer ${process.env.WISPR_API_KEY}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ expires_in: 3600 }), // 1 hour
});
const { access_token } = await response.json();
// Send access_token to client for direct WebSocket connection
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check key at wisprflow.ai/developers |
| WebSocket disconnect | Network interruption | Reconnect with backoff |
| Empty transcript | No speech detected | Check audio format and quality |

## Resources

- [Wispr Flow Developers](https://wisprflow.ai/developers)
- [API Documentation](https://api-docs.wisprflow.ai/introduction)
- [WebSocket Quickstart](https://api-docs.wisprflow.ai/websocket_quickstart)

## Next Steps

Proceed to `wispr-hello-world` for your first transcription.
