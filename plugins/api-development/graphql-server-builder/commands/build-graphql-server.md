---
description: Build a GraphQL server with schema-first design
shortcut: gql
---

# Build GraphQL Server

Create a production-ready GraphQL server with type-safe schemas, optimized resolvers, real-time subscriptions, authentication, and comprehensive tooling using schema-first design principles.

## When to Use This Command

Use `/build-graphql-server` when you need to:
- Build flexible APIs with client-specified queries
- Implement real-time features with subscriptions
- Reduce over-fetching and under-fetching of data
- Create strongly-typed API contracts
- Support multiple client applications with different data needs
- Build microservices with federation support

DON'T use this when:
- Building simple CRUD APIs (REST may be simpler)
- Clients have limited GraphQL knowledge (learning curve)
- Caching is critical and simple (REST caching is more straightforward)

## Design Decisions

This command implements **Apollo Server with DataLoader** as the primary approach because:
- Most mature GraphQL server implementation
- Excellent TypeScript support
- Built-in performance optimizations
- Rich ecosystem of tools and plugins
- Production-proven at scale
- Comprehensive monitoring with Apollo Studio

**Alternative considered: GraphQL Yoga**
- More lightweight and modular
- Better for serverless deployments
- Newer with smaller ecosystem
- Recommended for edge computing

**Alternative considered: Mercurius (Fastify)**
- Fastest GraphQL server
- Better for high-performance requirements
- Less mature ecosystem
- Recommended when performance is critical

## Prerequisites

Before running this command:
1. Define your domain models and relationships
2. Choose database and ORM/ODM
3. Plan authentication strategy
4. Determine subscription requirements
5. Identify performance requirements

## Implementation Process

### Step 1: Design GraphQL Schema
Create comprehensive type definitions with proper nullability and relationships.

### Step 2: Implement Resolvers
Build efficient resolvers with DataLoader for batching and caching.

### Step 3: Add Authentication & Authorization
Implement context-based auth with field-level permissions.

### Step 4: Set Up Subscriptions
Configure WebSocket server for real-time updates.

### Step 5: Optimize Performance
Add query complexity analysis, depth limiting, and caching.

## Output Format

The command generates:
- `schema/` - GraphQL schema definitions
- `resolvers/` - Resolver implementations
- `dataloaders/` - DataLoader configurations
- `directives/` - Custom schema directives
- `server.js` - Apollo Server setup
- `generated/types.ts` - TypeScript definitions
- `tests/` - Integration and unit tests

## Code Examples

### Example 1: Complete GraphQL Server with Apollo Server

