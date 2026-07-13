# Framework-Specific Templates

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
