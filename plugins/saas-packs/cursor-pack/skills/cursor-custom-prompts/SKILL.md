---
name: "cursor-custom-prompts"
description: |
  Create effective custom prompts for Cursor AI using project rules, prompt engineering patterns, and
  reusable templates. Triggers on "cursor prompts", "prompt engineering cursor", "better cursor prompts",
  "cursor instructions", "cursor prompt templates".
allowed-tools: "Read, Write, Edit, Bash(cmd:*)"
version: 1.0.0
license: MIT
author: "Jeremy Longshore <jeremy@intentsolutions.io>"
compatible-with: claude-code, codex, openclaw
tags: [saas, cursor, cursor-custom]

---
# Cursor Custom Prompts

Create effective prompts for Cursor AI. Covers prompt engineering fundamentals, reusable templates stored in project rules, and advanced techniques for consistent, high-quality code generation.

## Prompt Anatomy

A well-structured Cursor prompt has four parts:

```
1. CONTEXT   → @-mentions pointing to relevant code
2. TASK      → What you want done (specific, actionable)
3. CONSTRAINTS → Rules, patterns, limitations
4. FORMAT    → How the output should look
```

### Example: All Four Parts

```
@src/api/users/route.ts @src/types/user.ts         ← CONTEXT

Create a new API endpoint for updating user profiles. ← TASK

Constraints:                                         ← CONSTRAINTS
- Follow the same pattern as the users route
- Use Zod for input validation
- Return 400 for invalid input, 404 for missing user
- Only allow updating: name, email, avatarUrl

Return the endpoint code and the Zod schema as       ← FORMAT
separate code blocks.
```

## Prompt Templates

### Template: Feature Implementation

```
@[existing-similar-feature] @[relevant-types]

Implement [feature name] following the pattern in [reference file].

Requirements:
- [requirement 1]
- [requirement 2]
- [requirement 3]

Constraints:
- Same error handling pattern as [reference]
- Same file structure as [reference]
- Include TypeScript types for all public interfaces
```

### Template: Bug Fix

```
@[buggy-file] @Lint Errors

Bug: [describe the incorrect behavior]
Expected: [describe correct behavior]
Steps to reproduce: [1, 2, 3]

The error message is: [paste error]

Find the root cause and suggest a fix. Do not change
the public API surface.
```

### Template: Code Review

```
@[file-to-review]

Review this code for:
1. Logic errors or edge cases
2. Security vulnerabilities (injection, XSS, auth bypass)
3. Performance issues (N+1 queries, unnecessary re-renders)
4. TypeScript type safety (any casts, missing generics)
5. Naming and readability

List issues as: [severity] [line/area] [description] [suggestion]
```

### Template: Test Generation

```
@[source-file] @[existing-test-file]

Generate tests for [function/class name] covering:
- Happy path with valid inputs
- Edge cases: empty input, null, undefined, max values
- Error cases: invalid input, missing required fields
- Async behavior: success and failure scenarios

Follow the same test structure as [existing-test-file].
Use [vitest/jest/pytest] assertions.
```

### Template: Refactoring

```
@[file-to-refactor]

Refactor this code to [goal]:
- [specific change 1]
- [specific change 2]

Do NOT change:
- The public API (function signatures, return types)
- The test behavior (existing tests must still pass)
- External imports
```

## Storing Prompts as Project Rules

Convert frequently used prompts into `.cursor/rules/` for automatic injection:

```yaml
# .cursor/rules/code-generation.mdc
---
description: "Standards for AI-generated code"
globs: ""
alwaysApply: true
---
When generating code, always:
1. Add JSDoc comments on all exported functions
2. Include error handling (never let functions throw unhandled)
3. Use named exports (never default exports)
4. Add `import type` for type-only imports
5. Prefer const arrow functions for pure utilities
6. Use discriminated unions over boolean flags

When generating TypeScript:
- Strict mode: no `any`, no `as` casts without justification
- Prefer `unknown` over `any` for unknown types
- Use `satisfies` operator for type narrowing
- Infer types where TypeScript can; annotate where it cannot
```

```yaml
# .cursor/rules/test-patterns.mdc
---
description: "Test generation standards"
globs: "**/*.test.ts,**/*.spec.ts"
alwaysApply: false
---
When generating tests:
- Use describe/it blocks with readable descriptions
- Arrange/Act/Assert pattern (AAA)
- One assertion per test (prefer multiple focused tests)
- Mock external dependencies, not internal utilities
- Use factory functions for test data (not inline objects)
- Name test files: {module}.test.ts colocated with source
```

## Advanced Prompting Techniques

### Chain of Thought

Force the AI to reason before generating:

```
@src/services/billing.service.ts

I need to add proration logic for subscription upgrades.

Before writing code, first:
1. List the variables involved (current plan, new plan, billing cycle)
2. Show the proration formula with a concrete example
3. Identify edge cases (upgrade on last day, downgrade, free trial)

Then implement based on your analysis.
```

### Few-Shot Examples

Provide examples of what you want:

```
Convert these function signatures to the Result pattern:

Example input:
  async function getUser(id: string): Promise<User>

Example output:
  async function getUser(id: string): Promise<Result<User, NotFoundError>>

Now convert these:
- async function createOrder(input: CreateOrderInput): Promise<Order>
- async function deleteAccount(userId: string): Promise<void>
- async function sendEmail(to: string, body: string): Promise<boolean>
```

### Negative Constraints

Tell the AI what NOT to do:

```
Create a React form component for user registration.

DO NOT:
- Use class components
- Use any CSS-in-JS library
- Add client-side validation (server validates)
- Use controlled inputs for every field (use react-hook-form)
- Import anything not already in package.json
```

### Iterative Refinement

Build up complexity in steps:

```
Turn 1: "Create a basic Express route for GET /api/products"
Turn 2: "Add pagination with page and limit query params"
Turn 3: "Add filtering by category and price range"
Turn 4: "Add sorting by any field with asc/desc direction"
Turn 5: "Add input validation and comprehensive error responses"
```

Each turn adds one layer. The AI maintains context from previous turns.

## Common Prompt Anti-Patterns

| Anti-Pattern | Problem | Better Approach |
|-------------|---------|-----------------|
| "Make it better" | Too vague | "Add error handling for network failures" |
| "Rewrite everything" | Scope too large | "Refactor the validation logic in lines 40-80" |
| No context files | AI guesses patterns | Always add @Files references |
| Wall of text prompt | AI misses key points | Use numbered lists and headers |
| "Do what you think is best" | AI makes assumptions | Specify requirements explicitly |

## Enterprise Considerations

- **Prompt libraries**: Maintain a team-shared library of effective prompts in a wiki or docs/ directory
- **Standardization**: Use `.cursor/rules/` to encode team prompt standards so all developers get consistent behavior
- **Security**: Never include real credentials, PII, or regulated data in prompts
- **Reproducibility**: Document effective prompts alongside their output for knowledge sharing

## Resources

- [Cursor Rules Documentation](https://docs.cursor.com/context/rules)
- [@ Symbols Overview](https://docs.cursor.com/context/@-symbols/overview)
- [Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
