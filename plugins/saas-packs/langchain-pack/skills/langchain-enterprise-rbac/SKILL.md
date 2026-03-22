---
name: langchain-enterprise-rbac
description: |
  Implement role-based access control for LangChain applications
  with multi-tenant isolation, model access control, and usage quotas.
  Trigger: "langchain RBAC", "langchain permissions",
  "langchain access control", "langchain multi-tenant", "enterprise LLM auth".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, langchain, security, llm, authentication]

---
# LangChain Enterprise RBAC

## Overview

Role-based access control for multi-tenant LangChain applications: permission models, model access gating, tenant-scoped vector stores, usage quotas, and FastAPI middleware integration.

## Permission Model

```typescript
// permissions.ts
enum Permission {
  CHAIN_INVOKE = "chain:invoke",
  CHAIN_STREAM = "chain:stream",
  MODEL_GPT4O = "model:gpt-4o",
  MODEL_GPT4O_MINI = "model:gpt-4o-mini",
  MODEL_CLAUDE = "model:claude-sonnet",
  TOOLS_EXECUTE = "tools:execute",
  ADMIN_CONFIG = "admin:config",
  ADMIN_USERS = "admin:users",
}

interface Role {
  name: string;
  permissions: Permission[];
}

const ROLES: Record<string, Role> = {
  viewer: {
    name: "viewer",
    permissions: [Permission.CHAIN_INVOKE, Permission.MODEL_GPT4O_MINI],
  },
  user: {
    name: "user",
    permissions: [
      Permission.CHAIN_INVOKE,
      Permission.CHAIN_STREAM,
      Permission.MODEL_GPT4O_MINI,
      Permission.TOOLS_EXECUTE,
    ],
  },
  power_user: {
    name: "power_user",
    permissions: [
      Permission.CHAIN_INVOKE,
      Permission.CHAIN_STREAM,
      Permission.MODEL_GPT4O_MINI,
      Permission.MODEL_GPT4O,
      Permission.MODEL_CLAUDE,
      Permission.TOOLS_EXECUTE,
    ],
  },
  admin: {
    name: "admin",
    permissions: Object.values(Permission),
  },
};
```

## User and Tenant Models

```typescript
interface Tenant {
  id: string;
  name: string;
  monthlyTokenLimit: number;
  tokensUsed: number;
  allowedModels: string[];
}

interface User {
  id: string;
  tenantId: string;
  role: string;
  email: string;
}

function hasPermission(user: User, permission: Permission): boolean {
  const role = ROLES[user.role];
  if (!role) return false;
  return role.permissions.includes(permission);
}

function canUseModel(user: User, tenant: Tenant, model: string): boolean {
  const modelPermission = `model:${model}` as Permission;
  return (
    hasPermission(user, modelPermission) &&
    tenant.allowedModels.includes(model)
  );
}
```

## Middleware: Permission Enforcement

```typescript
// Express middleware
import { Request, Response, NextFunction } from "express";

function requirePermission(permission: Permission) {
  return (req: Request, res: Response, next: NextFunction) => {
    const user = req.user as User;  // set by auth middleware
    if (!user) {
      return res.status(401).json({ error: "Authentication required" });
    }
    if (!hasPermission(user, permission)) {
      return res.status(403).json({
        error: `Missing permission: ${permission}`,
        role: user.role,
      });
    }
    next();
  };
}

// Usage
app.post("/api/chat",
  requirePermission(Permission.CHAIN_INVOKE),
  async (req, res) => {
    const result = await chain.invoke({ input: req.body.input });
    res.json({ result });
  }
);

app.post("/api/chat/stream",
  requirePermission(Permission.CHAIN_STREAM),
  async (req, res) => {
    // streaming endpoint...
  }
);
```

## Model Access Control

