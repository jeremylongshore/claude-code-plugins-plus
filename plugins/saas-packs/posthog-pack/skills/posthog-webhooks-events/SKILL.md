---
name: posthog-webhooks-events
description: |
  Implement PostHog webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling PostHog event notifications securely.
  Trigger with phrases like "posthog webhook", "posthog events",
  "posthog webhook signature", "handle posthog events", "posthog notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# PostHog Webhooks & Events

## Overview
Handle PostHog webhooks triggered by Actions and event-based alerts. PostHog fires webhooks when defined Actions match incoming events, allowing you to send notifications, update external systems, or trigger workflows based on user behavior patterns detected in your product analytics.

## Prerequisites
- PostHog project with API access (cloud or self-hosted)
- PostHog project API key and personal API key
- HTTPS endpoint for receiving webhook deliveries
- Actions configured in PostHog dashboard

## Webhook Event Types

| Event Source | Trigger | Payload |
|-------------|---------|---------|
| Action webhook | Action matches event | Event properties, person data |
| Zapier integration | Action fires | Structured action data |
| HogQL alert | Query threshold exceeded | Alert details, query results |
| Feature flag change | Flag toggled | Flag key, rollout percentage |
| Export completed | Data export finishes | Export URL, row count |

## Instructions

### Step 1: Create an Action with Webhook
```bash
# Create an Action via API that fires a webhook
curl -X POST https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/actions/ \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "User Signed Up",
    "steps": [{"event": "$autocapture", "url_matching": "signup/complete"}],
    "post_to_slack": false
  }'
```

### Step 2: Configure Webhook Endpoint
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/webhooks/posthog", async (req, res) => {
  const { event, person, properties, timestamp } = req.body;
  res.status(200).json({ received: true });

  await handlePostHogAction(event, person, properties);
});

async function handlePostHogAction(event: string, person: any, properties: any) {
  switch (event) {
    case "user_signed_up":
      await onUserSignup(person, properties);
      break;
    case "subscription_upgraded":
      await onSubscriptionUpgrade(person, properties);
      break;
    case "feature_activated":
      await onFeatureActivated(person, properties);
      break;
    default:
      console.log(`PostHog action: ${event}`);
  }
}
```

### Step 3: Process User Events
```typescript
async function onUserSignup(person: any, properties: any) {
  const { distinct_id, $set } = person;
  const { $browser, $os, $referrer, utm_source } = properties;

  // Sync to CRM
  await crmClient.createContact({
    email: $set?.email,
    source: utm_source || $referrer,
    browser: $browser,
    os: $os,
    signupDate: new Date(),
  });

  // Send welcome Slack notification
  await slackNotify("#signups", {
    text: `New signup: ${$set?.email} via ${utm_source || "direct"}`,
  });
}

async function onSubscriptionUpgrade(person: any, properties: any) {
  const { plan, mrr, previous_plan } = properties;

  await revenueTracker.recordUpgrade({
    userId: person.distinct_id,
    fromPlan: previous_plan,
    toPlan: plan,
    mrr,
  });
}
```

### Step 4: Query Events via API
```typescript
async function queryRecentEvents(eventName: string, days: number = 7) {
  const response = await fetch(
    `https://app.posthog.com/api/projects/${process.env.POSTHOG_PROJECT_ID}/events/?event=${eventName}&after=-${days}d`,
    {
      headers: { "Authorization": `Bearer ${process.env.POSTHOG_PERSONAL_API_KEY}` },
    }
  );

  const data = await response.json();
  return data.results;
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Action not matched | Test Action with debug mode in PostHog |
| Missing person data | Anonymous user | Ensure `posthog.identify()` called first |
| Duplicate events | Action matches multiple | Refine Action event/URL filters |
| Rate limited | Too many API calls | Use batch endpoints for queries |

## Examples

### Track Feature Adoption
```typescript
async function onFeatureActivated(person: any, properties: any) {
  const { feature_name, $current_url } = properties;

  await analyticsDb.trackAdoption({
    userId: person.distinct_id,
    feature: feature_name,
    activatedAt: new Date(),
    context: $current_url,
  });
}
```

## Resources
- [PostHog Webhooks](https://posthog.com/docs/webhooks)
- [PostHog Actions](https://posthog.com/docs/data/actions)
- [PostHog API Reference](https://posthog.com/docs/api)

## Next Steps
For deployment setup, see `posthog-deploy-integration`.
