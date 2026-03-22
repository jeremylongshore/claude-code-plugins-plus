---
name: hootsuite-sdk-patterns
description: |
  Apply production-ready Hootsuite SDK patterns for TypeScript and Python.
  Use when implementing Hootsuite integrations, refactoring SDK usage,
  or establishing team coding standards for Hootsuite.
  Trigger with phrases like "hootsuite SDK patterns", "hootsuite best practices",
  "hootsuite code patterns", "idiomatic hootsuite".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hootsuite, social-media]
compatible-with: claude-code
---

# Hootsuite SDK Patterns

## Overview

Production patterns for Hootsuite REST API: typed client, token management, scheduling helpers, and Python integration.

## Instructions

### Step 1: Typed API Client

```typescript
// src/hootsuite/types.ts
interface SocialProfile {
  id: string;
  type: 'TWITTER' | 'FACEBOOK' | 'INSTAGRAM' | 'LINKEDIN' | 'PINTEREST' | 'YOUTUBE' | 'TIKTOK';
  socialNetworkUsername: string;
  socialNetworkId: string;
}

interface ScheduledMessage {
  id: string;
  text: string;
  state: 'SCHEDULED' | 'SENT' | 'FAILED' | 'REJECTED';
  socialProfileIds: string[];
  scheduledSendTime: string;
  sentAt?: string;
  mediaUrls?: Array<{ id: string }>;
}

interface HootsuiteResponse<T> {
  data: T;
}
```

### Step 2: Scheduling Helper with Timezone

```typescript
function scheduleForTimezone(
  hour: number,
  minute: number,
  timezone: string,
  daysFromNow = 0
): Date {
  const date = new Date();
  date.setDate(date.getDate() + daysFromNow);
  const dateStr = date.toISOString().split('T')[0];
  const timeStr = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}:00`;
  return new Date(`${dateStr}T${timeStr}`);
}

// Schedule posts at optimal times per platform
const OPTIMAL_TIMES = {
  TWITTER: { hour: 9, minute: 0 },
  INSTAGRAM: { hour: 11, minute: 0 },
  LINKEDIN: { hour: 7, minute: 30 },
  FACEBOOK: { hour: 13, minute: 0 },
};
```

### Step 3: Python Client

```python
# hootsuite/client.py
import os, requests, time
from dotenv import load_dotenv

load_dotenv()

class HootsuiteClient:
    BASE = 'https://platform.hootsuite.com/v1'

    def __init__(self):
        self.token = os.environ['HOOTSUITE_ACCESS_TOKEN']
        self.headers = {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}

    def get_profiles(self):
        r = requests.get(f'{self.BASE}/socialProfiles', headers=self.headers)
        r.raise_for_status()
        return r.json()['data']

    def schedule_message(self, profile_ids, text, scheduled_time):
        r = requests.post(f'{self.BASE}/messages', headers=self.headers, json={
            'text': text,
            'socialProfileIds': profile_ids,
            'scheduledSendTime': scheduled_time.isoformat(),
        })
        r.raise_for_status()
        return r.json()['data']
```

### Step 4: Cross-Platform Post Formatter

```typescript
function formatPost(text: string, platform: string): string {
  const limits: Record<string, number> = {
    TWITTER: 280, FACEBOOK: 63206, INSTAGRAM: 2200, LINKEDIN: 3000, TIKTOK: 2200,
  };
  const limit = limits[platform] || 2200;
  return text.length > limit ? text.substring(0, limit - 3) + '...' : text;
}
```

## Output

- Typed API client with token refresh
- Timezone-aware scheduling helpers
- Python client class
- Cross-platform post formatting

## Resources

- [Hootsuite REST API](https://apidocs.hootsuite.com/docs/api/index.html)
- [Message Scheduling](https://developer.hootsuite.com/docs/message-scheduling)

## Next Steps

Apply patterns in `hootsuite-core-workflow-a` for publishing.
