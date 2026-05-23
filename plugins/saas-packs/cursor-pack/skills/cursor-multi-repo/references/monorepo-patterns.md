# Monorepo Patterns

## Monorepo Patterns

### Common Structures

```
# Turborepo/Nx style
monorepo/
├── .cursorrules              # Root rules
├── apps/
│   ├── web/
│   │   ├── .cursorrules      # Web-specific
│   │   └── src/
│   └── api/
│       ├── .cursorrules      # API-specific
│       └── src/
├── packages/
│   ├── ui/
│   ├── shared/
│   └── config/
└── turbo.json
```

### Monorepo .cursorrules

```yaml
# Root .cursorrules

type: monorepo
tool: turborepo

packages:
  apps/web:
    framework: nextjs
    styling: tailwindcss

  apps/api:
    framework: fastify
    database: postgresql

  packages/ui:
    type: component-library
    framework: react

  packages/shared:
    type: shared-library

conventions:
  - Import shared code through package names
  - Types defined in packages/shared
  - UI components from packages/ui
  - Config from packages/config

build:
  - Use turbo for builds
  - Cache artifacts
  - Parallel where possible
```

### Working in Monorepo

```
Tips:

1. Open specific package when focused:
   cursor apps/web

2. Open root for cross-package work:
   cursor .

3. Use @-mentions with full paths:
   @packages/shared/types/user.ts

4. Index only active packages:
   Aggressive .cursorignore
```
