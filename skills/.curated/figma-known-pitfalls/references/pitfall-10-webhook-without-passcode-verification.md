# Pitfall 10: Webhook Without Passcode Verification

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 10: Webhook Without Passcode Verification' step of the workflow.

**Problem:** Anyone can POST to your webhook endpoint if you don't verify the passcode.

```typescript
// BAD -- trusts any incoming request
app.post('/webhooks/figma', (req, res) => {
  processEvent(req.body); // Attacker can send fake events
  res.sendStatus(200);
});

// GOOD -- verify passcode with timing-safe comparison
app.post('/webhooks/figma', (req, res) => {
  const received = req.body.passcode || '';
  const expected = process.env.FIGMA_WEBHOOK_PASSCODE!;

  if (received.length !== expected.length ||
      !crypto.timingSafeEqual(Buffer.from(received), Buffer.from(expected))) {
    return res.status(401).json({ error: 'Invalid passcode' });
  }

  res.status(200).json({ received: true });
  processEvent(req.body);
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
