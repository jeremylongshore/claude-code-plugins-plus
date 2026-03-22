---
name: canva-hello-world
description: |
  Create a minimal working Canva Connect API example.
  Use when starting a new Canva integration, testing your setup,
  or learning basic Canva REST API patterns.
  Trigger with phrases like "canva hello world", "canva example",
  "canva quick start", "simple canva code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, canva]
compatible-with: claude-code
---

# Canva Hello World

## Overview

Minimal working example: authenticate, get user profile, create a design, and export it as PNG. All via the Canva Connect REST API at `api.canva.com/rest/v1/*`.

## Prerequisites

- Completed `canva-install-auth` — valid OAuth access token
- Scopes enabled: `design:meta:read`, `design:content:write`, `design:content:read`

## Instructions

### Step 1: Create a Reusable API Helper

```typescript
// src/canva/client.ts
const CANVA_BASE = 'https://api.canva.com/rest/v1';

export async function canvaAPI(
  path: string,
  accessToken: string,
  options: RequestInit = {}
): Promise<any> {
  const res = await fetch(`${CANVA_BASE}${path}`, {
    ...options,
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Canva API ${res.status}: ${body}`);
  }

  return res.status === 204 ? null : res.json();
}
```

### Step 2: Get Your User Profile

```typescript
// GET /v1/users/me — no scopes required, rate limit: 10 req/min
const me = await canvaAPI('/users/me', accessToken);
console.log(`User ID: ${me.team_user.user_id}`);
console.log(`Team ID: ${me.team_user.team_id}`);
```

### Step 3: Create a Design

```typescript
// POST /v1/designs — scope: design:content:write, rate limit: 20 req/min
const design = await canvaAPI('/designs', accessToken, {
  method: 'POST',
  body: JSON.stringify({
    design_type: { type: 'preset', name: 'presentation' },
    title: 'Hello Canva API',
  }),
});

console.log(`Design created: ${design.design.id}`);
console.log(`Edit URL: ${design.design.urls.edit_url}`);   // expires in 30 days
console.log(`View URL: ${design.design.urls.view_url}`);   // expires in 30 days
```

### Step 4: Export the Design as PNG

```typescript
// POST /v1/exports — scope: design:content:read, rate limit: 20 req/min
const exportJob = await canvaAPI('/exports', accessToken, {
  method: 'POST',
  body: JSON.stringify({
    design_id: design.design.id,
    format: { type: 'png', transparent_background: false },
  }),
});

// Poll for completion — GET /v1/exports/{jobId}
let job = exportJob.job;
while (job.status === 'in_progress') {
  await new Promise(r => setTimeout(r, 2000));
  const poll = await canvaAPI(`/exports/${job.id}`, accessToken);
  job = poll.job;
}

if (job.status === 'success') {
  console.log('Download URLs (valid 24 hours):');
  job.urls.forEach((url: string, i: number) => console.log(`  Page ${i + 1}: ${url}`));
} else {
  console.error('Export failed:', job.error);
}
```

### Step 5: List Your Designs

```typescript
// GET /v1/designs — scope: design:meta:read, rate limit: 100 req/min
const designs = await canvaAPI('/designs?ownership=owned&limit=5', accessToken);

for (const d of designs.items) {
  console.log(`${d.title} (${d.id}) — ${d.page_count} pages`);
}
```

## Complete Example

```typescript
import { canvaAPI } from './canva/client';

async function main() {
  const token = process.env.CANVA_ACCESS_TOKEN!;

  // 1. Verify connection
  const me = await canvaAPI('/users/me', token);
  console.log(`Connected as user ${me.team_user.user_id}`);

  // 2. Create a design
  const { design } = await canvaAPI('/designs', token, {
    method: 'POST',
    body: JSON.stringify({
      design_type: { type: 'custom', width: 1080, height: 1080 },
      title: 'My First API Design',
    }),
  });
  console.log(`Created: ${design.id} — edit at ${design.urls.edit_url}`);

  // 3. Export as PDF
  const { job } = await canvaAPI('/exports', token, {
    method: 'POST',
    body: JSON.stringify({
      design_id: design.id,
      format: { type: 'pdf' },
    }),
  });
  console.log(`Export job ${job.id} started — status: ${job.status}`);
}

main().catch(console.error);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Expired or invalid token | Refresh token via `/v1/oauth/token` |
| 403 Forbidden | Missing required scope | Enable scope in integration settings |
| 404 Not Found | Design doesn't exist or no access | Verify design ID and ownership |
| 429 Too Many Requests | Rate limit exceeded | Respect `Retry-After` header |

## Resources

- [Canva Connect API Reference](https://www.canva.dev/docs/connect/api-reference/)
- [Designs API](https://www.canva.dev/docs/connect/api-reference/designs/)
- [Exports API](https://www.canva.dev/docs/connect/api-reference/exports/)

## Next Steps

Proceed to `canva-local-dev-loop` for development workflow setup.
