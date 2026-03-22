---
name: webflow-core-workflow-b
description: |
  Execute Webflow secondary workflows — Sites management, Pages API, Forms submissions,
  Ecommerce (products/orders/inventory), and Custom Code via the Data API v2.
  Use when managing sites, reading pages, handling form data, or working with
  Webflow Ecommerce products and orders.
  Trigger with phrases like "webflow sites", "webflow pages", "webflow forms",
  "webflow ecommerce", "webflow products", "webflow orders".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Core Workflow B — Sites, Pages, Forms & Ecommerce

## Overview

Beyond CMS content management, Webflow's Data API v2 covers site operations, page
metadata, form submissions, ecommerce (products, orders, inventory), and custom code
injection. This skill covers all non-CMS API domains.

## Prerequisites

- Completed `webflow-install-auth` setup
- Scopes needed: `sites:read`, `sites:write`, `pages:read`, `forms:read`,
  `ecommerce:read`, `ecommerce:write`, `custom_code:read`, `custom_code:write`

## Instructions

### 1. Sites Management

```typescript
import { WebflowClient } from "webflow-api";

const webflow = new WebflowClient({
  accessToken: process.env.WEBFLOW_API_TOKEN!,
});

// List all sites
async function listSites() {
  const { sites } = await webflow.sites.list();
  for (const site of sites!) {
    console.log(`${site.displayName} (${site.id})`);
    console.log(`  Short name: ${site.shortName}`);
    console.log(`  Timezone: ${site.timeZone}`);
    console.log(`  Created: ${site.createdOn}`);
    console.log(`  Last published: ${site.lastPublished}`);
    console.log(`  Custom domains: ${site.customDomains?.map(d => d.url).join(", ")}`);
    console.log(`  Default locale: ${site.locales?.[0]?.displayName}`);
  }
}

// Get single site details
async function getSite(siteId: string) {
  const site = await webflow.sites.get(siteId);
  return site;
}

// Publish site (rate limit: 1 per minute)
async function publishSite(siteId: string, domains?: string[]) {
  await webflow.sites.publish(siteId, {
    publishToWebflowSubdomain: true,
    customDomains: domains, // Optional: publish to specific domains
  });
  console.log("Site published successfully");
}
```

### 2. Pages API

```typescript
// List all pages for a site
async function listPages(siteId: string) {
  const { pages } = await webflow.pages.list(siteId);

  for (const page of pages!) {
    console.log(`${page.title} (${page.id})`);
    console.log(`  Slug: ${page.slug}`);
    console.log(`  SEO title: ${page.seo?.title}`);
    console.log(`  SEO description: ${page.seo?.description}`);
    console.log(`  Open Graph image: ${page.openGraph?.titleCopied}`);
    console.log(`  Created: ${page.createdOn}`);
    console.log(`  Published: ${page.publishedPath}`);
  }
}

// Get page metadata
async function getPage(pageId: string) {
  const page = await webflow.pages.getMetadata(pageId);
  return page;
}

// Update page SEO metadata
async function updatePageSEO(pageId: string) {
  await webflow.pages.updatePageSettings(pageId, {
    seo: {
      title: "New SEO Title — My Site",
      description: "Updated meta description for search engines.",
    },
    openGraph: {
      title: "New OG Title",
      description: "Updated Open Graph description for social shares.",
    },
  });
}
```

### 3. Form Submissions

```typescript
// List forms on a site
async function listForms(siteId: string) {
  const { forms } = await webflow.forms.list(siteId);

  for (const form of forms!) {
    console.log(`Form: ${form.displayName} (${form.id})`);
    console.log(`  Site ID: ${form.siteId}`);
    console.log(`  Page name: ${form.pageName}`);
    console.log(`  Submission count: ${form.submissionCount}`);
    console.log(`  Fields:`);
    for (const field of form.fields || []) {
      console.log(`    ${field.displayName} (${field.type})`);
    }
  }
}

// Get form submissions (paginated)
async function getFormSubmissions(formId: string) {
  const { formSubmissions } = await webflow.forms.listSubmissions(formId, {
    limit: 100,
    offset: 0,
  });

  for (const sub of formSubmissions!) {
    console.log(`Submission ${sub.id}:`);
    console.log(`  Submitted: ${sub.submittedAt}`);
    console.log(`  Data: ${JSON.stringify(sub.formData)}`);
  }
}

// Export all form submissions to CSV
async function exportFormData(formId: string) {
  const allSubmissions = [];
  let offset = 0;
  const limit = 100;

  while (true) {
    const { formSubmissions, pagination } =
      await webflow.forms.listSubmissions(formId, { limit, offset });

    allSubmissions.push(...(formSubmissions || []));
    if (allSubmissions.length >= (pagination?.total || 0)) break;
    offset += limit;
  }

  return allSubmissions.map(sub => sub.formData);
}
```

