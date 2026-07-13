# Step 7: Pre-Flight Verification

Deep-dive reference for the `figma-prod-checklist` skill — extracted from the 'Step 7: Pre-Flight Verification' step of the workflow.

```bash
#!/bin/bash
echo "=== Figma Production Pre-Flight ==="

# 1. Token valid?
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me)
echo "Auth: $STATUS (expect 200)"

# 2. File accessible?
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1")
echo "File: $STATUS (expect 200)"

# 3. Figma status page
echo -n "Figma Status: "
curl -s https://www.figmastatus.com/api/v2/status.json 2>/dev/null \
  | jq -r '.status.description // "Unable to check"'

echo "=== Pre-flight complete ==="
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
