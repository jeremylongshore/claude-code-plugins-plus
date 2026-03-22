---
name: figma-sdk-patterns
description: |
  Production-ready patterns for the Figma REST API and Plugin API.
  Use when building reusable Figma client wrappers, extracting design tokens,
  traversing node trees, or creating typed API helpers.
  Trigger with phrases like "figma patterns", "figma best practices",
  "figma client wrapper", "figma typed API".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma SDK Patterns

## Overview
Production patterns for the Figma REST API (external tools) and Plugin API (in-editor plugins). Figma has no official Node.js SDK -- you call `https://api.figma.com` directly with `fetch`. These patterns give you type safety, error handling, and reusable abstractions.

## Prerequisites
- `FIGMA_PAT` environment variable set
- TypeScript 5+ project
- Understanding of Figma node types

## Instructions

### Step 1: Typed REST API Client
```typescript
// src/figma-client.ts
export class FigmaClient {
  private baseUrl = 'https://api.figma.com';

  constructor(private token: string) {
    if (!token) throw new Error('Figma token is required');
  }

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      ...init,
      headers: {
        'X-Figma-Token': this.token,
        'Content-Type': 'application/json',
        ...init?.headers,
      },
    });

    if (res.status === 429) {
      const retryAfter = parseInt(res.headers.get('Retry-After') || '60');
      throw new FigmaRateLimitError(retryAfter);
    }
    if (res.status === 403) throw new FigmaAuthError('Invalid or expired token');
    if (res.status === 404) throw new FigmaNotFoundError(path);
    if (!res.ok) throw new FigmaApiError(res.status, await res.text());

    return res.json();
  }

  async getFile(fileKey: string) {
    return this.request<FigmaFileResponse>(`/v1/files/${fileKey}`);
  }

  async getFileNodes(fileKey: string, nodeIds: string[]) {
    const ids = encodeURIComponent(nodeIds.join(','));
    return this.request<FigmaNodesResponse>(`/v1/files/${fileKey}/nodes?ids=${ids}`);
  }

  async getImages(fileKey: string, nodeIds: string[], opts?: ImageOptions) {
    const params = new URLSearchParams({
      ids: nodeIds.join(','),
      format: opts?.format ?? 'png',
      scale: String(opts?.scale ?? 2),
    });
    return this.request<FigmaImagesResponse>(`/v1/images/${fileKey}?${params}`);
  }

  async getComments(fileKey: string) {
    return this.request<FigmaCommentsResponse>(`/v1/files/${fileKey}/comments`);
  }

  async postComment(fileKey: string, message: string, nodeId?: string) {
    return this.request(`/v1/files/${fileKey}/comments`, {
      method: 'POST',
      body: JSON.stringify({
        message,
        ...(nodeId && { client_meta: { node_id: nodeId } }),
      }),
    });
  }

  async getLocalVariables(fileKey: string) {
    return this.request<FigmaVariablesResponse>(
      `/v1/files/${fileKey}/variables/local`
    );
  }
}
```

### Step 2: Custom Error Classes
```typescript
// src/figma-errors.ts
export class FigmaApiError extends Error {
  constructor(public status: number, public body: string) {
    super(`Figma API error ${status}: ${body}`);
    this.name = 'FigmaApiError';
  }
}

export class FigmaRateLimitError extends FigmaApiError {
  constructor(public retryAfterSeconds: number) {
    super(429, `Rate limited. Retry after ${retryAfterSeconds}s`);
    this.name = 'FigmaRateLimitError';
  }
}

export class FigmaAuthError extends FigmaApiError {
  constructor(message: string) {
    super(403, message);
    this.name = 'FigmaAuthError';
  }
}

export class FigmaNotFoundError extends FigmaApiError {
  constructor(path: string) {
    super(404, `Resource not found: ${path}`);
    this.name = 'FigmaNotFoundError';
  }
}
```

