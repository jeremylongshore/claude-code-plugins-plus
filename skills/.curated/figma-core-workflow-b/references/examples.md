# figma-core-workflow-b: Worked Examples

Worked examples for the `figma-core-workflow-b` skill — extracted from the skill's Examples section.

## Quick Export via curl

```bash
# Export a single node as PNG at 2x
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/images/${FIGMA_FILE_KEY}?ids=0:1&format=png&scale=2" \
  | jq -r '.images["0:1"]'
# Returns a temporary URL to the rendered image
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
