# Environment-Aware Configuration

TypeScript configuration module that loads environment-specific settings with type-safe overrides.

```typescript
// src/config.ts
import { LATEST_API_VERSION } from "@shopify/shopify-api";

interface ShopifyEnvConfig {
  apiKey: string;
  apiSecret: string;
  appUrl: string;
  apiVersion: string;
  scopes: string[];
  environment: "development" | "staging" | "production";
  debug: boolean;
  sessionStorageType: "memory" | "sqlite" | "postgresql";
}

function getConfig(): ShopifyEnvConfig {
  const env = (process.env.NODE_ENV || "development") as ShopifyEnvConfig["environment"];

  const base = {
    apiKey: process.env.SHOPIFY_API_KEY!,
    apiSecret: process.env.SHOPIFY_API_SECRET!,
    appUrl: process.env.SHOPIFY_APP_URL!,
    apiVersion: process.env.SHOPIFY_API_VERSION || LATEST_API_VERSION,
    scopes: (process.env.SHOPIFY_SCOPES || "read_products").split(","),
    environment: env,
  };

  const envOverrides: Record<string, Partial<ShopifyEnvConfig>> = {
    development: {
      debug: true,
      sessionStorageType: "sqlite",
    },
    staging: {
      debug: false,
      sessionStorageType: "postgresql",
    },
    production: {
      debug: false,
      sessionStorageType: "postgresql",
    },
  };

  return { ...base, ...envOverrides[env] } as ShopifyEnvConfig;
}
```
