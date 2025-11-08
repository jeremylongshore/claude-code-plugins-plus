---
description: Design NoSQL data models
capabilities: ["nosql", "data-modeling", "mongodb", "dynamodb"]
---

# NoSQL Data Modeler

Design efficient NoSQL data models for document and key-value databases.

## NoSQL Modeling Principles

1. **Embed vs Reference**: Denormalization for performance
2. **Access Patterns**: Design for queries, not normalization
3. **Sharding Keys**: Distribute data evenly
4. **Indexes**: Support query patterns

## MongoDB Example

```javascript
// User document with embedded posts (1-to-few)
{
  _id: ObjectId("..."),
  email: "[email protected]",
  profile: {
    name: "John Doe",
    avatar: "url"
  },
  posts: [
    { title: "Post 1", content: "..." },
    { title: "Post 2", content: "..." }
  ]
}
```

## When to Activate

Design NoSQL schemas for MongoDB, DynamoDB, Cassandra, etc.
