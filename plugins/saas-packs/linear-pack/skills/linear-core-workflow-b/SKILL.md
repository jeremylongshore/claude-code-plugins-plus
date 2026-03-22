---
name: linear-core-workflow-b
description: |
  Project, cycle, and roadmap management workflows with Linear.
  Use when implementing sprint planning, managing projects and milestones,
  or organizing work into cycles.
  Trigger: "linear project", "linear cycle", "linear sprint",
  "linear roadmap", "linear planning", "linear milestone".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, linear, workflow]

---
# Linear Core Workflow B: Projects & Cycles

## Overview
Manage projects, cycles (sprints), milestones, and roadmaps using the Linear API. Projects group issues across teams with states (`planned`, `started`, `paused`, `completed`, `canceled`), target dates, and progress tracking. Cycles are time-boxed iterations (sprints) owned by a single team. Initiatives group projects at the organizational level.

## Prerequisites
- Linear SDK configured with API key or OAuth token
- Understanding of Linear's hierarchy: Organization > Team > Cycle/Project > Issue
- Team access with project create permissions

## Instructions

### Step 1: Project CRUD
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });

// List projects (optionally filter by team)
const projects = await client.projects({
  filter: {
    accessibleTeams: { some: { key: { eq: "ENG" } } },
    state: { nin: ["completed", "canceled"] },
  },
  orderBy: "updatedAt",
  first: 20,
});

for (const project of projects.nodes) {
  console.log(`${project.name} [${project.state}] — progress: ${Math.round(project.progress * 100)}%`);
}

// Create a project
const teams = await client.teams();
const eng = teams.nodes.find(t => t.key === "ENG")!;

const projectResult = await client.createProject({
  name: "Authentication Overhaul",
  description: "Modernize auth infrastructure with OAuth 2.0 + MFA.",
  teamIds: [eng.id],
  state: "planned",
  targetDate: "2026-06-30",
});

const project = await projectResult.project;
console.log(`Created project: ${project?.name} (${project?.id})`);

// Update project
await client.updateProject(project!.id, {
  state: "started",
  description: "Updated scope: includes SSO integration.",
});

// Get project by slug
const found = await client.projects({
  filter: { slugId: { eq: "auth-overhaul" } },
});
```

### Step 2: Project Milestones
```typescript
// Create milestones for a project
await client.createProjectMilestone({
  projectId: project!.id,
  name: "OAuth 2.0 Implementation",
  targetDate: "2026-04-15",
});

await client.createProjectMilestone({
  projectId: project!.id,
  name: "MFA Rollout",
  targetDate: "2026-05-30",
});

// List milestones
const milestones = await project!.projectMilestones();
for (const ms of milestones.nodes) {
  console.log(`  Milestone: ${ms.name} — target: ${ms.targetDate}`);
}
```

### Step 3: Assign Issues to Projects
```typescript
// Create issue directly in a project
await client.createIssue({
  teamId: eng.id,
  title: "Implement OAuth 2.0 login flow",
  projectId: project!.id,
  priority: 2,
});

// Move existing issue to project
await client.updateIssue("existing-issue-id", {
  projectId: project!.id,
});

// Get all issues in a project
const projectIssues = await project!.issues({ first: 100 });
for (const issue of projectIssues.nodes) {
  const state = await issue.state;
  console.log(`  ${issue.identifier}: ${issue.title} [${state?.name}]`);
}
```

### Step 4: Cycle (Sprint) Management
```typescript
// Get current and upcoming cycles for a team
const now = new Date().toISOString();
const cycles = await eng.cycles({
  filter: { endsAt: { gte: now } },
  orderBy: "startsAt",
});

for (const cycle of cycles.nodes) {
  console.log(`${cycle.name ?? "Unnamed"}: ${cycle.startsAt} → ${cycle.endsAt}`);
}

// Create a new 2-week cycle
const startsAt = new Date();
const endsAt = new Date();
endsAt.setDate(endsAt.getDate() + 14);

const cycleResult = await client.createCycle({
  teamId: eng.id,
  name: "Sprint 42",
  startsAt: startsAt.toISOString(),
  endsAt: endsAt.toISOString(),
});

const cycle = await cycleResult.cycle;
console.log(`Created cycle: ${cycle?.name}`);

