---
description: Implement database sharding strategies
---

# Database Sharding Manager

Distribute data across multiple database instances.

## Sharding Strategies

1. **Range-Based**: Shard by ID ranges (1-1M, 1M-2M)
2. **Hash-Based**: Hash key determines shard
3. **Geographic**: Shard by location
4. **Functional**: Shard by feature (users, orders)

## Sharding Example

```javascript
function getShardForUser(userId) {
  const shardCount = 4;
  const shardId = userId % shardCount;
  return database.getShard(shardId);
}

async function getUserData(userId) {
  const shard = getShardForUser(userId);
  return await shard.query('SELECT * FROM users WHERE id = ?', [userId]);
}
```

## When Invoked

Design sharding architecture for horizontal scaling.
