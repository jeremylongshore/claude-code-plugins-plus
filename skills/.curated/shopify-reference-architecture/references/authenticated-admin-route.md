# Authenticated Admin Route Pattern

Complete Remix route with authenticated loader and Polaris UI for product listing.

```typescript
// app/routes/app.products.tsx
import { json } from "@remix-run/node";
import { useLoaderData } from "@remix-run/react";
import { authenticate } from "../shopify.server";
import { Page, Layout, Card, DataTable } from "@shopify/polaris";

export async function loader({ request }: LoaderFunctionArgs) {
  const { admin } = await authenticate.admin(request);

  // admin.graphql is a pre-authenticated GraphQL client
  const response = await admin.graphql(`{
    products(first: 25, sortKey: UPDATED_AT, reverse: true) {
      edges {
        node {
          id
          title
          status
          totalInventory
          priceRangeV2 {
            minVariantPrice { amount currencyCode }
          }
        }
      }
    }
  }`);

  const data = await response.json();
  return json({ products: data.data.products.edges.map((e: any) => e.node) });
}

export default function Products() {
  const { products } = useLoaderData<typeof loader>();

  return (
    <Page title="Products">
      <Layout>
        <Layout.Section>
          <Card>
            <DataTable
              columnContentTypes={["text", "text", "numeric", "text"]}
              headings={["Title", "Status", "Inventory", "Price"]}
              rows={products.map((p: any) => [
                p.title,
                p.status,
                p.totalInventory,
                `$${p.priceRangeV2.minVariantPrice.amount}`,
              ])}
            />
          </Card>
        </Layout.Section>
      </Layout>
    </Page>
  );
}
```
