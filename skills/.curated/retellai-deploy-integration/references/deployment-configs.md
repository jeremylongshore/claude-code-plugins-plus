# Deployment Configuration Examples

## WebSocket Server

```typescript
// server.ts - WebSocket for real-time audio
import { WebSocketServer } from "ws";
import express from "express";

const app = express();
const server = app.listen(process.env.PORT || 3000);
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

## Fly.io Configuration

```toml
# fly.toml
app = "retellai-voice-server"
primary_region = "iad"

[env]
NODE_ENV = "production"

[http_service]
internal_port = 3000
force_https = true
auto_stop_machines = false
auto_start_machines = true
min_machines_running = 1

[checks]
  [checks.health]
    type = "http"
    port = 3000
    path = "/health"
    interval = "30s"
```

## Webhook Endpoint

```typescript
// api/webhooks/retellai.ts
app.post("/webhooks/retellai", express.raw({ type: "application/json" }), (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

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

## Register Agent Webhook

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
