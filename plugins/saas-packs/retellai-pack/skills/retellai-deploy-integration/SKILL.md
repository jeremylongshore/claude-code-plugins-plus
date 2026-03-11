---
name: retellai-deploy-integration
description: |
  Deploy Retell AI integrations to Vercel, Fly.io, and Cloud Run platforms.
  Use when deploying Retell AI-powered applications to production,
  configuring platform-specific secrets, or setting up deployment pipelines.
  Trigger with phrases like "deploy retellai", "retellai Vercel",
  "retellai production deploy", "retellai Cloud Run", "retellai Fly.io".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Deploy Integration

## Overview
Deploy Retell AI voice agent applications to production. Covers configuring voice agent webhooks, deploying WebSocket endpoints for real-time audio, and managing API credentials for Retell AI's call management API at `api.retellai.com`.

## Prerequisites
- Retell AI API key stored in `RETELL_API_KEY` environment variable
- Voice agent configured in Retell AI dashboard
- HTTPS endpoint for webhooks and WebSocket connections
- Platform CLI installed (vercel, fly, or gcloud)

## Instructions

### Step 1: Configure Secrets
```bash
# Fly.io (recommended for WebSocket support)
fly secrets set RETELL_API_KEY=your-key
fly secrets set RETELL_WEBHOOK_SECRET=your-secret

# Cloud Run
echo -n "your-key" | gcloud secrets create retell-api-key --data-file=-
```

### Step 2: Deploy WebSocket Server
```typescript
// server.ts - WebSocket for real-time audio
import { WebSocketServer } from "ws";
import express from "express";

const app = express();
const server = app.listen(process.env.PORT || 3000);  # 3000: 3 seconds in ms
const wss = new WebSocketServer({ server, path: "/ws/call" });

wss.on("connection", (ws, req) => {
  const callId = new URL(req.url!, `http://${req.headers.host}`).searchParams.get("call_id");
  console.log(`WebSocket connected for call: ${callId}`);

  ws.on("message", (data) => {
    // Process audio stream from Retell AI
    handleAudioChunk(callId!, data);
  });

  ws.on("close", () => {
    console.log(`Call ${callId} WebSocket closed`);
  });
});
```

### Step 3: Fly.io Deployment
```toml
# fly.toml
app = "retellai-voice-server"
primary_region = "iad"

[env]
NODE_ENV = "production"

[http_service]
internal_port = 3000  # 3000: 3 seconds in ms
force_https = true
auto_stop_machines = false
auto_start_machines = true
min_machines_running = 1

[checks]
  [checks.health]
    type = "http"
    port = 3000  # 3 seconds in ms
    path = "/health"
    interval = "30s"
```

```bash
fly deploy
```

### Step 4: Webhook Endpoint
```typescript
// api/webhooks/retellai.ts
app.post("/webhooks/retellai", express.raw({ type: "application/json" }), (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });  # HTTP 200 OK

  switch (event.event) {
    case "call_ended":
      processCallTranscript(event.call);
      break;
    case "call_analyzed":
      syncCallAnalysis(event.call);
      break;
  }
});
```

### Step 5: Register Agent Webhook
```bash
set -euo pipefail
curl -X PATCH https://api.retellai.com/v2/agent/$AGENT_ID \
  -H "Authorization: Bearer $RETELL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://your-app.fly.dev/webhooks/retellai",
    "websocket_url": "wss://your-app.fly.dev/ws/call"
  }'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| WebSocket disconnect | Server restart | Use `min_machines_running: 1` |
| Audio latency | Wrong region | Deploy close to Retell AI servers (US East) |
| Webhook signature fail | Wrong secret | Verify secret in Retell AI dashboard |
| Call quality issues | Network jitter | Use dedicated VM, not serverless |

## Examples


**Basic usage**: Apply retellai deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize retellai deploy integration for production environments with multiple constraints and team-specific requirements.

## Resources
- [Retell AI Documentation](https://docs.retellai.com)
- [Retell AI WebSocket API](https://docs.retellai.com/websocket)
- [Fly.io WebSocket Guide](https://fly.io/docs/reference/runtime-environment/#websocket)

## Next Steps
For multi-environment setup, see `retellai-multi-env-setup`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale