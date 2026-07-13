# Step 2: Understand the Node Tree

Deep-dive reference for the `figma-hello-world` skill — extracted from the 'Step 2: Understand the Node Tree' step of the workflow.

Every Figma file is a tree of typed nodes:

```
DOCUMENT (root)
├── CANVAS (page)
│   ├── FRAME (container / auto-layout)
│   │   ├── TEXT
│   │   ├── RECTANGLE
│   │   └── INSTANCE (component instance)
│   ├── GROUP
│   │   └── VECTOR
│   ├── COMPONENT (reusable master)
│   └── SECTION
```

Key node types: `DOCUMENT`, `CANVAS`, `FRAME`, `GROUP`, `RECTANGLE`, `ELLIPSE`, `TEXT`, `VECTOR`, `COMPONENT`, `COMPONENT_SET`, `INSTANCE`, `LINE`, `SECTION`, `BOOLEAN_OPERATION`.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
