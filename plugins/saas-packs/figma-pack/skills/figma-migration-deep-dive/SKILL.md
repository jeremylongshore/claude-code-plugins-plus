---
name: figma-migration-deep-dive
description: |
  Migrate design systems between Figma files, or from other tools to Figma via API.
  Use when migrating design tokens between files, syncing variables across libraries,
  or building automated migration pipelines for Figma.
  Trigger with phrases like "migrate figma", "figma migration",
  "move figma library", "figma file migration", "sync figma files".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Migration Deep Dive

## Overview
Automate migration of design data between Figma files, from other tools to Figma, or from Figma styles to the Variables API. Covers inventory, extraction, transformation, and validation.

## Prerequisites
- Source and destination Figma file keys
- `FIGMA_PAT` with `file_content:read` and `file_variables:write` (Enterprise) scopes
- Understanding of source file structure

## Instructions

### Step 1: Inventory Source File
```typescript
const PAT = process.env.FIGMA_PAT!;

async function inventoryFile(fileKey: string) {
  const res = await fetch(
    `https://api.figma.com/v1/files/${fileKey}`,
    { headers: { 'X-Figma-Token': PAT } }
  );
  const file = await res.json();

  const inventory = {
    name: file.name,
    pages: file.document.children.map((p: any) => p.name),
    componentCount: Object.keys(file.components).length,
    styleCount: Object.keys(file.styles).length,
    styles: {
      fills: Object.values(file.styles).filter((s: any) => s.style_type === 'FILL').length,
      text: Object.values(file.styles).filter((s: any) => s.style_type === 'TEXT').length,
      effects: Object.values(file.styles).filter((s: any) => s.style_type === 'EFFECT').length,
      grids: Object.values(file.styles).filter((s: any) => s.style_type === 'GRID').length,
    },
  };

  // Count total nodes
  let nodeCount = 0;
  function countNodes(node: any) {
    nodeCount++;
    if (node.children) node.children.forEach(countNodes);
  }
  countNodes(file.document);
  (inventory as any).totalNodes = nodeCount;

  return inventory;
}

// Usage
const inv = await inventoryFile(process.env.FIGMA_FILE_KEY!);
console.log(`File: ${inv.name}`);
console.log(`Pages: ${inv.pages.join(', ')}`);
console.log(`Components: ${inv.componentCount}, Styles: ${inv.styleCount}`);
console.log(`Total nodes: ${(inv as any).totalNodes}`);
```

### Step 2: Extract Styles from Source
```typescript
async function extractAllStyles(fileKey: string) {
  const file = await fetch(
    `https://api.figma.com/v1/files/${fileKey}`,
    { headers: { 'X-Figma-Token': PAT } }
  ).then(r => r.json());

  const styleNodeIds = Object.keys(file.styles);
  const nodesRes = await fetch(
    `https://api.figma.com/v1/files/${fileKey}/nodes?ids=${styleNodeIds.join(',')}`,
    { headers: { 'X-Figma-Token': PAT } }
  ).then(r => r.json());

  const extracted = [];
  for (const [nodeId, styleMeta] of Object.entries(file.styles) as any[]) {
    const node = nodesRes.nodes[nodeId]?.document;
    if (!node) continue;

    extracted.push({
      name: styleMeta.name,
      type: styleMeta.style_type,
      nodeId,
      data: {
        fills: node.fills,
        strokes: node.strokes,
        effects: node.effects,
        style: node.style,       // typography
        characters: node.characters,
      },
    });
  }

  return extracted;
}
```

### Step 3: Transform and Map to Target
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

### Step 4: Write to Target (Variables API)
```typescript
// Enterprise only: create variables in the target file
async function migrateToVariables(
  targetFileKey: string,
  tokens: MigrationToken[]
) {
  const colorTokens = tokens.filter(t => t.category === 'color');

  // Create variable collection and variables
  const payload = {
    variableCollections: [{
      action: 'CREATE' as const,
      id: 'temp_collection_1',
      name: 'Migrated Colors',
    }],
    variables: colorTokens.map((token, i) => ({
      action: 'CREATE' as const,
      id: `temp_var_${i}`,
      name: token.name.replace(/\//g, '/'), // preserve Figma group paths
      variableCollectionId: 'temp_collection_1',
      resolvedType: 'COLOR' as const,
      codeSyntax: { WEB: `--${token.name.toLowerCase().replace(/[\s/]+/g, '-')}` },
    })),
    variableModeValues: colorTokens.map((token, i) => ({
      variableId: `temp_var_${i}`,
      modeId: '', // Will use default mode
      value: {
        r: token.value.r / 255,
        g: token.value.g / 255,
        b: token.value.b / 255,
        a: token.value.a,
      },
    })),
  };

  const res = await fetch(
    `https://api.figma.com/v1/files/${targetFileKey}/variables`,
    {
      method: 'POST',
      headers: {
        'X-Figma-Token': PAT,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  );

  if (!res.ok) throw new Error(`Variable creation failed: ${res.status} ${await res.text()}`);
  return res.json();
}
```

### Step 5: Validation
```typescript
async function validateMigration(
  sourceFileKey: string,
  targetFileKey: string
): Promise<{ passed: boolean; issues: string[] }> {
  const sourceStyles = await extractAllStyles(sourceFileKey);
  const targetVars = await fetch(
    `https://api.figma.com/v1/files/${targetFileKey}/variables/local`,
    { headers: { 'X-Figma-Token': PAT } }
  ).then(r => r.json());

  const issues: string[] = [];
  const targetNames = new Set(
    Object.values(targetVars.meta.variables).map((v: any) => v.name)
  );

  for (const style of sourceStyles) {
    if (style.type === 'FILL' && !targetNames.has(style.name)) {
      issues.push(`Missing in target: ${style.name}`);
    }
  }

  return { passed: issues.length === 0, issues };
}
```

## Output
- Source file inventoried (components, styles, nodes)
- Styles extracted and transformed to tokens
- Tokens written to target file via Variables API
- Migration validated with comparison report

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 403 on Variables POST | Not Enterprise | Use JSON export instead of Variables API |
| Duplicate variable names | Name collision in target | Add prefix/suffix to migrated names |
| Missing node data | Node deleted between fetch and read | Re-fetch with error handling |
| Large file timeout | File >100MB | Use `/nodes` endpoint for specific pages |

## Resources
- [Figma Variables API](https://developers.figma.com/docs/rest-api/variables-endpoints/)
- [Figma File Endpoints](https://developers.figma.com/docs/rest-api/file-endpoints/)
- [Design Tokens Format](https://design-tokens.github.io/community-group/format/)

## Next Steps
For advanced troubleshooting, see `figma-advanced-troubleshooting`.
