---
name: gamma-sdk-patterns
description: |
  Learn idiomatic Gamma SDK patterns and best practices.
  Use when implementing complex presentation workflows,
  handling async operations, or structuring Gamma code.
  Trigger with phrases like "gamma patterns", "gamma best practices",
  "gamma SDK usage", "gamma async", "gamma code structure".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma SDK Patterns

## Overview
Learn idiomatic patterns and best practices for the Gamma SDK to build robust presentation automation.

## Prerequisites
- Completed `gamma-local-dev-loop` setup
- Familiarity with async/await patterns
- TypeScript recommended

## Instructions

### Step 1: Client Singleton
```typescript
// lib/gamma.ts
import { GammaClient } from '@gamma/sdk';

let client: GammaClient | null = null;

export function getGammaClient(): GammaClient {
  if (!client) {
    client = new GammaClient({
      apiKey: process.env.GAMMA_API_KEY,
      timeout: 30000,  # 30000: 30 seconds in ms
      retries: 3,
    });
  }
  return client;
}
```

### Step 2: Presentation Builder
```typescript
// lib/presentation-builder.ts
import { getGammaClient } from './gamma';

interface SlideContent {
  title: string;
  content: string;
  layout?: 'title' | 'content' | 'image' | 'split';
}

export class PresentationBuilder {
  private slides: SlideContent[] = [];
  private title: string = '';
  private style: string = 'professional';

  setTitle(title: string): this {
    this.title = title;
    return this;
  }

  addSlide(slide: SlideContent): this {
    this.slides.push(slide);
    return this;
  }

  setStyle(style: string): this {
    this.style = style;
    return this;
  }

  async build() {
    const gamma = getGammaClient();
    return gamma.presentations.create({
      title: this.title,
      slides: this.slides,
      style: this.style,
    });
  }
}
```

### Step 3: Error Handling Wrapper
```typescript
// lib/safe-gamma.ts
import { GammaError } from '@gamma/sdk';

export async function safeGammaCall<T>(
  fn: () => Promise<T>
): Promise<{ data: T; error: null } | { data: null; error: string }> {
  try {
    const data = await fn();
    return { data, error: null };
  } catch (err) {
    if (err instanceof GammaError) {
      return { data: null, error: err.message };
    }
    throw err;
  }
}
```

### Step 4: Template Factory
```typescript
// lib/templates.ts
type TemplateType = 'pitch-deck' | 'report' | 'tutorial' | 'proposal';

const TEMPLATES: Record<TemplateType, object> = {
  'pitch-deck': { slides: 10, style: 'bold' },
  'report': { slides: 15, style: 'professional' },
  'tutorial': { slides: 8, style: 'friendly' },
  'proposal': { slides: 12, style: 'corporate' },
};

export function fromTemplate(type: TemplateType, title: string) {
  return { ...TEMPLATES[type], title };
}
```

## Output
- Reusable client singleton
- Fluent builder pattern
- Type-safe error handling
- Template factory system

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | Multiple modules | Consistent config |
| Builder | Complex presentations | Readable code |
| Safe Call | Error boundaries | Graceful failures |
| Factory | Repeated templates | DRY code |

## Resources
- [Gamma SDK Patterns](https://gamma.app/docs/patterns)
- [TypeScript Design Patterns](https://refactoring.guru/design-patterns/typescript)

## Next Steps
Proceed to `gamma-core-workflow-a` for presentation generation workflows.

## Examples

**Basic usage**: Apply gamma sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize gamma sdk patterns for production environments with multiple constraints and team-specific requirements.