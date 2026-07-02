# Variant A: CLI Script (Simplest)

Deep-dive reference for the `figma-architecture-variants` skill — extracted from the 'Variant A: CLI Script (Simplest)' step of the workflow.

**Use case:** Extract design tokens, export icons, sync to code

```
Developer runs script
        │
        ▼
  ┌─────────────┐
  │ CLI Script   │  (Node.js)
  │ - extract.ts │
  └──────┬───────┘
         │ GET /v1/files/:key
         │ GET /v1/images/:key
         ▼
  ┌─────────────┐
  │ Figma REST  │
  │ API         │
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │ Output      │
  │ - tokens.css│
  │ - icons/    │
  └─────────────┘
```

```json
{
  "scripts": {
    "figma:tokens": "tsx scripts/extract-tokens.ts",
    "figma:icons": "tsx scripts/export-icons.ts",
    "figma:sync": "npm run figma:tokens && npm run figma:icons"
  }
}
```

**Pros:** Zero infrastructure, runs in CI, easy to debug
**Cons:** Not real-time, manual trigger, no webhook support

---

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
