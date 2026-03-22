---
name: hootsuite-core-workflow-a
description: |
  Execute Hootsuite primary workflow: Core Workflow A.
  Use when implementing primary use case,
  building main features, or core integration tasks.
  Trigger with phrases like "hootsuite main workflow",
  "primary task with hootsuite".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media, publishing]
compatible-with: claude-code
---

# Hootsuite Publishing — Schedule Posts with Media

## Overview

Schedule social media posts with images and videos using the Hootsuite REST API. The publishing workflow involves: uploading media to get a media ID, then scheduling a message referencing that media.

## Prerequisites

- Completed `hootsuite-install-auth` setup
- Social profiles connected in Hootsuite
- Media files (images/videos) for upload

## Instructions

### Step 1: Upload Media

```typescript
// publishing.ts
import 'dotenv/config';
import fs from 'fs';

const TOKEN = process.env.HOOTSUITE_ACCESS_TOKEN!;
const BASE = 'https://platform.hootsuite.com/v1';

// Step 1a: Create upload URL
async function createMediaUpload(sizeBytes: number, mimeType: string) {
  const response = await fetch(`${BASE}/media`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ sizeBytes, mimeType }),
  });
  const { data } = await response.json();
  console.log('Upload URL:', data.uploadUrl);
  console.log('Media ID:', data.id);
  return data; // { id, uploadUrl, uploadUrlDurationSeconds }
}

// Step 1b: Upload file to the S3 URL
async function uploadFile(uploadUrl: string, filePath: string, mimeType: string) {
  const fileBuffer = fs.readFileSync(filePath);
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: { 'Content-Type': mimeType },
    body: fileBuffer,
  });
  if (response.status !== 200) throw new Error(`Upload failed: ${response.status}`);
  console.log('File uploaded successfully');
}

// Step 1c: Check media status
async function getMediaStatus(mediaId: string) {
  const response = await fetch(`${BASE}/media/${mediaId}`, {
    headers: { 'Authorization': `Bearer ${TOKEN}` },
  });
  const { data } = await response.json();
  console.log('Media state:', data.state); // PENDING, READY, REJECTED
  return data;
}
```

### Step 2: Schedule Post with Media

```typescript
async function scheduleWithMedia(config: {
  profileIds: string[];
  text: string;
  mediaIds: string[];
  scheduledAt: Date;
}) {
  const response = await fetch(`${BASE}/messages`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text: config.text,
      socialProfileIds: config.profileIds,
      scheduledSendTime: config.scheduledAt.toISOString(),
      mediaUrls: config.mediaIds.map(id => ({ id })),
      emailNotification: false,
    }),
  });

  const result = await response.json();
  for (const msg of result.data) {
    console.log(`Message ${msg.id}: ${msg.state} → ${msg.scheduledSendTime}`);
  }
  return result;
}
```

### Step 3: Complete Publishing Flow

```typescript
async function publishPostWithImage(
  profileId: string,
  text: string,
  imagePath: string,
  scheduledAt: Date
) {
  // 1. Create upload URL
  const stats = fs.statSync(imagePath);
  const mimeType = imagePath.endsWith('.png') ? 'image/png' : 'image/jpeg';
  const media = await createMediaUpload(stats.size, mimeType);

  // 2. Upload file to S3
  await uploadFile(media.uploadUrl, imagePath, mimeType);

  // 3. Wait for media processing
  let status = await getMediaStatus(media.id);
  while (status.state === 'PENDING') {
    await new Promise(r => setTimeout(r, 2000));
    status = await getMediaStatus(media.id);
  }

  if (status.state !== 'READY') {
    throw new Error(`Media rejected: ${status.state}`);
  }

  // 4. Schedule post with media
  return scheduleWithMedia({
    profileIds: [profileId],
    text,
    mediaIds: [media.id],
    scheduledAt,
  });
}
```

### Step 4: Bulk Scheduling

```typescript
interface ScheduledPost {
  text: string;
  profileIds: string[];
  scheduledAt: Date;
  imagePath?: string;
}

async function bulkSchedule(posts: ScheduledPost[]) {
  const results = [];
  for (const post of posts) {
    if (post.imagePath) {
      results.push(await publishPostWithImage(post.profileIds[0], post.text, post.imagePath, post.scheduledAt));
    } else {
      results.push(await scheduleWithMedia({ profileIds: post.profileIds, text: post.text, mediaIds: [], scheduledAt: post.scheduledAt }));
    }
    await new Promise(r => setTimeout(r, 500)); // Rate limit buffer
  }
  return results;
}
```

## Output

- Media uploaded and processed
- Posts scheduled with images across social profiles
- Bulk scheduling support

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Media `REJECTED` | File too large or wrong format | Check size limits per network |
| `422 scheduledSendTime` | Date in the past | Must be future date |
| `413 Payload Too Large` | Image exceeds limit | Compress or resize image |
| Missing profile | Profile disconnected | Reconnect in Hootsuite dashboard |

## Resources

- [Message Scheduling](https://developer.hootsuite.com/docs/message-scheduling)
- [Media Upload](https://developer.hootsuite.com/docs/uploading-media)
- [REST API Reference](https://apidocs.hootsuite.com/docs/api/index.html)

## Next Steps

For analytics, see `hootsuite-core-workflow-b`.
