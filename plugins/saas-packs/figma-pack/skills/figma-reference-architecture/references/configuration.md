# Step 4: Configuration

Deep-dive reference for the `figma-reference-architecture` skill — extracted from the 'Step 4: Configuration' step of the workflow.

```typescript
// src/config.ts
export const config = {
  figma: {
    token: process.env.FIGMA_PAT!,
    fileKey: process.env.FIGMA_FILE_KEY!,
    webhookPasscode: process.env.FIGMA_WEBHOOK_PASSCODE,
  },
  cache: {
    fileTTL: 5 * 60 * 1000,      // 5 minutes for file metadata
    imageTTL: 24 * 60 * 60 * 1000, // 24 hours for image URLs
    maxEntries: 500,
  },
  api: {
    maxConcurrent: 3,
    retryAttempts: 3,
    requestTimeout: 30_000,
  },
};
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
