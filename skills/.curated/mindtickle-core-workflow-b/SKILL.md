---
name: mindtickle-core-workflow-b
description: 'Execute MindTickle secondary workflow: Rep Performance & Readiness.

  Trigger: "mindtickle rep performance & readiness", "secondary mindtickle workflow".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- mindtickle
- sales
compatibility: Designed for Claude Code
---
# MindTickle — Quiz & Assessment

## Overview

Create quizzes and assessments, grade submissions, and track scores across your sales
enablement programs in MindTickle. Use this workflow when building certification exams,
knowledge checks after training modules, or competency assessments that feed into
rep readiness scores. This is the secondary workflow — for training content and
course management, see `mindtickle-core-workflow-a`.

## Instructions

### Step 1: Create a Quiz with Question Bank

```typescript
const quiz = await client.assessments.create({
  title: 'Q2 Product Knowledge Certification',
  module_id: 'mod_product_q2',
  passing_score: 80,
  time_limit_minutes: 30,
  max_attempts: 2,
  questions: [
    { type: 'multiple_choice', text: 'What is the primary use case for Feature X?',
      options: ['Analytics', 'Automation', 'Security', 'Compliance'],
      correct: 1, points: 10 },
    { type: 'true_false', text: 'Feature Y supports SSO out of the box.',
      correct: true, points: 5 },
    { type: 'open_ended', text: 'Describe how you would position Feature X to a CFO.',
      points: 20, rubric: 'Must mention ROI, time savings, and compliance' },
  ],
});
console.log(`Quiz ${quiz.id} created — ${quiz.questions.length} questions, pass=${quiz.passing_score}%`);
```

### Step 2: Assign Quiz to a Team

```typescript
const assignment = await client.assessments.assign(quiz.id, {
  team_ids: ['team_sales_west', 'team_sales_east'],
  due_date: '2026-04-20',
  reminder_days: [7, 3, 1],
  notify: true,
});
console.log(`Assigned to ${assignment.total_reps} reps, due ${assignment.due_date}`);
```

### Step 3: Grade Submissions and Review Scores

```typescript
const submissions = await client.assessments.submissions(quiz.id, {
  status: 'completed',
  sort: 'score_desc',
});
submissions.items.forEach(s =>
  console.log(`${s.rep_name}: ${s.score}% (${s.passed ? 'PASS' : 'FAIL'}) — attempt ${s.attempt}/${quiz.max_attempts}`)
);
const pending = submissions.items.filter(s => s.pending_review);
for (const sub of pending) {
  await client.assessments.grade(quiz.id, sub.id, {
    question_scores: [{ question_id: 'q3', score: 15, feedback: 'Missed compliance angle' }],
  });
}
```

### Step 4: Export Score Analytics

```typescript
const analytics = await client.assessments.analytics(quiz.id, {
  group_by: 'team',
  metrics: ['avg_score', 'pass_rate', 'avg_completion_time'],
});
analytics.teams.forEach(t =>
  console.log(`${t.team_name}: avg=${t.avg_score}%, pass_rate=${t.pass_rate}%, avg_time=${t.avg_minutes}m`)
);
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Invalid or expired API token | Regenerate token in MindTickle admin |
| `404 Assessment not found` | Wrong quiz ID or deleted assessment | Verify with `client.assessments.list()` |
| `422 Invalid question format` | Missing required fields in question object | Include `type`, `text`, `correct`, and `points` |
| `409 Already submitted` | Rep exceeded max_attempts | Increase `max_attempts` or reset submission |
| `403 Assignment restricted` | Team not in the module's audience | Add team to module audience first |

## Output

A successful workflow creates a timed quiz with mixed question types, assigns it to
sales teams with automated reminders, grades submissions, and produces team-level
analytics showing pass rates, scores, and question difficulty breakdowns.

## Resources

- [MindTickle Platform Integrations](https://www.mindtickle.com/platform/integrations/)

## Next Steps

See `mindtickle-sdk-patterns` for authentication and webhook configuration.
