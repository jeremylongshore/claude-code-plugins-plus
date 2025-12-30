---
name: cursor-reference-architecture
description: |
  Reference architecture patterns for Cursor IDE projects. Triggers on "cursor architecture",
  "cursor project structure", "cursor best practices", "cursor team setup".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Reference Architecture

## Project Structure Patterns

### Feature-Based Architecture
```
project/
├── .cursorrules              # AI behavior configuration
├── .cursorignore             # Indexing exclusions
├── src/
│   ├── features/
│   │   ├── auth/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── api/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   ├── products/
│   │   └── orders/
│   ├── shared/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── utils/
│   │   └── types/
│   └── lib/
│       ├── api-client/
│       └── config/
├── tests/
└── docs/
```

### Layer-Based Architecture
```
project/
├── .cursorrules
├── src/
│   ├── presentation/         # UI Layer
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   ├── application/          # Business Logic
│   │   ├── services/
│   │   ├── use-cases/
│   │   └── dto/
│   ├── domain/               # Core Domain
│   │   ├── entities/
│   │   ├── repositories/
│   │   └── value-objects/
│   └── infrastructure/       # External Concerns
│       ├── api/
│       ├── database/
│       └── external-services/
└── tests/
```

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

## Team Configuration

### Shared Settings
```json
// .vscode/settings.json (committed)
{
  // Cursor AI Settings
  "cursor.completion.enabled": true,
  "cursor.chat.defaultModel": "gpt-4-turbo",

  // Editor Settings
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },

  // File Associations
  "files.associations": {
    ".cursorrules": "yaml"
  },

  // Search Exclusions (mirrors .cursorignore)
  "search.exclude": {
    "**/node_modules": true,
    "**/dist": true,
    "**/.next": true
  }
}
```

### Recommended Extensions
```json
// .vscode/extensions.json
{
  "recommendations": [
    "esbenp.prettier-vscode",
    "dbaeumer.vscode-eslint",
    "prisma.prisma",
    "bradlc.vscode-tailwindcss",
    "eamodio.gitlens",
    "github.copilot"  // Optional, may conflict
  ],
  "unwantedRecommendations": [
    "visualstudioexptteam.vscodeintellicode"  // Conflicts with Cursor
  ]
}
```

## Workflow Architecture

### Development Workflow
```
┌─────────────────────────────────────────────────────────┐
│                   CURSOR WORKFLOW                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. PLAN (Chat)                                         │
│     └─ Discuss architecture with AI                     │
│     └─ Get recommendations                              │
│                                                          │
│  2. SCAFFOLD (Composer)                                 │
│     └─ Generate initial structure                       │
│     └─ Create boilerplate files                         │
│                                                          │
│  3. IMPLEMENT (Tab Completion)                          │
│     └─ Code with AI suggestions                         │
│     └─ Auto-complete patterns                           │
│                                                          │
│  4. REFINE (Inline Edit)                               │
│     └─ Quick improvements                               │
│     └─ Bug fixes                                        │
│                                                          │
│  5. REVIEW (Chat)                                       │
│     └─ Code review assistance                           │
│     └─ Security check                                   │
│                                                          │
│  6. TEST (Composer)                                     │
│     └─ Generate test files                              │
│     └─ Coverage improvements                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### CI/CD Integration
```yaml
# Cursor-aware CI/CD considerations

# Pre-commit checks
pre-commit:
  - lint
  - typecheck
  - test
  - format-check

# PR requirements
pull-request:
  - All checks pass
  - Tests for new code
  - Documentation updated
  - No console.logs
  - No hardcoded secrets
```

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

## Security Architecture

### Sensitive File Handling
```gitignore
# .cursorignore - security focused

# Environment files
.env*
!.env.example

# Credentials
*.pem
*.key
*.p12
credentials/
secrets/

# Config with secrets
config/production.json
config/local.json
```

### Privacy Mode Strategy
```
Production code: Privacy mode OFF (full AI features)
Sensitive files: Privacy mode ON or excluded

Toggle per workspace:
Settings > Cursor > Privacy Mode
```

## Documentation Architecture

### AI-Friendly Documentation
```
docs/
├── README.md                 # Project overview
├── ARCHITECTURE.md           # System design
├── CONTRIBUTING.md           # How to contribute
├── API.md                    # API documentation
└── decisions/
    ├── 001-framework.md      # ADR: Framework choice
    └── 002-database.md       # ADR: Database choice
```

### In-Code Documentation
```typescript
/**
 * @cursor-context Authentication service for JWT-based auth
 * @cursor-related @lib/jwt.ts @middleware/auth.ts
 * @cursor-patterns Handle refresh tokens, httpOnly cookies
 */
export class AuthService {
  // Implementation
}
```
