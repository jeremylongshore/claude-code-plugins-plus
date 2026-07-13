# figma-local-dev-loop: Worked Examples

Worked examples for the `figma-local-dev-loop` skill — extracted from the skill's Examples section.

## Quick Plugin Skeleton

```typescript
// code.ts -- minimal Figma plugin
figma.showUI(__html__, { width: 300, height: 200 });

figma.ui.onmessage = (msg: { type: string; count: number }) => {
  if (msg.type === 'create-rectangles') {
    for (let i = 0; i < msg.count; i++) {
      const rect = figma.createRectangle();
      rect.x = i * 150;
      rect.fills = [{ type: 'SOLID', color: { r: 1, g: 0.5, b: 0 } }];
      figma.currentPage.appendChild(rect);
    }
    figma.closePlugin();
  }
};
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
