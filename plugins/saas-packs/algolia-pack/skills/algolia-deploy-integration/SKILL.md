---
name: algolia-deploy-integration
description: |
  Deploy Algolia-powered apps to Vercel, Fly.io, and Cloud Run with proper
  API key management and InstantSearch frontend integration.
  Trigger: "deploy algolia", "algolia Vercel", "algolia production deploy",
  "algolia Cloud Run", "algolia Fly.io", "algolia InstantSearch".
allowed-tools: Read, Write, Edit, Bash(vercel:*), Bash(fly:*), Bash(gcloud:*), Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, algolia]
compatible-with: claude-code
---

# Algolia Deploy Integration

## Overview

Deploy Algolia-powered applications to production platforms with proper API key separation (Admin on backend, Search-Only on frontend) and InstantSearch widget integration.

## Prerequisites

- Algolia App ID + Admin key (backend) + Search-Only key (frontend)
- Platform CLI installed (vercel, fly, or gcloud)
- `algoliasearch` v5 for backend, `react-instantsearch` or `instantsearch.js` for frontend

## Instructions

### Step 1: Backend API Key Configuration

#### Vercel

```bash
# Environment variables in Vercel
vercel env add ALGOLIA_APP_ID production       # Your Application ID
vercel env add ALGOLIA_ADMIN_KEY production     # Admin key (server-side only)
vercel env add ALGOLIA_SEARCH_KEY production    # Search-only key (can be public)

# For client-side access (Next.js convention)
vercel env add NEXT_PUBLIC_ALGOLIA_APP_ID production
vercel env add NEXT_PUBLIC_ALGOLIA_SEARCH_KEY production
```

#### Fly.io

```bash
fly secrets set \
  ALGOLIA_APP_ID=YourApplicationID \
  ALGOLIA_ADMIN_KEY=your_admin_key \
  ALGOLIA_SEARCH_KEY=your_search_key
```

#### Google Cloud Run

```bash
# Store in Secret Manager
echo -n "your_admin_key" | gcloud secrets create algolia-admin-key --data-file=-
echo -n "your_search_key" | gcloud secrets create algolia-search-key --data-file=-

# Deploy with secrets mounted as env vars
gcloud run deploy search-service \
  --image gcr.io/$PROJECT_ID/search-service \
  --set-secrets=ALGOLIA_ADMIN_KEY=algolia-admin-key:latest,ALGOLIA_SEARCH_KEY=algolia-search-key:latest \
  --region us-central1
```

### Step 2: Backend Search API (Next.js API Route)

```typescript
// app/api/search/route.ts
import { algoliasearch } from 'algoliasearch';
import { NextRequest, NextResponse } from 'next/server';

const client = algoliasearch(
  process.env.ALGOLIA_APP_ID!,
  process.env.ALGOLIA_ADMIN_KEY!
);

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.get('q') || '';
  const page = parseInt(request.nextUrl.searchParams.get('page') || '0');

  const { hits, nbHits, nbPages } = await client.searchSingleIndex({
    indexName: 'products',
    searchParams: {
      query,
      hitsPerPage: 20,
      page,
      attributesToRetrieve: ['name', 'price', 'image_url', 'category'],
      attributesToHighlight: ['name'],
    },
  });

  return NextResponse.json({ hits, totalHits: nbHits, totalPages: nbPages, page });
}
```

### Step 3: Frontend with InstantSearch (React)

```bash
npm install react-instantsearch algoliasearch
```

```tsx
// components/AlgoliaSearch.tsx
import { liteClient } from 'algoliasearch/lite';
import {
  InstantSearch,
  SearchBox,
  Hits,
  RefinementList,
  Pagination,
  Highlight,
} from 'react-instantsearch';

const searchClient = liteClient(
  process.env.NEXT_PUBLIC_ALGOLIA_APP_ID!,
  process.env.NEXT_PUBLIC_ALGOLIA_SEARCH_KEY!
);

function Hit({ hit }: { hit: any }) {
  return (
    <article>
      <h3><Highlight attribute="name" hit={hit} /></h3>
      <p>${hit.price}</p>
      <p>{hit.category}</p>
    </article>
  );
}

export default function AlgoliaSearch() {
  return (
    <InstantSearch searchClient={searchClient} indexName="products">
      <SearchBox placeholder="Search products..." />
      <div style={{ display: 'flex', gap: '2rem' }}>
        <aside>
          <h4>Category</h4>
          <RefinementList attribute="category" />
          <h4>Brand</h4>
          <RefinementList attribute="brand" searchable />
        </aside>
        <main>
          <Hits hitComponent={Hit} />
          <Pagination />
        </main>
      </div>
    </InstantSearch>
  );
}
```

### Step 4: Frontend with Vanilla InstantSearch.js

```bash
npm install instantsearch.js algoliasearch
```

```typescript
import instantsearch from 'instantsearch.js';
import { searchBox, hits, refinementList, pagination } from 'instantsearch.js/es/widgets';
import { liteClient } from 'algoliasearch/lite';

const searchClient = liteClient('YourAppID', 'YourSearchOnlyKey');

const search = instantsearch({
  indexName: 'products',
  searchClient,
});

search.addWidgets([
  searchBox({ container: '#searchbox' }),
  hits({
    container: '#hits',
    templates: {
      item: (hit, { html, components }) => html`
        <article>
          <h3>${components.Highlight({ hit, attribute: 'name' })}</h3>
          <p>$${hit.price}</p>
        </article>
      `,
    },
  }),
  refinementList({ container: '#category-filter', attribute: 'category' }),
  pagination({ container: '#pagination' }),
]);

search.start();
```

### Step 5: Health Check Endpoint

```typescript
// app/api/health/route.ts
import { algoliasearch } from 'algoliasearch';

const client = algoliasearch(process.env.ALGOLIA_APP_ID!, process.env.ALGOLIA_ADMIN_KEY!);

export async function GET() {
  const start = Date.now();
  try {
    const { items } = await client.listIndices();
    return Response.json({
      status: 'healthy',
      algolia: {
        connected: true,
        latencyMs: Date.now() - start,
        indexCount: items.length,
      },
    });
  } catch (error) {
    return Response.json({
      status: 'degraded',
      algolia: { connected: false, error: String(error) },
    }, { status: 503 });
  }
}
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `NEXT_PUBLIC_` var undefined | Not set in Vercel env | Add with `vercel env add` |
| InstantSearch shows no results | Wrong Search-Only key | Verify key ACL includes `search` |
| Backend write fails on Vercel | Using search key for indexing | Use `ALGOLIA_ADMIN_KEY` (non-public) |
| Cold start timeout | Large client init | Use lite client where possible |

## Resources

- [InstantSearch.js](https://www.algolia.com/doc/guides/building-search-ui/what-is-instantsearch/js/)
- [React InstantSearch](https://www.algolia.com/doc/guides/building-search-ui/what-is-instantsearch/react/)
- [Vercel Environment Variables](https://vercel.com/docs/environment-variables)

## Next Steps

For event tracking and analytics, see `algolia-webhooks-events`.
