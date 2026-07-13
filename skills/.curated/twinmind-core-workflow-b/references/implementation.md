# TwinMind Core Workflow B - Detailed Implementation

## Action Item Extractor

```typescript
export class ActionItemExtractor {
  private client = getTwinMindClient();

  async extractFromTranscript(transcriptId: string, options: ActionItemExtractionOptions = {}): Promise<ActionItem[]> {
    const response = await this.client.post('/extract/action-items', {
      transcript_id: transcriptId,
      include_context: options.includeContext ?? true,
      assign_from_speakers: options.assignFromSpeakers ?? true,
      infer_due_dates: options.inferDueDates ?? true,
      max_items: options.maxItems || 20,
    });
    return response.data.action_items.map((item: any) => ({
      id: item.id,
      text: item.text,
      assignee: item.assignee,
      dueDate: item.due_date,
      priority: this.inferPriority(item),
      context: item.context,
      status: 'pending',
    }));
  }

  private inferPriority(item: any): 'high' | 'medium' | 'low' {
    const text = item.text.toLowerCase();
    if (text.includes('urgent') || text.includes('asap') || text.includes('critical')) return 'high';
    if (text.includes('important') || text.includes('soon')) return 'medium';
    return 'low';
  }

  async categorizeItems(items: ActionItem[]): Promise<Map<string, ActionItem[]>> {
    const categories = new Map<string, ActionItem[]>();
    for (const item of items) {
      const cat = this.determineCategory(item);
      if (!categories.has(cat)) categories.set(cat, []);
      categories.get(cat)!.push(item);
    }
    return categories;
  }

  private determineCategory(item: ActionItem): string {
    const text = item.text.toLowerCase();
    if (text.includes('review') || text.includes('check')) return 'Review';
    if (text.includes('create') || text.includes('build')) return 'Development';
    if (text.includes('send') || text.includes('email')) return 'Communication';
    if (text.includes('schedule') || text.includes('meeting')) return 'Meetings';
    return 'General';
  }
}
```

## Follow-up Automation

```typescript
export class FollowUpAutomation {
  private client = getTwinMindClient();

  async generateFollowUp(transcriptId: string, options: FollowUpEmailOptions): Promise<GeneratedEmail> {
    const response = await this.client.post('/generate/follow-up', {
      transcript_id: transcriptId,
      recipients: options.recipients,
      include_summary: options.includeSummary ?? true,
      include_action_items: options.includeActionItems ?? true,
    });
    return { to: options.recipients, subject: response.data.subject, body: response.data.body };
  }

  async sendFollowUp(email: GeneratedEmail): Promise<{ messageId: string }> {
    const response = await this.client.post('/email/send', email);
    return { messageId: response.data.message_id };
  }

  async scheduleFollowUp(email: GeneratedEmail, sendAt: Date): Promise<{ scheduleId: string }> {
    const response = await this.client.post('/email/schedule', { ...email, send_at: sendAt.toISOString() });
    return { scheduleId: response.data.schedule_id };
  }
}
```

## Task Integrations

```typescript
export interface TaskIntegration {
  name: string;
  createTask(item: ActionItem): Promise<string>;
  updateTask(taskId: string, updates: Partial<ActionItem>): Promise<void>;
}

// Asana
export class AsanaIntegration implements TaskIntegration {
  name = 'Asana';
  constructor(private accessToken: string, private projectId: string) {}

  async createTask(item: ActionItem): Promise<string> {
    const response = await fetch('https://app.asana.com/api/1.0/tasks', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.accessToken}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ data: { name: item.text, notes: item.context, due_on: item.dueDate, projects: [this.projectId] } }),
    });
    return (await response.json()).data.gid;
  }
}

// Linear
export class LinearIntegration implements TaskIntegration {
  name = 'Linear';
  constructor(private apiKey: string, private teamId: string) {}

  async createTask(item: ActionItem): Promise<string> {
    const response = await fetch('https://api.linear.app/graphql', {
      method: 'POST',
      headers: { 'Authorization': this.apiKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: `mutation($input: IssueCreateInput!) { issueCreate(input: $input) { issue { id } } }`,
        variables: { input: { teamId: this.teamId, title: item.text, description: item.context, priority: item.priority === 'high' ? 1 : item.priority === 'medium' ? 2 : 3 } },
      }),
    });
    return (await response.json()).data.issueCreate.issue.id;
  }
}

export function getTaskIntegration(service: string): TaskIntegration {
  switch (service) {
    case 'asana': return new AsanaIntegration(process.env.ASANA_ACCESS_TOKEN!, process.env.ASANA_PROJECT_ID!);
    case 'linear': return new LinearIntegration(process.env.LINEAR_API_KEY!, process.env.LINEAR_TEAM_ID!);
    default: throw new Error(`Integration ${service} not supported`);
  }
}
```

## Complete Follow-up Workflow

```typescript
export async function runFollowUpWorkflow(options: FollowUpWorkflowOptions): Promise<FollowUpResult> {
  const extractor = new ActionItemExtractor();
  const followUp = new FollowUpAutomation();

  // Extract action items
  const actionItems = await extractor.extractFromTranscript(options.transcriptId, {
    includeContext: true, assignFromSpeakers: true, inferDueDates: true,
  });

  const result: FollowUpResult = { actionItems, createdTasks: [] };

  // Create tasks in external system
  if (options.taskIntegration) {
    const integration = getTaskIntegration(options.taskIntegration);
    for (const item of actionItems) {
      try {
        const externalId = await integration.createTask(item);
        result.createdTasks.push({ item, externalId });
      } catch (error) {
        console.error(`Failed to create task: ${item.text}`, error);
      }
    }
  }

  // Send or schedule follow-up email
  if (options.sendEmail && options.attendees.length > 0) {
    const email = await followUp.generateFollowUp(options.transcriptId, {
      recipients: options.attendees, includeSummary: true, includeActionItems: true,
    });
    if (options.emailDelay && options.emailDelay > 0) {
      const sendAt = new Date(Date.now() + options.emailDelay * 60 * 1000);
      result.emailScheduled = { ...(await followUp.scheduleFollowUp(email, sendAt)), sendAt };
    } else {
      result.emailSent = await followUp.sendFollowUp(email);
    }
  }

  return result;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
