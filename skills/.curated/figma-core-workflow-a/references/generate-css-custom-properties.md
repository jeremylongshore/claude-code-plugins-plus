# Step 4: Generate CSS Custom Properties

Deep-dive reference for the `figma-core-workflow-a` skill — extracted from the 'Step 4: Generate CSS Custom Properties' step of the workflow.

```typescript
function tokensToCss(tokens: DesignToken[]): string {
  const lines = [':root {'];
  for (const token of tokens) {
    const varName = `--${token.name.toLowerCase().replace(/[\s/]+/g, '-')}`;
    if (token.type === 'color') {
      lines.push(`  ${varName}: ${token.value};`);
    } else if (token.type === 'typography') {
      const t = JSON.parse(token.value);
      lines.push(`  ${varName}-family: ${t.fontFamily};`);
      lines.push(`  ${varName}-size: ${t.fontSize};`);
      lines.push(`  ${varName}-weight: ${t.fontWeight};`);
    }
  }
  lines.push('}');
  return lines.join('\n');
}

import { writeFileSync } from 'fs';
writeFileSync('src/styles/tokens.css', tokensToCss(tokens));
console.log(`Generated ${tokens.length} tokens to src/styles/tokens.css`);
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
