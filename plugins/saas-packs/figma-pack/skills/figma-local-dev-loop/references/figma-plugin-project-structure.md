# Step 2: Figma Plugin Project Structure

Deep-dive reference for the `figma-local-dev-loop` skill — extracted from the 'Step 2: Figma Plugin Project Structure' step of the workflow.

```
my-figma-plugin/
├── manifest.json             # Plugin manifest (required by Figma)
├── code.ts                   # Plugin backend (runs in sandbox)
├── ui.html                   # Plugin UI (runs in iframe)
├── package.json
└── tsconfig.json
```

**manifest.json** (required):

```json
{
  "name": "My Plugin",
  "id": "1234567890",
  "api": "1.0.0",
  "main": "dist/code.js",
  "ui": "dist/ui.html",
  "editorType": ["figma"],
  "permissions": ["currentuser"]
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
