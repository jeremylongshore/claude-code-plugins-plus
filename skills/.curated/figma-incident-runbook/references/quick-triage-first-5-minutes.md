# Step 1: Quick Triage (First 5 Minutes)

Deep-dive reference for the `figma-incident-runbook` skill — extracted from the 'Step 1: Quick Triage (First 5 Minutes)' step of the workflow.

```bash
#!/bin/bash
echo "=== Figma Incident Triage ==="

# 1. Is Figma itself down?
echo -n "Figma Status: "
curl -s https://www.figmastatus.com/api/v2/status.json 2>/dev/null \
  | jq -r '.status.description // "Cannot reach status page"'

# 2. Is our token valid?
echo -n "Auth Check: "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me)
echo "$HTTP_CODE"

# 3. Can we read a known file?
echo -n "File Access: "
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}?depth=1" \
  | jq -r '.name // "FAILED"'

# 4. Are we rate limited?
echo "Rate Limit Headers:"
curl -s -D - -o /dev/null \
  -H "X-Figma-Token: ${FIGMA_PAT}" \
  https://api.figma.com/v1/me 2>/dev/null \
  | grep -iE "(retry-after|rate-limit|figma)" || echo "No rate limit headers"
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
