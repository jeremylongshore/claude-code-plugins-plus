---
name: mindtickle-webhooks-events
description: 'Webhooks Events for MindTickle.

  Trigger: "mindtickle webhooks events".

  '
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle Webhooks & Events

## Overview

MindTickle emits webhook events as sales reps progress through enablement programs, complete courses, submit quizzes, and are provisioned or deprovisioned from the platform. These events enable integrations such as pushing completion certificates to an LMS, syncing learner progress to Salesforce rep profiles, triggering manager alerts when quiz scores fall below threshold, and automating user lifecycle management with your IdP. All payloads are HMAC-signed JSON scoped to your company, delivered over HTTPS.

## Prerequisites

- MindTickle admin access with API & Webhooks permissions enabled
- Webhook endpoint URL accessible over HTTPS (TLS 1.2+)
- Company-scoped signing secret from MindTickle Admin > Integrations (`MINDTICKLE_WEBHOOK_SECRET`)
- Express.js with raw body parsing for HMAC verification

## Webhook Registration

```typescript
import axios from "axios";

const res = await axios.post(
  "https://api.mindtickle.com/v2/webhooks",
  {
    url: "https://your-app.com/webhooks/mindtickle",
    events: ["course.completed", "quiz.submitted", "user.provisioned",
             "user.deprovisioned", "module.progress"],
    companyId: process.env.MINDTICKLE_COMPANY_ID,
  },
  { headers: { Authorization: `Bearer ${process.env.MINDTICKLE_API_TOKEN}`,
               "Content-Type": "application/json" } }
);
console.log("Webhook ID:", res.data.webhookId);
```

## Signature Verification

```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyMindTickleSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-mt-webhook-signature"] as string;
  const timestamp = req.headers["x-mt-webhook-timestamp"] as string;
  if (!signature || !timestamp) return res.status(401).send("Missing signature");

  const signedPayload = `${timestamp}:${(req as any).rawBody}`;
  const expected = crypto
    .createHmac("sha256", process.env.MINDTICKLE_WEBHOOK_SECRET!)
    .update(signedPayload)
    .digest("hex");

  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(403).send("Invalid signature");
  }
  next();
}
```

## Event Handler

```typescript
app.post("/webhooks/mindtickle", verifyMindTickleSignature, (req, res) => {
  const { event, data, companyId } = req.body;

  switch (event) {
    case "course.completed":
      console.log(`${data.userId} completed "${data.courseName}" — score: ${data.score}%`);
      break;
    case "quiz.submitted":
      console.log(`Quiz "${data.quizName}" by ${data.userId}: ${data.score}/${data.maxScore}`);
      break;
    case "user.provisioned":
      console.log(`User provisioned: ${data.email}, role: ${data.role}, team: ${data.teamId}`);
      break;
    case "user.deprovisioned":
      console.log(`User removed: ${data.userId}, reason: ${data.reason}`);
      break;
    case "module.progress":
      console.log(`${data.userId} at ${data.progressPct}% in module "${data.moduleName}"`);
      break;
    default:
      console.warn(`Unhandled event: ${event}`);
  }
  res.status(200).json({ received: true });
});
```

## Event Types

| Event | Payload Fields | Use Case |
|---|---|---|
| `course.completed` | `userId`, `courseName`, `courseId`, `score`, `completedAt` | Push certificates to LMS or update Salesforce training status |
| `quiz.submitted` | `userId`, `quizName`, `quizId`, `score`, `maxScore`, `passed` | Flag low-scoring reps for coaching follow-up |
| `user.provisioned` | `userId`, `email`, `role`, `teamId`, `provisionedBy` | Sync new hires to enablement programs automatically |
| `user.deprovisioned` | `userId`, `email`, `reason`, `deprovisionedAt` | Revoke access in downstream systems and archive data |
| `module.progress` | `userId`, `moduleName`, `moduleId`, `progressPct`, `timeSpentSec` | Build real-time leaderboards and progress dashboards |
| `certification.expired` | `userId`, `certName`, `expiredAt`, `renewalDeadline` | Trigger re-certification workflow in IdP |

## Retry & Idempotency

```typescript
const processed = new Set<string>();

function ensureIdempotent(req: Request, res: Response, next: NextFunction) {
  const eventId = req.headers["x-mt-event-id"] as string;
  if (processed.has(eventId)) {
    return res.status(200).json({ duplicate: true });
  }
  processed.add(eventId);
  next();
}
// MindTickle retries up to 4 times with linear backoff (5 min, 15 min, 60 min, 6 hours).
// After 24 hours of failures, the webhook is suspended and an admin email is sent.
```

## Error Handling

| Issue | Cause | Fix |
|---|---|---|
| 401 on all deliveries | Company-scoped secret rotated by admin | Re-copy secret from Admin > Integrations and redeploy |
| `user.provisioned` not firing | Webhook not subscribed to SCIM events | Add `user.provisioned` to the events array in subscription |
| Duplicate `course.completed` | Learner retook course, triggered redelivery | Deduplicate on `x-mt-event-id` header |
| Payload missing `score` field | Quiz configured as ungraded practice | Check `data.quizType` — practice quizzes omit scoring fields |
| Webhook suspended | Endpoint down for 24+ hours | Fix endpoint, then re-activate via `PATCH /v2/webhooks/{id}` |

## Resources

- [MindTickle Integrations Platform](https://www.mindtickle.com/platform/integrations/)

## Next Steps

See `mindtickle-security-basics`.
