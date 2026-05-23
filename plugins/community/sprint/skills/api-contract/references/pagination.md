# Pagination

## Pagination

For list endpoints:

```markdown
#### GET /products

List products with pagination.

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| page | integer | 1 | Page number |
| limit | integer | 20 | Items per page (max 100) |
| sort | string | createdAt | Sort field |
| order | string | desc | Sort order (asc/desc) |

**Response (200):**
```json
{
  "data": [Product],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

```

### Pagination Interface

```typescript
interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```
