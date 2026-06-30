# Xquik TypeScript Types: API Keys

```typescript

interface ApiKeyCreated {
  id: string;
  fullKey: string;
  prefix: string;
  name: string;
  createdAt: string;
}

interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  isActive: boolean;
  createdAt: string;
  lastUsedAt?: string;
}

```
