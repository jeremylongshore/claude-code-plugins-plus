---
name: podium-hello-world
description: |
  Podium hello world — business messaging and communication platform integration.
  Use when working with Podium API for messaging, reviews, or payments.
  Trigger with phrases like "podium hello world", "podium-hello-world".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, podium, messaging, reviews, payments]
compatible-with: claude-code, codex, openclaw
---

# Podium Hello World

## Overview
Send your first Podium message, list contacts, and check location details using the Podium REST API.

## Prerequisites
- Completed `podium-install-auth` setup with valid access token
- A Podium location ID

## Instructions

### Step 1: List Locations
```typescript
const { data } = await podium.get('/locations');
for (const loc of data.data) {
  console.log(`Location: ${loc.attributes.name} (ID: ${loc.id})`);
}
```

### Step 2: List Contacts
```typescript
const locationId = 'loc_xxxxx';
const { data } = await podium.get(`/locations/${locationId}/contacts`);
for (const contact of data.data) {
  console.log(`  ${contact.attributes.name} — ${contact.attributes.phone}`);
}
```

### Step 3: Send a Message
```typescript
// Messages are sent via the Podium platform to the customer's phone
const { data } = await podium.post(`/locations/${locationId}/messages`, {
  data: {
    attributes: {
      body: 'Hello from our integration! How can we help?',
      'contact-phone': '+15551234567',
    },
  },
});
console.log(`Message sent: ${data.data.id}`);
```

## Output
- Listed locations with IDs
- Retrieved contacts for a location
- Sent a test message via Podium

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `404 Location not found` | Wrong location ID | List locations first to get valid IDs |
| `422 Invalid phone` | Bad phone format | Use E.164 format: +15551234567 |
| `403 Forbidden` | Missing scope | Add `messages.write` scope to OAuth app |

## Resources
- [Podium API Reference](https://docs.podium.com/reference)
- [Sync Messages](https://docs.podium.com/docs/sync-messages-from-podium-conversations)

## Next Steps
Build messaging workflow: `podium-core-workflow-a`
