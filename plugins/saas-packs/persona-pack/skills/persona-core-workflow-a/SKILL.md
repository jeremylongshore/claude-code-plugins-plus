---
name: persona-core-workflow-a
description: |
  Build a complete KYC verification flow with Persona inquiries and embedded UI.
  Use when implementing identity verification, building KYC onboarding,
  or integrating Persona's hosted flow into your application.
  Trigger with phrases like "persona KYC flow", "identity verification",
  "persona inquiry workflow", "onboarding verification".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, kyc, verification, onboarding]
compatible-with: claude-code, codex, openclaw
---

# Persona Core Workflow A — KYC Inquiry Flow

## Overview
Build a complete KYC onboarding flow: create an inquiry from a template, embed the Persona verification UI in your web app, handle completion callbacks, and store verification results.

## Prerequisites
- Completed `persona-install-auth` setup
- Inquiry Template configured in Persona Dashboard
- Web application with a frontend (React, HTML, etc.)

## Instructions

### Step 1: Backend — Create Inquiry Endpoint
```typescript
// server.ts — Express endpoint to create inquiries
import express from 'express';
import axios from 'axios';

const app = express();
app.use(express.json());

const persona = axios.create({
  baseURL: 'https://withpersona.com/api/v1',
  headers: {
    'Authorization': `Bearer ${process.env.PERSONA_API_KEY}`,
    'Persona-Version': '2023-01-05',
  },
});

app.post('/api/verify', async (req, res) => {
  const { userId, email } = req.body;

  const { data } = await persona.post('/inquiries', {
    data: {
      attributes: {
        'inquiry-template-id': process.env.PERSONA_TEMPLATE_ID,
        'reference-id': userId,
        'fields': {
          'email-address': { type: 'string', value: email },
        },
      },
    },
  });

  res.json({
    inquiryId: data.data.id,
    sessionToken: data.data.attributes['session-token'],
  });
});
```

### Step 2: Frontend — Embed Persona Flow
```html
<!-- Include Persona's JavaScript SDK -->
<script src="https://cdn.withpersona.com/dist/persona-v5.0.0.js"></script>

<button id="verify-btn">Verify Identity</button>

<script>
document.getElementById('verify-btn').addEventListener('click', async () => {
  // Get inquiry from your backend
  const resp = await fetch('/api/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ userId: 'user-123', email: 'alice@example.com' }),
  });
  const { inquiryId, sessionToken } = await resp.json();

  // Launch Persona embedded flow
  const client = new Persona.Client({
    inquiryId,
    sessionToken,
    onComplete: ({ inquiryId, status }) => {
      console.log(`Verification ${status} for inquiry ${inquiryId}`);
      // Notify your backend
      fetch(`/api/verify/${inquiryId}/complete`, { method: 'POST' });
    },
    onCancel: ({ inquiryId }) => {
      console.log('User cancelled verification');
    },
    onError: (error) => {
      console.error('Persona error:', error);
    },
  });

  client.open();
});
</script>
```

### Step 3: Backend — Handle Completion
```typescript
app.post('/api/verify/:inquiryId/complete', async (req, res) => {
  const { inquiryId } = req.params;

  // Fetch the completed inquiry from Persona
  const { data } = await persona.get(`/inquiries/${inquiryId}`);
  const attrs = data.data.attributes;

  const result = {
    inquiryId,
    status: attrs.status,                    // completed, approved, declined
    referenceId: attrs['reference-id'],      // your user ID
    createdAt: attrs['created-at'],
    completedAt: attrs['completed-at'],
  };

  // Store in your database
  await db.users.update(result.referenceId, {
    kycStatus: result.status,
    kycInquiryId: result.inquiryId,
    kycCompletedAt: result.completedAt,
  });

  res.json({ status: result.status });
});
```

### Step 4: Resume Incomplete Inquiries
```typescript
app.get('/api/verify/resume/:userId', async (req, res) => {
  // Find existing incomplete inquiry for this user
  const { data } = await persona.get('/inquiries', {
    params: {
      'filter[reference-id]': req.params.userId,
      'filter[status]': 'created',
      'page[size]': 1,
    },
  });

  if (data.data.length > 0) {
    const inquiry = data.data[0];
    // Resume the existing inquiry instead of creating a new one
    const resumeResp = await persona.post(`/inquiries/${inquiry.id}/resume`);
    res.json({
      inquiryId: inquiry.id,
      sessionToken: resumeResp.data.data.attributes['session-token'],
    });
  } else {
    res.json({ message: 'No pending inquiry' });
  }
});
```

## Output
- Backend endpoint creating inquiries from templates
- Embedded Persona verification UI in web app
- Completion callback storing verification results
- Resume flow for incomplete verifications

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Invalid template` | Wrong template ID | Verify `itmpl_*` in Dashboard |
| SDK not loading | CSP blocking CDN | Add `cdn.withpersona.com` to CSP |
| `onComplete` not firing | User abandoned flow | Use `onCancel` handler |
| Stale session token | Token expired | Create new inquiry or resume |

## Resources
- [Inquiries Overview](https://docs.withpersona.com/inquiries)
- [Embedded Flow Integration](https://docs.withpersona.com/api-quickstart-tutorial)
- [Resume Inquiry](https://docs.withpersona.com/accessing-inquiry-status)

## Next Steps
- Add verification checks: `persona-core-workflow-b`
- Set up webhooks: `persona-webhooks-events`
