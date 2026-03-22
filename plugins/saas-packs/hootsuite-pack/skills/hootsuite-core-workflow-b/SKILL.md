---
name: hootsuite-core-workflow-b
description: |
  Execute Hootsuite secondary workflow: Core Workflow B.
  Use when implementing secondary use case,
  or complementing primary workflow.
  Trigger with phrases like "hootsuite secondary workflow",
  "secondary task with hootsuite".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media, analytics]
compatible-with: claude-code
---

# Hootsuite Analytics & URL Shortening

## Overview

Retrieve social media analytics and use Ow.ly URL shortening via the Hootsuite API. Track post performance, engagement metrics, and click-through rates.

## Prerequisites

- Completed `hootsuite-install-auth` setup
- Published posts with engagement data

## Instructions

### Step 1: Get Organization Analytics

```typescript
import 'dotenv/config';
const TOKEN = process.env.HOOTSUITE_ACCESS_TOKEN!;
const BASE = 'https://platform.hootsuite.com/v1';

async function getOrganization() {
  const response = await fetch(`${BASE}/me/organizations`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const { data } = await response.json();
  return data[0]; // Primary organization
}
```

### Step 2: Shorten URLs with Ow.ly

```typescript
async function shortenUrl(fullUrl: string) {
  const response = await fetch(`${BASE}/shorteners/owly`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ url: fullUrl }),
  });
  const { data } = await response.json();
  console.log(`${fullUrl} → ${data.shortUrl}`);
  return data;
}

// Shorten multiple URLs
async function shortenBatch(urls: string[]) {
  return Promise.all(urls.map(url => shortenUrl(url)));
}
```

### Step 3: Retrieve Message Analytics

```typescript
async function getMessageAnalytics(messageId: string) {
  const response = await fetch(`${BASE}/messages/${messageId}`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const { data } = await response.json();
  console.log(`Message: ${data.text?.substring(0, 50)}...`);
  console.log(`State: ${data.state}`);
  console.log(`Sent: ${data.sentAt}`);
  return data;
}

// List sent messages and their performance
async function getSentMessages(profileId: string) {
  const response = await fetch(
    `${BASE}/messages?socialProfileIds=${profileId}&state=SENT&limit=20`,
    { headers: { 'Authorization': `Bearer ${TOKEN}` } },
  );
  const { data } = await response.json();
  for (const msg of data) {
    console.log(`[${msg.sentAt}] ${msg.text?.substring(0, 60)}`);
  }
  return data;
}
```

### Step 4: Social Profile Metrics

```typescript
async function getProfileDetails(profileId: string) {
  const response = await fetch(`${BASE}/socialProfiles/${profileId}`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const { data } = await response.json();
  console.log(`Profile: @${data.socialNetworkUsername}`);
  console.log(`Network: ${data.type}`);
  console.log(`ID: ${data.id}`);
  return data;
}
```

## Output

- Organization analytics retrieved
- URLs shortened via Ow.ly
- Message performance data
- Social profile metrics

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `404` on message | Message deleted or wrong ID | Verify message ID |
| No analytics data | Post too recent | Wait for engagement data (24-48h) |
| Ow.ly rate limited | Too many shortening requests | Batch and throttle |

## Resources

- [Hootsuite API Reference](https://apidocs.hootsuite.com/docs/api/index.html)
- [URL Shortening](https://developer.hootsuite.com/docs/api-overview)
- [Analytics Guide](https://help.hootsuite.com/hc/en-us/articles/1260804306749)

## Next Steps

For common errors, see `hootsuite-common-errors`.
