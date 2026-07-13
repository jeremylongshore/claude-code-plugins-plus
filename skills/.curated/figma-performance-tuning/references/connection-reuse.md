# Step 5: Connection Reuse

Deep-dive reference for the `figma-performance-tuning` skill — extracted from the 'Step 5: Connection Reuse' step of the workflow.

```typescript
import { Agent } from 'undici';

// Reuse HTTP connections to api.figma.com
const figmaAgent = new Agent({
  keepAliveTimeout: 30_000,
  keepAliveMaxTimeout: 60_000,
  connections: 5,
});

// Use with Node.js 18+ built-in fetch
async function optimizedFetch(path: string, token: string) {
  return fetch(`https://api.figma.com${path}`, {
    headers: { 'X-Figma-Token': token },
    // @ts-ignore -- dispatcher is a Node.js fetch option
    dispatcher: figmaAgent,
  });
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