```javascript
// schema/schema.graphql
scalar DateTime
scalar Upload

directive @auth(requires: Role = USER) on FIELD_DEFINITION
directive @rateLimit(max: Int, window: String) on FIELD_DEFINITION
directive @deprecated(reason: String) on FIELD_DEFINITION | ENUM_VALUE

enum Role {
  USER
  MODERATOR
  ADMIN
}

type User {
  id: ID!
  username: String!
  email: String!
  role: Role!
  profile: Profile
  posts(
    first: Int
    after: String
    orderBy: PostOrderBy
    filter: PostFilter
  ): PostConnection!
  followers: [User!]!
  following: [User!]!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Profile {
  bio: String
  avatar: String
  website: String
  location: String
}

type Post {
  id: ID!
  title: String!
  content: String!
  excerpt: String
  author: User!
  tags: [Tag!]!
  comments(first: Int, after: String): CommentConnection!
  likes: Int!
  views: Int!
  published: Boolean!
  publishedAt: DateTime
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Comment {
  id: ID!
  content: String!
  author: User!
  post: Post!
  parentComment: Comment
  replies: [Comment!]!
  likes: Int!
  createdAt: DateTime!
  updatedAt: DateTime!
}

type Tag {
  id: ID!
  name: String!
  slug: String!
  posts(first: Int, after: String): PostConnection!
}

# Relay-style pagination types
type PostConnection {
  edges: [PostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type PostEdge {
  node: Post!
  cursor: String!
}

type CommentConnection {
  edges: [CommentEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type CommentEdge {
  node: Comment!
  cursor: String!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}

# Input types
input CreateUserInput {
  username: String!
  email: String!
  password: String!
  profile: ProfileInput
}

input ProfileInput {
  bio: String
  avatar: String
  website: String
  location: String
}

input CreatePostInput {
  title: String!
  content: String!
  tags: [String!]
  published: Boolean
}

input UpdatePostInput {
  title: String
  content: String
  tags: [String!]
  published: Boolean
}

input PostFilter {
  published: Boolean
  authorId: ID
  tags: [String!]
  searchQuery: String
}

enum PostOrderBy {
  CREATED_AT_DESC
  CREATED_AT_ASC
  LIKES_DESC
  VIEWS_DESC
  TITLE_ASC
}

# Root types
type Query {
  # User queries
  me: User @auth
  user(id: ID!): User
  users(
    first: Int
    after: String
    filter: UserFilter
  ): UserConnection!

  # Post queries
  post(id: ID!): Post
  posts(
    first: Int
    after: String
    orderBy: PostOrderBy
    filter: PostFilter
  ): PostConnection! @rateLimit(max: 100, window: "1m")

  searchPosts(query: String!, first: Int): [Post!]!
  trendingPosts(limit: Int = 10): [Post!]!

  # Tag queries
  tag(slug: String!): Tag
  tags: [Tag!]!
}

type Mutation {
  # Authentication
  signUp(input: CreateUserInput!): AuthPayload!
  signIn(email: String!, password: String!): AuthPayload!
  signOut: Boolean! @auth

  # User mutations
  updateProfile(input: ProfileInput!): User! @auth
  followUser(userId: ID!): User! @auth
  unfollowUser(userId: ID!): User! @auth

  # Post mutations
  createPost(input: CreatePostInput!): Post! @auth
  updatePost(id: ID!, input: UpdatePostInput!): Post! @auth
  deletePost(id: ID!): Boolean! @auth(requires: MODERATOR)
  likePost(postId: ID!): Post! @auth

  # Comment mutations
  addComment(postId: ID!, content: String!, parentId: ID): Comment! @auth
  updateComment(id: ID!, content: String!): Comment! @auth
  deleteComment(id: ID!): Boolean! @auth
}

type Subscription {
  # Post subscriptions
  postCreated(authorId: ID): Post!
  postUpdated(id: ID!): Post!
  postDeleted: ID!

  # Comment subscriptions
  commentAdded(postId: ID!): Comment!
  commentUpdated(postId: ID!): Comment!

  # User activity
  userOnlineStatus(userId: ID!): UserStatus!
}

type AuthPayload {
  token: String!
  user: User!
}

type UserStatus {
  userId: ID!
  online: Boolean!
  lastSeen: DateTime
}

// server.js - Apollo Server setup
const { ApolloServer } = require('@apollo/server');
const { expressMiddleware } = require('@apollo/server/express4');
const { ApolloServerPluginDrainHttpServer } = require('@apollo/server/plugin/drainHttpServer');
const { makeExecutableSchema } = require('@graphql-tools/schema');
const { WebSocketServer } = require('ws');
const { useServer } = require('graphql-ws/lib/use/ws');
const express = require('express');
const http = require('http');
const cors = require('cors');
const DataLoader = require('dataloader');
const depthLimit = require('graphql-depth-limit');
const costAnalysis = require('graphql-cost-analysis');

// Import schema and resolvers
const typeDefs = require('./schema/typeDefs');
const resolvers = require('./resolvers');
const { authDirective } = require('./directives/auth');
const { rateLimitDirective } = require('./directives/rateLimit');

// Create executable schema with directives
let schema = makeExecutableSchema({
  typeDefs,
  resolvers
});

// Apply schema directives
schema = authDirective(schema, 'auth');
schema = rateLimitDirective(schema, 'rateLimit');

// Create Express app and HTTP server
const app = express();
const httpServer = http.createServer(app);

// Create WebSocket server for subscriptions
const wsServer = new WebSocketServer({
  server: httpServer,
  path: '/graphql'
});

// Create DataLoaders for batching
function createDataLoaders(db) {
  return {
    userLoader: new DataLoader(async (userIds) => {
      const users = await db.user.findMany({
        where: { id: { in: userIds } }
      });
      const userMap = new Map(users.map(user => [user.id, user]));
      return userIds.map(id => userMap.get(id));
    }),

    postLoader: new DataLoader(async (postIds) => {
      const posts = await db.post.findMany({
        where: { id: { in: postIds } }
      });
      const postMap = new Map(posts.map(post => [post.id, post]));
      return postIds.map(id => postMap.get(id));
    }),

    commentsByPostLoader: new DataLoader(async (postIds) => {
      const comments = await db.comment.findMany({
        where: { postId: { in: postIds } },
        orderBy: { createdAt: 'desc' }
      });

      const commentsByPost = {};
      comments.forEach(comment => {
        if (!commentsByPost[comment.postId]) {
          commentsByPost[comment.postId] = [];
        }
        commentsByPost[comment.postId].push(comment);
      });

      return postIds.map(id => commentsByPost[id] || []);
    })
  };
}

// Configure WebSocket server for subscriptions
const serverCleanup = useServer(
  {
    schema,
    context: async (ctx) => {
      // Return context for subscriptions
      return {
        db,
        pubsub,
        user: await authenticateWebSocket(ctx.connectionParams)
      };
    }
  },
  wsServer
);

// Create Apollo Server
const server = new ApolloServer({
  schema,
  plugins: [
    ApolloServerPluginDrainHttpServer({ httpServer }),
    {
      async serverWillStart() {
        return {
          async drainServer() {
            await serverCleanup.dispose();
          }
        };
      }
    }
  ],
  validationRules: [
    depthLimit(10),
    costAnalysis({
      maximumCost: 1000,
      defaultCost: 1,
      scalarCost: 1,
      objectCost: 10,
      listFactor: 10
    })
  ],
  formatError: (error) => {
    // Custom error formatting
    console.error(error);

    // Remove stack trace in production
    if (process.env.NODE_ENV === 'production') {
      delete error.extensions.stacktrace;
    }

    return {
      message: error.message,
      extensions: {
        code: error.extensions.code,
        timestamp: Date.now()
      }
    };
  }
});

// Start server
async function startServer() {
  await server.start();

  app.use(
    '/graphql',
    cors(),
    express.json(),
    expressMiddleware(server, {
      context: async ({ req }) => {
        // Get the user from JWT token
        const token = req.headers.authorization?.replace('Bearer ', '');
        const user = token ? await verifyToken(token) : null;

        // Create DataLoaders for this request
        const loaders = createDataLoaders(db);

        return {
          db,
          user,
          loaders,
          pubsub,
          req
        };
      }
    })
  );

  await new Promise((resolve) => httpServer.listen({ port: 4000 }, resolve));
  console.log(`🚀 Server ready at http://localhost:4000/graphql`);
}

