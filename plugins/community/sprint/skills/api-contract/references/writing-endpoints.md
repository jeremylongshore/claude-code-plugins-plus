# Writing Endpoints

## Writing Endpoints

### Endpoint Definition

```markdown
#### POST /auth/register

Create a new user account.

**Request:**
```json
{
  "email": "string (required, valid email)",
  "password": "string (required, min 8 chars)",
  "name": "string (optional)"
}
```

**Response (201):**

```json
{
  "id": "uuid",
  "email": "string",
  "name": "string | null",
  "createdAt": "ISO 8601 datetime"
}
```

**Errors:**

- 400: Invalid request body
- 409: Email already exists
- 422: Validation failed

```

### Key Elements

| Element | Purpose |
|---------|---------|
| Method + Route | HTTP verb and path |
| Description | What the endpoint does |
| Request | Input schema with types and constraints |
| Response | Output schema with status code |
| Errors | Possible error responses |
