---
name: mindtickle-core-workflow-a
description: |
  Execute MindTickle primary workflow: Training Content Management.
  Trigger: "mindtickle training content management", "primary mindtickle workflow".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle — Course & Module Management

## Overview

Primary workflow for MindTickle sales readiness integration. Covers end-to-end course
management: creating training modules with mixed content (video, quiz, document),
assigning courses to individuals or teams with due dates and reminders, tracking
completion and quiz scores via the analytics API, and updating modules as content
evolves. Uses the MindTickle REST API with API key authentication. All list endpoints
support cursor-based pagination for large organizations.

## Instructions

### Step 1: Create a Course with Modules

```typescript
const course = await client.courses.create({
  title: 'Q2 Product Launch Readiness',
  description: 'Everything your team needs to sell the new platform tier',
  tags: ['product-launch', 'q2-2026'],
  modules: [
    { title: 'Overview', type: 'video',
      url: 'https://videos.example.com/q2-launch.mp4', duration_min: 12 },
    { title: 'Feature Deep Dive', type: 'document',
      url: 'https://docs.example.com/q2-features.pdf' },
    { title: 'Knowledge Check', type: 'quiz', questions: [
      { text: 'What is the key differentiator?', type: 'multiple_choice',
        options: ['Speed', 'Price', 'Integration'], correct: 2 },
      { text: 'Name one target persona.', type: 'free_text' },
    ]},
  ],
});
console.log(`Course created: ${course.id} with ${course.modules.length} modules`);
```

### Step 2: Assign Learners

```typescript
const assignment = await client.assignments.create({
  course_id: course.id,
  assignees: { type: 'team', team_ids: ['team_sales_west', 'team_sales_east'] },
  due_date: '2026-06-01',
  reminder: { enabled: true, days_before: [7, 3, 1] },
  late_policy: 'allow_completion',
});
console.log(`Assigned to ${assignment.assignee_count} learners`);
```

### Step 3: Track Progress and Scores

```typescript
const progress = await client.analytics.courseProgress(course.id);
progress.users.forEach(u =>
  console.log(`${u.name}: ${u.completion}% | Quiz: ${u.quiz_score ?? 'N/A'}`)
);
console.log(`Overall: ${progress.completion_rate}% | Avg score: ${progress.avg_score}`);
```

### Step 4: Update Module Content

```typescript
await client.modules.update(course.modules[0].id, {
  url: 'https://videos.example.com/q2-launch-v2.mp4',
  duration_min: 15,
});
console.log('Module updated — learners will see new content on next access');
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or missing API key | Verify `X-Api-Key` header value |
| `404 Not Found` | Course or module ID invalid | Confirm IDs from create responses |
| `409 Conflict` | Duplicate course title in org | Use unique title or update existing |
| `422 Validation Error` | Quiz missing correct answer | Ensure every MC question has `correct` index |
| `429 Rate Limited` | Exceeds 60 req/min | Implement retry with `Retry-After` header |

## Output

A successful run creates a course with video, document, and quiz modules, assigns it
to sales teams with reminders, and reports completion rates and average quiz scores.

## Resources

- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)
- [MindTickle API Reference](https://developer.mindtickle.com/docs)

## Next Steps

Continue with `mindtickle-core-workflow-b` for coaching and role-play scenarios.