// Add issues to cycle
const issueIds = ["issue-id-1", "issue-id-2", "issue-id-3"];
for (const issueId of issueIds) {
  await client.updateIssue(issueId, { cycleId: cycle!.id });
}
```

### Step 5: Cycle Metrics
```typescript
async function getCycleMetrics(cycleId: string) {
  const cycle = await client.cycle(cycleId);
  const issues = await cycle.issues();

  const byState = new Map<string, number>();
  let totalEstimate = 0;
  let completedEstimate = 0;

  for (const issue of issues.nodes) {
    const state = await issue.state;
    const name = state?.name ?? "Unknown";
    byState.set(name, (byState.get(name) ?? 0) + 1);

    totalEstimate += issue.estimate ?? 0;
    if (state?.type === "completed") {
      completedEstimate += issue.estimate ?? 0;
    }
  }

  return {
    totalIssues: issues.nodes.length,
    stateBreakdown: Object.fromEntries(byState),
    totalPoints: totalEstimate,
    completedPoints: completedEstimate,
    burndown: totalEstimate ? Math.round((completedEstimate / totalEstimate) * 100) : 0,
  };
}

const metrics = await getCycleMetrics(cycle!.id);
console.log(`Sprint progress: ${metrics.burndown}% (${metrics.completedPoints}/${metrics.totalPoints} pts)`);
```

### Step 6: Sprint Rollover
```typescript
async function rolloverCycle(fromCycleId: string, toCycleId: string) {
  const fromCycle = await client.cycle(fromCycleId);
  const unfinished = await fromCycle.issues({
    filter: { state: { type: { nin: ["completed", "canceled"] } } },
  });

  let moved = 0;
  for (const issue of unfinished.nodes) {
    await client.updateIssue(issue.id, { cycleId: toCycleId });
    moved++;
  }

  console.log(`Rolled over ${moved} unfinished issues`);
  return moved;
}
```

### Step 7: Team Velocity
```typescript
async function calculateVelocity(teamKey: string, sprintCount = 3) {
  const teams = await client.teams({ filter: { key: { eq: teamKey } } });
  const team = teams.nodes[0];

  // Get completed cycles
  const cycles = await team.cycles({
    filter: { completedAt: { neq: null } },
    orderBy: "completedAt",
    first: sprintCount,
  });

  const velocities = await Promise.all(
    cycles.nodes.map(async (cycle) => {
      const completed = await cycle.issues({
        filter: { state: { type: { eq: "completed" } } },
      });
      return completed.nodes.reduce((sum, i) => sum + (i.estimate ?? 0), 0);
    })
  );

  const avg = velocities.reduce((a, b) => a + b, 0) / velocities.length;
  return { velocities, average: Math.round(avg * 10) / 10 };
}

const velocity = await calculateVelocity("ENG");
console.log(`Average velocity: ${velocity.average} pts/sprint`);
```

### Step 8: Roadmap View
```typescript
async function getRoadmap(monthsAhead = 6) {
  const futureDate = new Date();
  futureDate.setMonth(futureDate.getMonth() + monthsAhead);

  const projects = await client.projects({
    filter: {
      state: { nin: ["completed", "canceled"] },
      targetDate: { lte: futureDate.toISOString() },
    },
    orderBy: "targetDate",
  });

  return projects.nodes.map(p => ({
    name: p.name,
    state: p.state,
    progress: `${Math.round(p.progress * 100)}%`,
    targetDate: p.targetDate,
  }));
}

const roadmap = await getRoadmap();
console.table(roadmap);
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Project not found` | Invalid project ID or deleted | Verify ID with `client.projects()` |
| `Cycle dates overlap` | Dates conflict with existing cycle | Check existing cycles: `team.cycles()` |
| `Permission denied` | No project access | Verify team membership |
| `Invalid date range` | `endsAt` before `startsAt` | Validate date ordering before API call |
| `Team not in project` | Issue team not in project's team list | Add team via `updateProject` first |

## Examples

### Sprint Planning Flow
```typescript
async function planSprint(teamKey: string, durationDays: number, issueIds: string[]) {
  const teams = await client.teams({ filter: { key: { eq: teamKey } } });
  const team = teams.nodes[0];

  const startsAt = new Date();
  const endsAt = new Date();
  endsAt.setDate(endsAt.getDate() + durationDays);

  const cycleResult = await client.createCycle({
    teamId: team.id,
    name: `Sprint ${new Date().toISOString().slice(0, 10)}`,
    startsAt: startsAt.toISOString(),
    endsAt: endsAt.toISOString(),
  });

  const cycle = await cycleResult.cycle;
  for (const id of issueIds) {
    await client.updateIssue(id, { cycleId: cycle!.id });
  }

  console.log(`Sprint created: ${cycle?.name} (${issueIds.length} issues)`);
  return cycle;
}
```

## Resources
- [Project Model Schema](https://studio.apollographql.com/public/Linear-API/variant/current/schema/reference/objects/Project)
- [Cycle Model Schema](https://studio.apollographql.com/public/Linear-API/variant/current/schema/reference/objects/Cycle)
- [Linear Roadmaps Documentation](https://linear.app/docs/roadmaps)
