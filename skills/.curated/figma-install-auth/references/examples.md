# figma-install-auth: Worked Examples

Worked examples for the `figma-install-auth` skill — extracted from the skill's Examples section.

## Reusable Figma Client Wrapper

```typescript
// src/figma-client.ts
export function figmaFetch(path: string, options: RequestInit = {}) {
  const token = process.env.FIGMA_PAT;
  if (!token) throw new Error('FIGMA_PAT environment variable is not set');

  return fetch(`https://api.figma.com${path}`, {
    ...options,
    headers: {
      'X-Figma-Token': token,
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
}

// Usage
const file = await figmaFetch(`/v1/files/${fileKey}`).then(r => r.json());
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
