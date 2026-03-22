---
name: miro-sdk-patterns
description: |
  Apply production-ready patterns for @mirohq/miro-api client usage.
  Use when implementing Miro integrations, refactoring SDK usage,
  or establishing coding standards for Miro REST API v2.
  Trigger with phrases like "miro SDK patterns", "miro best practices",
  "miro code patterns", "miro client wrapper", "miro typescript".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, miro, patterns, typescript]
compatible-with: claude-code
---

# Miro SDK Patterns

## Overview

Production-ready patterns for the `@mirohq/miro-api` Node.js client and direct REST API v2 usage. Covers the high-level `Miro` client (stateful, OAuth-aware) and the low-level `MiroApi` client (stateless, token-based).

## Prerequisites

- `@mirohq/miro-api` installed
- TypeScript 5+ project
- Understanding of Miro REST API v2 item model

## Two Client Modes

```typescript
import { Miro, MiroApi } from '@mirohq/miro-api';

// HIGH-LEVEL: Stateful, manages OAuth tokens per user
// Use for multi-user apps (SaaS, web apps with OAuth)
const miro = new Miro({
  clientId: process.env.MIRO_CLIENT_ID!,
  clientSecret: process.env.MIRO_CLIENT_SECRET!,
  redirectUrl: process.env.MIRO_REDIRECT_URI!,
});
const userApi = await miro.as('user-id');  // Returns MiroApi scoped to user

// LOW-LEVEL: Stateless, pass token directly
// Use for scripts, automation, single-user integrations
const api = new MiroApi(process.env.MIRO_ACCESS_TOKEN!);
```

## Pattern 1: Type-Safe Board Service

```typescript
// src/miro/board-service.ts
import { MiroApi } from '@mirohq/miro-api';

// Response types matching Miro REST API v2
interface MiroBoard {
  id: string;
  type: 'board';
  name: string;
  description: string;
  createdAt: string;
  modifiedAt: string;
}

interface MiroBoardItem {
  id: string;
  type: 'sticky_note' | 'shape' | 'card' | 'text' | 'frame' | 'image' | 'document' | 'embed' | 'app_card';
  data: Record<string, unknown>;
  position: { x: number; y: number; origin: string };
  geometry?: { width?: number; height?: number };
  createdAt: string;
  createdBy: { id: string; type: string };
}

interface PaginatedResponse<T> {
  data: T[];
  total: number;
  size: number;
  offset: number;
  limit: number;
  cursor?: string;
}

export class BoardService {
  constructor(private api: MiroApi) {}

  async getBoard(boardId: string): Promise<MiroBoard> {
    const response = await this.api.getBoard(boardId);
    return response.body as unknown as MiroBoard;
  }

  async listItems(
    boardId: string,
    options: { type?: string; limit?: number; cursor?: string } = {}
  ): Promise<PaginatedResponse<MiroBoardItem>> {
    const params = new URLSearchParams();
    if (options.type) params.set('type', options.type);
    if (options.limit) params.set('limit', String(options.limit));
    if (options.cursor) params.set('cursor', options.cursor);

    const response = await fetch(
      `https://api.miro.com/v2/boards/${boardId}/items?${params}`,
      { headers: this.authHeaders() }
    );
    return response.json();
  }

  async getAllItems(boardId: string): Promise<MiroBoardItem[]> {
    const items: MiroBoardItem[] = [];
    let cursor: string | undefined;

    do {
      const page = await this.listItems(boardId, { limit: 50, cursor });
      items.push(...page.data);
      cursor = page.cursor;
    } while (cursor);

    return items;
  }

  private authHeaders() {
    return {
      'Authorization': `Bearer ${process.env.MIRO_ACCESS_TOKEN}`,
      'Content-Type': 'application/json',
    };
  }
}
```

## Pattern 2: Item Factory

```typescript
// src/miro/item-factory.ts
type StickyNoteColor = 'light_yellow' | 'light_green' | 'light_blue'
  | 'light_pink' | 'gray' | 'light_cyan' | 'light_orange';

interface CreateStickyNoteParams {
  boardId: string;
  content: string;
  color?: StickyNoteColor;
  x?: number;
  y?: number;
  width?: number;
}

interface CreateShapeParams {
  boardId: string;
  content: string;
  shape?: 'rectangle' | 'circle' | 'triangle' | 'rhombus'
    | 'round_rectangle' | 'parallelogram' | 'star'
    | 'right_arrow' | 'left_arrow' | 'pentagon' | 'hexagon'
    | 'octagon' | 'trapezoid' | 'flow_chart_predefined_process'
    | 'can' | 'cross' | 'cloud';
  fillColor?: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}

interface CreateCardParams {
  boardId: string;
  title: string;
  description?: string;
  dueDate?: string;       // ISO 8601 date
  assigneeId?: string;
  x?: number;
  y?: number;
}

