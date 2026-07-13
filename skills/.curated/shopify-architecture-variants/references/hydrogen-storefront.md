Variant B: Headless Storefront (Hydrogen) project structure and Storefront API loader.

**Best for:** Custom storefronts, unique shopping experiences, PWAs

**When to use:** You're building a custom frontend that replaces the Shopify Online Store.

```
my-hydrogen-store/
├── app/
│   ├── routes/
│   │   ├── ($locale)._index.tsx           # Homepage
│   │   ├── ($locale).products.$handle.tsx # Product page
│   │   ├── ($locale).collections._index.tsx
│   │   ├── ($locale).cart.tsx             # Cart page
│   │   └── ($locale).account.tsx          # Customer account
│   ├── components/
│   │   ├── ProductCard.tsx
│   │   ├── Cart.tsx
│   │   └── Header.tsx
│   ├── lib/
│   │   └── shopify.ts                     # Storefront API client
│   └── root.tsx
├── public/
└── hydrogen.config.ts
```

**Key packages:** `@shopify/hydrogen`, `@shopify/hydrogen-react`, `@shopify/remix-oxygen`

**API used:** Storefront GraphQL API (public, no admin tokens needed)

**Hosting:** Shopify Oxygen (recommended) or any edge platform

```typescript
// Hydrogen product page — uses Storefront API
export async function loader({ params, context }: LoaderFunctionArgs) {
  const { storefront } = context;
  const { product } = await storefront.query(PRODUCT_QUERY, {
    variables: { handle: params.handle },
  });
  return json({ product });
}
```
