---
name: cursor-composer-workflows
description: |
  Master Cursor Composer for multi-file AI edits. Triggers on "cursor composer",
  "multi-file edit", "cursor generate files", "composer workflow", "cursor scaffold".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Composer Workflows

## Composer Overview

### What is Composer?
```
Composer = Multi-file AI code generation/editing
- Create multiple files at once
- Refactor across codebase
- Generate entire features
- Scaffold new projects
```

### Opening Composer
```
Mac: Cmd+I
Windows/Linux: Ctrl+I
Or: Click "Composer" button in sidebar
```

## Basic Composer Usage

### Creating Files
```
Prompt: "Create a React component for a user profile card with:
- Avatar image
- Name and email
- Edit button
- TypeScript + Tailwind CSS"

Composer creates:
- components/UserProfileCard.tsx
- components/UserProfileCard.test.tsx
- types/user.ts (if needed)
```

### Editing Multiple Files
```
Prompt: "Refactor all API calls to use the new fetchWithAuth wrapper:
- Replace fetch() with fetchWithAuth()
- Add proper error handling
- Update TypeScript types"

Composer edits:
- api/users.ts
- api/products.ts
- api/orders.ts
- lib/fetchWithAuth.ts (creates)
```

## Composer Workflow Patterns

### Feature Generation
```
1. Describe the feature completely
2. Specify technologies/patterns
3. Include file structure preference
4. Request tests if needed

Example:
"Create a complete authentication feature:
- Login/register pages (React + Tailwind)
- Auth context with useAuth hook
- Protected route wrapper
- JWT token handling
- API routes for /auth/login, /auth/register
- Unit tests for auth logic
- Follow existing project patterns"
```

### Incremental Building
```
Session 1: "Create the database schema for a blog"
Session 2: "Add API routes for CRUD operations"
Session 3: "Create the frontend components"
Session 4: "Add form validation"
Session 5: "Write integration tests"

Each session builds on previous work
```

### Pattern Replication
```
"Look at how UserService is structured in services/UserService.ts
Create similar services for:
- ProductService
- OrderService
- InventoryService

Follow the same patterns for:
- Error handling
- Logging
- Type definitions"
```

## Advanced Composer Techniques

### Context Injection
```
Use @-mentions to give context:

"@auth.ts @middleware.ts
Create a rate-limiting middleware that:
- Uses the same patterns as auth.ts
- Integrates with existing middleware chain
- Adds Redis-based rate limiting"
```

### File Structure Control
```
Be explicit about structure:

"Create in this structure:
src/
  features/
    auth/
      components/
        LoginForm.tsx
        RegisterForm.tsx
      hooks/
        useAuth.ts
      api/
        authApi.ts
      types/
        auth.types.ts
      index.ts"
```

### Incremental Refinement
```
Initial: "Create a user dashboard"
Refine: "Add a sidebar navigation"
Refine: "Make the layout responsive"
Refine: "Add dark mode support"
Refine: "Optimize for performance"
```

## Best Practices

### Clear Specifications
```
Good prompt structure:
1. What to create/modify
2. Technology stack
3. Specific requirements
4. Patterns to follow
5. Files to reference

Example:
"CREATE: Payment processing module
TECH: TypeScript, Stripe SDK, Express
REQUIREMENTS:
- Webhook handler for payment events
- Idempotent payment creation
- Refund handling
- Audit logging
FOLLOW: patterns in @orderService.ts
REFERENCE: Stripe best practices"
```

### Review Before Apply
```
Composer shows preview:
1. Review each file change
2. Check for unintended modifications
3. Verify imports are correct
4. Ensure tests are included
5. Click "Apply" or request changes
```

### Iterative Workflow
```
Don't try to do everything at once:

Phase 1: Core functionality
Phase 2: Error handling
Phase 3: Tests
Phase 4: Documentation
Phase 5: Optimization

Review and test between phases
```

## Common Use Cases

### API Development
```
"Create a REST API for product management:
- GET/POST/PUT/DELETE /products
- Pagination support
- Search and filtering
- Input validation
- Error responses following RFC 7807
- TypeScript types
- Integration tests"
```

### Component Libraries
```
"Create a form component library:
- TextInput with validation
- Select with async options
- DatePicker
- FileUpload with progress
- Form wrapper with submission handling
- Storybook stories for each
- Unit tests"
```

### Database Operations
```
"Create database layer for user management:
- Prisma schema for User model
- Repository pattern implementation
- Migration file
- Seed data script
- Query helpers for common operations"
```

### Refactoring
```
"Refactor the authentication system:
- Move from localStorage to httpOnly cookies
- Add refresh token rotation
- Update all components using auth
- Add CSRF protection
- Update tests"
```

## Troubleshooting Composer

### Composer Not Finding Files
```
Solutions:
1. Use explicit paths: @src/components/Button.tsx
2. Check indexing is complete
3. File not in .cursorignore
4. Use relative paths from project root
```

### Changes Not As Expected
```
Solutions:
1. Be more specific in prompt
2. Provide example of desired output
3. Reference existing patterns
4. Break into smaller changes
```

### Composer Timeouts
```
For large changes:
1. Break into smaller requests
2. Use faster model
3. Reduce context size
4. Wait and retry
```

## Keyboard Shortcuts

```
Cmd+I / Ctrl+I    Open Composer
Tab               Accept current suggestion
Esc               Cancel/close
Enter             Send prompt
Shift+Enter       New line in prompt
Cmd+Enter         Apply all changes
```
