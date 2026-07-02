# Step 2: Run Load Tests

Deep-dive reference for the `figma-load-scale` skill — extracted from the 'Step 2: Run Load Tests' step of the workflow.

```bash
# Probe rate limits
k6 run \
  --env FIGMA_PAT="${FIGMA_PAT}" \
  --env FIGMA_FILE_KEY="${FIGMA_FILE_KEY}" \
  figma-load-test.js

# Export results to JSON for analysis
k6 run \
  --env FIGMA_PAT="${FIGMA_PAT}" \
  --env FIGMA_FILE_KEY="${FIGMA_FILE_KEY}" \
  --out json=results.json \
  figma-load-test.js
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
