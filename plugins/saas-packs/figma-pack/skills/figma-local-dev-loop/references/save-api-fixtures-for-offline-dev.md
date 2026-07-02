# Step 5: Save API Fixtures for Offline Dev

Deep-dive reference for the `figma-local-dev-loop` skill — extracted from the 'Step 5: Save API Fixtures for Offline Dev' step of the workflow.

```bash
# Snapshot a Figma file for offline testing
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  > tests/fixtures/sample-file.json

# Snapshot specific nodes
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}/nodes?ids=0:1,0:2" \
  > tests/fixtures/sample-nodes.json
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
