# Pitfall 2: Ignoring Rate Limit Headers

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 2: Ignoring Rate Limit Headers' step of the workflow.

**Problem:** Blasting requests and crashing on 429 without reading `Retry-After`.

```typescript
// BAD -- no rate limit handling
for (const id of nodeIds) {
  await figmaFetch(`/v1/files/${fileKey}/nodes?ids=${id}`); // 429!
}

// GOOD -- batch IDs and honor Retry-After
const ids = nodeIds.join(',');
const res = await fetch(`https://api.figma.com/v1/files/${fileKey}/nodes?ids=${ids}`, {
  headers: { 'X-Figma-Token': token },
});
if (res.status === 429) {
  const wait = parseInt(res.headers.get('Retry-After') || '60');
  await new Promise(r => setTimeout(r, wait * 1000));
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
