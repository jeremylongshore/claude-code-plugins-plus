---
name: appfolio-sdk-patterns
description: |
  Apply production-ready patterns for AppFolio REST API integration.
  Trigger: "appfolio patterns".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio sdk patterns | sed 's/\b\(.\)/\u\1/g'

## Overview
Production patterns for AppFolio API: typed client, pagination, response caching, and error handling.

## Instructions

### Step 1: Typed API Client
```typescript
// src/appfolio/typed-client.ts
import axios, { AxiosInstance } from "axios";

interface Property {
  id: string; name: string; property_type: string;
  address: { street: string; city: string; state: string; zip: string };
  unit_count: number;
}

interface Tenant {
  id: string; first_name: string; last_name: string;
  email: string; phone: string; unit_id: string;
}

interface Lease {
  id: string; unit_id: string; tenant_name: string;
  start_date: string; end_date: string; rent_amount: number; status: string;
}

class AppFolioTypedClient {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: process.env.APPFOLIO_BASE_URL,
      auth: { username: process.env.APPFOLIO_CLIENT_ID!, password: process.env.APPFOLIO_CLIENT_SECRET! },
      timeout: 30000,
    });
  }

  async getProperties(): Promise<Property[]> { return (await this.api.get("/properties")).data; }
  async getTenants(): Promise<Tenant[]> { return (await this.api.get("/tenants")).data; }
  async getLeases(): Promise<Lease[]> { return (await this.api.get("/leases")).data; }
}

export { AppFolioTypedClient, Property, Tenant, Lease };
```

### Step 2: Response Cache
```typescript
const cache = new Map<string, { data: any; expiry: number }>();

async function cachedGet<T>(client: AxiosInstance, path: string, ttlMs = 60000): Promise<T> {
  const cached = cache.get(path);
  if (cached && cached.expiry > Date.now()) return cached.data;
  const { data } = await client.get(path);
  cache.set(path, { data, expiry: Date.now() + ttlMs });
  return data;
}
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
