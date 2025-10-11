---
description: Build a GraphQL server with schema-first design
shortcut: gql
---

# Build GraphQL Server

Create a production-ready GraphQL server with type-safe schema, resolvers, authentication, and real-time subscriptions.

## What You Do

1. **Ask for schema details:**
   - What types/models? (User, Post, Comment)
   - What queries? (getUser, listPosts)
   - What mutations? (createUser, updatePost)
   - Subscriptions needed? (onNewPost, onCommentAdded)
   - Framework? (Apollo Server, GraphQL Yoga, Mercurius)

2. **Generate complete GraphQL structure:**
   - **Schema definition** - Types, queries, mutations, subscriptions
   - **Resolvers** - Business logic for each field
   - **Data loaders** - Batch and cache database queries
   - **Directives** - Custom @auth, @deprecated, @cost
   - **Subscriptions** - Real-time updates with WebSockets
   - **Error handling** - Custom errors with extensions

3. **Follow GraphQL best practices:**
   - Schema-first design with SDL
   - Proper nullability (`!` for required fields)
   - Connection pattern for pagination
   - Input types for mutations
   - Relay-compatible cursor pagination
   - DataLoader for N+1 query prevention
   - Query depth limiting
   - Query complexity analysis

4. **Generate tooling:**
   - GraphQL Playground/GraphiQL
   - Schema introspection
   - Apollo Studio integration
   - Automatic documentation
   - TypeScript types from schema

## Example Schema

```graphql
type User {
  id: ID!
  name: String!
  email: String!
  posts(first: Int, after: String): PostConnection!
  createdAt: DateTime!
}

type Post {
  id: ID!
  title: String!
  content: String!
  author: User!
  comments: [Comment!]!
  publishedAt: DateTime
}

type Query {
  user(id: ID!): User
  users(first: Int, after: String): UserConnection!
  post(id: ID!): Post
  searchPosts(query: String!): [Post!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updatePost(id: ID!, input: UpdatePostInput!): Post!
  deletePost(id: ID!): Boolean!
}

type Subscription {
  postCreated: Post!
  commentAdded(postId: ID!): Comment!
}

input CreateUserInput {
  name: String!
  email: String!
}

type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}
```

## Key Features

- **Type safety** - Strong typing with schema validation
- **Real-time** - WebSocket subscriptions
- **Batching** - DataLoader for efficient queries
- **Authentication** - Context-based auth, directive guards
- **Pagination** - Relay-style cursor pagination
- **Caching** - Field-level caching with Apollo
- **Introspection** - Self-documenting API
- **Error handling** - Typed error responses
- **Rate limiting** - Query complexity limits
- **Monitoring** - Apollo Studio metrics

Generate production-ready GraphQL servers with best practices and proper architecture.
