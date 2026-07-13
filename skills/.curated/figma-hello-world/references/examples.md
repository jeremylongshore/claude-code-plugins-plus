# figma-hello-world: Worked Examples

Worked examples for the `figma-hello-world` skill — extracted from the skill's Examples section.

## Quick Node Counter

```bash
# Count total nodes in a file
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq '[.. | .id? // empty] | length'
```

## Get File Thumbnail

```bash
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" \
  | jq -r '.thumbnailUrl'
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
