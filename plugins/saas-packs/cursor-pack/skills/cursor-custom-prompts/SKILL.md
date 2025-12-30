---
name: cursor-custom-prompts
description: |
  Create effective custom prompts for Cursor AI. Triggers on "cursor prompts",
  "prompt engineering cursor", "better cursor prompts", "cursor instructions".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Custom Prompts for Cursor

## Prompt Engineering Fundamentals

### Effective Prompt Structure
```
[CONTEXT] What you're working on
[TASK] What you want to accomplish
[CONSTRAINTS] Requirements and limitations
[FORMAT] How you want the output
[EXAMPLES] Reference patterns if needed
```

### Example Well-Structured Prompt
```
CONTEXT: Working on a Next.js 14 e-commerce app with TypeScript

TASK: Create a shopping cart hook that:
- Manages cart items in localStorage
- Syncs with server when user logs in
- Handles quantity updates
- Calculates totals with tax

CONSTRAINTS:
- Use Zustand for state management
- Follow existing patterns in @hooks/useAuth.ts
- Handle offline scenarios gracefully
- TypeScript strict mode

FORMAT:
- Single useCart.ts file
- Export named hook and types
- Include JSDoc comments
```

## Prompt Templates

### Code Generation
```
Template:
"Create [COMPONENT_TYPE] for [PURPOSE]:

Requirements:
- [Requirement 1]
- [Requirement 2]

Technology:
- [Framework/Library]
- [Styling approach]

Follow patterns from @[reference-file]

Include:
- TypeScript types
- Error handling
- Tests (optional)"
```

### Code Review
```
Template:
"Review this code for:
- [ ] Security vulnerabilities
- [ ] Performance issues
- [ ] Best practice violations
- [ ] Missing error handling
- [ ] Type safety problems

Suggest specific improvements with code examples."
```

### Debugging
```
Template:
"Debug this issue:

ERROR: [exact error message]

EXPECTED: [what should happen]

ACTUAL: [what actually happens]

RELEVANT CODE:
[code snippet]

What I've tried:
- [attempt 1]
- [attempt 2]"
```

### Refactoring
```
Template:
"Refactor [CODE/FILE] to:
- [Goal 1]
- [Goal 2]

Preserve:
- [What must not change]
- [Behavior to maintain]

Apply patterns from:
- @[reference-file]"
```

## Domain-Specific Prompts

### API Development
```
"Create REST endpoint for [resource]:

Method: [GET/POST/PUT/DELETE]
Path: /api/[path]

Request:
- Body: [schema]
- Params: [params]
- Query: [query params]

Response:
- Success: [schema]
- Errors: [error codes]

Include:
- Input validation (Zod)
- Error handling
- TypeScript types
- Rate limiting (optional)"
```

### React Components
```
"Create React component [Name]:

Purpose: [what it does]

Props:
- [prop1]: [type] - [description]
- [prop2]: [type] - [description]

State:
- [what state it manages]

Behavior:
- [interaction 1]
- [interaction 2]

Styling: Tailwind CSS
Accessibility: WCAG 2.1 AA"
```

### Database Operations
```
"Create database [operation] for [entity]:

ORM: Prisma
Operation: [CRUD type]

Schema context:
@prisma/schema.prisma

Requirements:
- [Requirement 1]
- [Requirement 2]

Return:
- [What to return]

Handle:
- Not found
- Validation errors
- Database errors"
```

## Advanced Techniques

### Chain-of-Thought Prompting
```
"Let's approach this step by step:

1. First, analyze the current code structure
2. Identify what needs to change
3. Plan the refactoring steps
4. Implement each step
5. Verify the changes

Start by analyzing @[file]"
```

### Few-Shot Learning
```
"Following this pattern:

Example 1:
Input: User model
Output: [show expected code]

Example 2:
Input: Product model
Output: [show expected code]

Now create for:
Input: Order model"
```

### Role-Based Prompting
```
"Acting as a senior security engineer:

Review this authentication code for vulnerabilities:
@auth/login.ts

Focus on:
- Injection attacks
- Session handling
- Password security
- Token management"
```

### Constraint Prompting
```
"Create a solution that:

MUST:
- Use existing types from @types/
- Follow error handling patterns
- Be fully typed

MUST NOT:
- Use any external libraries
- Modify existing interfaces
- Use 'any' type

SHOULD:
- Be performant for large datasets
- Include comprehensive comments"
```

## Prompt Library

### Quick Actions
```
Explain: "Explain what this code does in plain English"
Simplify: "Simplify this code while maintaining functionality"
Optimize: "Optimize this for performance"
Document: "Add comprehensive JSDoc comments"
Type: "Add TypeScript types to this JavaScript code"
Test: "Write unit tests for this function"
```

### Transformations
```
"Convert this to TypeScript with strict types"
"Refactor to use async/await instead of callbacks"
"Extract this into a reusable hook"
"Convert class component to functional"
"Split this file into smaller modules"
```

### Analysis
```
"What are potential bugs in this code?"
"How can this be more maintainable?"
"What edge cases are not handled?"
"Are there any security concerns?"
"What would break if [scenario]?"
```

## .cursorrules Integration

### Embedding Prompts
```yaml
# .cursorrules

prompts:
  component:
    template: |
      Create React component following:
      - Functional component with TypeScript
      - Tailwind for styling
      - Handle loading/error states
      - Include prop types interface

  api:
    template: |
      Create API route following:
      - Zod validation
      - Proper error responses
      - TypeScript types
      - Logging included
```

### Prompt Aliases
```yaml
shortcuts:
  /component: "Create a new React component..."
  /api: "Create a new API endpoint..."
  /test: "Write tests for..."
  /review: "Review code for issues..."
```

## Best Practices

### Do's
```
DO:
- Be specific about requirements
- Provide context with @-mentions
- Include examples when helpful
- Specify constraints clearly
- Break complex tasks into steps
- Reference existing patterns
```

### Don'ts
```
DON'T:
- Be vague ("make it better")
- Assume context is understood
- Ask for too much at once
- Ignore generated code review
- Use ambiguous terms
- Skip error case requirements
```

### Iteration
```
Prompt refinement cycle:

1. Initial prompt
2. Review output
3. Identify gaps
4. Refine prompt
5. Regenerate
6. Repeat until satisfied

Track effective prompts for reuse
```
