# Pitfall 9: SVG Export with Scale Parameter

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 9: SVG Export with Scale Parameter' step of the workflow.

**Problem:** Figma ignores the `scale` parameter for SVG exports. SVGs always export at 1x.

```typescript
// BAD -- scale has no effect on SVG
await figmaFetch(`/v1/images/${key}?ids=${id}&format=svg&scale=2`);

// GOOD -- SVG is vector; scale is meaningless. Use scale for PNG/JPG only.
await figmaFetch(`/v1/images/${key}?ids=${id}&format=svg`);      // SVG: always 1x
await figmaFetch(`/v1/images/${key}?ids=${id}&format=png&scale=2`); // PNG: 2x
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
