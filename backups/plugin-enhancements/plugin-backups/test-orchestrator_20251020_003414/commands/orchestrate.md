---
description: Orchestrate complex test workflows with smart execution
shortcut: orch
---

# Test Orchestrator

Orchestrate complex test execution workflows with dependency management, parallel execution, smart test selection, and optimized CI/CD integration.

## What You Do

1. **Test Workflow Design**: Create test execution graphs with dependencies
2. **Parallel Execution**: Identify and run independent tests in parallel
3. **Smart Selection**: Run only affected tests based on code changes
4. **Dependency Management**: Ensure tests run in correct order
5. **Resource Optimization**: Balance test execution across available resources

## Output Example

```javascript
// test-orchestration.config.js
module.exports = {
  stages: [
    {
      name: 'unit-tests',
      parallel: true,
      tests: ['**/*.unit.test.js'],
      maxWorkers: 4
    },
    {
      name: 'integration-tests',
      dependsOn: ['unit-tests'],
      parallel: true,
      tests: ['**/*.integration.test.js'],
      maxWorkers: 2
    },
    {
      name: 'e2e-tests',
      dependsOn: ['integration-tests'],
      parallel: false,
      tests: ['**/*.e2e.test.js']
    }
  ],

  smartSelection: {
    enabled: true,
    algorithm: 'affected-files',
    fallback: 'all-tests'
  },

  retries: {
    flaky: 2,
    timeout: 1
  }
};
```

```bash
# Smart test selection based on changed files
$ test-orchestrator run --changed

Analyzing changes...
  Modified files: 3
  Affected tests: 47 (4% of total)

Executing test plan:
  Stage 1: Unit Tests (32 tests, parallel)
     Completed in 12s
  Stage 2: Integration Tests (12 tests, parallel)
     Completed in 28s
  Stage 3: E2E Tests (3 tests, sequential)
     Completed in 45s

Total: 47 tests in 85s (instead of 18m for full suite)
```
