# Domain-Specific Prompts

## Domain-Specific Prompts

### API Development

```
"Create REST endpoint for [resource]:

Method: [GET/POST/PUT/DELETE]
Path: /api/[path]

Request:
- Body: [schema]
- Params: [params]
- Query: [query params]

Response:
- Success: [schema]
- Errors: [error codes]

Include:
- Input validation (Zod)
- Error handling
- TypeScript types
- Rate limiting (optional)"
```

### React Components

```
"Create React component [Name]:

Purpose: [what it does]

Props:
- [prop1]: [type] - [description]
- [prop2]: [type] - [description]

State:
- [what state it manages]

Behavior:
- [interaction 1]
- [interaction 2]

Styling: Tailwind CSS
Accessibility: WCAG 2.1 AA"
```

### Database Operations

```
"Create database [operation] for [entity]:

ORM: Prisma
Operation: [CRUD type]

Schema context:
@prisma/schema.prisma

Requirements:
- [Requirement 1]
- [Requirement 2]

Return:
- [What to return]

Handle:
- Not found
- Validation errors
- Database errors"
```
