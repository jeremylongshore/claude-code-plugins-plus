# GraphQL Server Examples

## Schema Definition (SDL)

```graphql
# schema/typeDefs.graphql
type Query {
  users(page: Int = 1, limit: Int = 20): UserConnection!
  user(id: ID!): User
  products(filter: ProductFilter): [Product!]!
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!
}

type Subscription {
  productUpdated(categoryId: ID): Product!
  orderStatusChanged(orderId: ID!): Order!
}

type User {
  id: ID!
  name: String!
  email: String!
  orders: [Order!]!
  createdAt: DateTime!
}

type UserConnection {
  data: [User!]!
  pagination: Pagination!
}

type Pagination {
  page: Int!
  limit: Int!
  total: Int!
}

type Product {
  id: ID!
  name: String!
  price: Float!
  category: Category!
  reviews: [Review!]!
}

input CreateUserInput {
  name: String!
  email: String!
  role: Role = USER
}

input ProductFilter {
  categoryId: ID
  minPrice: Float
  maxPrice: Float
}

enum Role { USER ADMIN }
scalar DateTime
```

## Resolvers with DataLoader

```javascript
// resolvers/user.js
const DataLoader = require('dataloader');

function createLoaders() {
  return {
    ordersByUser: new DataLoader(async (userIds) => {
      const orders = await db.orders.findAll({ where: { userId: userIds } });
      return userIds.map(id => orders.filter(o => o.userId === id));
    }),
    userById: new DataLoader(async (ids) => {
      const users = await db.users.findAll({ where: { id: ids } });
      return ids.map(id => users.find(u => u.id === id));
    }),
  };
}

const resolvers = {
  Query: {
    users: async (_, { page, limit }) => {
      const offset = (page - 1) * limit;
      const [data, total] = await Promise.all([
        db.users.findAll({ limit, offset }),
        db.users.count(),
      ]);
      return { data, pagination: { page, limit, total } };
    },
    user: (_, { id }, { loaders }) => loaders.userById.load(id),
  },

  Mutation: {
    createUser: async (_, { input }, { user }) => {
      if (!user) throw new AuthenticationError('Login required');
      return db.users.create(input);
    },
    deleteUser: async (_, { id }, { user }) => {
      if (!user?.roles?.includes('ADMIN')) throw new ForbiddenError('Admin only');
      await db.users.destroy({ where: { id } });
      return true;
    },
  },

  User: {
    orders: (parent, _, { loaders }) => loaders.ordersByUser.load(parent.id),
  },
};
```

## Apollo Server Setup

```javascript
const { ApolloServer } = require('@apollo/server');
const { expressMiddleware } = require('@apollo/server/express4');
const { makeExecutableSchema } = require('@graphql-tools/schema');
const { useServer } = require('graphql-ws/lib/use/ws');
const { WebSocketServer } = require('ws');

const schema = makeExecutableSchema({ typeDefs, resolvers });
const server = new ApolloServer({
  schema,
  plugins: [
    { requestDidStart: () => ({ willSendResponse({ response }) {
      // Query complexity check
    }})},
  ],
});

await server.start();

app.use('/graphql', expressMiddleware(server, {
  context: async ({ req }) => ({
    user: await getUserFromToken(req.headers.authorization),
    loaders: createLoaders(),
  }),
}));

// WebSocket subscriptions
const wsServer = new WebSocketServer({ server: httpServer, path: '/graphql' });
useServer({ schema, context: (ctx) => ({
  user: getUserFromToken(ctx.connectionParams?.authorization),
})}, wsServer);
```

## Query Complexity Limiting

```javascript
const { createComplexityLimitRule } = require('graphql-validation-complexity');

const complexityPlugin = {
  requestDidStart: () => ({
    didResolveOperation({ request, document }) {
      const complexity = getComplexity(document, {
        maximumComplexity: 1000,
        defaultCost: 1,
        scalarCost: 0,
        objectCost: 2,
        listFactor: 10,
      });
      if (complexity > 1000) {
        throw new Error(`Query complexity ${complexity} exceeds maximum 1000`);
      }
    },
  }),
};

// Depth limiting
const depthLimit = require('graphql-depth-limit');
const validationRules = [depthLimit(7)];
```

## Subscription Example

```javascript
// resolvers/subscription.js
const { PubSub } = require('graphql-subscriptions');
const pubsub = new PubSub();

const subscriptionResolvers = {
  Subscription: {
    productUpdated: {
      subscribe: (_, { categoryId }) => {
        if (categoryId) {
          return pubsub.asyncIterator(`PRODUCT_UPDATED_${categoryId}`);
        }
        return pubsub.asyncIterator('PRODUCT_UPDATED');
      },
    },
  },
};

// Publish from mutation
async function updateProduct(id, input) {
  const product = await db.products.update(id, input);
  pubsub.publish('PRODUCT_UPDATED', { productUpdated: product });
  pubsub.publish(`PRODUCT_UPDATED_${product.categoryId}`, { productUpdated: product });
  return product;
}
```

## GraphQL Queries (curl)

```bash
# Query users with nested orders
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"{ users(page: 1, limit: 5) { data { id name email orders { id total } } pagination { total } } }"}'

# Create user mutation
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"mutation { createUser(input: { name: \"Alice\", email: \"alice@example.com\" }) { id name } }"}'

# Expected response
# {"data":{"createUser":{"id":"usr_abc","name":"Alice"}}}
```

## Integration Tests

```javascript
describe('GraphQL', () => {
  it('lists users with pagination', async () => {
    const res = await server.executeOperation({
      query: '{ users(page: 1, limit: 5) { data { id name } pagination { total } } }',
    });
    expect(res.body.singleResult.data.users.data.length).toBeLessThanOrEqual(5);
  });

  it('rejects complex queries', async () => {
    const deep = '{ users { data { orders { items { product { category { name } } } } } } }';
    const res = await server.executeOperation({ query: deep });
    expect(res.body.singleResult.errors).toBeDefined();
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
