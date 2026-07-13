# Variant C: Figma Plugin (In-Editor)

Deep-dive reference for the `figma-architecture-variants` skill — extracted from the 'Variant C: Figma Plugin (In-Editor)' step of the workflow.

**Use case:** Design linting, component generation, data population

```
  ┌─────────────────────────────────────────┐
  │             Figma Desktop App            │
  │                                         │
  │  ┌─────────────┐   ┌─────────────────┐ │
  │  │ Plugin       │   │ Canvas          │ │
  │  │ Sandbox     │   │ (your design)   │ │
  │  │             │   │                 │ │
  │  │ code.ts     │◄──│ figma.currentPage│ │
  │  │ figma.*     │──►│ figma.createRect │ │
  │  │             │   │                 │ │
  │  ├─────────────┤   └─────────────────┘ │
  │  │ UI iframe   │                        │
  │  │ ui.html     │                        │
  │  │ (React/HTML)│                        │
  │  └─────────────┘                        │
  └─────────────────────────────────────────┘
```

```json
// manifest.json
{
  "name": "My Design Linter",
  "id": "1234567890",
  "api": "1.0.0",
  "main": "dist/code.js",
  "ui": "dist/ui.html",
  "editorType": ["figma"],
  "permissions": ["currentuser"]
}
```

```typescript
// code.ts -- Plugin API (runs in Figma sandbox)
// Access the document directly -- no REST API needed
const page = figma.currentPage;
const frames = page.findAll(n => n.type === 'FRAME');

// Create nodes programmatically
const rect = figma.createRectangle();
rect.resize(200, 100);
rect.fills = [{ type: 'SOLID', color: { r: 1, g: 0.5, b: 0 } }];
page.appendChild(rect);

// Read component properties
const components = page.findAll(n => n.type === 'COMPONENT') as ComponentNode[];
for (const comp of components) {
  console.log(`${comp.name}: ${comp.width}x${comp.height}`);
}
```

**Pros:** Direct document access, instant feedback, rich UI
**Cons:** Only works in Figma desktop, no server-side processing, sandboxed

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
