# Step 2: Configuration by Environment

Deep-dive reference for the `figma-multi-env-setup` skill — extracted from the 'Step 2: Configuration by Environment' step of the workflow.

```typescript
// src/config/figma.ts
interface FigmaEnvConfig {
  token: string;
  fileKey: string;
  cacheTTL: number;
  webhookPasscode?: string;
  maxConcurrency: number;
}

function getFigmaConfig(): FigmaEnvConfig {
  const env = process.env.NODE_ENV || 'development';

  const configs: Record<string, Partial<FigmaEnvConfig>> = {
    development: {
      token: process.env.FIGMA_PAT_DEV!,
      fileKey: process.env.FIGMA_FILE_KEY_DEV!,
      cacheTTL: 10_000,
      maxConcurrency: 1,
    },
    staging: {
      token: process.env.FIGMA_PAT_STAGING!,
      fileKey: process.env.FIGMA_FILE_KEY_STAGING!,
      cacheTTL: 60_000,
      maxConcurrency: 3,
    },
    production: {
      token: process.env.FIGMA_PAT_PROD!,
      fileKey: process.env.FIGMA_FILE_KEY_PROD!,
      cacheTTL: 300_000,
      maxConcurrency: 5,
      webhookPasscode: process.env.FIGMA_WEBHOOK_PASSCODE,
    },
  };

  const config = configs[env];
  if (!config?.token) throw new Error(`Figma token not configured for env: ${env}`);
  if (!config?.fileKey) throw new Error(`Figma file key not configured for env: ${env}`);

  return config as FigmaEnvConfig;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
