# Outbound Data Events — Full Walkthrough

Submit custom events to track contact activity in Intercom via the Events API.

## Step 5: Track Data Events

```typescript
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

// Submit a data event
await client.dataEvents.create({
  eventName: "completed-onboarding",
  createdAt: Math.floor(Date.now() / 1000),
  userId: "user-12345", // External ID of the contact
  metadata: {
    steps_completed: 5,
    time_to_complete_minutes: 12,
    plan: "pro",
  },
});

// Event naming convention: past-tense verb-noun
// Good: "placed-order", "upgraded-plan", "invited-teammate"
// Bad: "order", "click", "page_view"
```

## Step 6: Bulk Event Submission

```typescript
// Submit events for multiple users efficiently
async function trackBulkEvents(
  client: IntercomClient,
  events: Array<{ userId: string; eventName: string; metadata?: Record<string, any> }>
): Promise<{ succeeded: number; failed: number }> {
  let succeeded = 0;
  let failed = 0;

  // Intercom doesn't have a batch events endpoint; throttle individual calls
  for (const event of events) {
    try {
      await client.dataEvents.create({
        eventName: event.eventName,
        createdAt: Math.floor(Date.now() / 1000),
        userId: event.userId,
        metadata: event.metadata,
      });
      succeeded++;

      // Rate limit: slight delay between calls
      if (succeeded % 50 === 0) {
        await new Promise(r => setTimeout(r, 500));
      }
    } catch (error) {
      failed++;
      console.error(`Failed to track event for ${event.userId}:`, error);
    }
  }

  return { succeeded, failed };
}
```