export class ItemFactory {
  constructor(private token: string) {}

  async createStickyNote(params: CreateStickyNoteParams): Promise<MiroBoardItem> {
    return this.post(`/v2/boards/${params.boardId}/sticky_notes`, {
      data: { content: params.content, shape: 'square' },
      style: { fillColor: params.color ?? 'light_yellow', textAlign: 'center' },
      position: { x: params.x ?? 0, y: params.y ?? 0 },
      geometry: { width: params.width ?? 199 },
    });
  }

  async createShape(params: CreateShapeParams): Promise<MiroBoardItem> {
    return this.post(`/v2/boards/${params.boardId}/shapes`, {
      data: { content: params.content, shape: params.shape ?? 'round_rectangle' },
      style: { fillColor: params.fillColor ?? '#4262ff', textAlign: 'center' },
      position: { x: params.x ?? 0, y: params.y ?? 0 },
      geometry: { width: params.width ?? 200, height: params.height ?? 100 },
    });
  }

  async createCard(params: CreateCardParams): Promise<MiroBoardItem> {
    return this.post(`/v2/boards/${params.boardId}/cards`, {
      data: {
        title: params.title,
        description: params.description,
        dueDate: params.dueDate,
        assigneeId: params.assigneeId,
      },
      position: { x: params.x ?? 0, y: params.y ?? 0 },
    });
  }

  private async post(path: string, body: unknown): Promise<MiroBoardItem> {
    const res = await fetch(`https://api.miro.com${path}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new MiroApiError(res.status, err.message ?? 'API request failed', err.code);
    }
    return res.json();
  }
}
```

## Pattern 3: Error Handling Wrapper

```typescript
// src/miro/errors.ts
export class MiroApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'MiroApiError';
  }

  get isRetryable(): boolean {
    return this.status === 429 || (this.status >= 500 && this.status < 600);
  }

  get isAuthError(): boolean {
    return this.status === 401 || this.status === 403;
  }
}

async function safeMiroCall<T>(
  operation: () => Promise<T>,
  context: string
): Promise<{ data: T | null; error: MiroApiError | null }> {
  try {
    const data = await operation();
    return { data, error: null };
  } catch (err) {
    if (err instanceof MiroApiError) {
      console.error(`[Miro:${context}] ${err.status}: ${err.message}`);
      return { data: null, error: err };
    }
    throw err;  // Re-throw unexpected errors
  }
}
```

## Pattern 4: Multi-Tenant Client Factory

```typescript
// src/miro/multi-tenant.ts
import { Miro, MiroApi } from '@mirohq/miro-api';

// For SaaS apps serving multiple Miro users
const clients = new Map<string, MiroApi>();

export async function getClientForUser(userId: string): Promise<MiroApi> {
  if (!clients.has(userId)) {
    const miro = new Miro({
      clientId: process.env.MIRO_CLIENT_ID!,
      clientSecret: process.env.MIRO_CLIENT_SECRET!,
      redirectUrl: process.env.MIRO_REDIRECT_URI!,
    });

    if (!await miro.isAuthorized(userId)) {
      throw new Error(`User ${userId} has not authorized Miro`);
    }

    const api = await miro.as(userId);
    clients.set(userId, api);
  }

  return clients.get(userId)!;
}
```

## Pattern 5: Response Validation with Zod

```typescript
import { z } from 'zod';

const MiroBoardSchema = z.object({
  id: z.string(),
  type: z.literal('board'),
  name: z.string(),
  description: z.string().optional(),
  createdAt: z.string().datetime(),
  modifiedAt: z.string().datetime(),
});

const MiroItemSchema = z.object({
  id: z.string(),
  type: z.enum(['sticky_note', 'shape', 'card', 'text', 'frame', 'image', 'document', 'embed', 'app_card']),
  data: z.record(z.unknown()),
  position: z.object({ x: z.number(), y: z.number() }),
});

function validateBoardResponse(data: unknown) {
  return MiroBoardSchema.parse(data);
}
```

## Error Handling

| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Type-safe service | Board/item CRUD | Catches shape mismatches at compile time |
| Item factory | Bulk item creation | Consistent defaults, validated params |
| Error wrapper | All API calls | Classifies errors as retryable vs auth vs input |
| Multi-tenant | SaaS applications | Isolates users, manages token lifecycle |
| Zod validation | Response parsing | Runtime safety against API changes |

## Resources

- [Miro Node.js Client](https://developers.miro.com/docs/miro-nodejs-api-client)
- [Miro Node.js Readme](https://developers.miro.com/docs/miro-nodejs-readme)
- [REST API Reference](https://developers.miro.com/docs/rest-api-reference-guide)

## Next Steps

Apply these patterns in `miro-core-workflow-a` for board management operations.
