# Step 4: Idempotency for Duplicate Events

Deep-dive reference for the `figma-webhooks-events` skill — extracted from the 'Step 4: Idempotency for Duplicate Events' step of the workflow.

```typescript
// Figma may deliver the same event multiple times
const processedEvents = new Set<string>();

function deduplicateEvent(event: FigmaWebhookEvent): boolean {
  const key = `${event.webhook_id}:${event.timestamp}`;
  if (processedEvents.has(key)) {
    console.log(`Duplicate event skipped: ${key}`);
    return false;
  }
  processedEvents.add(key);
  // Clean up old entries (keep last 1000)
  if (processedEvents.size > 1000) {
    const oldest = Array.from(processedEvents).slice(0, 500);
    oldest.forEach(k => processedEvents.delete(k));
  }
  return true;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
