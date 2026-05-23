# Best Practices

## Best Practices

### Be Specific

```markdown
// Good
"email": "string (required, valid email format)"

// Bad
"email": "string"
```

### Include Examples

```markdown
**Request Example:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

```

### Document All States

Include responses for:
- Success (200, 201, 204)
- Client errors (400, 401, 403, 404, 422)
- Empty states (empty arrays, null values)

### Keep It DRY

Reference shared types instead of duplicating:

```markdown
**Response:** `User` (see TypeScript Interfaces)
```

### No Implementation Details

The contract defines WHAT, not HOW:

- Don't mention database columns
- Don't specify frameworks
- Don't include file paths