### 4. Ecommerce — Products & SKUs

```typescript
// List all products
async function listProducts(siteId: string) {
  const { items } = await webflow.products.list(siteId, {
    limit: 100,
    offset: 0,
  });

  for (const product of items!) {
    console.log(`Product: ${product.product?.fieldData?.name}`);
    console.log(`  ID: ${product.product?.id}`);
    console.log(`  Slug: ${product.product?.fieldData?.slug}`);
    console.log(`  SKUs:`);
    for (const sku of product.skus || []) {
      console.log(`    ${sku.fieldData?.name}: $${sku.fieldData?.price?.value}`);
      console.log(`    Inventory: ${sku.fieldData?.quantity}`);
    }
  }
}

// Get single product with all SKUs
async function getProduct(siteId: string, productId: string) {
  const product = await webflow.products.get(siteId, productId);
  return product;
}

// Create a product
async function createProduct(siteId: string) {
  const product = await webflow.products.create(siteId, {
    product: {
      fieldData: {
        name: "Premium Widget",
        slug: "premium-widget",
        description: "<p>Our best-selling widget</p>",
      },
    },
    sku: {
      fieldData: {
        name: "Default",
        slug: "default",
        price: { value: 2999, unit: "USD" }, // Price in cents
        quantity: 100,
        "sku-properties": [],
      },
    },
  });

  console.log(`Created product: ${product.product?.id}`);
}

// Update inventory
async function updateInventory(
  siteId: string,
  collectionId: string,
  itemId: string,
  quantity: number
) {
  await webflow.inventory.update(collectionId, itemId, {
    inventoryType: "finite",
    updateQuantity: quantity,
  });
}
```

### 5. Ecommerce — Orders

```typescript
// List orders
async function listOrders(siteId: string) {
  const { orders } = await webflow.orders.list(siteId, {
    limit: 100,
  });

  for (const order of orders!) {
    console.log(`Order #${order.orderId} (${order.status})`);
    console.log(`  Customer: ${order.customerInfo?.fullName}`);
    console.log(`  Email: ${order.customerInfo?.email}`);
    console.log(`  Total: $${(order.customerPaid?.value || 0) / 100}`);
    console.log(`  Items: ${order.purchasedItems?.length}`);
    console.log(`  Created: ${order.acceptedOn}`);
  }
}

// Get order details
async function getOrder(siteId: string, orderId: string) {
  const order = await webflow.orders.get(siteId, orderId);
  return order;
}

// Update order status (fulfill, refund)
async function fulfillOrder(siteId: string, orderId: string) {
  await webflow.orders.update(siteId, orderId, {
    status: "fulfilled",
  });
}

// Refund an order
async function refundOrder(siteId: string, orderId: string) {
  await webflow.orders.refund(siteId, orderId);
  console.log(`Refunded order: ${orderId}`);
}
```

### 6. Custom Code

```typescript
// Register custom code to the site head/footer
async function addSiteCustomCode(siteId: string) {
  // Register hosted script
  await webflow.scripts.registerHosted(siteId, {
    hostedLocation: "https://cdn.example.com/analytics.js",
    integrityHash: "sha384-...",
    canCopy: false,
    version: "1.0.0",
    displayName: "Analytics Script",
  });

  // Register inline script
  await webflow.scripts.registerInline(siteId, {
    sourceCode: "console.log('Hello from custom code');",
    version: "1.0.0",
    canCopy: true,
    displayName: "Debug Script",
  });
}
```

## Output

- Sites: list, get details, publish with domain control
- Pages: list, read SEO metadata, update Open Graph settings
- Forms: list forms, read all submissions, export data
- Ecommerce: CRUD products/SKUs, manage orders, update inventory
- Custom Code: register hosted and inline scripts

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `403 Forbidden` on ecommerce | Missing `ecommerce:read` scope | Add scope to token |
| Site publish `429` | >1 publish/minute | Wait 60s between publishes |
| Empty products list | Ecommerce not enabled on site | Enable Ecommerce in Webflow dashboard |
| Form `404` | Wrong form_id | List forms with `forms.list(siteId)` first |
| Order refund fails | Order already refunded | Check order status before refunding |

## Resources

- [Sites API](https://developers.webflow.com/data/reference/sites)
- [Pages API](https://developers.webflow.com/data/reference/pages)
- [Forms API](https://developers.webflow.com/data/reference/forms)
- [Ecommerce Products](https://developers.webflow.com/data/reference/ecommerce/products/list)
- [Custom Code API](https://developers.webflow.com/data/reference/custom-code)

## Next Steps

For common errors, see `webflow-common-errors`.
