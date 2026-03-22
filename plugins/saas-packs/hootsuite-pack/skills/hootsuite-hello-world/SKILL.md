---
name: hootsuite-hello-world
description: |
  Create a minimal working Hootsuite example.
  Use when starting a new Hootsuite integration, testing your setup,
  or learning basic Hootsuite API patterns.
  Trigger with phrases like "hootsuite hello world", "hootsuite example",
  "hootsuite quick start", "simple hootsuite code".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite Hello World

## Overview

List your social media profiles and schedule a post using the Hootsuite REST API. The API base URL is `https://platform.hootsuite.com/v1/`.

## Prerequisites

- Completed `hootsuite-install-auth` setup
- Valid access token
- At least one social profile connected in Hootsuite

## Instructions

### Step 1: List Social Profiles

```typescript
// hello-hootsuite.ts
import 'dotenv/config';

const TOKEN = process.env.HOOTSUITE_ACCESS_TOKEN!;
const BASE = 'https://platform.hootsuite.com/v1';

async function listProfiles() {
  const response = await fetch(`${BASE}/socialProfiles`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const { data } = await response.json();

  for (const profile of data) {
    console.log(`${profile.type}: @${profile.socialNetworkUsername} (ID: ${profile.id})`);
  }
  return data;
}

listProfiles().catch(console.error);
```

### Step 2: Schedule a Post

```typescript
async function schedulePost(socialProfileId: string, text: string, scheduledAt: Date) {
  const response = await fetch(`${BASE}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      socialProfileIds: [socialProfileId],
      scheduledSendTime: scheduledAt.toISOString(),
      emailNotification: false,
    }),
  });

  const result = await response.json();
  console.log('Scheduled message ID:', result.data[0]?.id);
  console.log('State:', result.data[0]?.state);
  console.log('Scheduled for:', result.data[0]?.scheduledSendTime);
  return result;
}

// Schedule a post 1 hour from now
const profiles = await listProfiles();
if (profiles.length > 0) {
  const oneHourLater = new Date(Date.now() + 3600000);
  await schedulePost(profiles[0].id, 'Hello from the Hootsuite API!', oneHourLater);
}
```

### Step 3: List Scheduled Messages

```typescript
async function listMessages() {
  const response = await fetch(`${BASE}/messages?state=SCHEDULED&limit=10`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const { data } = await response.json();
  for (const msg of data) {
    console.log(`[${msg.state}] ${msg.text?.substring(0, 60)}... → ${msg.scheduledSendTime}`);
  }
}
```

### Step 4: curl Quick Test

```bash
# List profiles
curl -s -H "Authorization: Bearer $HOOTSUITE_ACCESS_TOKEN" \
  https://platform.hootsuite.com/v1/socialProfiles | python3 -m json.tool

# Get current user
curl -s -H "Authorization: Bearer $HOOTSUITE_ACCESS_TOKEN" \
  https://platform.hootsuite.com/v1/me | python3 -m json.tool
```

## Output

- Listed social media profiles with IDs
- Scheduled a post to a social profile
- Retrieved scheduled messages

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Expired token | Refresh token via OAuth flow |
| `403 Forbidden` | Insufficient permissions | Check app scopes |
| `422 Unprocessable` | Invalid profile ID or past date | Verify profile ID and future date |
| No profiles returned | No social accounts connected | Connect accounts in Hootsuite dashboard |

## Resources

- [Messages API](https://developer.hootsuite.com/docs/message-scheduling)
- [Social Profiles API](https://apidocs.hootsuite.com/docs/api/index.html)
- [REST API Reference](https://developer.hootsuite.com/docs/using-rest-apis)

## Next Steps

Proceed to `hootsuite-local-dev-loop` for development workflow.
