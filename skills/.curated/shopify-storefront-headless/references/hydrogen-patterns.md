Hydrogen framework setup, client configuration, and Remix loader patterns.

## Project Scaffolding

```bash
# Create a new Hydrogen project
npx @shopify/create-hydrogen@latest my-store

# Or with Shopify CLI
shopify hydrogen init --template demo-store
```

## Storefront Client in Hydrogen

```typescript
// app/lib/createStorefrontClient.server.ts
import { createStorefrontClient } from "@shopify/hydrogen";

export function getStorefrontClient(env: Env) {
  return createStorefrontClient({
    storeDomain: env.PUBLIC_STORE_DOMAIN,
    publicStorefrontToken: env.PUBLIC_STOREFRONT_API_TOKEN,
    privateStorefrontToken: env.PRIVATE_STOREFRONT_API_TOKEN, // optional, server-side
    storefrontApiVersion: env.PUBLIC_STOREFRONT_API_VERSION || "2025-01",
  });
}
```

## Loader Pattern (Product Page)

```typescript
// app/routes/($locale).products.$handle.tsx
import { json, type LoaderFunctionArgs } from "@shopify/remix-oxygen";
import { useLoaderData } from "@remix-run/react";

const PRODUCT_QUERY = `#graphql
  query Product($handle: String!) {
    product(handle: $handle) {
      id
      title
      description
      descriptionHtml
      vendor
      availableForSale
      options {
        name
        values
      }
      selectedVariant: variantBySelectedOptions(selectedOptions: $selectedOptions) {
        id
        price { amount currencyCode }
        availableForSale
      }
      variants(first: 100) {
        nodes {
          id
          title
          price { amount currencyCode }
          availableForSale
          selectedOptions { name value }
          image { url altText width height }
        }
      }
      images(first: 10) {
        nodes { url altText width height }
      }
      seo { title description }
    }
  }
`;

export async function loader({ params, context }: LoaderFunctionArgs) {
  const { storefront } = context;
  const { product } = await storefront.query(PRODUCT_QUERY, {
    variables: { handle: params.handle },
  });

  if (!product) {
    throw new Response("Product not found", { status: 404 });
  }

  return json({ product });
}

export default function ProductPage() {
  const { product } = useLoaderData<typeof loader>();
  return (
    <div>
      <h1>{product.title}</h1>
      {/* Product UI */}
    </div>
  );
}
```

## Deferred Loading (Streaming)

```typescript
// Use defer for non-critical data to speed up initial render
import { defer, type LoaderFunctionArgs } from "@shopify/remix-oxygen";

export async function loader({ context }: LoaderFunctionArgs) {
  const { storefront } = context;

  // Critical: await immediately
  const featuredProducts = await storefront.query(FEATURED_QUERY);

  // Non-critical: defer (loads after initial render)
  const recommendations = storefront.query(RECOMMENDATIONS_QUERY);

  return defer({
    featuredProducts,
    recommendations, // This is a Promise, resolved client-side
  });
}
```

## Collection Page Pattern

```typescript
// app/routes/($locale).collections.$handle.tsx
const COLLECTION_QUERY = `#graphql
  query Collection($handle: String!, $first: Int!, $after: String) {
    collection(handle: $handle) {
      id
      title
      description
      products(first: $first, after: $after, sortKey: BEST_SELLING) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          title
          handle
          availableForSale
          priceRange {
            minVariantPrice { amount currencyCode }
          }
          featuredImage { url altText }
        }
      }
    }
  }
`;

export async function loader({ params, request, context }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const after = url.searchParams.get("cursor");

  const { collection } = await context.storefront.query(COLLECTION_QUERY, {
    variables: {
      handle: params.handle,
      first: 24,
      after,
    },
  });

  if (!collection) {
    throw new Response("Collection not found", { status: 404 });
  }

  return json({ collection });
}
```

## Environment Variables

```env
# .env (Hydrogen project)
PUBLIC_STORE_DOMAIN="my-store.myshopify.com"
PUBLIC_STOREFRONT_API_TOKEN="public-token-here"
PRIVATE_STOREFRONT_API_TOKEN="private-token-here"  # Server-side only, higher rate limits
PUBLIC_STOREFRONT_API_VERSION="2025-01"
SESSION_SECRET="random-secret-for-sessions"
```
