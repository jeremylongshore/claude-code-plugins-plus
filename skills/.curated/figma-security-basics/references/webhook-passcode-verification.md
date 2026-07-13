# Step 4: Webhook Passcode Verification

Deep-dive reference for the `figma-security-basics` skill — extracted from the 'Step 4: Webhook Passcode Verification' step of the workflow.

Figma webhooks use a `passcode` field (not HMAC signatures) for verification:

```typescript
// When creating a webhook, you provide a passcode:
// POST /v2/webhooks
// { "event_type": "FILE_UPDATE", "team_id": "...", "endpoint": "...", "passcode": "my-secret" }

// Figma sends the passcode back in the webhook payload body
interface FigmaWebhookPayload {
  event_type: string;
  passcode: string;      // Your secret, echoed back
  timestamp: string;
  file_key?: string;
  file_name?: string;
  webhook_id: string;
}

function verifyFigmaWebhook(
  payload: FigmaWebhookPayload,
  expectedPasscode: string
): boolean {
  // Timing-safe comparison to prevent timing attacks
  if (payload.passcode.length !== expectedPasscode.length) return false;

  const a = Buffer.from(payload.passcode);
  const b = Buffer.from(expectedPasscode);
  return crypto.timingSafeEqual(a, b);
}

// Express handler
app.post('/webhooks/figma', express.json(), (req, res) => {
  const payload: FigmaWebhookPayload = req.body;

  if (!verifyFigmaWebhook(payload, process.env.FIGMA_WEBHOOK_PASSCODE!)) {
    console.warn('Invalid webhook passcode');
    return res.status(401).json({ error: 'Invalid passcode' });
  }

  // Process the event
  handleFigmaEvent(payload);
  res.status(200).json({ received: true });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
