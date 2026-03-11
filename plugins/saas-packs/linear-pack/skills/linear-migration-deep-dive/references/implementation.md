# Linear Migration Deep Dive - Detailed Implementation

## Workflow Mapping

```typescript
// Jira to Linear status mapping
const JIRA_STATUS_MAP: Record<string, string> = {
  "To Do": "Todo",
  "In Progress": "In Progress",
  "In Review": "In Review",
  "Done": "Done",
  "Closed": "Done",
  "Backlog": "Backlog",
  "Blocked": "In Progress", // Linear uses labels for blocked
};

// Jira to Linear priority mapping
const JIRA_PRIORITY_MAP: Record<string, number> = {
  "Highest": 1, // Urgent
  "High": 2,
  "Medium": 3,
  "Low": 4,
  "Lowest": 4,
};

// Jira to Linear issue type mapping
const JIRA_TYPE_MAP: Record<string, { labelName: string }> = {
  "Bug": { labelName: "Bug" },
  "Story": { labelName: "Feature" },
  "Task": { labelName: "Task" },
  "Epic": { labelName: "Epic" },
  "Subtask": { labelName: "Subtask" },
};

// Asana to Linear mapping
const ASANA_SECTION_MAP: Record<string, string> = {
  "To Do": "Todo",
  "Doing": "In Progress",
  "Review": "In Review",
  "Complete": "Done",
};
```

## Jira Export

```typescript
import JiraClient from "jira-client";

const jira = new JiraClient({
  host: process.env.JIRA_HOST,
  basic_auth: { email: process.env.JIRA_EMAIL, api_token: process.env.JIRA_API_TOKEN },
});

interface JiraIssue {
  key: string;
  fields: {
    summary: string;
    description: string;
    status: { name: string };
    priority: { name: string };
    issuetype: { name: string };
    assignee: { emailAddress: string } | null;
    reporter: { emailAddress: string };
    created: string;
    updated: string;
    parent?: { key: string };
    subtasks: { key: string }[];
    labels: string[];
    customfield_10001?: number; // Story points
  };
}

export async function exportJiraProject(projectKey: string): Promise<JiraIssue[]> {
  const issues: JiraIssue[] = [];
  let startAt = 0;
  const maxResults = 100;

  while (true) {
    const result = await jira.searchJira(
      `project = ${projectKey} ORDER BY created ASC`,
      {
        startAt,
        maxResults,
        fields: ["summary", "description", "status", "priority", "issuetype", "assignee", "reporter", "created", "updated", "parent", "subtasks", "labels", "customfield_10001"],
      }
    );

    issues.push(...result.issues);
    if (issues.length >= result.total) break;
    startAt += maxResults;
  }

  await fs.writeFile(`jira-export-${projectKey}-${Date.now()}.json`, JSON.stringify(issues, null, 2));
  return issues;
}
```

## Asana Export

```typescript
import Asana from "asana";

const asana = Asana.Client.create().useAccessToken(process.env.ASANA_TOKEN);

export async function exportAsanaProject(projectGid: string) {
  const tasks = [];

  const result = await asana.tasks.getTasks({
    project: projectGid,
    opt_fields: ["name", "notes", "assignee", "due_on", "completed", "memberships.section.name", "tags.name", "parent.gid", "subtasks.gid", "created_at", "modified_at"],
  });

  for await (const task of result) {
    tasks.push(task);
  }

  return tasks;
}
```

## Data Transformation

```typescript
import { LinearClient } from "@linear/sdk";

interface LinearIssueInput {
  teamId: string;
  title: string;
  description?: string;
  priority?: number;
  stateId?: string;
  assigneeId?: string;
  labelIds?: string[];
  estimate?: number;
  parentId?: string;
}

interface TransformContext {
  linearClient: LinearClient;
  teamId: string;
  stateMap: Map<string, string>;
  userMap: Map<string, string>;
  labelMap: Map<string, string>;
  issueIdMap: Map<string, string>; // sourceId -> linearId
}

export async function transformJiraIssue(jiraIssue: JiraIssue, context: TransformContext): Promise<LinearIssueInput> {
  const linearStatus = JIRA_STATUS_MAP[jiraIssue.fields.status.name] || "Todo";
  const stateId = context.stateMap.get(linearStatus);
  const priority = JIRA_PRIORITY_MAP[jiraIssue.fields.priority?.name] || 0;

  const assigneeEmail = jiraIssue.fields.assignee?.emailAddress;
  const assigneeId = assigneeEmail ? context.userMap.get(assigneeEmail) : undefined;

  const labelIds: string[] = [];
  const typeLabel = JIRA_TYPE_MAP[jiraIssue.fields.issuetype.name];
  if (typeLabel && context.labelMap.has(typeLabel.labelName)) {
    labelIds.push(context.labelMap.get(typeLabel.labelName)!);
  }
  for (const label of jiraIssue.fields.labels) {
    const linearLabelId = context.labelMap.get(label);
    if (linearLabelId) labelIds.push(linearLabelId);
  }

  const description = convertJiraToMarkdown(jiraIssue.fields.description);

  return {
    teamId: context.teamId,
    title: `[${jiraIssue.key}] ${jiraIssue.fields.summary}`,
    description,
    priority,
    stateId,
    assigneeId,
    labelIds,
    estimate: jiraIssue.fields.customfield_10001,
  };
}

function convertJiraToMarkdown(jiraMarkup: string | null): string {
  if (!jiraMarkup) return "";

  let md = jiraMarkup;

  // Headers
  md = md.replace(/h1\. /g, "# ");
  md = md.replace(/h2\. /g, "## ");
  md = md.replace(/h3\. /g, "### ");

  // Bold and italic
  md = md.replace(/\*([^*]+)\*/g, "**$1**");
  md = md.replace(/_([^_]+)_/g, "*$1*");

  // Code blocks
  md = md.replace(/\{code(:([^}]+))?\}([\s\S]*?)\{code\}/g, "```$2\n$3\n```");
  md = md.replace(/\{noformat\}([\s\S]*?)\{noformat\}/g, "```\n$1\n```");

  // Lists
  md = md.replace(/^# /gm, "1. ");
  md = md.replace(/^\* /gm, "- ");

  // Links
  md = md.replace(/\[([^\]|]+)\|([^\]]+)\]/g, "[$1]($2)");
  md = md.replace(/\[([^\]]+)\]/g, "[$1]($1)");

  return md;
}
```