startServer().catch(console.error);
```

### Example 2: Optimized Resolvers with DataLoader

```javascript
// resolvers/index.js
const { GraphQLScalarType } = require('graphql');
const { PubSub, withFilter } = require('graphql-subscriptions');
const DataLoader = require('dataloader');

const pubsub = new PubSub();

const resolvers = {
  // Custom scalar for DateTime
  DateTime: new GraphQLScalarType({
    name: 'DateTime',
    serialize: (value) => value.toISOString(),
    parseValue: (value) => new Date(value),
    parseLiteral: (ast) => new Date(ast.value)
  }),

  Query: {
    me: async (_, __, { user, loaders }) => {
      if (!user) throw new Error('Not authenticated');
      return loaders.userLoader.load(user.id);
    },

    user: async (_, { id }, { loaders }) => {
      return loaders.userLoader.load(id);
    },

    users: async (_, { first = 10, after, filter }, { db }) => {
      const cursor = after ? { id: after } : undefined;

      const users = await db.user.findMany({
        take: first + 1,
        skip: cursor ? 1 : 0,
        cursor,
        where: filter,
        orderBy: { createdAt: 'desc' }
      });

      const hasNextPage = users.length > first;
      const edges = users.slice(0, first).map(user => ({
        node: user,
        cursor: user.id
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!after,
          startCursor: edges[0]?.cursor,
          endCursor: edges[edges.length - 1]?.cursor
        },
        totalCount: await db.user.count({ where: filter })
      };
    },

    post: async (_, { id }, { loaders }) => {
      const post = await loaders.postLoader.load(id);

      if (post && !post.published) {
        // Check if user can view unpublished posts
        const canView = await checkPostPermission(post, user);
        if (!canView) return null;
      }

      return post;
    },

    posts: async (_, { first = 10, after, orderBy = 'CREATED_AT_DESC', filter }, { db }) => {
      // Build where clause from filter
      const where = {};

      if (filter) {
        if (filter.published !== undefined) {
          where.published = filter.published;
        }
        if (filter.authorId) {
          where.authorId = filter.authorId;
        }
        if (filter.tags?.length) {
          where.tags = {
            some: {
              name: { in: filter.tags }
            }
          };
        }
        if (filter.searchQuery) {
          where.OR = [
            { title: { contains: filter.searchQuery, mode: 'insensitive' } },
            { content: { contains: filter.searchQuery, mode: 'insensitive' } }
          ];
        }
      }

      // Build orderBy from enum
      const orderByMap = {
        CREATED_AT_DESC: { createdAt: 'desc' },
        CREATED_AT_ASC: { createdAt: 'asc' },
        LIKES_DESC: { likes: 'desc' },
        VIEWS_DESC: { views: 'desc' },
        TITLE_ASC: { title: 'asc' }
      };

      const cursor = after ? { id: after } : undefined;

      const posts = await db.post.findMany({
        take: first + 1,
        skip: cursor ? 1 : 0,
        cursor,
        where,
        orderBy: orderByMap[orderBy],
        include: {
          _count: {
            select: { comments: true, likes: true }
          }
        }
      });

      const hasNextPage = posts.length > first;
      const edges = posts.slice(0, first).map(post => ({
        node: post,
        cursor: post.id
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!after,
          startCursor: edges[0]?.cursor,
          endCursor: edges[edges.length - 1]?.cursor
        },
        totalCount: await db.post.count({ where })
      };
    },

    searchPosts: async (_, { query, first = 10 }, { db }) => {
      return db.post.findMany({
        where: {
          published: true,
          OR: [
            { title: { contains: query, mode: 'insensitive' } },
            { content: { contains: query, mode: 'insensitive' } },
            { tags: { some: { name: { contains: query, mode: 'insensitive' } } } }
          ]
        },
        take: first,
        orderBy: { createdAt: 'desc' }
      });
    },

    trendingPosts: async (_, { limit = 10 }, { db }) => {
      // Get trending posts based on recent engagement
      const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);

      return db.post.findMany({
        where: {
          published: true,
          OR: [
            { likes: { gte: 10 } },
            { comments: { some: { createdAt: { gte: oneDayAgo } } } }
          ]
        },
        orderBy: [
          { likes: 'desc' },
          { views: 'desc' },
          { createdAt: 'desc' }
        ],
        take: limit
      });
    }
  },

  Mutation: {
    signUp: async (_, { input }, { db }) => {
      // Validate input
      const existingUser = await db.user.findUnique({
        where: { email: input.email }
      });

      if (existingUser) {
        throw new Error('User already exists');
      }

      // Hash password
      const hashedPassword = await bcrypt.hash(input.password, 10);

      // Create user with profile
      const user = await db.user.create({
        data: {
          username: input.username,
          email: input.email,
          password: hashedPassword,
          profile: input.profile ? {
            create: input.profile
          } : undefined
        },
        include: { profile: true }
      });

      // Generate JWT token
      const token = generateToken(user);

      return { token, user };
    },

    createPost: async (_, { input }, { db, user, pubsub }) => {
      if (!user) throw new Error('Not authenticated');

      const post = await db.post.create({
        data: {
          ...input,
          authorId: user.id,
          tags: input.tags ? {
            connectOrCreate: input.tags.map(tag => ({
              where: { slug: slugify(tag) },
              create: { name: tag, slug: slugify(tag) }
            }))
          } : undefined
        },
        include: {
          author: true,
          tags: true
        }
      });

      // Publish subscription event
      pubsub.publish('POST_CREATED', { postCreated: post });

      return post;
    },

    updatePost: async (_, { id, input }, { db, user }) => {
      if (!user) throw new Error('Not authenticated');

      // Check ownership
      const post = await db.post.findUnique({
        where: { id }
      });

      if (!post) throw new Error('Post not found');
      if (post.authorId !== user.id && user.role !== 'ADMIN') {
        throw new Error('Not authorized');
      }

      // Update post
      const updatedPost = await db.post.update({
        where: { id },
        data: {
          ...input,
          tags: input.tags ? {
            set: [],
            connectOrCreate: input.tags.map(tag => ({
              where: { slug: slugify(tag) },
              create: { name: tag, slug: slugify(tag) }
            }))
          } : undefined
        },
        include: {
          author: true,
          tags: true
        }
      });

      // Publish subscription event
      pubsub.publish('POST_UPDATED', { postUpdated: updatedPost });

      return updatedPost;
    },

    likePost: async (_, { postId }, { db, user }) => {
      if (!user) throw new Error('Not authenticated');

      // Check if already liked
      const existingLike = await db.like.findUnique({
        where: {
          userId_postId: {
            userId: user.id,
            postId
          }
        }
      });

      if (existingLike) {
        // Unlike
        await db.like.delete({
          where: { id: existingLike.id }
        });

        return db.post.update({
          where: { id: postId },
          data: { likes: { decrement: 1 } },
          include: { author: true, tags: true }
        });
      } else {
        // Like
        await db.like.create({
          data: {
            userId: user.id,
            postId
          }
        });

        return db.post.update({
          where: { id: postId },
          data: { likes: { increment: 1 } },
          include: { author: true, tags: true }
        });
      }
    }
  },

  Subscription: {
    postCreated: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['POST_CREATED']),
        (payload, variables) => {
          // Filter by authorId if provided
          if (variables.authorId) {
            return payload.postCreated.authorId === variables.authorId;
          }
          return true;
        }
      )
    },

    commentAdded: {
      subscribe: withFilter(
        () => pubsub.asyncIterator(['COMMENT_ADDED']),
        (payload, variables) => {
          return payload.commentAdded.postId === variables.postId;
        }
      )
    }
  },

  // Field resolvers for relationships
  User: {
    posts: async (user, { first = 10, after }, { db }) => {
      // Implement cursor-based pagination for user posts
      const cursor = after ? { id: after } : undefined;

      const posts = await db.post.findMany({
        where: { authorId: user.id },
        take: first + 1,
        skip: cursor ? 1 : 0,
        cursor,
        orderBy: { createdAt: 'desc' }
      });

      const hasNextPage = posts.length > first;
      const edges = posts.slice(0, first).map(post => ({
        node: post,
        cursor: post.id
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!after,
          startCursor: edges[0]?.cursor,
          endCursor: edges[edges.length - 1]?.cursor
        },
        totalCount: await db.post.count({ where: { authorId: user.id } })
      };
    },

    followers: async (user, _, { loaders }) => {
      return loaders.followersLoader.load(user.id);
    },

    following: async (user, _, { loaders }) => {
      return loaders.followingLoader.load(user.id);
    }
  },

  Post: {
    author: async (post, _, { loaders }) => {
      return loaders.userLoader.load(post.authorId);
    },

    comments: async (post, { first = 10, after }, { db }) => {
      // Use DataLoader for better performance
      const comments = await loaders.commentsByPostLoader.load(post.id);

      // Apply pagination
      const startIndex = after ? comments.findIndex(c => c.id === after) + 1 : 0;
      const paginatedComments = comments.slice(startIndex, startIndex + first + 1);

      const hasNextPage = paginatedComments.length > first;
      const edges = paginatedComments.slice(0, first).map(comment => ({
        node: comment,
        cursor: comment.id
      }));

      return {
        edges,
        pageInfo: {
          hasNextPage,
          hasPreviousPage: !!after,
          startCursor: edges[0]?.cursor,
          endCursor: edges[edges.length - 1]?.cursor
        },
        totalCount: comments.length
      };
    }
  },

  Comment: {
    author: async (comment, _, { loaders }) => {
      return loaders.userLoader.load(comment.authorId);
    },

    post: async (comment, _, { loaders }) => {
      return loaders.postLoader.load(comment.postId);
    }
  }
};

