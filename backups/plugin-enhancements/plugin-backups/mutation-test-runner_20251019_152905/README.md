# Mutation Test Runner Plugin

Validate test suite effectiveness through mutation testing - introducing code changes and verifying tests catch them.

## Features

- **Mutation generation** - Arithmetic, logical, conditional mutations
- **Test validation** - Verify tests catch introduced bugs
- **Mutation score calculation** - Test quality metric
- **Survivor analysis** - Identify weak test coverage
- **Framework support** - Stryker, PITest, mutmut, Mutant

## Installation

```bash
/plugin install mutation-test-runner@claude-code-plugins-plus
```

## Usage

```
Run mutation testing on the validator module
Analyze mutation test results and suggest improvements
```

## Mutation Types

- **Arithmetic** - `+` → `-`, `*` → `/`
- **Comparison** - `>` → `>=`, `==` → `!=`
- **Logical** - `&&` → `||`, `!` removal
- **Boolean** - `true` → `false`
- **Conditionals** - Remove if statements

## License

MIT
