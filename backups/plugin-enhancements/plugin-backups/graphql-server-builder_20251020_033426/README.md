# GraphQL Server Builder Plugin

Build production-ready GraphQL servers with schema-first design, resolvers, subscriptions, and best practices.

## Installation

```bash
/plugin install graphql-server-builder@claude-code-plugins-plus
```

## Usage

```bash
/build-graphql-server
# or shortcut
/gql
```

## Features

- Schema-first design with SDL
- Type-safe resolvers
- DataLoader for N+1 prevention
- Real-time subscriptions
- Authentication directives
- Pagination (Relay-style)
- Error handling
- GraphQL Playground

## Generated Structure

```
graphql/
├── schema/
│   ├── user.graphql
│   └── post.graphql
├── resolvers/
│   ├── Query.js
│   ├── Mutation.js
│   └── Subscription.js
├── dataloaders/
│   └── index.js
├── directives/
│   └── auth.js
└── server.js
```

## License

MIT