module.exports = resolvers;
```

### Example 3: Custom Directives and Performance Optimization

```javascript
// directives/auth.js
const { mapSchema, getDirective, MapperKind } = require('@graphql-tools/utils');
const { defaultFieldResolver } = require('graphql');

function authDirective(schema, directiveName) {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const authDirective = getDirective(schema, fieldConfig, directiveName)?.[0];

      if (authDirective) {
        const { requires } = authDirective;
        const { resolve = defaultFieldResolver } = fieldConfig;

        fieldConfig.resolve = async function (source, args, context, info) {
          // Check if user is authenticated
          if (!context.user) {
            throw new Error('Not authenticated');
          }

          // Check role requirements
          if (requires) {
            const hasRole = checkUserRole(context.user, requires);
            if (!hasRole) {
              throw new Error(`Requires ${requires} role`);
            }
          }

          return resolve(source, args, context, info);
        };

        return fieldConfig;
      }
    }
  });
}

// directives/rateLimit.js
const { RateLimiterMemory } = require('rate-limiter-flexible');

const rateLimiters = new Map();

function rateLimitDirective(schema, directiveName) {
  return mapSchema(schema, {
    [MapperKind.OBJECT_FIELD]: (fieldConfig) => {
      const rateLimitDirective = getDirective(schema, fieldConfig, directiveName)?.[0];

      if (rateLimitDirective) {
        const { max, window } = rateLimitDirective;
        const { resolve = defaultFieldResolver } = fieldConfig;

        // Create rate limiter for this field
        const key = `${fieldConfig.name}_${max}_${window}`;
        if (!rateLimiters.has(key)) {
          rateLimiters.set(key, new RateLimiterMemory({
            points: max,
            duration: parseDuration(window)
          }));
        }

        const limiter = rateLimiters.get(key);

        fieldConfig.resolve = async function (source, args, context, info) {
          const userId = context.user?.id || context.req.ip;

          try {
            await limiter.consume(userId);
          } catch (e) {
            throw new Error(`Rate limit exceeded. Max ${max} requests per ${window}`);
          }

          return resolve(source, args, context, info);
        };

        return fieldConfig;
      }
    }
  });
}

