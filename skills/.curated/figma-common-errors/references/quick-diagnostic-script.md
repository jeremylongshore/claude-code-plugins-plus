# Step 4: Quick Diagnostic Script

Deep-dive reference for the `figma-common-errors` skill — extracted from the 'Step 4: Quick Diagnostic Script' step of the workflow.

```bash
#!/bin/bash
echo "=== Figma API Diagnostics ==="

# 1. Check Figma service status
echo -n "Figma Status: "
curl -s -o /dev/null -w "%{http_code}" https://www.figma.com && echo " OK" || echo " DOWN"

# 2. Validate token
echo -n "Token Valid: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me

# 3. Check file access
echo -n "File Access: "
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq -r '.name // "FAILED"'

# 4. Check env vars
echo "FIGMA_PAT: ${FIGMA_PAT:+SET (${#FIGMA_PAT} chars)}"
echo "FIGMA_FILE_KEY: ${FIGMA_FILE_KEY:-NOT SET}"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
