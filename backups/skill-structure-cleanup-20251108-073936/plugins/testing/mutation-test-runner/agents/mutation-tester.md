---
description: Validate test quality through mutation testing
capabilities: ["mutation-testing", "test-effectiveness", "code-mutations", "survivor-analysis"]
---

# Mutation Test Runner Agent

Validate test suite quality by introducing code mutations and verifying tests catch them.

## Mutation Testing Concept

Mutation testing modifies ("mutates") code to check if tests detect the changes:
- **Mutant killed**  - Test failed (good, caught the bug)
- **Mutant survived**  - Test passed (bad, missed the bug)

## Common Mutations

1. **Arithmetic Operators** - `+` to `-`, `*` to `/`
2. **Comparison Operators** - `>` to `>=`, `==` to `!=`
3. **Logical Operators** - `&&` to `||`, `!` removal
4. **Boolean Literals** - `true` to `false`
5. **Return Values** - Change return values
6. **Conditionals** - Remove if statements
7. **Increments** - `++` to `--`

## Example

```javascript
// Original code
function isPositive(num) {
  return num > 0;
}

// Mutation 1: Change > to >=
function isPositive(num) {
  return num >= 0;  // Should fail test for isPositive(0)
}

// Mutation 2: Change > to <
function isPositive(num) {
  return num < 0;  // Should fail all tests
}
```

## Mutation Testing Tools

- **JavaScript**: Stryker Mutator
- **Python**: mutmut, cosmic-ray
- **Java**: PITest
- **C#**: Stryker.NET
- **Ruby**: Mutant

## Report Format

```
Mutation Testing Report
=======================
Total Mutants: 150
Killed: 142 (94.7%) 
Survived: 8 (5.3%) 
Timeout: 0
No Coverage: 0

Mutation Score: 94.7%

Survived Mutants:
  src/utils/validator.js:23
    - Replaced > with >= 
    - Suggests missing boundary test

  src/api/users.js:45
    - Replaced && with ||
    - Suggests missing logic test

Recommendations:
  1. Add boundary test for validator edge case
  2. Test logical conditions in user API
  3. Overall test quality: Excellent (>90%)
```

## Best Practices

- Run after achieving high code coverage
- Focus on survived mutants
- Add tests to kill survivors
- Aim for 80%+ mutation score
- Expensive operation - run periodically
