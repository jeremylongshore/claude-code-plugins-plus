# Step 1: Reduce Payload Size

Deep-dive reference for the `figma-performance-tuning` skill — extracted from the 'Step 1: Reduce Payload Size' step of the workflow.

```typescript
// BAD: fetches the entire file tree (can be 10+ MB for large files)
const file = await fetch(`https://api.figma.com/v1/files/${fileKey}`, {
  headers: { 'X-Figma-Token': token },
}).then(r => r.json());

// GOOD: use depth parameter to limit tree depth
// depth=1 returns only pages (CANVAS nodes), not their children
const fileMeta = await fetch(
  `https://api.figma.com/v1/files/${fileKey}?depth=1`,
  { headers: { 'X-Figma-Token': token } }
).then(r => r.json());

// GOOD: fetch only specific nodes you need
const nodes = await fetch(
  `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${nodeIds.join(',')}`,
  { headers: { 'X-Figma-Token': token } }
).then(r => r.json());

// GOOD: use plugin_data or branch_data params only when needed
// By default, plugin data and branch data are NOT returned
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
