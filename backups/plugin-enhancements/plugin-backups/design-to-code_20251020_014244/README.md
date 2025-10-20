# Design to Code

**Convert Figma designs and screenshots to production-ready code components**

Transform design files into React, Svelte, or Vue components with built-in accessibility.

##  Features

- **Figma Parser** - Extract components from Figma JSON exports
- **Screenshot Analysis** - Analyze UI layouts from images
- **Code Generation** - React, Svelte, Vue components
- **A11y Built-in** - ARIA labels, semantic HTML, keyboard navigation
- **Style Extraction** - Colors, typography, spacing

##  Installation

```bash
/plugin install design-to-code@claude-code-plugins-plus
```

##  3 MCP Tools

### 1. `parse_figma`
Extract components from Figma JSON export.

```json
{
  "json": "{\"name\": \"Button\", ...}",
  "framework": "react"
}
```

### 2. `analyze_screenshot`
Analyze screenshot layout and extract UI elements.

```json
{
  "imagePath": "/path/to/screenshot.png",
  "framework": "svelte"
}
```

### 3. `generate_component`
Generate code from layout specification.

```json
{
  "layout": {
    "type": "container",
    "children": [...]
  },
  "framework": "react",
  "includeA11y": true
}
```

##  Quick Start

```javascript
// 1. Parse Figma design
const design = await parse_figma({
  json: figmaExport,
  framework: 'react'
});

// 2. Generate component
const component = await generate_component({
  layout: design.layout,
  framework: 'react',
  includeA11y: true
});

// Result: Production-ready React component with accessibility
```

##  Accessibility Features

All generated components include:
-  **ARIA labels** - Screen reader support
-  **Semantic HTML** - Proper element usage
-  **Keyboard navigation** - Tab order, focus states
-  **Color contrast** - WCAG AA compliance checking

##  Supported Frameworks

- **React** - JSX with hooks
- **Svelte** - Single-file components
- **Vue** - Composition API

##  License

MIT License

---

**Made with ️ by [Intent Solutions](https://intentsolutions.io)**
