# Pitfall 1: Fetching Full File Trees

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 1: Fetching Full File Trees' step of the workflow.

**Problem:** `GET /v1/files/:key` without `depth` returns the entire document tree. Large files can be 10-100 MB of JSON.

```typescript
// BAD -- downloads entire file tree
const file = await figmaFetch(`/v1/files/${fileKey}`);

// GOOD -- only get metadata and page names
const file = await figmaFetch(`/v1/files/${fileKey}?depth=1`);

// GOOD -- fetch only the nodes you need
const nodes = await figmaFetch(`/v1/files/${fileKey}/nodes?ids=${ids}`);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
