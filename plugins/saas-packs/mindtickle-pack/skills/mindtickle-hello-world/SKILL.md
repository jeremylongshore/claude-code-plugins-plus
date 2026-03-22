---
name: mindtickle-hello-world
description: |
  Create a minimal working MindTickle example.
  Trigger: "mindtickle hello world", "mindtickle example", "test mindtickle".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle Hello World

## Overview
Minimal working examples demonstrating core MindTickle API functionality.

## Instructions

### Step 1: Create Training Module
```typescript
const module = await client.modules.create({
  title: 'Q1 Product Update Training',
  type: 'course',
  description: 'Learn about new product features for Q1',
  tags: ['product', 'q1-2026'],
  content: [
    { type: 'video', url: 'https://videos.example.com/q1-update.mp4', title: 'Overview' },
    { type: 'quiz', questions: [
      { text: 'What is the key new feature?', type: 'multiple_choice',
        options: ['Feature A', 'Feature B', 'Feature C'], correct: 0 }
    ]}
  ]
});
console.log(`Module created: ${module.id}`);
```

### Step 2: Assign to Sales Reps
```typescript
await client.assignments.create({
  module_id: module.id,
  assignees: { type: 'team', team_ids: ['team_sales_west', 'team_sales_east'] },
  due_date: '2026-04-15',
  reminder: { enabled: true, days_before: [7, 3, 1] }
});
```

### Step 3: Track Completion
```typescript
const progress = await client.analytics.moduleProgress(module.id);
progress.users.forEach(u =>
  console.log(`${u.name}: ${u.completion}% | Score: ${u.quiz_score || 'N/A'}`)
);
console.log(`Overall: ${progress.completion_rate}% complete`);
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Auth error | Invalid credentials | Check MINDTICKLE_API_KEY |
| Not found | Invalid endpoint | Verify API URL |
| Rate limit | Too many requests | Implement backoff |

## Resources
- [MindTickle API Docs](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-local-dev-loop`.
