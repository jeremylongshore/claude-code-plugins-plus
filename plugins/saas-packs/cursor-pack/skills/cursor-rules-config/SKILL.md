---
name: cursor-rules-config
description: |
  Configure .cursorrules for project-specific AI behavior. Triggers on "cursorrules",
  ".cursorrules", "cursor rules", "cursor config", "cursor project settings".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# .cursorrules Configuration Guide

## Overview

### What is .cursorrules?
```
.cursorrules is a project-level configuration file that:
- Guides AI code generation style
- Enforces coding standards
- Provides project context
- Customizes AI behavior per project
```

### File Location
```
Place at project root:
my-project/
├── .cursorrules      ← Here
├── src/
├── package.json
└── ...
```

## Basic Configuration

### Minimal Example
```yaml
# .cursorrules

# Project language and framework
language: typescript
framework: react

# Key coding rules
rules:
  - Use functional components
  - Prefer async/await over callbacks
  - Always handle errors explicitly
```

### Standard Template
```yaml
# .cursorrules

project: my-awesome-app
description: E-commerce platform built with Next.js

language: typescript
framework: nextjs
styling: tailwindcss
testing: vitest

rules:
  # Code Style
  - Use TypeScript strict mode
  - Prefer const over let
  - Use arrow functions for callbacks
  - Maximum line length: 100 characters

  # React Patterns
  - Use functional components only
  - Prefer hooks over HOCs
  - Use React Query for data fetching
  - Handle loading and error states

  # Architecture
  - Follow feature-based folder structure
  - Keep components under 200 lines
  - Extract business logic to hooks
  - Use dependency injection for services

naming:
  files: kebab-case
  components: PascalCase
  functions: camelCase
  constants: SCREAMING_SNAKE_CASE
  types: PascalCase with suffix (UserDTO, ProductResponse)

imports:
  order:
    - react, next (framework)
    - third-party packages
    - @/components
    - @/hooks
    - @/lib
    - @/types
    - relative imports
```

## Advanced Configuration

### Context Section
```yaml
context:
  # Key architectural decisions
  architecture: |
    We use a feature-based architecture where each feature
    (auth, products, cart) contains its own components, hooks,
    and API calls. Shared utilities go in lib/.

  # Important patterns
  patterns: |
    - Data fetching: useQuery from @tanstack/react-query
    - Forms: react-hook-form with zod validation
    - State: Zustand for global state
    - API: tRPC for type-safe APIs

  # Things to avoid
  avoid: |
    - Class components
    - Redux (we use Zustand)
    - CSS-in-JS (we use Tailwind)
    - Direct fetch() calls (use our api client)
```

### Examples Section
```yaml
examples:
  component: |
    // Example component structure
    import { useState } from 'react';
    import { Button } from '@/components/ui';

    interface Props {
      title: string;
      onAction: () => void;
    }

    export function MyComponent({ title, onAction }: Props) {
      const [loading, setLoading] = useState(false);

      return (
        <div className="p-4">
          <h2 className="text-lg font-bold">{title}</h2>
          <Button onClick={onAction} loading={loading}>
            Action
          </Button>
        </div>
      );
    }

  api-route: |
    // Example API route
    import { NextRequest, NextResponse } from 'next/server';
    import { z } from 'zod';

    const schema = z.object({
      name: z.string().min(1),
    });

    export async function POST(req: NextRequest) {
      try {
        const body = await req.json();
        const data = schema.parse(body);
        // Process...
        return NextResponse.json({ success: true });
      } catch (error) {
        return NextResponse.json(
          { error: 'Invalid request' },
          { status: 400 }
        );
      }
    }
```

### Testing Section
```yaml
testing:
  framework: vitest
  patterns:
    - Use describe/it blocks
    - Follow AAA pattern (Arrange, Act, Assert)
    - Mock external dependencies
    - Test edge cases and error paths

  example: |
    import { describe, it, expect, vi } from 'vitest';
    import { render, screen } from '@testing-library/react';
    import { MyComponent } from './MyComponent';

    describe('MyComponent', () => {
      it('renders title correctly', () => {
        render(<MyComponent title="Test" onAction={vi.fn()} />);
        expect(screen.getByText('Test')).toBeInTheDocument();
      });

      it('calls onAction when button clicked', async () => {
        const onAction = vi.fn();
        render(<MyComponent title="Test" onAction={onAction} />);
        await userEvent.click(screen.getByRole('button'));
        expect(onAction).toHaveBeenCalled();
      });
    });
```

## Framework-Specific Templates

### Next.js App Router
```yaml
# .cursorrules for Next.js App Router

framework: nextjs-app-router
version: "14"

rules:
  - Use App Router conventions (app/ directory)
  - Server Components by default
  - "use client" only when needed
  - Use Server Actions for mutations
  - Implement loading.tsx and error.tsx

file-conventions:
  - page.tsx for routes
  - layout.tsx for layouts
  - loading.tsx for suspense
  - error.tsx for error boundaries
  - not-found.tsx for 404s
```

### Express/Node.js Backend
```yaml
# .cursorrules for Express API

framework: express
database: postgresql
orm: prisma

rules:
  - Use async/await for all async operations
  - Implement proper error handling middleware
  - Validate all inputs with zod
  - Use dependency injection for testability
  - Follow REST conventions

structure:
  - routes/ for Express routers
  - controllers/ for request handlers
  - services/ for business logic
  - repositories/ for data access
  - middleware/ for Express middleware
```

### Python FastAPI
```yaml
# .cursorrules for FastAPI

language: python
framework: fastapi
version: "0.100+"

rules:
  - Use Pydantic models for validation
  - Implement proper dependency injection
  - Use async where beneficial
  - Follow PEP 8 style guide
  - Type hints on all functions

structure:
  - app/routers/ for route handlers
  - app/models/ for Pydantic models
  - app/services/ for business logic
  - app/db/ for database operations
```

## Tips for Effective Rules

### Be Specific
```yaml
# Vague (less effective)
rules:
  - Write good code
  - Handle errors

# Specific (more effective)
rules:
  - Wrap async operations in try/catch
  - Return typed error responses using ApiError class
  - Log errors with context using logger.error()
```

### Include Examples
```yaml
# Examples help AI understand your patterns
error-handling-example: |
  try {
    const result = await someOperation();
    return { success: true, data: result };
  } catch (error) {
    logger.error('Operation failed', { error, context });
    throw new ApiError('OPERATION_FAILED', 500);
  }
```

### Reference Project Files
```yaml
context:
  reference-files:
    - See @lib/api-client.ts for API patterns
    - See @components/Button.tsx for component structure
    - See @hooks/useAuth.ts for hook patterns
```

## Verification

### Test Your Rules
```
1. Create new file
2. Ask Cursor to generate code
3. Check if it follows your rules
4. Refine rules if needed
```

### Common Issues
```
Problem: Rules not applied
Solution: Ensure .cursorrules is at project root

Problem: Inconsistent output
Solution: Add more specific examples

Problem: Rules conflict
Solution: Prioritize rules, remove conflicts
```