// services/caching.js
const Redis = require('ioredis');
const { createHash } = require('crypto');

class GraphQLCache {
  constructor(redis = new Redis()) {
    this.redis = redis;
  }

  async get(key) {
    const cached = await this.redis.get(key);
    return cached ? JSON.parse(cached) : null;
  }

  async set(key, value, ttl = 300) {
    await this.redis.setex(key, ttl, JSON.stringify(value));
  }

  createCacheKey(info, args) {
    const query = info.fieldName;
    const argsString = JSON.stringify(args);
    return createHash('md5').update(`${query}:${argsString}`).digest('hex');
  }

  // Cache resolver wrapper
  cacheResolver(resolver, options = {}) {
    const { ttl = 300 } = options;

    return async (source, args, context, info) => {
      // Skip caching for mutations and subscriptions
      if (info.operation.operation !== 'query') {
        return resolver(source, args, context, info);
      }

      const cacheKey = this.createCacheKey(info, args);
      const cached = await this.get(cacheKey);

      if (cached) {
        return cached;
      }

      const result = await resolver(source, args, context, info);
      await this.set(cacheKey, result, ttl);

      return result;
    };
  }
}

module.exports = { authDirective, rateLimitDirective, GraphQLCache };
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Query depth limit exceeded" | Query too deeply nested | Adjust depth limit or simplify query |
| "Query complexity too high" | Query too expensive | Optimize query or increase complexity budget |
| "N+1 query detected" | Missing DataLoader | Implement DataLoader for relationship |
| "Subscription connection failed" | WebSocket issues | Check WebSocket configuration |
| "Schema validation failed" | Invalid GraphQL schema | Fix schema syntax errors |

