---
name: anima-reference-architecture
description: |
  Implement reference architecture for Anima design-to-code automation.
  Use when designing a design system automation pipeline, structuring
  a Figma-to-React project, or planning team-scale design handoff.
  Trigger: "anima architecture", "design-to-code architecture",
  "anima project structure", "figma automation architecture".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, figma, anima, architecture]
compatible-with: claude-code
---

# Anima Reference Architecture

## System Architecture

```
┌────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Figma Design  │────▶│ Figma API    │────▶│ Anima SDK       │
│  (Components)  │     │ (Webhooks)   │     │ (Code Gen)      │
└────────────────┘     └──────────────┘     └────────┬────────┘
                                                      │
                                            ┌─────────▼────────┐
                                            │ Post-Processing   │
                                            │ - Token mapping   │
                                            │ - Normalization   │
                                            │ - Lint/format     │
                                            └─────────┬────────┘
                                                      │
                                            ┌─────────▼────────┐
                                            │ Output            │
                                            │ - React/Vue/HTML  │
                                            │ - PR creation     │
                                            │ - Storybook sync  │
                                            └──────────────────┘
```

## Project Structure

```
design-to-code/
├── src/
│   ├── anima/
│   │   ├── client.ts              # Singleton SDK client
│   │   ├── cache.ts               # Generation cache
│   │   ├── retry.ts               # Error recovery
│   │   └── presets.ts             # Framework/styling presets
│   ├── pipeline/
│   │   ├── scanner.ts             # Figma component discovery
│   │   ├── generator.ts           # Batch code generation
│   │   ├── change-detector.ts     # Figma version tracking
│   │   └── runner.ts              # Pipeline orchestrator
│   ├── post-process/
│   │   ├── normalizer.ts          # Output normalization
│   │   ├── token-mapper.ts        # Design token mapping
│   │   └── organizer.ts           # File organization + barrel exports
│   ├── webhooks/
│   │   └── figma-handler.ts       # Figma webhook receiver
│   └── server.ts                  # Express API (optional)
├── scripts/
│   ├── generate-components.ts     # CLI generation script
│   └── compare-presets.ts         # Side-by-side preset comparison
├── fixtures/
│   └── component-map.json         # Figma node ID → component name mapping
├── generated/                     # Output directory (gitignored or committed)
├── .anima-cache/                  # Generation cache (gitignored)
└── package.json
```

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| SDK | `@animaapp/anima-sdk` | Official, server-side, typed |
| Change detection | Figma Webhooks v2 | Event-driven, no polling waste |
| Caching | File-based with MD5 keys | Simple, no external dependencies |
| Post-processing | Custom normalizer | Match project conventions |
| CI integration | GitHub Actions scheduled | Avoid real-time generation costs |
| Output framework | React + Tailwind + shadcn | Most production-ready output |

## Output

- Complete design-to-code pipeline architecture
- Project structure with all components
- Design decision rationale documented

## Resources

- [Anima API](https://docs.animaapp.com/docs/anima-api)
- [Anima SDK GitHub](https://github.com/AnimaApp/anima-sdk)
- [Figma Webhooks](https://www.figma.com/developers/api#webhooks-v2)
- [Anima Figma Plugin](https://www.figma.com/community/plugin/857346721138427857)

## Next Steps

Start with `anima-install-auth`, then follow skills through production deployment.
