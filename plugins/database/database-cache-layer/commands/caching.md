---
description: Implement database caching strategies
---

# Database Cache Layer

Implement caching to reduce database load.

## Caching Strategies

1. **Query Result Cache**: Cache query results (Redis)
2. **ORM-Level Cache**: Framework caching
3. **Application Cache**: In-memory caching
4. **CDN Caching**: Static content

## Redis Example

```javascript
const redis = require('redis');
const client = redis.createClient();

async function getUser(id) {
  // Check cache first
  const cached = await client.get(`user:${id}`);
  if (cached) return JSON.parse(cached);

  // Query database
  const user = await db.query('SELECT * FROM users WHERE id = $1', [id]);

  // Cache for 1 hour
  await client.setex(`user:${id}`, 3600, JSON.stringify(user));

  return user;
}
```

## When Invoked

Design caching layer for database optimization.
