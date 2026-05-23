# Advanced Techniques

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
