# Configuration File Architecture

## Configuration File Architecture

### Essential Cursor Files

```
project/
├── .cursorrules              # Project-specific AI rules
├── .cursorignore             # Files to exclude from indexing
├── .vscode/
│   ├── settings.json         # Cursor/VS Code settings
│   ├── extensions.json       # Recommended extensions
│   └── launch.json           # Debug configurations
└── cursor.config.json        # Team cursor configuration (optional)
```

### .cursorrules Template

```yaml
# .cursorrules

project: my-app
version: 1.0.0
team: engineering

# Technology Stack
stack:
  language: typescript
  runtime: node
  framework: nextjs
  database: postgresql
  orm: prisma
  styling: tailwindcss
  testing: vitest

# Coding Standards
standards:
  style-guide: airbnb
  formatting: prettier
  linting: eslint

# AI Rules
rules:
  general:
    - Always use TypeScript with strict mode
    - Prefer functional programming patterns
    - Write self-documenting code with clear names
    - Maximum file length: 300 lines

  components:
    - Use functional components only
    - Implement proper prop types
    - Handle loading/error states
    - Extract logic to custom hooks

  testing:
    - Write tests for business logic
    - Use testing-library patterns
    - Mock external dependencies
    - Aim for 80% coverage

# File Patterns
patterns:
  components: "PascalCase.tsx"
  hooks: "use{Name}.ts"
  services: "{name}Service.ts"
  types: "{name}.types.ts"
  tests: "{name}.test.ts"

# Common Imports
imports:
  "@/components": "src/components"
  "@/hooks": "src/hooks"
  "@/lib": "src/lib"
  "@/types": "src/types"
```
