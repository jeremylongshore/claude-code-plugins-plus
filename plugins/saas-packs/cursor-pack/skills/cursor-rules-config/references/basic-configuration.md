# Basic Configuration

## Basic Configuration

### Minimal Example

```yaml
# .cursorrules

# Project language and framework
language: typescript
framework: react

# Key coding rules
rules:
  - Use functional components
  - Prefer async/await over callbacks
  - Always handle errors explicitly
```

### Standard Template

```yaml
# .cursorrules

project: my-awesome-app
description: E-commerce platform built with Next.js

language: typescript
framework: nextjs
styling: tailwindcss
testing: vitest

rules:
  # Code Style
  - Use TypeScript strict mode
  - Prefer const over let
  - Use arrow functions for callbacks
  - Maximum line length: 100 characters

  # React Patterns
  - Use functional components only
  - Prefer hooks over HOCs
  - Use React Query for data fetching
  - Handle loading and error states

  # Architecture
  - Follow feature-based folder structure
  - Keep components under 200 lines
  - Extract business logic to hooks
  - Use dependency injection for services

naming:
  files: kebab-case
  components: PascalCase
  functions: camelCase
  constants: SCREAMING_SNAKE_CASE
  types: PascalCase with suffix (UserDTO, ProductResponse)

imports:
  order:
    - react, next (framework)
    - third-party packages
    - @/components
    - @/hooks
    - @/lib
    - @/types
    - relative imports
```