## Batch Import

```typescript
interface ImportStats {
  total: number;
  created: number;
  skipped: number;
  errors: { sourceId: string; error: string }[];
}

export async function importToLinear(issues: JiraIssue[], context: TransformContext): Promise<ImportStats> {
  const stats: ImportStats = { total: issues.length, created: 0, skipped: 0, errors: [] };

  const sorted = sortByHierarchy(issues);

  for (const jiraIssue of sorted) {
    try {
      if (context.issueIdMap.has(jiraIssue.key)) { stats.skipped++; continue; }

      const input = await transformJiraIssue(jiraIssue, context);

      if (jiraIssue.fields.parent) {
        input.parentId = context.issueIdMap.get(jiraIssue.fields.parent.key);
      }

      const result = await context.linearClient.createIssue(input);

      if (result.success) {
        const issue = await result.issue;
        context.issueIdMap.set(jiraIssue.key, issue!.id);
        stats.created++;
        await sleep(100); // Rate limit
      } else {
        throw new Error("Create failed");
      }
    } catch (error) {
      stats.errors.push({
        sourceId: jiraIssue.key,
        error: error instanceof Error ? error.message : "Unknown error",
      });
    }
  }

  return stats;
}

function sortByHierarchy(issues: JiraIssue[]): JiraIssue[] {
  const byKey = new Map(issues.map(i => [i.key, i]));
  const sorted: JiraIssue[] = [];
  const processed = new Set<string>();

  function addWithDependencies(issue: JiraIssue): void {
    if (processed.has(issue.key)) return;
    if (issue.fields.parent) {
      const parent = byKey.get(issue.fields.parent.key);
      if (parent) addWithDependencies(parent);
    }
    sorted.push(issue);
    processed.add(issue.key);
  }

  for (const issue of issues) {
    addWithDependencies(issue);
  }

  return sorted;
}
```

## Validation and Post-Migration Report

```typescript
export async function validateMigration(
  sourceIssues: JiraIssue[],
  context: TransformContext
): Promise<{ valid: boolean; issues: string[] }> {
  const issues: string[] = [];

  for (const source of sourceIssues) {
    if (!context.issueIdMap.has(source.key)) {
      issues.push(`Missing: ${source.key}`);
    }
  }

  const sampleSize = Math.min(50, sourceIssues.length);
  const sample = sourceIssues.slice(0, sampleSize);

  for (const source of sample) {
    const linearId = context.issueIdMap.get(source.key);
    if (!linearId) continue;

    try {
      const linearIssue = await context.linearClient.issue(linearId);

      if (!linearIssue.title.includes(source.key)) {
        issues.push(`Title mismatch: ${source.key}`);
      }

      const expectedPriority = JIRA_PRIORITY_MAP[source.fields.priority?.name] || 0;
      if (linearIssue.priority !== expectedPriority) {
        issues.push(`Priority mismatch: ${source.key} (${linearIssue.priority} != ${expectedPriority})`);
      }
    } catch (error) {
      issues.push(`Verify failed: ${source.key} - ${error}`);
    }
  }

  return { valid: issues.length === 0, issues };
}

export async function createMigrationReport(stats: ImportStats, context: TransformContext): Promise<string> {
  const report = `
# Migration Report

**Date:** ${new Date().toISOString()}
**Source:** Jira
**Target:** Linear

## Statistics
- Total issues: ${stats.total}
- Successfully imported: ${stats.created}
- Skipped (duplicates): ${stats.skipped}
- Errors: ${stats.errors.length}

## ID Mapping
${Array.from(context.issueIdMap.entries()).map(([source, linear]) => `- ${source} -> ${linear}`).join("\n")}

## Errors
${stats.errors.map(e => `- ${e.sourceId}: ${e.error}`).join("\n") || "None"}

## Next Steps
1. Verify critical issues manually
2. Update integrations to use Linear
3. Archive source project after parallel run
4. Train team on Linear workflows
`;

  await fs.writeFile("migration-report.md", report);
  return report;
}
```
