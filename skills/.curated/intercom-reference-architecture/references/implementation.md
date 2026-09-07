# Intercom Reference Architecture — Full Implementation Walkthrough

This is the complete, code-level walkthrough for the layered Intercom
integration summarized in `SKILL.md`. Each step below maps to one layer of the
architecture. Implement them in order — the client layer is the dependency root
for every service.

## Layer architecture

```
┌─────────────────────────────────────────────┐
│              API / Webhook Layer             │
│   Express routes, webhook endpoints         │
├─────────────────────────────────────────────┤
│              Service Layer                   │
│   contacts.service, conversations.service   │
│   Business logic, orchestration             │
├─────────────────────────────────────────────┤
│              Intercom Client Layer           │
│   intercom-client SDK, error handling       │
│   Caching, rate limit management            │
├─────────────────────────────────────────────┤
│              Infrastructure                  │
│   Redis cache, job queue, monitoring        │
└─────────────────────────────────────────────┘
```

## Step 1: Client Layer

A lazy singleton keeps one authenticated `IntercomClient` per process and wraps
raw SDK errors into a typed, retry-aware `IntercomServiceError`.

```typescript
// src/intercom/client.ts
import { IntercomClient, IntercomError } from "intercom-client";

let instance: IntercomClient | null = null;

export function getClient(): IntercomClient {
  if (!instance) {
    const token = process.env.INTERCOM_ACCESS_TOKEN;
    if (!token) throw new Error("INTERCOM_ACCESS_TOKEN required");
    instance = new IntercomClient({ token });
  }
  return instance;
}

// Typed error wrapper
export class IntercomServiceError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly code: string,
    public readonly retryable: boolean,
    public readonly requestId?: string
  ) {
    super(message);
    this.name = "IntercomServiceError";
  }

  static from(err: unknown): IntercomServiceError {
    if (err instanceof IntercomError) {
      const retryable = err.statusCode === 429 || (err.statusCode ?? 0) >= 500;
      return new IntercomServiceError(
        err.message,
        err.statusCode ?? 500,
        err.body?.errors?.[0]?.code ?? "unknown",
        retryable,
        err.body?.request_id
      );
    }
    return new IntercomServiceError(
      (err as Error).message, 500, "internal", false
    );
  }
}
```

## Step 2: Contacts Service

Search-before-create avoids `409` conflicts, and `syncFromCRM` maps your
system-of-record fields onto Intercom custom attributes. `searchAll` is an async
generator that transparently walks Intercom's cursor pagination.

```typescript
// src/services/contacts.service.ts
import { getClient, IntercomServiceError } from "../intercom/client";
import { Intercom } from "intercom-client";

export class ContactsService {
  private client = getClient();

  async findOrCreate(params: {
    email: string;
    externalId: string;
    name?: string;
    customAttributes?: Record<string, any>;
  }): Promise<Intercom.Contact> {
    // Search first to avoid 409 conflicts
    const existing = await this.client.contacts.search({
      query: { field: "external_id", operator: "=", value: params.externalId },
    });

    if (existing.data.length > 0) {
      return existing.data[0];
    }

    return this.client.contacts.create({
      role: "user",
      externalId: params.externalId,
      email: params.email,
      name: params.name,
      customAttributes: params.customAttributes,
    });
  }

  async syncFromCRM(crmUser: {
    id: string;
    email: string;
    name: string;
    plan: string;
    company: string;
  }): Promise<Intercom.Contact> {
    const contact = await this.findOrCreate({
      email: crmUser.email,
      externalId: crmUser.id,
      name: crmUser.name,
      customAttributes: {
        plan: crmUser.plan,
        company_name: crmUser.company,
        last_synced_at: Math.floor(Date.now() / 1000),
      },
    });

    return contact;
  }

  async mergeLead(leadId: string, userId: string): Promise<Intercom.Contact> {
    return this.client.contacts.merge({ from: leadId, into: userId });
  }

  async *searchAll(
    query: Intercom.SearchRequest["query"]
  ): AsyncGenerator<Intercom.Contact> {
    let startingAfter: string | undefined;
    do {
      const page = await this.client.contacts.search({
        query,
        pagination: { per_page: 50, starting_after: startingAfter },
      });
      for (const contact of page.data) yield contact;
      startingAfter = page.pages?.next?.startingAfter ?? undefined;
    } while (startingAfter);
  }
}
```

## Step 3: Conversations Service

Wraps the conversation lifecycle — admin replies, internal notes, close, and a
scoped search for an admin's open queue.

```typescript
// src/services/conversations.service.ts
import { getClient } from "../intercom/client";

export class ConversationsService {
  private client = getClient();

  async replyAsAdmin(
    conversationId: string,
    adminId: string,
    body: string
  ): Promise<void> {
    await this.client.conversations.reply({
      conversationId,
      type: "admin",
      adminId,
      body,
    });
  }

  async addNote(
    conversationId: string,
    adminId: string,
    note: string
  ): Promise<void> {
    await this.client.conversations.reply({
      conversationId,
      type: "note",
      adminId,
      body: note,
    });
  }

  async closeWithMessage(
    conversationId: string,
    adminId: string,
    message?: string
  ): Promise<void> {
    await this.client.conversations.close({
      conversationId,
      adminId,
      body: message,
    });
  }

  async getOpenConversationsForAdmin(adminId: string) {
    return this.client.conversations.search({
      query: {
        operator: "AND",
        value: [
          { field: "state", operator: "=", value: "open" },
          { field: "admin_assignee_id", operator: "=", value: adminId },
        ],
      },
      sort: { field: "updated_at", order: "descending" },
    });
  }
}
```

## Step 4: Articles Service (Help Center)

Create and list Help Center articles, defaulting new articles to `draft` so
nothing publishes accidentally.

```typescript
// src/services/articles.service.ts
import { getClient } from "../intercom/client";

export class ArticlesService {
  private client = getClient();

  async createArticle(params: {
    title: string;
    body: string;
    authorId: string;
    parentId?: string; // Collection ID
    state?: "published" | "draft";
  }) {
    return this.client.articles.create({
      title: params.title,
      body: params.body,
      authorId: params.authorId,
      parentId: params.parentId,
      state: params.state || "draft",
    });
  }

  async *listAll() {
    const response = await this.client.articles.list();
    for await (const article of response) {
      yield article;
    }
  }

  async listCollections() {
    return this.client.helpCenter.listCollections();
  }
}
```

## Step 5: Data Flow

Intercom pushes events to your webhook router; your service layer performs API
calls back to Intercom and persists to your own database + cache.

```
┌──────────────┐   Webhook POST     ┌───────────────┐
│   Intercom   │ ─────────────────▶  │  Webhook      │
│   Platform   │                     │  Router       │
│              │ ◀── API calls ──── │               │
└──────────────┘                     └───────┬───────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Service Layer  │
                                    │  - Contacts      │
                                    │  - Conversations │
                                    │  - Articles      │
                                    └────────┬────────┘
                                             │
                                    ┌────────▼────────┐
                                    │   Your Database  │
                                    │   + Cache (Redis)│
                                    └─────────────────┘
```
