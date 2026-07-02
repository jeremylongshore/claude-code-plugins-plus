# Step 2: Download Exported Images

Deep-dive reference for the `figma-core-workflow-b` skill — extracted from the 'Step 2: Download Exported Images' step of the workflow.

```typescript
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

async function downloadAssets(
  nodeIds: string[],
  outputDir: string,
  format: 'png' | 'svg' = 'svg'
) {
  mkdirSync(outputDir, { recursive: true });

  const imageUrls = await exportImages(nodeIds, format);
  const results: { nodeId: string; path: string; success: boolean }[] = [];

  for (const [nodeId, url] of Object.entries(imageUrls)) {
    if (!url) {
      console.warn(`Node ${nodeId}: render returned null (invisible or invalid)`);
      results.push({ nodeId, path: '', success: false });
      continue;
    }

    const res = await fetch(url);
    const buffer = Buffer.from(await res.arrayBuffer());
    const filename = `${nodeId.replace(':', '-')}.${format}`;
    const filepath = join(outputDir, filename);
    writeFileSync(filepath, buffer);
    results.push({ nodeId, path: filepath, success: true });
  }

  return results;
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
