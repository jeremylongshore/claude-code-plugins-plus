# Pitfall 7: Not Handling null Image Renders

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 7: Not Handling null Image Renders' step of the workflow.

**Problem:** The images endpoint returns `null` for nodes that cannot be rendered (invisible, deleted, empty).

```typescript
// BAD -- assumes all nodes render successfully
const images = data.images;
for (const [id, url] of Object.entries(images)) {
  const img = await fetch(url); // TypeError: Cannot construct URL from null
}

// GOOD -- filter out null entries
for (const [id, url] of Object.entries(images)) {
  if (!url) {
    console.warn(`Node ${id} could not be rendered (null)`);
    continue;
  }
  const img = await fetch(url);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
