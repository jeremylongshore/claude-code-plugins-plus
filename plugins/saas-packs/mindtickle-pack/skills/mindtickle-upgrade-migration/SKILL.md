---
name: mindtickle-upgrade-migration
description: |
  Upgrade Migration for MindTickle.
  Trigger: "mindtickle upgrade migration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Upgrade & Migration

## Overview

MindTickle is a sales enablement and readiness platform with APIs for managing courses, quizzes, user progress, and coaching sessions. The API exposes endpoints for content management, learner analytics, and CRM integration. Tracking API changes is essential because MindTickle evolves its content schema (course structures, quiz question types, scoring rubrics), user progress tracking fields, and SSO/SCIM provisioning models — breaking integrations that sync training completion data to Salesforce or automate onboarding workflows.

## Version Detection

```typescript
const MINDTICKLE_BASE = "https://api.mindtickle.com/v2";

async function detectMindTickleVersion(apiKey: string): Promise<void> {
  const res = await fetch(`${MINDTICKLE_BASE}/users`, {
    headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
  });
  const version = res.headers.get("x-mt-api-version") ?? "v2";
  console.log(`MindTickle API version: ${version}`);

  // Check for deprecated course fields
  const coursesRes = await fetch(`${MINDTICKLE_BASE}/courses?limit=1`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  const data = await coursesRes.json();
  const knownFields = ["id", "title", "modules", "status", "created_at", "assigned_users"];
  if (data.courses?.[0]) {
    const actual = Object.keys(data.courses[0]);
    const newFields = actual.filter((f) => !knownFields.includes(f));
    if (newFields.length) console.log(`New course fields: ${newFields.join(", ")}`);
  }
}
```

## Migration Checklist

- [ ] Review MindTickle release notes for API schema changes
- [ ] Audit codebase for hardcoded course status enums (`draft`, `published`, `archived`)
- [ ] Verify quiz question type support — new types may require parser updates
- [ ] Check user progress response for new completion metric fields
- [ ] Update SCIM provisioning payload if user attribute schema changed
- [ ] Test coaching session API for new rubric scoring fields
- [ ] Validate CRM sync field mappings (Salesforce/HubSpot) after API update
- [ ] Check if module ordering mechanism changed (position vs. sort_order)
- [ ] Update webhook handlers for course completion and quiz score events
- [ ] Run learner analytics export to verify report format compatibility

## Schema Migration

```typescript
// MindTickle course progress: flat completion → structured module-level tracking
interface OldProgress {
  user_id: string;
  course_id: string;
  completed: boolean;
  score: number;
  completed_at?: string;
}

interface NewProgress {
  user_id: string;
  course_id: string;
  status: "not_started" | "in_progress" | "completed" | "expired";
  overall_score: number;
  modules: Array<{
    module_id: string;
    status: string;
    score: number;
    attempts: number;
    time_spent_seconds: number;
  }>;
  certifications: Array<{ cert_id: string; issued_at: string; expires_at?: string }>;
  completed_at?: string;
}

function migrateProgress(old: OldProgress): NewProgress {
  return {
    user_id: old.user_id,
    course_id: old.course_id,
    status: old.completed ? "completed" : "not_started",
    overall_score: old.score,
    modules: [],
    certifications: [],
    completed_at: old.completed_at,
  };
}
```

## Rollback Strategy

```typescript
class MindTickleClient {
  private apiVersion: "v1" | "v2";

  constructor(private apiKey: string, version: "v1" | "v2" = "v2") {
    this.apiVersion = version;
  }

  async getCourses(limit = 50): Promise<any> {
    try {
      const res = await fetch(`https://api.mindtickle.com/${this.apiVersion}/courses?limit=${limit}`, {
        headers: { Authorization: `Bearer ${this.apiKey}` },
      });
      if (!res.ok) throw new Error(`MindTickle ${res.status}`);
      return await res.json();
    } catch (err) {
      if (this.apiVersion === "v2") {
        console.warn("Falling back to MindTickle API v1");
        this.apiVersion = "v1";
        return this.getCourses(limit);
      }
      throw err;
    }
  }
}
```

## Error Handling

| Migration Issue | Symptom | Fix |
|----------------|---------|-----|
| Course status enum expanded | `400` creating course with unrecognized status value | Fetch valid statuses from `/courses/statuses` endpoint |
| Quiz question type unsupported | Quiz import fails with `unknown_question_type` | Add parser support for new question types (drag-drop, hotspot) |
| SCIM attribute renamed | User provisioning fails with `invalid attribute` | Update SCIM payload to match current user schema from `/schemas` |
| Progress field restructured | Code crashes accessing `progress.completed` (now `progress.status`) | Update to check `status === "completed"` instead of boolean |
| Webhook signature algorithm changed | Webhook verification fails on all events | Update HMAC verification to use new algorithm from MindTickle docs |

## Resources

- [MindTickle Integrations](https://www.mindtickle.com/platform/integrations/)
- [MindTickle API Documentation](https://developers.mindtickle.com/)

## Next Steps

For CI pipeline integration, see `mindtickle-ci-integration`.
