# Composer Workflow Patterns

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
