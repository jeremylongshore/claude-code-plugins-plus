# Monorepo Architecture

## Monorepo Architecture

### Turborepo Structure

```
monorepo/
├── .cursorrules              # Root rules (inherited)
├── .cursorignore             # Root exclusions
├── apps/
│   ├── web/
│   │   ├── .cursorrules      # App-specific overrides
│   │   └── src/
│   └── api/
│       ├── .cursorrules
│       └── src/
├── packages/
│   ├── ui/
│   │   ├── .cursorrules
│   │   └── src/
│   └── shared/
│       └── src/
└── turbo.json
```

### Workspace .cursorrules

```yaml
# Root .cursorrules for monorepo

project: my-monorepo
type: turborepo

workspaces:
  apps/web:
    framework: nextjs
    rules:
      - Use App Router
      - Server Components default

  apps/api:
    framework: express
    rules:
      - REST conventions
      - Validate all inputs

  packages/ui:
    type: component-library
    rules:
      - Headless components
      - Full accessibility
      - Storybook stories required
```
