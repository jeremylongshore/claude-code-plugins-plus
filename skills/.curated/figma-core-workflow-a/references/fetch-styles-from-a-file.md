# Step 1: Fetch Styles from a File

Deep-dive reference for the `figma-core-workflow-a` skill — extracted from the 'Step 1: Fetch Styles from a File' step of the workflow.

```typescript
import { FigmaClient } from './figma-client';

const client = new FigmaClient(process.env.FIGMA_PAT!);
const fileKey = process.env.FIGMA_FILE_KEY!;

// GET /v1/files/:key -- returns styles map in response
const file = await client.getFile(fileKey);

// file.styles is a map: nodeId -> { key, name, style_type, description }
// style_type: "FILL" | "TEXT" | "EFFECT" | "GRID"
const colorStyles = Object.entries(file.styles)
  .filter(([, s]) => s.style_type === 'FILL')
  .map(([nodeId, s]) => ({ nodeId, name: s.name }));

const textStyles = Object.entries(file.styles)
  .filter(([, s]) => s.style_type === 'TEXT')
  .map(([nodeId, s]) => ({ nodeId, name: s.name }));

console.log(`Found ${colorStyles.length} color styles, ${textStyles.length} text styles`);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
