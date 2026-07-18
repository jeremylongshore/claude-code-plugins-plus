# Notion Architecture Variants — Full Implementation

Complete, copy-ready code for all five Notion backend architectures. Each variant assumes `NOTION_TOKEN` is set and the relevant database has been shared with your integration (see `## Prerequisites` in SKILL.md).

## Variant 1: Headless CMS (Blog / Content Site)

Use Notion as a content management system — authors write in Notion, your site fetches and renders content via the API.

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const CONTENT_DB = process.env.NOTION_CONTENT_DB!;

// Database schema in Notion:
// Title (title), Slug (rich_text), Status (select: Draft/Review/Published),
// Published Date (date), Author (people), Tags (multi_select),
// Excerpt (rich_text), Cover Image (files)

interface BlogPost {
  id: string;
  title: string;
  slug: string;
  status: string;
  publishedDate: string | null;
  author: string;
  tags: string[];
  excerpt: string;
}

// Fetch published posts for the blog index
async function getPublishedPosts(): Promise<BlogPost[]> {
  const response = await notion.databases.query({
    database_id: CONTENT_DB,
    filter: {
      property: 'Status',
      select: { equals: 'Published' },
    },
    sorts: [{ property: 'Published Date', direction: 'descending' }],
    page_size: 100,
  });

  return response.results
    .filter((p): p is any => 'properties' in p)
    .map(page => ({
      id: page.id,
      title: page.properties['Title']?.title?.[0]?.plain_text ?? 'Untitled',
      slug: page.properties['Slug']?.rich_text?.[0]?.plain_text ?? page.id,
      status: page.properties['Status']?.select?.name ?? 'Draft',
      publishedDate: page.properties['Published Date']?.date?.start ?? null,
      author: page.properties['Author']?.people?.[0]?.name ?? 'Unknown',
      tags: page.properties['Tags']?.multi_select?.map((t: any) => t.name) ?? [],
      excerpt: page.properties['Excerpt']?.rich_text?.[0]?.plain_text ?? '',
    }));
}

// Fetch full page content as blocks (for rendering)
async function getPostContent(pageId: string): Promise<any[]> {
  const blocks: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.blocks.children.list({
      block_id: pageId,
      page_size: 100,
      start_cursor: cursor,
    });

    blocks.push(...response.results);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;
  } while (cursor);

  return blocks;
}

// Render blocks to HTML (simplified)
function blockToHtml(block: any): string {
  const type = block.type;
  switch (type) {
    case 'paragraph':
      const text = block.paragraph.rich_text.map((t: any) => t.plain_text).join('');
      return text ? `<p>${text}</p>` : '';
    case 'heading_1':
      return `<h1>${block.heading_1.rich_text.map((t: any) => t.plain_text).join('')}</h1>`;
    case 'heading_2':
      return `<h2>${block.heading_2.rich_text.map((t: any) => t.plain_text).join('')}</h2>`;
    case 'heading_3':
      return `<h3>${block.heading_3.rich_text.map((t: any) => t.plain_text).join('')}</h3>`;
    case 'bulleted_list_item':
      return `<li>${block.bulleted_list_item.rich_text.map((t: any) => t.plain_text).join('')}</li>`;
    case 'code':
      return `<pre><code class="${block.code.language}">${block.code.rich_text.map((t: any) => t.plain_text).join('')}</code></pre>`;
    case 'image':
      const url = block.image.type === 'external' ? block.image.external.url : block.image.file.url;
      return `<img src="${url}" alt="" />`;
    default:
      return `<!-- unsupported block type: ${type} -->`;
  }
}
```

## Variant 2: Task Tracker (Project Management)

Use Notion as a project management backend — read/write tasks, update statuses, assign team members.

```typescript
const TASKS_DB = process.env.NOTION_TASKS_DB!;

// Database schema:
// Name (title), Status (select: Backlog/Todo/In Progress/Done),
// Priority (select: P0/P1/P2/P3), Assignee (people),
// Due Date (date), Sprint (select), Labels (multi_select),
// Story Points (number)

