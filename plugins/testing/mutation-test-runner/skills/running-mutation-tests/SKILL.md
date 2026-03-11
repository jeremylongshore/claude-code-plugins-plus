---
name: running-mutation-tests
description: |
  Execute mutation testing to evaluate test suite effectiveness.
  Use when performing specialized testing.
  Trigger with phrases like "run mutation tests", "test the tests", or "validate test effectiveness".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:mutation-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Mutation Test Runner

## Overview

Execute mutation testing to evaluate the effectiveness of a test suite by systematically introducing small code changes (mutants) and checking whether existing tests detect them. A killed mutant means the tests caught the change; a surviving mutant reveals a testing gap.

## Prerequisites

- Mutation testing framework installed (Stryker, mutmut, PITest, or go-mutesting)
- Existing test suite with reasonable pass rate (all tests must pass before mutation testing)
- Source code with functions and logic suitable for mutation (conditionals, arithmetic, return values)
- Sufficient CI resources (mutation testing runs the test suite once per mutant -- CPU-intensive)
- Configuration file for the mutation tool specifying target files and test commands

## Instructions

1. Verify the existing test suite passes completely:
   - Run the full test suite and confirm 100% pass rate.
   - Fix any failing or skipped tests before proceeding.
   - Mutation testing is meaningless if the baseline tests are broken.
2. Configure the mutation testing tool:
   - Stryker: Create `stryker.config.mjs` with `mutate` patterns, test runner, and thresholds.
   - mutmut: Configure `setup.cfg` or `pyproject.toml` with `[mutmut]` section.
   - PITest: Add Maven/Gradle plugin with target classes and test configurations.
3. Select target files for mutation:
   - Focus on business logic modules (not configuration, constants, or type definitions).
   - Exclude auto-generated code, third-party wrappers, and test utilities.
   - Start with a small scope (one module) to validate setup before expanding.
4. Run the mutation testing suite:
   - Execute `npx stryker run`, `mutmut run`, or `mvn pitest:mutationCoverage`.
   - Monitor progress -- expect long execution times (10-100x normal test runtime).
   - Use incremental mode if available to skip already-tested mutants.
5. Analyze the mutation report:
   - **Killed mutants**: Tests detected the change -- indicates strong test coverage.
   - **Survived mutants**: Tests did not catch the change -- indicates a testing gap.
   - **Timed out mutants**: Mutation caused an infinite loop -- generally acceptable.
   - **No coverage mutants**: The mutated code is not exercised by any test.
6. For each surviving mutant, determine the appropriate action:
   - Write a new test that specifically catches the mutation.
   - Or determine the mutation is equivalent (functionally identical to original) and mark as ignored.
7. Set mutation score thresholds (recommended: 80% kill rate) and integrate into CI as a quality gate.

## Output

- Mutation testing report (HTML or JSON) with killed/survived/timed-out counts
- Mutation score percentage (killed / total non-equivalent mutants)
- Surviving mutant inventory with file, line, mutation type, and suggested test
- New test cases written to kill surviving mutants
- CI configuration with mutation score threshold enforcement

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Mutation run takes hours | Too many files in scope or slow test suite | Narrow `mutate` scope to critical modules; use `--incremental` mode; parallelize with `--concurrency` |
| All mutants survive | Tests only check for truthiness, not specific values | Strengthen assertions -- use `toBe(42)` instead of `toBeTruthy()`; add boundary checks |
| Equivalent mutant false positive | Mutation produces functionally identical code (e.g., `x >= 0` vs `x > -1`) | Mark as equivalent in config; ignore in score calculation; document rationale |
| Out of memory during run | Too many concurrent mutation workers | Reduce `--concurrency` setting; increase Node.js `--max-old-space-size`; reduce shard size |
| Stryker "initial test run failed" | Test suite does not pass cleanly before mutations begin | Fix all failing tests first; ensure `npm test` exits 0; check test runner configuration |

## Examples

**Stryker configuration for TypeScript project:**
```javascript
// stryker.config.mjs
export default {
  mutate: ['src/**/*.ts', '!src/**/*.d.ts', '!src/**/index.ts'],
  testRunner: 'jest',
  jest: { configFile: 'jest.config.ts' },
  reporters: ['html', 'clear-text', 'progress'],
  thresholds: { high: 80, low: 60, break: 50 },
  concurrency: 4,
  timeoutMS: 10000,  # 10000: 10 seconds in ms
};
```

**Example surviving mutant and fix:**
```
Mutant: src/utils/discount.ts:15 -- ConditionalExpression
  Original:  if (total > 100)
  Mutant:    if (total >= 100)
  Status:    SURVIVED

Fix -- add boundary test:
it('does not apply discount at exactly 100', () => {
  expect(calculateDiscount(100)).toBe(0);
});
it('applies discount above 100', () => {
  expect(calculateDiscount(101)).toBe(10.1);
});
```

**mutmut for Python:**
```bash
# Run mutation testing
mutmut run --paths-to-mutate=src/ --tests-dir=tests/

# View surviving mutants
mutmut results

# Inspect a specific mutant
mutmut show 42
```

## Resources

- Stryker Mutator: https://stryker-mutator.io/
- mutmut (Python): https://github.com/boxed/mutmut
- PITest (Java): https://pitest.org/
- go-mutesting: https://github.com/zimmski/go-mutesting
- Mutation testing theory: https://en.wikipedia.org/wiki/Mutation_testing