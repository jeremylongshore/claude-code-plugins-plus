# Pitfall 6: Forgetting Color Format Conversion

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 6: Forgetting Color Format Conversion' step of the workflow.

**Problem:** Figma returns colors as 0-1 floats, not 0-255 integers.

```typescript
// BAD -- using Figma values directly as RGB
const { r, g, b } = node.fills[0].color;
return `rgb(${r}, ${g}, ${b})`; // rgb(0.8, 0.2, 0.4) -- invalid!

// GOOD -- convert to 0-255 range
return `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`;
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
