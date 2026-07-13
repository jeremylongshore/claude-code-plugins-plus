# Project Configuration

## Project Configuration

### .cursorrules Setup

```
[ ] .cursorrules file created
[ ] Coding standards defined
[ ] Framework-specific rules added
[ ] Team conventions documented
[ ] Examples included for complex patterns
```

### Sample .cursorrules

```yaml
# .cursorrules
project: my-app
language: typescript
framework: nextjs

rules:
  - Use TypeScript strict mode
  - Prefer functional components
  - Use Tailwind for styling
  - Write tests for all business logic
  - Use async/await over callbacks
  - Handle all error cases explicitly

naming:
  components: PascalCase
  functions: camelCase
  constants: SCREAMING_SNAKE_CASE
  files: kebab-case

imports:
  order:
    - react
    - next
    - third-party
    - @/components
    - @/lib
    - relative

testing:
  framework: vitest
  coverage: 80%
```

### Indexing Configuration

```
[ ] .cursorignore configured
[ ] Large directories excluded
[ ] Build outputs excluded
[ ] Indexing completed successfully
[ ] @codebase queries working
```
