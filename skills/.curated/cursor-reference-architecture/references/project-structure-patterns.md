# Project Structure Patterns

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
