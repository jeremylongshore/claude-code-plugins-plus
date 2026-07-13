Variant A: Embedded Admin App (Remix) project structure and authenticated loader pattern.

**Best for:** Admin panel apps, merchant tools, dashboards, order management

**When to use:** You need to add functionality to the Shopify admin for merchants.

```
my-shopify-app/
├── app/
│   ├── routes/
│   │   ├── app._index.tsx         # Dashboard (inside Shopify admin)
│   │   ├── app.products.tsx       # Feature pages
│   │   ├── auth.$.tsx             # OAuth handler
│   │   └── webhooks.tsx           # Webhook receiver
│   ├── shopify.server.ts          # @shopify/shopify-app-remix
│   └── root.tsx
├── extensions/                     # Optional extensions
├── prisma/schema.prisma           # Session + app data
├── shopify.app.toml
└── package.json
```

**Key packages:** `@shopify/shopify-app-remix`, `@shopify/polaris`, `@shopify/app-bridge-react`

**API used:** Admin GraphQL API (server-side via `authenticate.admin()`)

**Auth:** OAuth with session token exchange (handled by the Remix adapter)

```typescript
// Authenticated loader — runs server-side inside Shopify admin
export async function loader({ request }: LoaderFunctionArgs) {
  const { admin } = await authenticate.admin(request);
  const response = await admin.graphql(`{ shop { name plan { displayName } } }`);
  return json(await response.json());
}
```