```typescript
import { ChatOpenAI } from "@langchain/openai";
import { ChatAnthropic } from "@langchain/anthropic";

class ModelGateway {
  private models: Record<string, any> = {};

  constructor() {
    this.models["gpt-4o-mini"] = new ChatOpenAI({ model: "gpt-4o-mini" });
    this.models["gpt-4o"] = new ChatOpenAI({ model: "gpt-4o" });
    this.models["claude-sonnet"] = new ChatAnthropic({ model: "claude-sonnet-4-20250514" });
  }

  getModel(modelName: string, user: User, tenant: Tenant) {
    if (!canUseModel(user, tenant, modelName)) {
      throw new Error(
        `User ${user.email} (role: ${user.role}) cannot access model: ${modelName}`
      );
    }

    if (tenant.tokensUsed >= tenant.monthlyTokenLimit) {
      throw new Error(
        `Tenant ${tenant.name} exceeded monthly token limit (${tenant.monthlyTokenLimit})`
      );
    }

    return this.models[modelName];
  }
}
```

## Tenant-Scoped Vector Store

```typescript
// Isolate each tenant's documents in the vector store
import { PineconeStore } from "@langchain/pinecone";

class TenantScopedRetriever {
  constructor(
    private vectorStore: PineconeStore,
    private tenantId: string,
  ) {}

  async retrieve(query: string, k = 4) {
    // Filter by tenant ID — prevents cross-tenant data leakage
    return this.vectorStore.similaritySearch(query, k, {
      tenantId: { $eq: this.tenantId },
    });
  }

  asRetriever(k = 4) {
    return this.vectorStore.asRetriever({
      k,
      filter: { tenantId: { $eq: this.tenantId } },
    });
  }
}

// When ingesting documents, always tag with tenant ID
async function ingestForTenant(tenantId: string, docs: any[]) {
  const tagged = docs.map((doc) => ({
    ...doc,
    metadata: { ...doc.metadata, tenantId },
  }));
  await vectorStore.addDocuments(tagged);
}
```

## Usage Quota Tracking

```typescript
class UsageQuotaManager {
  private usage = new Map<string, number>();

  async trackUsage(tenantId: string, tokens: number) {
    const current = this.usage.get(tenantId) ?? 0;
    this.usage.set(tenantId, current + tokens);
  }

  async checkQuota(tenant: Tenant): Promise<boolean> {
    const used = this.usage.get(tenant.id) ?? 0;
    return used < tenant.monthlyTokenLimit;
  }

  async getUsageReport(tenantId: string) {
    return {
      tenantId,
      tokensUsed: this.usage.get(tenantId) ?? 0,
      period: new Date().toISOString().slice(0, 7), // YYYY-MM
    };
  }
}

// Integrate with callback
class QuotaCallback extends BaseCallbackHandler {
  name = "QuotaCallback";

  constructor(
    private quotaManager: UsageQuotaManager,
    private tenantId: string,
  ) { super(); }

  async handleLLMEnd(output: any) {
    const tokens = output.llmOutput?.tokenUsage?.totalTokens ?? 0;
    await this.quotaManager.trackUsage(this.tenantId, tokens);
  }
}
```

## Python FastAPI Equivalent

```python
from fastapi import Depends, HTTPException

async def get_current_user(token: str = Depends(oauth2_scheme)):
    user = decode_jwt(token)
    if not user:
        raise HTTPException(status_code=401)
    return user

def require_permission(permission: str):
    async def checker(user = Depends(get_current_user)):
        if permission not in ROLES[user.role]["permissions"]:
            raise HTTPException(status_code=403, detail=f"Missing: {permission}")
        return user
    return checker

@app.post("/api/chat")
async def chat(input: dict, user = Depends(require_permission("chain:invoke"))):
    return await chain.ainvoke({"input": input["text"]})
```

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| 401 Unauthorized | Missing or invalid token | Check auth middleware, token format |
| 403 Forbidden | Insufficient permissions | Upgrade user role or add permission |
| Tenant data leak | Missing filter on vector store | Always filter by `tenantId` |
| Quota exceeded | High usage | Increase tenant limit or optimize |

## Resources

- [RBAC Best Practices (Auth0)](https://auth0.com/docs/manage-users/access-control/rbac)
- [Multi-Tenant Architecture](https://learn.microsoft.com/en-us/azure/architecture/guide/multitenant/)
- [OAuth 2.0 Scopes](https://oauth.net/2/scope/)

## Next Steps

Use `langchain-data-handling` for tenant-scoped RAG pipelines.