interface Task {
  id: string;
  name: string;
  status: string;
  priority: string;
  assignee: string | null;
  dueDate: string | null;
  labels: string[];
}

// Get sprint board view
async function getSprintTasks(sprint: string): Promise<Record<string, Task[]>> {
  const response = await notion.databases.query({
    database_id: TASKS_DB,
    filter: {
      and: [
        { property: 'Sprint', select: { equals: sprint } },
        { property: 'Status', select: { does_not_equal: 'Archived' } },
      ],
    },
    sorts: [{ property: 'Priority', direction: 'ascending' }],
  });

  const tasks = response.results
    .filter((p): p is any => 'properties' in p)
    .map(page => ({
      id: page.id,
      name: page.properties['Name']?.title?.[0]?.plain_text ?? 'Untitled',
      status: page.properties['Status']?.select?.name ?? 'Backlog',
      priority: page.properties['Priority']?.select?.name ?? 'P3',
      assignee: page.properties['Assignee']?.people?.[0]?.name ?? null,
      dueDate: page.properties['Due Date']?.date?.start ?? null,
      labels: page.properties['Labels']?.multi_select?.map((l: any) => l.name) ?? [],
    }));

  // Group by status for board view
  return tasks.reduce((board, task) => {
    (board[task.status] ??= []).push(task);
    return board;
  }, {} as Record<string, Task[]>);
}

// Move task between columns
async function updateTaskStatus(taskId: string, newStatus: string): Promise<void> {
  await notion.pages.update({
    page_id: taskId,
    properties: {
      Status: { select: { name: newStatus } },
    },
  });
}

// Create task from external source (Slack, email, API)
async function createTask(input: {
  name: string;
  priority?: string;
  assigneeId?: string;
  dueDate?: string;
  labels?: string[];
}): Promise<string> {
  const properties: any = {
    Name: { title: [{ text: { content: input.name } }] },
    Status: { select: { name: 'Backlog' } },
  };

  if (input.priority) properties.Priority = { select: { name: input.priority } };
  if (input.assigneeId) properties.Assignee = { people: [{ id: input.assigneeId }] };
  if (input.dueDate) properties['Due Date'] = { date: { start: input.dueDate } };
  if (input.labels) properties.Labels = { multi_select: input.labels.map(name => ({ name })) };

  const page = await notion.pages.create({
    parent: { database_id: TASKS_DB },
    properties,
  });

  return page.id;
}
```

## Variant 3–5: Knowledge Base (Wiki), Form Handler, and Data Pipeline

Three additional patterns for common Notion use cases.

```typescript
// === KNOWLEDGE BASE (WIKI) ===
const WIKI_DB = process.env.NOTION_WIKI_DB!;

// Database schema:
// Title (title), Category (select), Tags (multi_select),
// Last Updated (last_edited_time), Author (created_by)

// Full-text search across wiki articles
async function searchWiki(query: string): Promise<any[]> {
  // Notion's search endpoint searches across all shared content
  const response = await notion.search({
    query,
    filter: { value: 'page', property: 'object' },
    sort: { direction: 'descending', timestamp: 'last_edited_time' },
    page_size: 20,
  });

  return response.results
    .filter((r: any) => r.parent?.database_id === WIKI_DB)
    .map((page: any) => ({
      id: page.id,
      title: page.properties?.['Title']?.title?.[0]?.plain_text ?? 'Untitled',
      lastEdited: page.last_edited_time,
      url: page.url,
    }));
}

// Build table of contents from page blocks
async function getTableOfContents(pageId: string): Promise<Array<{ level: number; text: string }>> {
  const blocks = await notion.blocks.children.list({ block_id: pageId, page_size: 100 });

  return blocks.results
    .filter((b: any) => b.type?.startsWith('heading_'))
    .map((b: any) => ({
      level: parseInt(b.type.replace('heading_', '')),
      text: b[b.type].rich_text.map((t: any) => t.plain_text).join(''),
    }));
}

// === FORM SUBMISSION HANDLER ===
const SUBMISSIONS_DB = process.env.NOTION_SUBMISSIONS_DB!;

