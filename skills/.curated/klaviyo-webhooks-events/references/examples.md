# Klaviyo Webhooks — Worked Examples

Concrete end-to-end scenarios that build on the full walkthrough in
[implementation.md](implementation.md). Use these to see how the individual
steps combine in real integrations, and how to exercise the endpoint locally
before pointing production traffic at it.

## Example 1: Sync new profiles into your own database

Subscribe to `profile.created` and `profile.updated`, then upsert each profile
into your users table. This is the most common webhook use case — keeping your
system-of-record in step with Klaviyo profile changes in near real time.

1. Register the subscription (Step 1 of the walkthrough) with both topics:

```typescript
webhookTopics: {
  data: [
    { type: 'webhook-topic', id: 'profile.created' },
    { type: 'webhook-topic', id: 'profile.updated' },
  ],
},
```

1. The router (Step 4) already maps both topics to upsert/update handlers. A
   `profile.created` payload arrives as:

```json
{
  "type": "profile.created",
  "data": {
    "id": "01H8XVZ...",
    "attributes": { "email": "jane@example.com", "firstName": "Jane" }
  }
}
```

1. `routeWebhookEvent` dispatches it to the `profile.created` handler, which
   upserts `{ email, firstName, klaviyoProfileId }` into `db.users`.

## Example 2: Track campaign sends into analytics

Subscribe to `campaign.sent`. The handler in Step 4 forwards each send to your
analytics pipeline:

```typescript
'campaign.sent': async (data) => {
  console.log(`Campaign sent: ${data.attributes.name}`);
  await analytics.track('campaign_sent', { campaignId: data.id });
},
```

Because the endpoint returns `200` immediately after the router resolves and the
event ID is recorded in Redis (Step 5), a Klaviyo retry of the same `campaign.sent`
event is short-circuited by the idempotency check and never double-counted.

## Testing Webhooks Locally

```bash
# 1. Start your app
npm run dev  # localhost:3000

# 2. Expose via ngrok
ngrok http 3000

# 3. Register ngrok URL as webhook endpoint in Klaviyo
# https://abc123.ngrok.io/webhooks/klaviyo

# 4. Trigger an event (e.g., create a profile) and watch your logs
```

A correctly wired endpoint logs the received topic, returns `200` with
`{ received: true }`, and (on a replayed event) returns `{ status: 'already_processed' }`.
An invalid signature returns `401` with `{ error: 'Invalid signature' }` — the
fastest way to confirm your signing secret matches the value from the
`createWebhook` response.