### Step 3: Type Definitions
```typescript
// src/figma-types.ts
export interface FigmaNode {
  id: string;
  name: string;
  type: string;
  children?: FigmaNode[];
  fills?: Paint[];
  strokes?: Paint[];
  absoluteBoundingBox?: { x: number; y: number; width: number; height: number };
  characters?: string;         // TEXT nodes
  style?: TypeStyle;           // TEXT nodes
  componentId?: string;        // INSTANCE nodes
  backgroundColor?: Color;     // CANVAS nodes
}

export interface FigmaFileResponse {
  name: string;
  lastModified: string;
  version: string;
  thumbnailUrl: string;
  document: FigmaNode;
  components: Record<string, ComponentMeta>;
  styles: Record<string, StyleMeta>;
}

export interface FigmaNodesResponse {
  nodes: Record<string, { document: FigmaNode; components: Record<string, ComponentMeta> }>;
}

export interface FigmaImagesResponse {
  images: Record<string, string | null>;  // nodeId -> URL (null = render failed)
}

export interface ImageOptions {
  format?: 'png' | 'svg' | 'jpg' | 'pdf';
  scale?: number;  // 0.01 to 4. SVG always exports at 1x.
}

interface Paint { type: string; color?: Color; opacity?: number }
interface Color { r: number; g: number; b: number; a?: number }
interface TypeStyle { fontFamily: string; fontSize: number; fontWeight: number }
interface ComponentMeta { key: string; name: string; description: string }
interface StyleMeta { key: string; name: string; style_type: 'FILL' | 'TEXT' | 'EFFECT' | 'GRID' }
```

### Step 4: Node Tree Walker
```typescript
// Walk the Figma document tree with a visitor pattern
function walkNodes(node: FigmaNode, visitor: (n: FigmaNode) => void) {
  visitor(node);
  if (node.children) {
    for (const child of node.children) {
      walkNodes(child, visitor);
    }
  }
}

// Example: find all TEXT nodes
function findTextNodes(root: FigmaNode): FigmaNode[] {
  const results: FigmaNode[] = [];
  walkNodes(root, (n) => {
    if (n.type === 'TEXT') results.push(n);
  });
  return results;
}

// Example: find all COMPONENT nodes
function findComponents(root: FigmaNode): FigmaNode[] {
  const results: FigmaNode[] = [];
  walkNodes(root, (n) => {
    if (n.type === 'COMPONENT') results.push(n);
  });
  return results;
}
```

### Step 5: Singleton with Retry
```typescript
// Singleton instance with automatic retry on transient errors
let client: FigmaClient | null = null;

export function getFigmaClient(): FigmaClient {
  if (!client) {
    client = new FigmaClient(process.env.FIGMA_PAT!);
  }
  return client;
}

export async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries = 3
): Promise<T> {
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await fn();
    } catch (err) {
      if (err instanceof FigmaRateLimitError) {
        await new Promise(r => setTimeout(r, err.retryAfterSeconds * 1000));
        continue;
      }
      if (attempt === maxRetries) throw err;
      await new Promise(r => setTimeout(r, 1000 * Math.pow(2, attempt)));
    }
  }
  throw new Error('Unreachable');
}
```

## Output
- Typed Figma REST API client with full error handling
- Custom error hierarchy for rate limits, auth, not found
- Node tree walker for extracting design data
- Singleton pattern with retry logic

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Typed errors | `catch (e) { if (e instanceof FigmaRateLimitError) }` | Targeted recovery |
| Node walker | Traversing arbitrarily deep trees | Handles any file structure |
| Retry wrapper | Transient 429/5xx errors | Automatic recovery |
| Singleton | Shared client across modules | Consistent config, one token |

## Resources
- [Figma REST API Reference](https://developers.figma.com/docs/rest-api/)
- [Figma REST API OpenAPI Spec](https://github.com/figma/rest-api-spec)
- [figma-api npm package](https://www.npmjs.com/package/figma-api) (community SDK)

## Next Steps
Apply patterns in `figma-core-workflow-a` for real-world file inspection.