// Database schema:
// Name (title), Email (email), Message (rich_text),
// Submitted At (date), Status (select: New/Reviewed/Responded)

async function handleFormSubmission(form: {
  name: string;
  email: string;
  message: string;
}): Promise<{ pageId: string; url: string }> {
  const page = await notion.pages.create({
    parent: { database_id: SUBMISSIONS_DB },
    properties: {
      Name: { title: [{ text: { content: form.name } }] },
      Email: { email: form.email },
      Message: { rich_text: [{ text: { content: form.message.substring(0, 2000) } }] }, // Notion rich_text caps a single text object at 2000 chars
      'Submitted At': { date: { start: new Date().toISOString() } },
      Status: { select: { name: 'New' } },
    },
  });

  return { pageId: page.id, url: (page as any).url };
}

// === DATA PIPELINE SOURCE ===
const METRICS_DB = process.env.NOTION_METRICS_DB!;

// Use Notion as data source — extract, transform, load to analytics
async function extractMetricsForAnalytics(since: string): Promise<any[]> {
  const allRecords: any[] = [];
  let cursor: string | undefined;

  do {
    const response = await notion.databases.query({
      database_id: METRICS_DB,
      filter: {
        timestamp: 'last_edited_time',
        last_edited_time: { on_or_after: since },
      },
      page_size: 100,
      start_cursor: cursor,
    });

    // Transform Notion properties to flat analytics schema
    const transformed = response.results
      .filter((p): p is any => 'properties' in p)
      .map(page => ({
        notion_id: page.id,
        created: page.created_time,
        updated: page.last_edited_time,
        // Extract properties into flat columns for the analytics warehouse
        ...Object.fromEntries(
          Object.entries(page.properties).map(([key, prop]: [string, any]) => {
            switch (prop.type) {
              case 'title': return [key, prop.title?.[0]?.plain_text ?? ''];
              case 'number': return [key, prop.number];
              case 'select': return [key, prop.select?.name ?? null];
              case 'date': return [key, prop.date?.start ?? null];
              case 'checkbox': return [key, prop.checkbox];
              default: return [key, null];
            }
          })
        ),
      }));

    allRecords.push(...transformed);
    cursor = response.has_more ? (response.next_cursor ?? undefined) : undefined;

    await new Promise(r => setTimeout(r, 350)); // Rate limit
  } while (cursor);

  return allRecords;
}
```

## Python equivalents

```python
from notion_client import Client

notion = Client(auth=os.environ["NOTION_TOKEN"])

# CMS: get published posts
def get_published_posts(content_db: str):
    response = notion.databases.query(
        database_id=content_db,
        filter={"property": "Status", "select": {"equals": "Published"}},
        sorts=[{"property": "Published Date", "direction": "descending"}],
    )
    return [
        {
            "id": p["id"],
            "title": p["properties"]["Title"]["title"][0]["plain_text"]
                if p["properties"]["Title"]["title"] else "Untitled",
            "slug": p["properties"]["Slug"]["rich_text"][0]["plain_text"]
                if p["properties"]["Slug"]["rich_text"] else p["id"],
        }
        for p in response["results"]
    ]

# Form handler
def handle_submission(db_id: str, name: str, email: str, message: str):
    return notion.pages.create(
        parent={"database_id": db_id},
        properties={
            "Name": {"title": [{"text": {"content": name}}]},
            "Email": {"email": email},
            "Message": {"rich_text": [{"text": {"content": message[:2000]}}]},
            "Status": {"select": {"name": "New"}},
        },
    )

# Data pipeline extract
def extract_for_analytics(db_id: str, since_iso: str):
    records = []
    cursor = None
    while True:
        kwargs = {
            "database_id": db_id,
            "filter": {"timestamp": "last_edited_time", "last_edited_time": {"on_or_after": since_iso}},
            "page_size": 100,
        }
        if cursor:
            kwargs["start_cursor"] = cursor
        response = notion.databases.query(**kwargs)
        records.extend(response["results"])
        if not response.get("has_more"):
            break
        cursor = response.get("next_cursor")
    return records
```