## Configuration Options

**Server Options**
- `introspection`: Enable schema introspection (disable in production)
- `playground`: Enable GraphQL Playground
- `cors`: CORS configuration
- `uploads`: File upload support
- `subscriptions`: WebSocket configuration

**Performance Options**
- `depthLimit`: Maximum query depth (default: 10)
- `costAnalysis`: Query cost limits
- `dataLoader`: Batching configuration
- `caching`: Response caching settings
- `persistedQueries`: APQ support

## Best Practices

DO:
- Use DataLoader for all database queries
- Implement proper error handling
- Add field-level authorization
- Version your schema carefully
- Monitor query complexity
- Cache expensive queries

DON'T:
- Expose internal errors to clients
- Allow unlimited query depth
- Ignore N+1 query problems
- Over-fetch in resolvers
- Mix business logic with resolvers

## Performance Considerations

- Implement DataLoader for batching and caching
- Use query complexity analysis
- Add response caching with Redis
- Enable persisted queries
- Monitor resolver performance
- Use database query optimization

## Security Considerations

- Implement authentication and authorization
- Use query depth limiting
- Add rate limiting
- Validate and sanitize inputs
- Hide internal error details
- Enable CORS appropriately

## Related Commands

- `/api-authentication-builder` - Add auth to GraphQL
- `/api-documentation-generator` - Generate GraphQL docs
- `/api-testing-framework` - Test GraphQL APIs
- `/graphql-federation` - Implement microservices

## Version History

- v1.0.0 (2024-10): Initial implementation with Apollo Server 4
- Planned v1.1.0: Add federation support for microservices