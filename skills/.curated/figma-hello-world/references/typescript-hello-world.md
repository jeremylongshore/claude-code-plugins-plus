# Step 3: TypeScript Hello World

Deep-dive reference for the `figma-hello-world` skill — extracted from the 'Step 3: TypeScript Hello World' step of the workflow.

```typescript
// hello-figma.ts
const PAT = process.env.FIGMA_PAT!;
const FILE_KEY = process.env.FIGMA_FILE_KEY!;

interface FigmaNode {
  id: string;
  name: string;
  type: string;
  children?: FigmaNode[];
}

interface FigmaFileResponse {
  name: string;
  lastModified: string;
  version: string;
  document: FigmaNode;
  components: Record<string, { key: string; name: string; description: string }>;
  styles: Record<string, { key: string; name: string; style_type: string }>;
}

async function main() {
  const res = await fetch(
    `https://api.figma.com/v1/files/${FILE_KEY}`,
    { headers: { 'X-Figma-Token': PAT } }
  );

  if (!res.ok) {
    throw new Error(`Figma API error: ${res.status} ${res.statusText}`);
  }

  const file: FigmaFileResponse = await res.json();

  console.log(`File: ${file.name}`);
  console.log(`Last modified: ${file.lastModified}`);
  console.log(`Components: ${Object.keys(file.components).length}`);
  console.log(`Styles: ${Object.keys(file.styles).length}`);

  // Walk the first page and list top-level frames
  const firstPage = file.document.children?.[0];
  if (firstPage) {
    console.log(`\nPage: ${firstPage.name}`);
    for (const child of firstPage.children ?? []) {
      console.log(`  ${child.type}: ${child.name} (${child.id})`);
    }
  }
}

main().catch(console.error);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
