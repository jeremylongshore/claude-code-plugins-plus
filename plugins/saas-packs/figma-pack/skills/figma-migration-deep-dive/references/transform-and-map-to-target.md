# Step 3: Transform and Map to Target

Deep-dive reference for the `figma-migration-deep-dive` skill — extracted from the 'Step 3: Transform and Map to Target' step of the workflow.

```typescript
// Map extracted styles to design tokens JSON
interface MigrationToken {
  name: string;
  category: 'color' | 'typography' | 'effect';
  source: { file: string; nodeId: string };
  value: any;
}

function transformStyles(styles: any[], sourceFileKey: string): MigrationToken[] {
  return styles.map(style => {
    switch (style.type) {
      case 'FILL':
        const fill = style.data.fills?.[0];
        return {
          name: style.name,
          category: 'color' as const,
          source: { file: sourceFileKey, nodeId: style.nodeId },
          value: fill?.color
            ? {
                r: Math.round(fill.color.r * 255),
                g: Math.round(fill.color.g * 255),
                b: Math.round(fill.color.b * 255),
                a: fill.color.a ?? 1,
              }
            : null,
        };
      case 'TEXT':
        return {
          name: style.name,
          category: 'typography' as const,
          source: { file: sourceFileKey, nodeId: style.nodeId },
          value: style.data.style
            ? {
                fontFamily: style.data.style.fontFamily,
                fontSize: style.data.style.fontSize,
                fontWeight: style.data.style.fontWeight,
                lineHeight: style.data.style.lineHeightPx,
              }
            : null,
        };
      default:
        return {
          name: style.name,
          category: 'effect' as const,
          source: { file: sourceFileKey, nodeId: style.nodeId },
          value: style.data.effects,
        };
    }
  }).filter(t => t.value !== null);
}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
