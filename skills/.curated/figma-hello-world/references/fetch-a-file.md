# Step 1: Fetch a File

Deep-dive reference for the `figma-hello-world` skill — extracted from the 'Step 1: Fetch a File' step of the workflow.

```bash
# Get the full document JSON for a file
curl -s -H "X-Figma-Token: ${FIGMA_PAT}" \
  "https://api.figma.com/v1/files/${FIGMA_FILE_KEY}" | jq '{
    name: .name,
    lastModified: .lastModified,
    version: .version,
    pages: [.document.children[] | .name]
  }'
```

Expected output:

```json
{
  "name": "My Design File",
  "lastModified": "2025-03-15T10:30:00Z",
  "version": "1234567890",
  "pages": ["Page 1", "Components", "Tokens"]
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
