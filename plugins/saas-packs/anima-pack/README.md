# Anima Skill Pack

> Claude Code skills for Anima design-to-code automation — Figma to React/Vue/HTML with Tailwind, MUI, shadcn (18 skills)

Anima converts Figma designs into production-ready code using AI-powered code generation. These skills use the real `@animaapp/anima-sdk` npm package with the `generateCode` API supporting React, Vue, HTML, TypeScript, Tailwind, MUI, AntD, and shadcn output.

## Installation

```bash
/plugin install anima-pack@claude-code-plugins-plus
```

## Skills Included

### Standard Skills (S01-S12)

| Skill | What It Does |
|-------|-------------|
| `anima-install-auth` | Install `@animaapp/anima-sdk`, configure Anima + Figma tokens |
| `anima-hello-world` | Generate React/Vue/HTML from Figma with all framework presets |
| `anima-local-dev-loop` | Multi-preset comparison, Vite preview, iterative generation |
| `anima-sdk-patterns` | Singleton client, generation cache, output normalizer, retry |
| `anima-core-workflow-a` | Automated Figma-to-React pipeline with component scanning |
| `anima-core-workflow-b` | Website-to-code cloning, design token mapping, post-processing |
| `anima-common-errors` | Diagnose auth, node, generation, and output quality errors |
| `anima-debug-bundle` | Diagnostic bundle with SDK version and Figma access status |
| `anima-rate-limits` | Bottleneck throttler (10 gen/min), batch generator, 429 retry |
| `anima-security-basics` | Token scope restriction, server-side enforcement, secret manager |
| `anima-prod-checklist` | Production readiness validation for design-to-code pipelines |
| `anima-upgrade-migration` | SDK upgrades, manual plugin to automated SDK migration |

### Pro Skills (P13-P18)

| Skill | What It Does |
|-------|-------------|
| `anima-ci-integration` | GitHub Actions scheduled design sync with auto-PR creation |
| `anima-deploy-integration` | Deploy SDK as Express/Vercel/Cloud Run service |
| `anima-webhooks-events` | Figma Webhooks v2 triggering auto-generation on design change |
| `anima-performance-tuning` | File-based cache, incremental generation, output optimization |
| `anima-cost-tuning` | Usage tracking, smart generation policy, cache hit reporting |
| `anima-reference-architecture` | Full design-to-code pipeline architecture with project structure |

## Key Concepts

- **Real SDK** — All code uses `@animaapp/anima-sdk` (`import { Anima } from '@animaapp/anima-sdk'`)
- **Server-side only** — SDK runs on backend; never ship tokens to browser
- **Figma API integration** — Uses Figma Personal Access Tokens and Webhooks v2
- **Framework support** — React, Vue, HTML with Tailwind, CSS, MUI, AntD, shadcn

## License

MIT
