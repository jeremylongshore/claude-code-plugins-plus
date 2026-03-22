---
name: adobe-design-token-sync
description: |
  Execute Adobe secondary workflow: Design Token Sync.
  Use when keeping CSS variables in sync with design system,
  or generating Tailwind theme config from design files.
  Trigger with phrases like "adobe design tokens",
  "sync design tokens with adobe".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, adobe]
---

# Adobe Design Token Sync

## Overview
Extract design tokens (colors, typography, spacing) from design files
and sync them to code as CSS variables, Tailwind config, or JSON.


## Prerequisites
- Completed `adobe-install-auth` setup
- Familiarity with `adobe-export-assets`
- Valid API credentials configured

## Instructions

### Step 1: Extract Styles from File
```typescript
const styles = await client.files.styles(fileId);
const colors = styles.filter(s => s.style_type === 'FILL');
const typography = styles.filter(s => s.style_type === 'TEXT');
console.log(`Colors: ${colors.length}, Typography: ${typography.length}`);

```

### Step 2: Transform to CSS Variables
```typescript
const cssVars = colors.map(c => {
  const { r, g, b, a } = c.color;
  return `--${c.name.toLowerCase().replace(/\s+/g, '-')}: rgba(${Math.round(r*255)}, ${Math.round(g*255)}, ${Math.round(b*255)}, ${a});`;
}).join('\n  ');
const css = `:root {\n  ${cssVars}\n}`;

```

### Step 3: Write Token Files
```typescript
fs.writeFileSync('src/styles/tokens.css', css);
fs.writeFileSync('src/tokens.json', JSON.stringify(tokenMap, null, 2));
console.log('Design tokens synced to code');

```

## Output
- Completed Design Token Sync execution

- Design tokens extracted and written to code files
- CSS variables and/or Tailwind config synced

- Success confirmation or error details

## Error Handling
| Aspect | Export & Asset Pipeline | Design Token Sync |
|--------|------------|------------|
| Use Case | exporting icons and images for a web build pipeline | keeping CSS variables in sync with design system |
| Complexity | Medium | Medium |
| Performance | Standard | Fast (API reads only) |

## Examples

### Complete Workflow
```typescript
async function syncTokens(fileId: string) {
  const styles = await client.files.styles(fileId);
  const tokens = transformToCSS(styles);
  fs.writeFileSync('tokens.css', tokens);
  return styles.length;
}

```

### Error Recovery
```typescript
try {
  const styles = await client.files.styles(fileId);
  return styles;
} catch (err) {
  if (err.status === 403) {
    console.error('Missing file access. Share file with your API token user.');
  }
  throw err;
}

```

## Resources
- [Adobe Documentation](https://docs.adobe.com)
- [Adobe API Reference](https://docs.adobe.com/api)

## Next Steps
For common errors, see `adobe-common-errors`.