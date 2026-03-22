---
name: appfolio-local-dev-loop
description: |
  Set up local development for AppFolio property management API integration.
  Trigger: "appfolio local dev".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio local dev loop | sed 's/\b\(.\)/\u\1/g'

## Overview
Local development workflow for AppFolio API integration with mock data and sandbox testing.

## Instructions

### Step 1: Project Setup
```bash
mkdir appfolio-integration && cd appfolio-integration
npm init -y
npm install axios dotenv typescript @types/node
npm install -D vitest msw  # For API mocking
```

### Step 2: Mock Server for Development
```typescript
// src/dev/mock-server.ts
import express from "express";
const app = express();
app.use(express.json());

const mockProperties = [
  { id: "1", name: "Sunset Apartments", address: { street: "123 Sunset Blvd", city: "Los Angeles", state: "CA" }, property_type: "residential", unit_count: 24 },
  { id: "2", name: "Downtown Office", address: { street: "456 Main St", city: "San Francisco", state: "CA" }, property_type: "commercial", unit_count: 8 },
];

app.get("/api/v1/properties", (req, res) => res.json(mockProperties));
app.get("/api/v1/tenants", (req, res) => res.json([
  { id: "t1", first_name: "Jane", last_name: "Smith", email: "jane@example.com", unit_id: "u1" },
]));
app.get("/api/v1/leases", (req, res) => res.json([
  { id: "l1", unit_id: "u1", start_date: "2025-01-01", end_date: "2026-01-01", rent_amount: 2500, status: "active" },
]));

app.listen(3001, () => console.log("Mock AppFolio API on :3001"));
```

### Step 3: Dev Scripts
```json
{
  "scripts": {
    "dev:mock": "tsx src/dev/mock-server.ts",
    "dev:test": "APPFOLIO_BASE_URL=http://localhost:3001/api/v1 tsx src/hello-world.ts"
  }
}
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
