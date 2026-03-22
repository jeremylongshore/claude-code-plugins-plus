---
name: figma-core-workflow-a
description: |
  Extract design tokens, colors, typography, and spacing from Figma files via REST API.
  Use when building a design-to-code pipeline, syncing design tokens,
  or extracting styles from a Figma design system file.
  Trigger with phrases like "figma design tokens", "extract figma styles",
  "figma to CSS", "sync figma colors", "figma typography".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Core Workflow A -- Design Token Extraction

## Overview
The primary workflow for Figma API integrations: extracting design tokens (colors, typography, spacing) from a Figma file and converting them to CSS custom properties, JSON tokens, or Tailwind config.

## Prerequisites
- Completed `figma-install-auth` setup
- A Figma file with published styles or variables
- `FIGMA_PAT` and `FIGMA_FILE_KEY` env vars set

## Instructions

### Step 1: Fetch Styles from a File
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

### Step 2: Resolve Style Values from Nodes
```typescript
// Fetch the actual nodes to get fill colors and text properties
const styleNodeIds = colorStyles.map(s => s.nodeId);
const nodesResponse = await client.getFileNodes(fileKey, styleNodeIds);

interface DesignToken {
  name: string;
  type: 'color' | 'typography' | 'spacing';
  value: string;
}

const tokens: DesignToken[] = [];

for (const [nodeId, nodeData] of Object.entries(nodesResponse.nodes)) {
  const node = nodeData.document;
  const styleName = colorStyles.find(s => s.nodeId === nodeId)?.name;

  if (node.fills?.[0]?.type === 'SOLID' && node.fills[0].color) {
    const { r, g, b, a } = node.fills[0].color;
    // Figma colors are 0-1 floats; convert to 0-255
    const hex = '#' + [r, g, b].map(v =>
      Math.round(v * 255).toString(16).padStart(2, '0')
    ).join('');

    tokens.push({
      name: styleName ?? node.name,
      type: 'color',
      value: a !== undefined && a < 1
        ? `rgba(${Math.round(r*255)}, ${Math.round(g*255)}, ${Math.round(b*255)}, ${a.toFixed(2)})`
        : hex,
    });
  }
}
```

### Step 3: Extract Typography Tokens
```typescript
// Fetch text style nodes
const textNodeIds = textStyles.map(s => s.nodeId);
const textNodes = await client.getFileNodes(fileKey, textNodeIds);

for (const [nodeId, nodeData] of Object.entries(textNodes.nodes)) {
  const node = nodeData.document;
  const styleName = textStyles.find(s => s.nodeId === nodeId)?.name;

  if (node.style) {
    tokens.push({
      name: styleName ?? node.name,
      type: 'typography',
      value: JSON.stringify({
        fontFamily: node.style.fontFamily,
        fontSize: `${node.style.fontSize}px`,
        fontWeight: node.style.fontWeight,
        lineHeight: node.style.lineHeightPx
          ? `${node.style.lineHeightPx}px`
          : 'normal',
        letterSpacing: node.style.letterSpacing
          ? `${node.style.letterSpacing}px`
          : '0',
      }),
    });
  }
}
```

### Step 4: Generate CSS Custom Properties
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

### Step 5: Use Variables API (Enterprise)
```typescript
// GET /v1/files/:key/variables/local (Tier 2, requires file_variables:read)
const vars = await client.getLocalVariables(fileKey);

// vars.meta.variables: Record<variableId, Variable>
// vars.meta.variableCollections: Record<collectionId, Collection>
for (const [id, variable] of Object.entries(vars.meta.variables)) {
  const collection = vars.meta.variableCollections[variable.variableCollectionId];
  console.log(`${collection.name}/${variable.name}: ${variable.resolvedType}`);
  // resolvedType: "COLOR" | "FLOAT" | "STRING" | "BOOLEAN"

  // Each variable has values per mode
  for (const [modeId, value] of Object.entries(variable.valuesByMode)) {
    const modeName = collection.modes.find(m => m.modeId === modeId)?.name;
    console.log(`  ${modeName}: ${JSON.stringify(value)}`);
  }
}
```

## Output
- Design tokens extracted from Figma styles or variables
- CSS custom properties file generated
- Color values converted from Figma's 0-1 float format to hex/rgba
- Typography properties mapped to CSS-compatible values

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Empty `styles` map | File has no published styles | Publish styles in Figma first |
| `null` node in response | Node was deleted | Filter nulls before processing |
| 403 on variables endpoint | Not Enterprise plan | Use styles endpoint instead |
| Color looks wrong | Forgot 0-1 to 0-255 conversion | Multiply by 255 before hex |

## Resources
- [Figma File Endpoints](https://developers.figma.com/docs/rest-api/file-endpoints/)
- [Figma Variables API](https://developers.figma.com/docs/rest-api/variables-endpoints/)
- [Design Tokens Format](https://design-tokens.github.io/community-group/format/)

## Next Steps
For asset export, see `figma-core-workflow-b`.
