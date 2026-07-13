# Pitfall 4: Hardcoded PATs

Deep-dive reference for the `figma-known-pitfalls` skill — extracted from the 'Pitfall 4: Hardcoded PATs' step of the workflow.

**Problem:** Personal access tokens committed to source code.

```typescript
// BAD -- token in source code (visible forever in git history)
const token = 'figd_actual_token_value_here';

// GOOD -- environment variable
const token = process.env.FIGMA_PAT!;
if (!token) throw new Error('FIGMA_PAT not set');
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
